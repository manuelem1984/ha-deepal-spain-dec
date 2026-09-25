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
    CHECK_CONTROL_CODE,
    CONTROL_AIR_CONDITIONER,
    CONTROL_CONDITION_INQUIRY,
    CONTROL_DEFROST,
    CONTROL_DOORS,
    CONTROL_FLASHING_HONKING,
    CONTROL_GET_SERIAL_NO,
    CONTROL_RESULT,
    CONTROL_SEATS_HEAT,
    CONTROL_SEATS_WIND,
    CONTROL_STEERING_WHEEL_HEAT,
    CONTROL_TRUNK,
    CONTROL_WINDOWS,
    CONDITION_OVERLAY,
    DEFAULT_APP_VERSION,
    DEFAULT_LANGUAGE,
    GET_SECURITY_CODE_STATUS,
    REQUEST_TIMEOUT,
    SPAIN_COUNTRY,
)
from .crypto import (
    decrypt_with_private_key,
    encrypt_login_value,
    sign_command_payload,
)
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

        # Remote-control PIN (doors/windows/trunk only — every other
        # command works without it). Set from the config entry's
        # options by __init__.py when the PIN block is enabled; None
        # otherwise, in which case _signed_command(require_rc_token=
        # True) refuses those three commands outright. rc_token is
        # the short-lived credential exchanged for it (see
        # check_control_code()) — cached and reused across commands,
        # refreshed only when the server rejects a reused one.
        self.control_pin: str | None = None
        self.rc_token: str | None = None

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
    # Reverse-engineered by cross-checking with an independent reference
    # implementation targeting the same backend; not yet confirmed
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

    async def get_security_code_status(self) -> dict[str, Any]:
        """Fetch the control PIN status before exchanging it.

        Called immediately before check_control_code(), mirroring
        what the official app itself always does first.
        """
        data = await self.post(
            GET_SECURITY_CODE_STATUS,
            {},
        )
        return data if isinstance(data, dict) else {}

    async def check_control_code(self, control_pin: str) -> str:
        """Exchange the remote-control PIN for an rcToken.

        Checks the remaining attempts first (get_security_code_status)
        and refuses locally, without even trying, when none are left
        — safer than risking a longer server-side lockout by
        submitting a PIN we already know will be rejected. The PIN
        itself is RSA-encrypted the same way as the email/mobile
        number at login (encrypt_login_value), since it's the same
        public key and padding Deepal's API expects for any sensitive
        value sent in a request body.
        """
        status = await self.get_security_code_status()
        retry_quantity = status.get("retryQuantity")

        try:
            remaining = (
                int(retry_quantity)
                if retry_quantity is not None
                else None
            )
        except (TypeError, ValueError):
            remaining = None

        if remaining is not None and remaining <= 0:
            raise DeepalRateLimitError(
                "No quedan intentos para comprobar el PIN de control; "
                "espera a que se levante el bloqueo o restablece el "
                "PIN desde la aplicación oficial."
            )

        data = await self.post(
            CHECK_CONTROL_CODE,
            {"safeCode": encrypt_login_value(control_pin)},
        )

        if not isinstance(data, dict) or not data.get("rcToken"):
            raise DeepalApiError(
                "La comprobación del PIN de control no devolvió un "
                "rcToken."
            )

        self.rc_token = str(data["rcToken"])
        return self.rc_token

    async def _signed_command(
        self,
        path: str,
        vehicle_id: str,
        payload: dict[str, Any],
        *,
        require_rc_token: bool = False,
    ) -> str:
        """Sign and send a remote-command payload, returning its commandId.

        require_rc_token=True is for the PIN-gated commands (doors,
        windows, trunk): reuses a cached rc_token when there is one,
        exchanges the stored control_pin for a fresh one otherwise
        (raising DeepalCommandNotReady if no PIN is configured at
        all), and — if the server rejects a *reused* token — clears
        it, exchanges a new one, and retries the command exactly
        once. A token obtained fresh in this same call is never
        retried on failure, since a second consecutive rejection is
        unlikely to be about the token's freshness.
        """
        if not self.private_key_pem:
            raise DeepalCommandNotReady(
                "The login private key is required to sign remote "
                "commands; reauthenticate the integration to generate "
                "one."
            )

        reused_rc_token = False

        if require_rc_token:
            if self.rc_token:
                reused_rc_token = True
            elif self.control_pin:
                await self.check_control_code(self.control_pin)
            else:
                raise DeepalCommandNotReady(
                    "El PIN de control es necesario para este "
                    "comando; configúralo en las opciones de la "
                    "integración."
                )

        serial_no = await self._get_decrypted_serial_number()

        def _build_signed_payload() -> dict[str, Any]:
            signed_payload: dict[str, Any] = {
                **payload,
                # "seriralNo" (sic) matches the field name the server
                # actually expects — a manufacturer typo, not ours.
                "seriralNo": serial_no,
                "vehicleId": vehicle_id,
            }
            if require_rc_token and self.rc_token:
                # Part of what gets signed below, same as every other
                # field — not a separate step.
                signed_payload["rcToken"] = self.rc_token
            signed_payload["sign"] = sign_command_payload(
                self.private_key_pem,
                signed_payload,
            )
            return signed_payload

        try:
            data = await self.post(path, _build_signed_payload())
        except (DeepalApiError, DeepalAuthError):
            # A cached rcToken is itself a session that eventually
            # expires; the server only reveals that by rejecting a
            # command that reused it. Exchange a fresh one with the
            # stored PIN and retry once — never for a freshly
            # obtained token, which failing again points elsewhere.
            if not (
                require_rc_token
                and reused_rc_token
                and self.control_pin
            ):
                raise

            self.rc_token = None
            await self.check_control_code(self.control_pin)
            data = await self.post(path, _build_signed_payload())

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
        signature to compute — confirmed by reading an independent
        reference client directly. See
        coordinator._classify_command_result() for how the response
        (a "resultCode" field) is interpreted.
        """
        data = await self.post(
            CONTROL_RESULT,
            {"vehicleId": vehicle_id, "commandId": command_id},
        )
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _seat_payload(
        command: str,
        *,
        master_switch: int | None,
        master_level: int | None,
        copilot_switch: int | None,
        copilot_level: int | None,
    ) -> dict[str, Any]:
        """Build a seat heat/vent command payload.

        Confirmed by reading an independent reference implementation
        (tested there against a real vehicle): turning a seat off
        must send switch: 0 *without* a level field — sending an
        explicit level of 0 is rejected by the server
        (COMMON_1_1_01_005). So a falsy level is omitted entirely
        here, the same way a None switch/level already is.
        """
        payload: dict[str, Any] = {"command": command}

        if master_switch is not None:
            payload["masterSwitch"] = master_switch
        if master_level:
            payload["masterLevel"] = master_level
        if copilot_switch is not None:
            payload["copilotSwitch"] = copilot_switch
        if copilot_level:
            payload["copilotLevel"] = copilot_level

        return payload

    async def control_seats_heat(
        self,
        vehicle_id: str,
        *,
        master_switch: int | None = None,
        master_level: int | None = None,
        copilot_switch: int | None = None,
        copilot_level: int | None = None,
    ) -> str:
        """Set the driver ("master") / passenger ("copilot") seat heat level.

        Only pass the switch+level for the seat(s) being changed;
        leave the other pair as None. A level of 0 (or None) turns
        that seat's heating off — see _seat_payload for why it must
        be omitted from the payload, not sent as 0.
        """
        return await self._signed_command(
            CONTROL_SEATS_HEAT,
            vehicle_id,
            self._seat_payload(
                "seats_heat",
                master_switch=master_switch,
                master_level=master_level,
                copilot_switch=copilot_switch,
                copilot_level=copilot_level,
            ),
        )

    async def control_seats_wind(
        self,
        vehicle_id: str,
        *,
        master_switch: int | None = None,
        master_level: int | None = None,
        copilot_switch: int | None = None,
        copilot_level: int | None = None,
    ) -> str:
        """Set the driver ("master") / passenger ("copilot") seat vent level.

        Same rules as control_seats_heat: only pass the pair being
        changed, and a level of 0/None turns that seat's ventilation
        off.
        """
        return await self._signed_command(
            CONTROL_SEATS_WIND,
            vehicle_id,
            self._seat_payload(
                "seats_wind",
                master_switch=master_switch,
                master_level=master_level,
                copilot_switch=copilot_switch,
                copilot_level=copilot_level,
            ),
        )

    async def control_steering_wheel_heat(
        self,
        vehicle_id: str,
        enabled: bool,
    ) -> str:
        """Turn the steering wheel heating on or off."""
        return await self._signed_command(
            CONTROL_STEERING_WHEEL_HEAT,
            vehicle_id,
            {"command": "steering_wheel_heating", "open": enabled},
        )

    async def control_defrost(
        self,
        vehicle_id: str,
        enabled: bool,
    ) -> str:
        """Turn the front defrost on or off.

        Cross-checked against an independent reference client, which
        has this exact method; exposed here as a Home Assistant entity
        since v1.3.1b4.
        """
        return await self._signed_command(
            CONTROL_DEFROST,
            vehicle_id,
            {"command": "defrost", "enabled": enabled},
        )

    async def get_condition_overlay(
        self,
        vehicle_id: str,
    ) -> dict[str, Any]:
        """Fetch a richer, on-demand condition snapshot for a few unreliable fields.

        Plain authenticated POST — no serial number, no RSA signature
        (different gateway from the control_* commands). Requesting
        only the "seat", "hvac" and "vehicleStatus" categories, the
        ones this integration actually overlays — see
        coordinator._async_overlay_condition(). The response is
        nested by category (e.g. body["seat"]["leftFront"]), unlike
        the flat MQTT payload.
        """
        data = await self.post(
            CONDITION_OVERLAY,
            {
                "vechileCriteria": {  # sic — manufacturer's own typo
                    "seat": "1",
                    "hvac": "1",
                    "vehicleStatus": "1",
                },
                "vehicleId": vehicle_id,
            },
        )
        return data if isinstance(data, dict) else {}

    async def control_doors(
        self,
        vehicle_id: str,
        locked: bool,
    ) -> str:
        """Lock or unlock every door at once (needs the control PIN).

        There is no per-door lock/unlock — this is the same single
        "central locking" action the car's own remote/key fob does.
        """
        return await self._signed_command(
            CONTROL_DOORS,
            vehicle_id,
            {"command": "doors", "lock": locked},
            require_rc_token=True,
        )

    async def control_trunk(
        self,
        vehicle_id: str,
        open_trunk: bool,
    ) -> str:
        """Open or close the trunk (needs the control PIN).

        Payload shape is a best-effort guess (a plain "open" boolean,
        matching every other simple on/off command in this file) —
        not yet confirmed against a real vehicle. See
        docs/remote-control.md.
        """
        return await self._signed_command(
            CONTROL_TRUNK,
            vehicle_id,
            {"command": "trunk", "open": open_trunk},
            require_rc_token=True,
        )

    async def control_windows(
        self,
        vehicle_id: str,
        *,
        window: str,
        open_window: bool,
    ) -> str:
        """Open or close one window (needs the control PIN).

        `window` is one of "leftFront", "rightFront", "leftRear",
        "rightRear" — the same four position names already used
        elsewhere in this API (seats, tires). Sends only the one
        window being changed, the same convention
        control_seats_heat()/control_seats_wind() use for master vs.
        copilot.

        Unlike the other PIN-gated commands, the exact payload shape
        for windows specifically has not been reverse-engineered from
        a confirmed source — this guess (one boolean field per window
        position) follows the naming convention the rest of the API
        already uses, but has not been tried against a real vehicle
        yet. See docs/remote-control.md before relying on it.
        """
        return await self._signed_command(
            CONTROL_WINDOWS,
            vehicle_id,
            {"command": "windows", window: open_window},
            require_rc_token=True,
        )
