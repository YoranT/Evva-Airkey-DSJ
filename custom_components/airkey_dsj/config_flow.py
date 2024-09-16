import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from .const import DOMAIN

class AirkeyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Evva Airkey."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Evva Airkey", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=15): int,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema
        )

    async def async_step_import(self, user_input=None):
        """Handle the import from YAML."""
        return await self.async_step_user(user_input)
