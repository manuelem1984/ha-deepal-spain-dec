"""Data coordinator for Deepal Spain DEC."""

from __future__ import annotations

import asyncio
import dataclasses
import ssl
from collections.abc import Callable, Coroutine
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
from .telemetry import parse_condition_overlay

_LOGGER = logging.getLogger(__name__)

DEFAULT_UPDATE_INTERVAL = timedelta(minutes=5)

# How long to poll control/control-result for, and how often, before
# giving up and treating the command as still-pending (not failed).
_COMMAND_RESULT_TIMEOUT = 15.0
_COMMAND_RESULT_INTERVAL = 1.0

# How long a command that shares state (optimistic_update) will wait
# for the lock before giving up — a single command can already take
# up to _COMMAND_RESULT_TIMEOUT plus a few retries, so a queued second
# one needs real headroom, but not forever in case something is
# genuinely stuck.
_COMMAND_LOCK_TIMEOUT = 30.0

# resultCode -> status, exactly as classified by an independent
# reference implementation for this backend, confirmed by reading its
# source directly. Any code not listed here is treated as
# "failed" (fail closed) rather than silently assumed successful.
_COMMAND_RESULT_CODES: dict[int, str] = {
    -100: "pending",
    0: "success",
    1201: "success",
    1015: "already_done",
    -1: "failed",
    -2: "failed",
}


def _classify_command_result(payload: dict[str, Any]) -> str:
    """Classify a control-result payload by its resultCode.

    Returns one of "pending", "success", "already_done" or "failed".
    A missing resultCode means the vehicle hasn't reported back yet
    ("pending"); an unrecognized one is treated as "failed".
    """
    raw_code = payload.get("resultCode")

    if raw_code is None:
        return "pending"

    try:
        code = int(raw_code)
    except (TypeError, ValueError):
        return "failed"

    return _COMMAND_RESULT_CODES.get(code, "failed")


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

        # Guards against two commands that both mutate self.data (via
        # optimistic_update) racing each other — e.g. two climate
        # calls, or a climate call and a seat-heat call, fired close
        # together. A plain fire-and-forget command with no
        # optimistic_update (lights, horn) never touches this lock at
        # all, so it can always run immediately regardless of what
        # else is in flight.
        self._command_lock = asyncio.Lock()

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
        telemetry = await self._async_overlay_condition(telemetry)
        return telemetry

    async def _async_overlay_condition(
        self,
        telemetry: DeepalTelemetry,
    ) -> DeepalTelemetry:
        """Replace a handful of MQTT-unreliable fields with a better source.

        Seat heat/vent level and steering wheel heat/front defrost
        on-off were confirmed (comparing two real diagnostics dumps a
        few minutes apart, with the actual state changed and
        confirmed via the official app in between) to not reliably
        follow the vehicle's real state over MQTT. This calls a
        separate, richer on-demand endpoint for just those fields and
        overlays them — see docs/remote-control.md.

        Best-effort: any failure here just leaves the MQTT-derived
        (already known unreliable) values from `telemetry` as they
        were, rather than breaking the whole poll over it.
        """
        try:
            raw = await self.api.get_condition_overlay(
                self.vehicle.vehicle_id
            )
        except DeepalApiError as error:
            _LOGGER.debug(
                "Deepal condition overlay failed for %s, keeping "
                "MQTT-derived values for the affected fields: %s",
                self.vehicle.vehicle_id,
                error,
            )
            return telemetry

        overlay_fields = parse_condition_overlay(raw)

        if not overlay_fields:
            return telemetry

        return dataclasses.replace(telemetry, **overlay_fields)

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
        command_factory: Callable[[], Coroutine[Any, Any, str]],
        *,
        optimistic_update: dict[str, Any] | None = None,
        serialize: bool | None = None,
        refresh_after: bool = True,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> None:
        """Run a signed remote command and translate failures for entities.

        command_factory is a zero-argument callable that returns a
        *fresh* coroutine each time it's called (e.g.
        ``lambda: self.api.control_air_conditioner(...)``), not an
        already-created coroutine — a coroutine object can only be
        awaited once, and this may need to call it a second time after
        a silent session refresh (see _send_command_with_session_retry).

        Commands that queue behind each other via a lock (waiting up
        to _COMMAND_LOCK_TIMEOUT seconds their turn instead of racing)
        are the ones that either mutate self.data (optimistic_update
        given) or explicitly ask to serialize — e.g. two climate
        calls, or a seat-heat call and a seat-vent call on the same
        seat, since the real vehicle can't have both on at once. A
        command with neither (lights, horn) touches nothing shared,
        so it always runs immediately regardless of what else is in
        flight. serialize=None (the default) means "only if
        optimistic_update is given" — pass it explicitly (e.g.
        serialize=True with optimistic_update=None) for a command
        that shares real vehicle state without also updating
        self.data, such as an assumed-state entity that doesn't trust
        the vehicle's own reported status for that feature.

        After Deepal's servers accept the command (returning a
        commandId), this polls control/control-result briefly to
        confirm the *vehicle itself* accepted it too — a signed
        command can still be rejected asynchronously (e.g. the car is
        asleep or busy) even though the initial HTTP request
        succeeded. See _async_confirm_command_accepted().

        optimistic_update, if given, is a {field_name: expected_value}
        mapping applied to the coordinator's data immediately after
        that's confirmed — e.g. {"climate_on": True} — so the entity
        reflects the change right away instead of waiting on a poll.
        This is still a guess, not a telemetry confirmation: the
        vehicle is then nudged (control_condition_inquiry) and polled
        up to max_retries times, `retry_delay` seconds apart, until a
        real poll confirms the same values; if it never does within
        those retries, the optimistic guess is left in place until the
        next regular poll cycle corrects it either way. See
        docs/remote-control.md for the current limitations of this
        approach (still no rollback if the command silently no-ops
        server-side despite being accepted).
        """
        if serialize is None:
            serialize = optimistic_update is not None

        if not serialize:
            await self._async_send_command_locked(
                command_factory,
                optimistic_update=optimistic_update,
                refresh_after=refresh_after,
                max_retries=max_retries,
                retry_delay=retry_delay,
            )
            return

        try:
            async with asyncio.timeout(_COMMAND_LOCK_TIMEOUT):
                async with self._command_lock:
                    await self._async_send_command_locked(
                        command_factory,
                        optimistic_update=optimistic_update,
                        refresh_after=refresh_after,
                        max_retries=max_retries,
                        retry_delay=retry_delay,
                    )
        except TimeoutError as error:
            raise HomeAssistantError(
                "Hay otro comando de Deepal en curso desde hace "
                "demasiado tiempo; inténtalo de nuevo en unos "
                "segundos."
            ) from error

    async def _async_send_command_locked(
        self,
        command_factory: Callable[[], Coroutine[Any, Any, str]],
        *,
        optimistic_update: dict[str, Any] | None,
        refresh_after: bool,
        max_retries: int,
        retry_delay: float,
    ) -> None:
        """Do the actual work of async_send_command.

        Split out so async_send_command can decide, before running
        any of this, whether it needs the lock at all.
        """
        try:
            command_id = await self._send_command_with_session_retry(
                command_factory
            )
        except DeepalAuthError as error:
            raise HomeAssistantError(
                "La sesión de Deepal ha caducado y no se ha "
                "podido renovar sola; reautentica la integración: "
                f"{error}"
            ) from error
        except DeepalApiError as error:
            raise HomeAssistantError(
                f"El comando de Deepal ha fallado: {error}"
            ) from error

        await self._async_confirm_command_accepted(command_id)

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

    async def _async_confirm_command_accepted(
        self,
        command_id: str,
    ) -> None:
        """Poll control-result to confirm the vehicle accepted the command.

        Having a commandId only means Deepal's servers accepted the
        HTTP request — the vehicle can still reject it afterwards
        (observed elsewhere as "TBOX_..." result
        messages, typically when the car is asleep or busy). This
        polls briefly and raises a clear HomeAssistantError if the
        vehicle reports a failure; if it neither confirms nor fails
        within _COMMAND_RESULT_TIMEOUT seconds, it's left as pending
        and the command proceeds anyway — the optimistic-update poll
        loop that follows is the fallback for that case.
        """
        loop = asyncio.get_running_loop()
        deadline = loop.time() + _COMMAND_RESULT_TIMEOUT

        while True:
            try:
                result = await self.api.get_command_result(
                    self.vehicle.vehicle_id,
                    command_id,
                )
            except DeepalApiError:
                # Best-effort check only; don't block the command on
                # this endpoint being unavailable.
                return

            status = _classify_command_result(result)

            if status == "failed":
                error_message = result.get("errorMsg") or "sin detalle"
                hint = (
                    " (puede que el vehículo esté dormido u ocupado; "
                    "prueba de nuevo después de usarlo un poco)"
                    if "TBOX_" in str(error_message)
                    else ""
                )
                raise HomeAssistantError(
                    f"El vehículo rechazó el comando: {error_message}"
                    f"{hint}"
                )

            if status in ("success", "already_done"):
                return

            if loop.time() >= deadline:
                _LOGGER.debug(
                    "Deepal command %s result still pending after "
                    "%.0fs; continuing anyway",
                    command_id,
                    _COMMAND_RESULT_TIMEOUT,
                )
                return

            await asyncio.sleep(_COMMAND_RESULT_INTERVAL)

    async def _send_command_with_session_retry(
        self,
        command_factory: Callable[[], Coroutine[Any, Any, str]],
    ) -> str:
        """Run a signed command, silently refreshing the session once if needed.

        Mirrors the same recovery _async_update_data() already does
        for regular telemetry polls. Without this, every signed
        command (climate, lights, horn...) surfaced a "reauthenticate"
        error on the very first call after the token went stale, even
        though a plain poll already recovers from that exact situation
        on its own — observed in practice: a failed command followed
        by pressing "Actualizar datos del vehículo" (a plain poll)
        then letting the *next* command through fine.
        """
        try:
            return await command_factory()
        except DeepalAuthError as error:
            if not self.session.refresh_token:
                raise

            try:
                await self._refresh_session()
            except DeepalApiError as refresh_error:
                raise DeepalAuthError(
                    f"Session refresh failed: {refresh_error}"
                ) from refresh_error

            return await command_factory()

