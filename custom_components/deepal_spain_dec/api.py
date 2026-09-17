"""Deepal Spain DEC HTTP API client."""

from __future__ import annotations

import json
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import (
    BASE_URL,
    CA_BASE_URL,
    DEFAULT_APP_VERSION,
    DEFAULT_LANGUAGE,
    REQUEST_TIMEOUT,
    SPAIN_COUNTRY,
)
from .models import DeepalVehicle


class DeepalApiError(Exception):
    """Base exception for Deepal API errors."""


class DeepalAuthError(DeepalApiError):
    """Raised when Deepal authentication fails."""


class DeepalRateLimitError(DeepalApiError):
    """Raised when Deepal limits verification-code requests."""


class DeepalApiClient:
    """HTTP client for the Deepal Spain cloud API."""

    def __init__(
        self,
        session: ClientSession,
        *,
        device_id: str,
        access_token: str = "",
        cac_token: str | None = None,
    ) -> None:
        """Initialize the Deepal API client."""
        self._session = session
        self.device_id = device_id
        self.access_token = access_token
        self.cac_token = cac_token

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

            if (
                "AUTH" in code.upper()
                or code.startswith("401")
                or code in {"APP_1_1_02_004", "APP_1_1_02_005"}
            ):
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

    async def get_vehicles(self) -> list"""Return vehicles associated with the authenticated account."""
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
