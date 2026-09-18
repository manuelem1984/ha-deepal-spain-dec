"""MQTT client for Deepal Spain DEC."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import gzip
import json
import logging
import ssl
import struct
import time
from dataclasses import dataclass
from typing import Any

from .crypto import decrypt_mqtt_payload, encrypt_mqtt_payload
from .models import DeepalTelemetry
from .telemetry import parameters_to_telemetry


_LOGGER = logging.getLogger(__name__)

MQTT_CONNECTION_TIMEOUT = 15
MQTT_TELEMETRY_TIMEOUT = 18

# service_code values currently mapped into DeepalTelemetry.
# Anything outside this set is logged (at debug level) but discarded,
# so it's easy to spot new services the vehicle exposes.
KNOWN_SERVICE_CODES = {
    None,
    "car_condition",
    "BDC_Service",
    "BMS_Service",
    "OBC_Service",
    "THU_Service",
}

# Fields that already arrive from the vehicle (inside the known
# service codes) but are not yet mapped into DeepalTelemetry.
# Logged with their real values so the semantics (booleans, units,
# scales) can be confirmed before wiring up new entities.
CANDIDATE_KEYS = (
    "acChargeGunConnectionState",
    "dcChargeGunConnectionState",
    "chargeCoverStatus",
    "lfPressureWarning",
    "rfPressureWarning",
    "lrPressureWarning",
    "rrPressureWarning",
    "driverSeatHeatStatus",
    "passengerSeatHeatStatus",
    "driverSeatAirStatus",
    "passengerSeatAirStatus",
    "steeringWheelHeating",
    "airRecycleStatus",
    "frontDefrostStatus",
    "airPurifierStatus",
    "skyWindowDegree",
    "frontFoglamp",
    "rearFoglamp",
    "keyLowPower",
    "reverseRadarStatus",
    "batt12VLightStatus",
    "brakeFluidLightStatus",
    "tpmsLightStatus",
    "epbLightStatus",
    "absLightStatus",
    "airbagSystemStatus",
    "oilPressureLightStatus",
    "powerStatusFeedBack",
)


def log_telemetry_snapshot(parameters: dict[str, Any]) -> None:
    """Log received keys plus the raw values of unmapped candidates.

    Only runs the formatting work when debug logging is enabled.
    """
    if not _LOGGER.isEnabledFor(logging.DEBUG):
        return

    _LOGGER.debug(
        "Deepal MQTT: mapped keys received=%s",
        sorted(parameters.keys()),
    )

    candidates = {
        key: parameters[key]
        for key in CANDIDATE_KEYS
        if key in parameters
    }

    if candidates:
        _LOGGER.debug(
            "Deepal MQTT: candidate values=%s",
            json.dumps(candidates, ensure_ascii=False, sort_keys=True),
        )

    missing = sorted(set(CANDIDATE_KEYS) - set(parameters))
    if missing:
        _LOGGER.debug(
            "Deepal MQTT: candidates not present in this payload=%s",
            missing,
        )


@dataclass(slots=True)
class DeepalMqttConnection:
    """Normalized Deepal MQTT connection configuration."""

    host: str
    port: int
    subscribe_topics: list[str]
    login_publish_topic: str
    properties_publish_topic: str
    login_device_id: str
    vehicle_device_id: str


def mqtt_string(value: str) -> bytes:
    """Encode a string using the MQTT length-prefixed format."""
    encoded_value = value.encode()
    return struct.pack("!H", len(encoded_value)) + encoded_value


def mqtt_remaining_length(length: int) -> bytes:
    """Encode the MQTT remaining-length field."""
    output = bytearray()

    while True:
        encoded_byte = length % 128
        length //= 128

        if length:
            encoded_byte |= 128

        output.append(encoded_byte)

        if not length:
            return bytes(output)


def build_connect_packet(
    client_id: str,
    username: str,
    password: str,
) -> bytes:
    """Build an MQTT CONNECT packet."""
    payload = (
        mqtt_string(client_id)
        + mqtt_string(username)
        + mqtt_string(password)
    )

    variable_header = (
        mqtt_string("MQTT")
        + bytes([4, 0xC2])
        + struct.pack("!H", 60)
    )

    body = variable_header + payload

    return (
        bytes([0x10])
        + mqtt_remaining_length(len(body))
        + body
    )


def build_subscribe_packet(
    packet_id: int,
    topics: list[str],
) -> bytes:
    """Build an MQTT SUBSCRIBE packet."""
    payload = b"".join(
        mqtt_string(topic) + b"\x01"
        for topic in topics
    )

    body = struct.pack("!H", packet_id) + payload

    return (
        bytes([0x82])
        + mqtt_remaining_length(len(body))
        + body
    )


def build_publish_packet(
    topic: str,
    payload: dict[str, Any],
) -> bytes:
    """Build an MQTT PUBLISH packet."""
    encoded_payload = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()

    body = mqtt_string(topic) + encoded_payload

    return (
        bytes([0x30])
        + mqtt_remaining_length(len(body))
        + body
    )


def build_puback_packet(packet_id: int) -> bytes:
    """Build an MQTT PUBACK packet."""
    return (
        bytes([0x40, 0x02])
        + struct.pack("!H", packet_id)
    )


async def read_packet(
    reader: asyncio.StreamReader,
) -> tuple[int, bytes]:
    """Read a complete MQTT packet."""
    first_byte = (await reader.readexactly(1))[0]

    multiplier = 1
    remaining_length = 0

    while True:
        encoded_byte = (await reader.readexactly(1))[0]

        remaining_length += (
            encoded_byte & 0x7F
        ) * multiplier

        if not encoded_byte & 0x80:
            break

        multiplier *= 128

        if multiplier > 128 * 128 * 128:
            raise ValueError(
                "Malformed MQTT remaining length"
            )

    body = await reader.readexactly(remaining_length)

    return first_byte, body


def parse_publish_packet(
    first_byte: int,
    body: bytes,
) -> tuple[str, dict[str, Any], int | None]:
    """Parse an MQTT PUBLISH packet."""
    position = 0

    if len(body) < 2:
        raise ValueError(
            "MQTT PUBLISH packet is too short"
        )

    topic_length = struct.unpack(
        "!H",
        body[position : position + 2],
    )[0]

    position += 2

    if len(body) < position + topic_length:
        raise ValueError(
            "MQTT PUBLISH packet contains an invalid topic"
        )

    topic = body[
        position : position + topic_length
    ].decode(errors="replace")

    position += topic_length

    packet_id: int | None = None
    qos = (first_byte >> 1) & 0x03

    if qos:
        if len(body) < position + 2:
            raise ValueError(
                "MQTT PUBLISH packet has no packet identifier"
            )

        packet_id = struct.unpack(
            "!H",
            body[position : position + 2],
        )[0]

        position += 2

    decoded_payload = json.loads(
        body[position:].decode()
    )

    if not isinstance(decoded_payload, dict):
        raise ValueError(
            "MQTT PUBLISH payload is not a JSON object"
        )

    return topic, decoded_payload, packet_id


def extract_topic_did(topic: str) -> str | None:
    """Extract the device identifier from a Deepal MQTT topic."""
    parts = topic.split("/")

    if len(parts) > 2 and parts[0] == "$vdp":
        return parts[1]

    return None


def parse_connection_config(
    config: dict[str, Any],
) -> DeepalMqttConnection:
    """Extract broker and topic information from getConnConf."""
    connection_infos = config.get(
        "mqttConnectionInfos"
    ) or []

    if not connection_infos:
        raise ValueError(
            "MQTT configuration does not contain "
            "connection information"
        )

    connection_info = connection_infos[0] or {}

    if not isinstance(connection_info, dict):
        raise ValueError(
            "MQTT connection information is invalid"
        )

    cluster_infos = connection_info.get(
        "clusterInfos"
    ) or []

    if not cluster_infos:
        raise ValueError(
            "MQTT configuration does not contain "
            "cluster information"
        )

    cluster_info = cluster_infos[0] or {}

    if not isinstance(cluster_info, dict):
        raise ValueError(
            "MQTT cluster information is invalid"
        )

    host = str(
        cluster_info.get("brokerUrl") or ""
    ).replace("ssl://", "")

    try:
        port = int(
            cluster_info.get("brokerPort") or 8883
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            "MQTT broker port is invalid"
        ) from error

    subscribe_topics: list[str] = []

    login_publish_topic: str | None = None
    properties_publish_topic: str | None = None

    login_device_id: str | None = None
    vehicle_device_id: str | None = None

    topic_infos = connection_info.get(
        "topicInfos"
    ) or []

    for topic_info in topic_infos:
        if not isinstance(topic_info, dict):
            continue

        message_type = topic_info.get("msgType")

        for topic in topic_info.get("pubTopics") or []:
            if not isinstance(topic, str):
                continue

            if (
                message_type == "loginout"
                and "/loginout/req" in topic
            ):
                login_publish_topic = topic
                login_device_id = extract_topic_did(
                    topic
                )

            if (
                message_type == "properties"
                and "/properties/get/req" in topic
            ):
                properties_publish_topic = topic
                vehicle_device_id = extract_topic_did(
                    topic
                )

        for topic in topic_info.get("subTopics") or []:
            if not isinstance(topic, str):
                continue

            if (
                "/commands/" not in topic
                and "/set/" not in topic
            ):
                subscribe_topics.append(topic)

            if (
                vehicle_device_id is None
                and "/properties/" in topic
            ):
                vehicle_device_id = extract_topic_did(
                    topic
                )

    if not host:
        raise ValueError(
            "MQTT configuration does not contain a broker host"
        )

    if not subscribe_topics:
        raise ValueError(
            "MQTT configuration does not contain "
            "subscription topics"
        )

    if not login_publish_topic:
        raise ValueError(
            "MQTT configuration does not contain "
            "the login publish topic"
        )

    if not properties_publish_topic:
        raise ValueError(
            "MQTT configuration does not contain "
            "the properties publish topic"
        )

    if not login_device_id:
        raise ValueError(
            "MQTT configuration does not contain "
            "the login device identifier"
        )

    if not vehicle_device_id:
        raise ValueError(
            "MQTT configuration does not contain "
            "the vehicle device identifier"
        )

    return DeepalMqttConnection(
        host=host,
        port=port,
        subscribe_topics=sorted(
            set(subscribe_topics)
        ),
        login_publish_topic=login_publish_topic,
        properties_publish_topic=properties_publish_topic,
        login_device_id=login_device_id,
        vehicle_device_id=vehicle_device_id,
    )


def create_request_id(device_id: str) -> str:
    """Create a unique Deepal MQTT request identifier."""
    return f"{device_id}_{int(time.time() * 1_000_000)}"


def build_login_payload(
    login_device_id: str,
    request_id: str,
) -> dict[str, Any]:
    """Build the Deepal MQTT login payload."""
    return {
        "did": login_device_id,
        "r": request_id,
        "v": "v1.0.0",
        "mt": "loginout",
        "z": "unzip",
        "a": 0,
        "e": 0,
        "tf": 0,
        "dt": datetime.now(UTC).isoformat().replace(
            "+00:00",
            "Z",
        ),
        "pl": True,
        "sers": [
            {
                "service_code": "login",
                "params": {
                    "encryptEnable": 1,
                    "zipType": "gzip",
                    "ts": int(time.time() * 1000),
                },
            }
        ],
    }


def extract_secret_key(
    payload: dict[str, Any],
) -> str | None:
    """Extract the MQTT encryption key from the login response."""
    for item in payload.get("rs") or []:
        if not isinstance(item, dict):
            continue

        for key in ("params", "data"):
            value = item.get(key)

            if (
                isinstance(value, dict)
                and value.get("secretKey")
            ):
                return str(value["secretKey"])

    return None


def build_condition_payload(
    vehicle_device_id: str,
    login_device_id: str,
    secret_key: str,
    request_id: str,
) -> dict[str, Any]:
    """Build the encrypted request for vehicle telemetry."""
    services = [
        {
            "service_code": "car_condition",
            "params": {
                "fetchPropertyType": 0,
            },
        }
    ]

    return {
        "did": vehicle_device_id,
        "r": request_id,
        "v": "v1.0.0",
        "mt": "properties",
        "e": 1,
        "z": "gzip",
        "tf": 0,
        "dt": datetime.now(UTC).isoformat().replace(
            "+00:00",
            "Z",
        ),
        "b": {
            "ruid": login_device_id,
        },
        "sers": encrypt_mqtt_payload(
            services,
            secret_key,
            request_id,
        ),
        "rt": "",
    }


def extract_telemetry_parameters(
    payload: dict[str, Any],
    secret_key: str,
) -> dict[str, Any]:
    """Decrypt telemetry parameters from an MQTT response."""
    request_id = payload.get("r")

    if not isinstance(request_id, str):
        return {}

    parameters: dict[str, Any] = {}

    for field in ("rs", "sers"):
        encrypted_value = payload.get(field)

        if (
            not isinstance(encrypted_value, str)
            or not encrypted_value
        ):
            continue

        try:
            items = decrypt_mqtt_payload(
                encrypted_value,
                secret_key,
                request_id,
            )
        except (
            ValueError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            gzip.BadGzipFile,
        ):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            service_code = item.get("service_code")
            item_parameters = item.get("params")

            if isinstance(item_parameters, dict):
                if service_code not in KNOWN_SERVICE_CODES:
                    _LOGGER.debug(
                        "Deepal MQTT: unmapped service_code=%s "
                        "keys=%s",
                        service_code,
                        sorted(item_parameters.keys()),
                    )
                    continue

                parameters.update(item_parameters)
            elif service_code not in KNOWN_SERVICE_CODES:
                _LOGGER.debug(
                    "Deepal MQTT: unmapped service_code=%s "
                    "(no dict params, raw=%r)",
                    service_code,
                    item_parameters,
                )

    return parameters


class DeepalMqttClient:
    """Read vehicle telemetry from the Deepal MQTT broker."""

    def __init__(
        self,
        connection: DeepalMqttConnection,
        auth_token: str,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        """Initialize the MQTT client.

        ssl_context should be built once via hass.async_add_executor_job
        (see coordinator.py) and reused across calls: creating one reads
        the system's trust store from disk, which is a blocking
        operation and must not happen directly on the event loop. If
        omitted, one is created lazily here as a fallback (e.g. for
        direct/manual use outside Home Assistant), at the cost of that
        same blocking warning.
        """
        self._connection = connection
        self._auth_token = auth_token
        self._ssl_context = ssl_context

        # Raw vehicle parameters from the most recent successful
        # fetch_telemetry() call, kept for diagnostics.py so we can
        # show both mapped and not-yet-mapped fields.
        self.last_raw_parameters: dict[str, Any] = {}

    async def fetch_telemetry(self) -> DeepalTelemetry:
        """Connect to MQTT and retrieve vehicle telemetry."""
        ssl_context = self._ssl_context or ssl.create_default_context()

        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(
                self._connection.host,
                self._connection.port,
                ssl=ssl_context,
                server_hostname=self._connection.host,
            ),
            timeout=MQTT_CONNECTION_TIMEOUT,
        )

        try:
            await self._connect(
                writer,
                reader,
            )

            await self._subscribe(
                writer,
                reader,
            )

            login_request_id = create_request_id(
                self._connection.login_device_id
            )

            writer.write(
                build_publish_packet(
                    self._connection.login_publish_topic,
                    build_login_payload(
                        self._connection.login_device_id,
                        login_request_id,
                    ),
                )
            )
            await writer.drain()

            secret_key: str | None = None
            partial_parameters: dict[str, Any] = {}
            condition_requested = False

            deadline = (
                time.monotonic()
                + MQTT_TELEMETRY_TIMEOUT
            )

            while time.monotonic() < deadline:
                remaining_timeout = max(
                    1,
                    deadline - time.monotonic(),
                )

                first_byte, body = await asyncio.wait_for(
                    read_packet(reader),
                    timeout=remaining_timeout,
                )

                packet_type = first_byte >> 4

                if packet_type != 3:
                    continue

                topic, payload, packet_id = (
                    parse_publish_packet(
                        first_byte,
                        body,
                    )
                )

                if packet_id is not None:
                    writer.write(
                        build_puback_packet(packet_id)
                    )
                    await writer.drain()

                if secret_key is None:
                    secret_key = extract_secret_key(
                        payload
                    )

                    if secret_key:
                        condition_request_id = (
                            create_request_id(
                                self._connection.vehicle_device_id
                            )
                        )

                        condition_payload = (
                            build_condition_payload(
                                self._connection.vehicle_device_id,
                                self._connection.login_device_id,
                                secret_key,
                                condition_request_id,
                            )
                        )

                        writer.write(
                            build_publish_packet(
                                self._connection.properties_publish_topic,
                                condition_payload,
                            )
                        )
                        await writer.drain()

                        condition_requested = True

                    continue

                parameters = extract_telemetry_parameters(
                    payload,
                    secret_key,
                )

                if not parameters:
                    continue

                partial_parameters.update(parameters)

                if (
                    topic.endswith("/properties/get/res")
                    and len(partial_parameters) > 10
                ):
                    log_telemetry_snapshot(partial_parameters)
                    self.last_raw_parameters = dict(
                        partial_parameters
                    )
                    return parameters_to_telemetry(
                        partial_parameters
                    )

                if (
                    condition_requested
                    and len(partial_parameters) > 30
                ):
                    log_telemetry_snapshot(partial_parameters)
                    self.last_raw_parameters = dict(
                        partial_parameters
                    )
                    return parameters_to_telemetry(
                        partial_parameters
                    )

            if partial_parameters:
                log_telemetry_snapshot(partial_parameters)
                self.last_raw_parameters = dict(
                    partial_parameters
                )
                return parameters_to_telemetry(
                    partial_parameters
                )

            raise TimeoutError(
                "Deepal MQTT telemetry was not received"
            )

        finally:
            writer.close()

            try:
                await writer.wait_closed()
            except (
                ConnectionError,
                TimeoutError,
                ssl.SSLError,
            ):
                pass

    async def _connect(
        self,
        writer: asyncio.StreamWriter,
        reader: asyncio.StreamReader,
    ) -> None:
        """Authenticate with the MQTT broker."""
        device_id = self._connection.login_device_id

        writer.write(
            build_connect_packet(
                device_id,
                device_id,
                self._auth_token,
            )
        )
        await writer.drain()

        first_byte, body = await asyncio.wait_for(
            read_packet(reader),
            timeout=MQTT_CONNECTION_TIMEOUT,
        )

        return_code = (
            body[1]
            if first_byte == 0x20 and len(body) >= 2
            else None
        )

        if return_code != 0:
            raise ConnectionError(
                "Deepal MQTT broker rejected the connection: "
                f"return_code={return_code}"
            )

    async def _subscribe(
        self,
        writer: asyncio.StreamWriter,
        reader: asyncio.StreamReader,
    ) -> None:
        """Subscribe to vehicle MQTT topics."""
        if not self._connection.subscribe_topics:
            raise ValueError(
                "Deepal MQTT configuration contains no topics"
            )

        writer.write(
            build_subscribe_packet(
                1,
                self._connection.subscribe_topics,
            )
        )
        await writer.drain()

        first_byte, _ = await asyncio.wait_for(
            read_packet(reader),
            timeout=MQTT_CONNECTION_TIMEOUT,
        )

        packet_type = first_byte >> 4

        if packet_type != 9:
            raise ConnectionError(
                "Deepal MQTT broker did not return SUBACK"
            )
