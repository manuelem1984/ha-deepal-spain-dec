"""Data coordinator for Deepal Spain DEC."""

from __future__ import annotations

import ssl
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import DeepalApiClient, DeepalApiError, DeepalAuthError
from .auth import DeepalAuthenticator
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CAC_TOKEN,
    CONF_REFRESH_TOKEN,
)
from .models import (
    DeepalSession,
    DeepalTelemetry,
    DeepalVehicle,
)
from .mqtt import (
    DeepalMqttClient,
    parse_connection_config,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_UPDATE_INTERVAL = timedelta(minutes=5)


class DeepalSpainCoordinator(
    DataUpdateCoordinator[DeepalTelemetry]
):
    """Coordinate Deepal vehicle telemetry updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: DeepalApiClient,
        session: DeepalSession,
        vehicle: DeepalVehicle,
    ) -> None:
        """Initialize the Deepal Spain coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Deepal Spain {vehicle.vehicle_id}",
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )

        self.entry = entry
        self.api = api
        self.session = session
        self.vehicle = vehicle

        # Raw vehicle parameters from the most recent successful update,
        # kept for diagnostics.py (shows both mapped and unmapped fields).
        self.last_raw_parameters: dict = {}

        # Built once via the executor (blocking I/O: reads the system's
        # trust store from disk) and reused for every MQTT connection,
        # instead of rebuilding it on the event loop on every poll.
        self._ssl_context: ssl.SSLContext | None = None

    async def _async_update_data(
        self,
    ) -> DeepalTelemetry:
        """Fetch fresh telemetry from the Deepal cloud."""
        if not self.vehicle.mqtt_enabled:
            raise UpdateFailed(
                "The vehicle does not use the supported MQTT protocol"
            )

        if not self.session.user_id:
            raise UpdateFailed(
                "The Deepal session does not contain a user ID"
            )

        try:
            return await self._fetch_telemetry_once()

        except DeepalAuthError as error:
            # Some Deepal accounts (e.g. secondary/shared-vehicle
            # accounts, as opposed to the vehicle's owner account) get
            # an access token with a short lifetime — observed to
            # expire roughly every hour. Try a silent refresh with the
            # stored refresh_token first; only fall back to asking the
            # user to sign in again if that isn't possible or fails
            # too.
            if not self.session.refresh_token:
                raise ConfigEntryAuthFailed(
                    "Deepal session token is no longer valid and no "
                    "refresh token is available: "
                    f"{error}"
                ) from error

            try:
                await self._refresh_session()
            except DeepalApiError as refresh_error:
                raise ConfigEntryAuthFailed(
                    "Deepal session token is no longer valid and "
                    f"refreshing it failed: {refresh_error}"
                ) from refresh_error

            try:
                return await self._fetch_telemetry_once()
            except DeepalAuthError as retry_error:
                raise ConfigEntryAuthFailed(
                    "Deepal session token is still invalid after "
                    f"refreshing it: {retry_error}"
                ) from retry_error

        except (
            DeepalApiError,
            ConnectionError,
            TimeoutError,
            ValueError,
        ) as error:
            raise UpdateFailed(
                f"Unable to update Deepal telemetry: {error}"
            ) from error

    async def _fetch_telemetry_once(self) -> DeepalTelemetry:
        """Fetch telemetry once, with the current session tokens."""
        if self._ssl_context is None:
            self._ssl_context = await self.hass.async_add_executor_job(
                ssl.create_default_context
            )

        mqtt_config = await self.api.get_mqtt_connection_config(
            self.vehicle.vehicle_id
        )

        mqtt_connection = parse_connection_config(mqtt_config)

        mqtt_auth_token = await self.api.get_mqtt_auth_token(
            self.session.user_id
        )

        mqtt_client = DeepalMqttClient(
            mqtt_connection,
            mqtt_auth_token,
            self._ssl_context,
        )

        telemetry = await mqtt_client.fetch_telemetry()
        self.last_raw_parameters = mqtt_client.last_raw_parameters
        return telemetry

    async def _refresh_session(self) -> None:
        """Silently renew the session using the stored refresh token.

        Updates self.session and self.api in place, and persists the
        new tokens onto the config entry so a Home Assistant restart
        doesn't go back to the stale ones. Raises DeepalApiError
        (unchanged) if the refresh itself fails.
        """
        authenticator = DeepalAuthenticator(self.api)

        self.session = await authenticator.refresh_session(
            self.session
        )

        self.hass.config_entries.async_update_entry(
            self.entry,
            data={
                **self.entry.data,
                CONF_ACCESS_TOKEN: self.session.access_token,
                CONF_REFRESH_TOKEN: self.session.refresh_token,
                CONF_CAC_TOKEN: self.session.cac_token,
            },
        )

        _LOGGER.debug(
            "Deepal session token refreshed silently for %s",
            self.vehicle.vehicle_id,
        )
