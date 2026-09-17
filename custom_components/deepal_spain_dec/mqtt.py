"""MQTT client for Deepal Spain DEC."""

from __future__ import annotations

import asyncio
import json
import struct
from typing import Any


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
        raise ValueError("MQTT PUBLISH packet is too short")

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


def build_puback_packet(packet_id: int) -> bytes:
    """Build an MQTT PUBACK packet."""
    return (
        bytes([0x40, 0x02])
        + struct.pack("!H", packet_id)
    )
def extract_topic_did(topic: str) -> str | None:
    """Extract the device identifier from a Deepal MQTT topic."""
    parts = topic.split("/")

    if len(parts) > 2 and parts[0] == "$vdp":
        return parts[1]

    return None


def parse_connection_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Extract broker and topic information from getConnConf."""
    connection_infos = config.get("mqttConnectionInfos") or []

    if not connection_infos:
        raise ValueError(
            "MQTT configuration does not contain connection information"
        )

    connection_info = connection_infos[0] or {}
    cluster_infos = connection_info.get("clusterInfos") or []

    if not cluster_infos:
        raise ValueError(
            "MQTT configuration does not contain cluster information"
        )

    cluster_info = cluster_infos[0] or {}

    host = str(
        cluster_info.get("brokerUrl") or ""
    ).replace("ssl://", "")

    port = int(cluster_info.get("brokerPort") or 8883)

    subscribe_topics: list[str] = []
    login_publish_topic: str | None = None
    properties_publish_topic: str | None = None
    login_device_id: str | None = None
    vehicle_device_id: str | None = None

    for topic_info in connection_info.get("topicInfos") or []:
        message_type = topic_info.get("msgType")

        for topic in topic_info.get("pubTopics") or []:
            if (
                message_type == "loginout"
                and "/loginout/req" in topic
            ):
                login_publish_topic = topic
                login_device_id = extract_topic_did(topic)

            if (
                message_type == "properties"
                and "/properties/get/req" in topic
            ):
                properties_publish_topic = topic
                vehicle_device_id = extract_topic_did(topic)

        for topic in topic_info.get("subTopics") or []:
            if (
                "/commands/" not in topic
                and "/set/" not in topic
            ):
                subscribe_topics.append(topic)

            if (
                vehicle_device_id is None
                and "/properties/" in topic
            ):
                vehicle_device_id = extract_topic_did(topic)

    if not all(
        (
            host,
            login_publish_topic,
            properties_publish_topic,
            login_device_id,
            vehicle_device_id,
        )
    ):
        raise ValueError(
            "MQTT configuration is missing required broker or topic data"
        )

    return {
        "host": host,
        "port": port,
        "subscribe_topics": sorted(set(subscribe_topics)),
        "login_publish_topic": login_publish_topic,
        "properties_publish_topic": properties_publish_topic,
        "login_device_id": login_device_id,
        "vehicle_device_id": vehicle_device_id,
    }
