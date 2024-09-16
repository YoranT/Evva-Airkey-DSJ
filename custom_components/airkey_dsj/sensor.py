import logging
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "events": "Events",
    "credits": "Credits",
    "areas": "Areas",
    "maintenance_tasks": "Maintenance Tasks",
    "media": "Media",
    "persons": "Persons",
    "blacklists": "Blacklists",
    "authorizations": "Authorizations",
    "locks": "Locks",
}

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Evva Airkey sensors from a config entry."""
    _LOGGER.debug("Setting up Evva Airkey sensors.")
    
    api_key = config_entry.data[CONF_API_KEY]
    scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, 15)

    entities = []
    for sensor_type in SENSOR_TYPES:
        _LOGGER.debug(f"Creating sensor for {sensor_type}")
        entities.append(AirkeySensor(sensor_type, api_key, scan_interval))

    _LOGGER.debug(f"Adding {len(entities)} sensors.")
    async_add_entities(entities, True)

class AirkeySensor(SensorEntity):
    """Representation of an Evva Airkey sensor."""

    def __init__(self, sensor_type, api_key, scan_interval):
        """Initialize the sensor."""
        self._type = sensor_type
        self._name = SENSOR_TYPES[sensor_type]
        self._state = None
        self._api_key = api_key
        self._scan_interval = scan_interval
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Airkey {self._name}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    async def async_update(self):
        """Fetch new state data for the sensor."""
        _LOGGER.debug(f"Updating Airkey sensor: {self._name}")

        data, attributes = await self.fetch_data()

        # Plaats een korte waarde in de state, zoals de lengte van de data of een simpele status
        if data:
            self._state = len(data) if isinstance(data, list) else "OK"
            self._attributes = attributes

    async def fetch_data(self):
        """Helper function to perform the API request."""
        url = self._get_api_url()

        headers = {
            "X-API-Key": self._api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug(f"Fetched data for {self._name}: {data}")

                    # Plaats de volledige data in attributes in plaats van direct in state
                    attributes = {"raw_data": data}
                    return data, attributes
                else:
                    _LOGGER.error(f"Error fetching data from {url}, status: {response.status}")
                    return None, {}

    def _get_api_url(self):
        """Construct the correct API URL based on the sensor type."""
        base_url = "https://api.airkey.evva.com:443/cloud/v1/"
        endpoints = {
            "events": f"{base_url}events?createdAfter=2024-08-01T09:15:10.295Z&limit=1000",
            "credits": f"{base_url}credits",
            "areas": f"{base_url}areas",
            "maintenance_tasks": f"{base_url}maintenance-tasks",
            "media": f"{base_url}media",
            "persons": f"{base_url}persons",
            "blacklists": f"{base_url}blacklists?limit=1000",
            "authorizations": f"{base_url}authorizations?limit=1000",
            "locks": f"{base_url}locks?limit=1000",
        }
        return endpoints.get(self._type, base_url)
