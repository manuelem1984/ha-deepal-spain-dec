"""Data coordinator for Deepal Spain DEC."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import DeepalApiClient, DeepalApiError
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

        self.api = api
        self.session = session
        self.vehicle = vehicle

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
            mqtt_config = (
                await self.api.get_mqtt_connection_config(
                    self.vehicle.vehicle_id
                )
            )

            mqtt_connection = parse_connection_config(
                mqtt_config
            )

            mqtt_auth_token = (
                await self.api.get_mqtt_auth_token(
                    self.session.user_id
                )
            )

            mqtt_client = DeepalMqttClient(
                mqtt_connection,
                mqtt_auth_token,
            )

            return await mqtt_client.fetch_telemetry()

        except (
            DeepalApiError,
            ConnectionError,
            TimeoutError,
            ValueError,
        ) as error:
            raise UpdateFailed(
                f"Unable to update Deepal telemetry: {error}"
            ) from error
