"""Data coordinator for Deepal Spain DEC."""

from __future__ import annotations

import asyncio
import dataclasses
import ssl
from collections.abc import Coroutine
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    HomeAssistantError,
)
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

    async def async_send_command(
        self,
        command: Coroutine[Any, Any, str],
        *,
        optimistic_update: dict[str, Any] | None = None,
        refresh_after: bool = True,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> None:
        """Run a signed remote command and translate failures for entities.

        optimistic_update, if given, is a {field_name: expected_value}
        mapping applied to the coordinator's data immediately after the
        command succeeds — e.g. {"climate_on": True} — so the entity
        reflects the change right away instead of waiting on a poll.
        This is a guess, not a confirmation: the vehicle is then
        nudged (control_condition_inquiry) and polled up to
        max_retries times, `retry_delay` seconds apart, until a real
        poll confirms the same values; if it never does within those
        retries, the optimistic guess is left in place until the next
        regular poll cycle corrects it either way. See
        docs/remote-control.md for the current limitations of this
        approach (still no rollback if the command silently no-ops
        server-side).
        """
        try:
            await command
        except DeepalAuthError as error:
            raise HomeAssistantError(
                "La sesión de Deepal ha caducado; reautentica la "
                f"integración: {error}"
            ) from error
        except DeepalApiError as error:
            raise HomeAssistantError(
                f"El comando de Deepal ha fallado: {error}"
            ) from error

        if optimistic_update and self.data is not None:
            self.async_set_updated_data(
                dataclasses.replace(
                    self.data,
                    **optimistic_update,
                )
            )

        if not refresh_after:
            return

        try:
            await self.api.control_condition_inquiry(
                self.vehicle.vehicle_id
            )
        except DeepalApiError:
            # Best-effort nudge only; the regular poll cycle will
            # catch up regardless.
            pass

        for attempt in range(max_retries):
            await self.async_request_refresh()

            if not optimistic_update:
                return

            confirmed = self.data is not None and all(
                getattr(self.data, field) == value
                for field, value in optimistic_update.items()
            )

            if confirmed:
                return

            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)

        await self.async_request_refresh()
