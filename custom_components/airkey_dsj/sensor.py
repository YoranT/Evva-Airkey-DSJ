import logging
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "locks": "Locks"
}

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Evva Airkey sensors and devices from a config entry."""
    _LOGGER.debug("Setting up Evva Airkey locks and devices.")

    api_key = config_entry.data[CONF_API_KEY]
    scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, 15)
    entities = []

    device_registry = async_get_device_registry(hass)

    # Fetch only the 'locks' data
    data = await fetch_sensor_data(api_key, "locks")

    if not data:
        _LOGGER.error("No data returned for locks")
        return

    for lock in data:  # Process each lock in the lockList
        lock_id = lock.get("id")
        lock_name = lock.get("lockDoor", {}).get("name", "Unknown")
        device_name = f"Lock_{lock_id}_{lock_name}"  # Create the device name

        # Create or get the device for this lock
        device = device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, lock_id)},  # Unique identifier for the device
            name=device_name,  # Use the constructed device name
            manufacturer="Evva",
            model="Lock"
        )

        # Add sensor entities for this lock
        entities.append(SensorItemEntity(lock, "locks", "name", api_key, scan_interval, lock_id, device_name))
        entities.append(SensorItemEntity(lock, "locks", "status", api_key, scan_interval, lock_id, device_name))
        entities.append(SensorItemEntity(lock, "locks", "location", api_key, scan_interval, lock_id, device_name))
        entities.append(SensorItemEntity(lock, "locks", "firmware", api_key, scan_interval, lock_id, device_name))

    _LOGGER.debug(f"Adding {len(entities)} entities.")
    async_add_entities(entities, True)

async def fetch_sensor_data(api_key, sensor_type):
    """Fetch sensor data from the API based on sensor type."""
    url = _get_api_url(sensor_type)

    headers = {
        "X-API-Key": api_key,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                _LOGGER.debug(f"Fetched {sensor_type} data: {data}")

                # Return the lockList directly for locks
                if sensor_type == "locks":
                    return data.get('lockList', [])

                return data if isinstance(data, list) else []

            else:
                _LOGGER.error(f"Error fetching {sensor_type} data, status: {response.status}")
                return None

def _get_api_url(sensor_type):
    """Construct the correct API URL based on the sensor type."""
    base_url = "https://integration.api.airkey.evva.com:443/cloud/v1/"
    endpoints = {
        "locks": f"{base_url}locks?limit=1000",
    }
    return endpoints.get(sensor_type, base_url)

class SensorItemEntity(SensorEntity):
    """Representation of a sensor item entity."""

    def __init__(self, item, sensor_type, data_type, api_key, scan_interval, lock_id, device_name):
        """Initialize the sensor entity."""
        self._item = item
        self._sensor_type = sensor_type
        self._data_type = data_type
        self._api_key = api_key
        self._scan_interval = scan_interval
        self._lock_id = lock_id  # Unique identifier for the device
        self._device_name = device_name  # Name of the lock/device
        self._name = f"{self._device_name} - {data_type.capitalize()}"
        self._state = self._get_item_state()

    def _get_item_state(self):
        """Return the appropriate state based on the data type."""
        if self._data_type == "name":
            return self._item.get("lockDoor", {}).get("name", "Unknown")
        elif self._data_type == "status":
            return "Active" if not self._item.get("removalRequested", False) else "Inactive"
        elif self._data_type == "location":
            return self._item.get("lockDoor", {}).get("location", "Unknown")
        elif self._data_type == "firmware":
            return self._item.get("lockFirmware", {}).get("appletVersion", "Unknown")
        return "Unknown"

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def device_info(self):
        """Return device info to group entities under the same device."""
        return {
            "identifiers": {(DOMAIN, self._lock_id)},  # Group by lock_id for the device
            "name": self._device_name,  # Use the lock_id_name format for the device name
            "manufacturer": "Evva",
            "model": self._sensor_type,
        }

    async def async_update(self):
        """Update the entity state."""
        _LOGGER.debug(f"Updating {self._name} entity.")
        self._state = self._get_item_state()
