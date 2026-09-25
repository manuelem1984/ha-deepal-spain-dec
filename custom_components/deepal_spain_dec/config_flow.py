"""Configuration flow for Deepal Spain DEC."""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    DeepalApiClient,
    DeepalApiError,
    DeepalRateLimitError,
)
from .auth import DeepalAuthenticator
from .const import (
    ARM_DURATION_OPTIONS,
    CONF_ACCESS_TOKEN,
    CONF_ARM_DURATION,
    CONF_ARM_NOTIFY,
    CONF_CAC_TOKEN,
    CONF_CAC_USER_ID,
    CONF_CA_USER_ID,
    CONF_CONTROL_PIN,
    CONF_DEVICE_ID,
    CONF_EMAIL,
    CONF_LOGIN_METHOD,
    CONF_MOBILE,
    CONF_MQTT_ENABLED,
    CONF_PIN_ENABLED,
    CONF_PIN_MODE,
    CONF_VEHICLE_COLOR,
    CONF_VEHICLE_TRIM,
    DEFAULT_ARM_DURATION_SECONDS,
    DEFAULT_ARM_NOTIFY,
    DEFAULT_PIN_MODE,
    DOMAIN,
    PIN_MODES,
    VEHICLE_COLORS,
    VEHICLE_TRIMS,
    CONF_PRIVATE_KEY,
    CONF_REFRESH_TOKEN,
    CONF_USER_ID,
    CONF_VEHICLE_ID,
    CONF_VEHICLE_IMAGE_URL,
    CONF_VEHICLE_MODEL,
    CONF_VEHICLE_VIN,
    LOGIN_METHOD_EMAIL,
    LOGIN_METHOD_SMS,
)


LOGIN_METHODS = {
    LOGIN_METHOD_EMAIL: "Correo electrónico",
    LOGIN_METHOD_SMS: "SMS (+34)",
}


class DeepalSpainDecConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle the Deepal Spain DEC configuration flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> DeepalSpainOptionsFlow:
        """Return the options flow for this handler."""
        return DeepalSpainOptionsFlow()

    def __init__(self) -> None:
        """Initialize the configuration flow."""
        self._api: DeepalApiClient | None = None
        self._authenticator: DeepalAuthenticator | None = None
        self._login_method: str | None = None
        self._identifier: str | None = None

        # Set by async_step_reauth() so a reauthentication reuses the
        # same device_id the entry was originally created with, instead
        # of registering a brand new device with Deepal.
        self._device_id: str | None = None

    async def async_step_reauth(
        self,
        entry_data: Mapping[str, Any],
    ):
        """Start reauthentication after the stored session token stops working."""
        self._login_method = entry_data.get(CONF_LOGIN_METHOD)
        self._device_id = entry_data.get(CONF_DEVICE_ID)

        return await self.async_step_user()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Choose the Spanish Deepal login method."""
        if user_input is not None:
            self._login_method = user_input[CONF_LOGIN_METHOD]

            if self._login_method == LOGIN_METHOD_EMAIL:
                return await self.async_step_email()

            return await self.async_step_sms()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LOGIN_METHOD,
                    default=(
                        self._login_method or LOGIN_METHOD_EMAIL
                    ),
                ): vol.In(LOGIN_METHODS),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    async def async_step_email(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Request a verification code by email."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = str(user_input[CONF_EMAIL]).strip().lower()

            try:
                self._create_authenticator()
                await self._authenticator.send_email_code(email)
            except DeepalRateLimitError:
                errors["base"] = "too_many_codes"
            except DeepalApiError:
                errors["base"] = "send_code_failed"
            else:
                self._identifier = email
                return await self.async_step_verification_code()

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
            }
        )

        return self.async_show_form(
            step_id="email",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_sms(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Request a verification code by Spanish SMS."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mobile = self._normalize_mobile(
                str(user_input[CONF_MOBILE])
            )

            if len(mobile) != 9:
                errors[CONF_MOBILE] = "invalid_mobile"
            else:
                try:
                    self._create_authenticator()
                    await self._authenticator.send_sms_code(mobile)
                except DeepalRateLimitError:
                    errors["base"] = "too_many_codes"
                except DeepalApiError:
                    errors["base"] = "send_code_failed"
                else:
                    self._identifier = mobile
                    return await self.async_step_verification_code()

        schema = vol.Schema(
            {
                vol.Required(CONF_MOBILE): str,
            }
        )

        return self.async_show_form(
            step_id="sms",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_verification_code(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Validate the verification code and create the entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            auth_code = str(
                user_input["auth_code"]
            ).strip()

            if (
                self._authenticator is None
                or self._api is None
                or self._identifier is None
                or self._login_method is None
            ):
                return self.async_abort(
                    reason="authentication_state_missing"
                )

            try:
                if self._login_method == LOGIN_METHOD_EMAIL:
                    session = await self._authenticator.login_email(
                        self._identifier,
                        auth_code,
                    )
                else:
                    session = await self._authenticator.login_sms(
                        self._identifier,
                        auth_code,
                    )

                vehicles = await self._api.get_vehicles()

            except DeepalRateLimitError:
                errors["base"] = "too_many_codes"
            except DeepalApiError:
                errors["base"] = "login_failed"
            else:
                if not vehicles:
                    errors["base"] = "no_vehicles"
                else:
                    vehicle = vehicles[0]

                    entry_data = {
                        CONF_LOGIN_METHOD: self._login_method,
                        CONF_ACCESS_TOKEN: session.access_token,
                        CONF_REFRESH_TOKEN: session.refresh_token,
                        CONF_CAC_TOKEN: session.cac_token,
                        CONF_USER_ID: session.user_id,
                        CONF_CA_USER_ID: session.ca_user_id,
                        CONF_CAC_USER_ID: session.cac_user_id,
                        CONF_DEVICE_ID: self._api.device_id,
                        CONF_PRIVATE_KEY: (
                            self._authenticator.private_key_pem
                        ),
                        CONF_VEHICLE_ID: vehicle.vehicle_id,
                        CONF_VEHICLE_VIN: vehicle.vin,
                        CONF_VEHICLE_MODEL: vehicle.model_name,
                        CONF_VEHICLE_IMAGE_URL: vehicle.image_url,
                        CONF_MQTT_ENABLED: vehicle.mqtt_enabled,
                    }

                    if self.source == SOURCE_REAUTH:
                        # Same account, but make sure it's still the
                        # same vehicle before overwriting the entry.
                        await self.async_set_unique_id(
                            vehicle.vehicle_id
                        )
                        self._abort_if_unique_id_mismatch(
                            reason="reauth_vehicle_mismatch"
                        )

                        return self.async_update_reload_and_abort(
                            self._get_reauth_entry(),
                            data_updates=entry_data,
                        )

                    await self.async_set_unique_id(
                        vehicle.vehicle_id
                    )
                    self._abort_if_unique_id_configured()

                    title = (
                        vehicle.model_name
                        or vehicle.vin
                        or f"Deepal {vehicle.vehicle_id}"
                    )

                    return self.async_create_entry(
                        title=title,
                        data=entry_data,
                    )

        schema = vol.Schema(
            {
                vol.Required("auth_code"): str,
            }
        )

        return self.async_show_form(
            step_id="verification_code",
            data_schema=schema,
            errors=errors,
        )

    def _create_authenticator(self) -> None:
        """Create the API client and authenticator.

        Reuses the existing device_id during a reauthentication, so Deepal
        sees the same device instead of registering a brand new one.
        """
        device_id = self._device_id or secrets.token_hex(16)

        self._api = DeepalApiClient(
            async_get_clientsession(self.hass),
            device_id=device_id,
        )

        self._authenticator = DeepalAuthenticator(
            self._api
        )

    @staticmethod
    def _normalize_mobile(mobile: str) -> str:
        """Normalize a Spanish mobile number."""
        normalized = (
            mobile.replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if normalized.startswith("+34"):
            normalized = normalized[3:]
        elif normalized.startswith("0034"):
            normalized = normalized[4:]
        elif normalized.startswith("34") and len(normalized) == 11:
            normalized = normalized[2:]

        return normalized


class DeepalSpainOptionsFlow(config_entries.OptionsFlow):
    """Handle Deepal Spain DEC options.

    Two independent blocks: the vehicle's trim/color (purely
    cosmetic, used by image.py), and the remote-control PIN block
    (doors/windows/trunk) — off by default, and only turned on once
    the PIN itself has been verified against the real account right
    here, not just accepted on faith. self.config_entry is provided
    by the base OptionsFlow class; it must not be set manually here.
    """

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Choose the vehicle's trim/color and the PIN block, together."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._async_validate_pin_block(user_input)

            if not errors:
                if not user_input.get(CONF_PIN_ENABLED):
                    # Disabling the block always starts fresh next
                    # time — no stale PIN, mode or duration left
                    # over from a previous configuration.
                    user_input[CONF_CONTROL_PIN] = None
                    user_input[CONF_PIN_MODE] = DEFAULT_PIN_MODE
                    user_input[CONF_ARM_DURATION] = str(
                        DEFAULT_ARM_DURATION_SECONDS
                    )
                    user_input[CONF_ARM_NOTIFY] = DEFAULT_ARM_NOTIFY

                return self.async_create_entry(
                    title="",
                    data=user_input,
                )

        current_trim = self.config_entry.options.get(
            CONF_VEHICLE_TRIM
        )
        current_color = self.config_entry.options.get(
            CONF_VEHICLE_COLOR
        )
        current_pin_enabled = self.config_entry.options.get(
            CONF_PIN_ENABLED, False
        )
        current_pin_mode = self.config_entry.options.get(
            CONF_PIN_MODE, DEFAULT_PIN_MODE
        )
        current_arm_duration = str(
            self.config_entry.options.get(
                CONF_ARM_DURATION, DEFAULT_ARM_DURATION_SECONDS
            )
        )
        current_arm_notify = self.config_entry.options.get(
            CONF_ARM_NOTIFY, DEFAULT_ARM_NOTIFY
        )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_VEHICLE_TRIM,
                    description={"suggested_value": current_trim},
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=key,
                                label=label,
                            )
                            for key, label in VEHICLE_TRIMS.items()
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_VEHICLE_COLOR,
                    description={"suggested_value": current_color},
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=key,
                                label=label,
                            )
                            for key, label in VEHICLE_COLORS.items()
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_PIN_ENABLED,
                    default=current_pin_enabled,
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_CONTROL_PIN,
                    description={
                        "suggested_value": (
                            self.config_entry.options.get(
                                CONF_CONTROL_PIN
                            )
                        )
                    },
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.PASSWORD
                    )
                ),
                vol.Required(
                    CONF_PIN_MODE,
                    default=current_pin_mode,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=key,
                                label=label,
                            )
                            for key, label in PIN_MODES.items()
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_ARM_DURATION,
                    default=current_arm_duration,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=value,
                                label=f"{value} segundos",
                            )
                            for value in ARM_DURATION_OPTIONS
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_ARM_NOTIFY,
                    default=current_arm_notify,
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )

    async def _async_validate_pin_block(
        self,
        user_input: dict[str, Any],
    ) -> dict[str, str]:
        """Verify the PIN against the real account when enabling the block.

        Only runs the check when CONF_PIN_ENABLED is being turned on
        with a PIN provided — disabling the block, or resubmitting the
        form with it already enabled and the PIN field left as-is,
        never re-verifies. On success, caches the resulting rcToken
        on the live API client so the very first PIN-gated command
        doesn't need to exchange one all over again.
        """
        if not user_input.get(CONF_PIN_ENABLED):
            return {}

        pin_value = user_input.get(CONF_CONTROL_PIN)

        if not pin_value:
            return {"base": "pin_required"}

        coordinator = self.hass.data[DOMAIN][
            self.config_entry.entry_id
        ]

        try:
            await coordinator.api.check_control_code(pin_value)
        except DeepalRateLimitError:
            return {"base": "pin_rate_limited"}
        except DeepalApiError:
            return {"base": "pin_invalid"}

        return {}
