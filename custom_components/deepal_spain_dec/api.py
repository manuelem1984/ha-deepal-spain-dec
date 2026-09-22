"""Deepal Spain DEC HTTP API client."""

from __future__ import annotations

import json
import time
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .api_errors import (
    DeepalApiError,
    DeepalAuthError,
    DeepalCommandNotReady,
    DeepalRateLimitError,
    is_auth_error,
)
from .const import (
    BASE_URL,
    CA_BASE_URL,
    CONTROL_AIR_CONDITIONER,
    CONTROL_CONDITION_INQUIRY,
    CONTROL_FLASHING_HONKING,
    CONTROL_GET_SERIAL_NO,
    CONTROL_RESULT,
    DEFAULT_APP_VERSION,
    DEFAULT_LANGUAGE,
    REQUEST_TIMEOUT,
    SPAIN_COUNTRY,
)
from .crypto import decrypt_with_private_key, sign_command_payload
from .models import DeepalVehicle

__all__ = [
    "DeepalApiClient",
    "DeepalApiError",
    "DeepalAuthError",
    "DeepalCommandNotReady",
    "DeepalRateLimitError",
]


class DeepalApiClient:
    """HTTP client for the Deepal Spain cloud API."""

    def __init__(
        self,
        session: ClientSession,
        *,
        device_id: str,
        access_token: str = "",
        cac_token: str | None = None,
        private_key_pem: str | None = None,
    ) -> None:
        """Initialize the Deepal API client."""
        self._session = session
        self.device_id = device_id
        self.access_token = access_token
        self.cac_token = cac_token
        # Needed to decrypt the vehicle serial number and to sign
        # remote commands (see _signed_command below); absent on
        # entries created before signed commands existed and never
        # reauthenticated since.
        self.private_key_pem = private_key_pem

    def update_tokens(
        self,
        *,
        access_token: str,
        cac_token: str | None = None,
    ) -> None:
        """Update authentication tokens."""
        self.access_token = access_token
        self.cac_token = cac_token

    def _headers(self, *, include_auth: bool) -> dict[str, str]:
        """Return headers used by the Spanish Deepal application."""
        headers = {
            "authorization": "",
            "appid": "ca",
            "language": DEFAULT_LANGUAGE,
            "appversion": DEFAULT_APP_VERSION,
            "apptype": "Android",
            "devicetype": "samsung",
            "deviceid": self.device_id,
            "selectcountry": SPAIN_COUNTRY,
            "x-os-version": "9",
            "accept-language": DEFAULT_LANGUAGE,
            "content-type": "application/json; charset=UTF-8",
            "user-agent": "okhttp/4.12.0",
        }

        if include_auth and self.access_token:
            headers["authorization"] = (
                f"{self.access_token}|{self.cac_token}"
                if self.cac_token and "|" not in self.access_token
                else self.access_token
            )

        return headers

    async def post(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        include_auth: bool = True,
        use_ca_gateway: bool = False,
        include_tsp_token: bool = False,
    ) -> Any:
        """Send a POST request to the Deepal Spain cloud."""
        base_url = CA_BASE_URL if use_ca_gateway else BASE_URL
        url = f"{base_url}{path}"

        headers = self._headers(include_auth=include_auth)

        if include_tsp_token:
            if not self.access_token:
                raise DeepalAuthError(
                    "X-Tsp-User-Token requires an access token"
                )

            headers["X-Tsp-User-Token"] = self.access_token

        request_body = json.dumps(
            payload or {},
            separators=(",", ":"),
            ensure_ascii=False,
        )

        try:
            async with self._session.post(
                url,
                data=request_body,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            ) as response:
                response.raise_for_status()
                body = await response.json(content_type=None)

        except ClientResponseError as err:
            if err.status in (401, 403):
                raise DeepalAuthError(
                    f"Deepal authentication failed: HTTP {err.status}"
                ) from err

            raise DeepalApiError(
                f"Deepal HTTP error {err.status} for {path}"
            ) from err

        except (ClientError, TimeoutError) as err:
            raise DeepalApiError(
                f"Deepal request failed for {path}: {err}"
            ) from err

        if not isinstance(body, dict):
            raise DeepalApiError(
                f"Unexpected Deepal response for {path}"
            )

        if body.get("success") is False:
            code = str(body.get("code") or "")
            message = str(body.get("msg") or "")

            if code == "CAC_1_1_01_033":
                raise DeepalRateLimitError(
                    f"Deepal rate limit: {code} {message}"
                )

            if is_auth_error(code, message):
                raise DeepalAuthError(
                    f"Deepal authentication failed: {code} {message}"
                )

            raise DeepalApiError(
                f"Deepal API error for {path}: {code} {message}"
            )

        return body.get("data")

    async def post_ca(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        """Send an authenticated request to the Spanish CA gateway."""
        return await self.post(
            path,
            payload,
            use_ca_gateway=True,
            include_tsp_token=True,
        )

    async def get_vehicles(self) -> list[DeepalVehicle]:
        """Return vehicles associated with the authenticated account."""
        data = await self.post(
            "/intl-app-gw/intl-app-user/api/car/vehicles"
        )

        if not isinstance(data, list):
            raise DeepalApiError(
                "Vehicle response did not contain a list"
            )

        vehicles: list[DeepalVehicle] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            vehicle_id = item.get("carId")

            if vehicle_id is None:
                continue

            vehicles.append(
                DeepalVehicle(
                    vehicle_id=str(vehicle_id),
                    vin=item.get("vin"),
                    model_name=item.get("modelName"),
                    image_url=(
                        item.get("vehicleImageUrl")
                        or item.get("imageUrl")
                        or item.get("carImageUrl")
                        or item.get("modelImageUrl")
                    ),
                    mqtt_enabled=(
                        str(item.get("protocolType") or "").upper()
                        == "MQTT"
                    ),
                )
            )

        return vehicles

    async def get_mqtt_connection_config(
        self,
        vehicle_id: str,
    ) -> dict[str, Any]:
        """Return the MQTT connection configuration for a vehicle."""
        data = await self.post_ca(
            "/user-apigw/vot-connect-conf-center/api/device/getConnConf",
            {
                "deviceId": self.device_id,
                "carId": vehicle_id,
                "deviceType": 1,
                "confTimestamp": 0,
                "deviceTimestamp": str(int(time.time() * 1000)),
            },
        )

        if not isinstance(data, dict):
            raise DeepalApiError(
                "MQTT connection response did not contain an object"
            )

        return data

    async def get_mqtt_auth_token(
        self,
        user_id: str,
    ) -> str:
        """Return the MQTT authentication token for a user."""
        if not user_id:
            raise DeepalAuthError(
                "MQTT authentication requires a user ID"
            )

        data = await self.post_ca(
            "/user-apigw/vot-connect-auth-center/api/auth/"
            "getAuthTokenByUserId",
            {
                "userId": user_id,
            },
        )

        if not isinstance(data, dict) or not data.get("authToken"):
            raise DeepalApiError(
                "MQTT authentication response did not contain authToken"
            )

        return str(data["authToken"])

    # ------------------------------------------------------------------
    # Remote commands (no control PIN required)
    #
    # Reverse-engineered by cross-checking with another open-source
    # Deepal integration targeting the same backend; not yet confirmed
    # by us against a real command sent to a vehicle. See
    # docs/remote-control.md before relying on this in production.
    # ------------------------------------------------------------------

    async def get_serial_number(self) -> str:
        """Return the vehicle's encrypted serial number, still encrypted."""
        data = await self.post(
            CONTROL_GET_SERIAL_NO,
            {"type": "1"},
        )

        if not isinstance(data, str) or not data:
            raise DeepalApiError(
                "Serial number response did not contain a string"
            )

        return data

    async def _get_decrypted_serial_number(self) -> str:
        """Fetch and decrypt the serial number with the login private key."""
        if not self.private_key_pem:
            raise DeepalCommandNotReady(
                "The login private key is required to sign remote "
                "commands; reauthenticate the integration to generate "
                "one."
            )

        encrypted = await self.get_serial_number()

        try:
            return decrypt_with_private_key(
                self.private_key_pem,
                encrypted,
            )
        except ValueError as err:
            raise DeepalCommandNotReady(
                f"Could not decrypt the vehicle serial number: {err}"
            ) from err

    async def _signed_command(
        self,
        path: str,
        vehicle_id: str,
        payload: dict[str, Any],
    ) -> str:
        """Sign and send a remote-command payload, returning its commandId."""
        if not self.private_key_pem:
            raise DeepalCommandNotReady(
                "The login private key is required to sign remote "
                "commands; reauthenticate the integration to generate "
                "one."
            )

        serial_no = await self._get_decrypted_serial_number()

        signed_payload: dict[str, Any] = {
            **payload,
            # "seriralNo" (sic) matches the field name the server
            # actually expects — a manufacturer typo, not ours.
            "seriralNo": serial_no,
            "vehicleId": vehicle_id,
        }
        signed_payload["sign"] = sign_command_payload(
            self.private_key_pem,
            signed_payload,
        )

        data = await self.post(path, signed_payload)

        if not isinstance(data, dict) or not data.get("commandId"):
            raise DeepalApiError(
                f"Control command did not return a commandId for {path}"
            )

        return str(data["commandId"])

    async def control_air_conditioner(
        self,
        vehicle_id: str,
        *,
        enabled: bool,
        target_temp_c: float,
        run_time: int = 30,
        wind_mode: int = 1,
    ) -> str:
        """Turn the cabin air conditioner on/off and set its target temperature."""
        return await self._signed_command(
            CONTROL_AIR_CONDITIONER,
            vehicle_id,
            {
                "command": "air",
                "enabled": enabled,
                "runTime": run_time,
                "targetTemp": int(round(target_temp_c * 10)),
                "windMode": wind_mode,
            },
        )

    async def control_condition_inquiry(
        self,
        vehicle_id: str,
    ) -> str:
        """Ask the vehicle to report fresh condition data right away."""
        return await self._signed_command(
            CONTROL_CONDITION_INQUIRY,
            vehicle_id,
            {"command": "COMMAND_GET_NEW_CONDITION"},
        )

    async def control_flashing_honking(
        self,
        vehicle_id: str,
        action_type: int,
    ) -> str:
        """Flash the lights and/or sound the horn (see FLASH_HONK_* in const.py)."""
        return await self._signed_command(
            CONTROL_FLASHING_HONKING,
            vehicle_id,
            {"command": "flash_bee", "type": action_type},
        )

    async def get_command_result(
        self,
        vehicle_id: str,
        command_id: str,
    ) -> dict[str, Any]:
        """Fetch the raw status payload of a previously sent signed command.

        Unlike the other control_* methods, this one is a plain
        authenticated POST — no serial number to fetch, no RSA
        signature to compute — confirmed by reading
        ha-deepal-alternative's own client code directly. See
        coordinator._classify_command_result() for how the response
        (a "resultCode" field) is interpreted.
        """
        data = await self.post(
            CONTROL_RESULT,
            {"vehicleId": vehicle_id, "commandId": command_id},
        )
        return data if isinstance(data, dict) else {}
