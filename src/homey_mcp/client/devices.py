import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class DeviceAPI:
    def __init__(self, client):
        self.client = client

    async def get_devices(self) -> Dict[str, Any]:
        """Get all devices (with caching)."""
        # Demo mode data - EXTENDED AND CORRECTED
        if self.client.config.offline_mode or self.client.config.demo_mode:
            demo_devices = {
                "light1": {
                    "id": "light1",
                    "name": "Living Room Lamp",
                    "class": "light",
                    "zoneName": "Living Room", 
                    "available": True,
                    "capabilitiesObj": {
                        "onoff": {"value": False, "title": "On/Off"},
                        "dim": {"value": 0.8, "title": "Brightness"},  # 0.0-1.0 (80%)
                        "light_hue": {"value": 0.2, "title": "Color"},  # 0.0-1.0 (hue)
                        "light_saturation": {"value": 0.9, "title": "Saturation"},  # 0.0-1.0
                        "light_temperature": {"value": 0.5, "title": "Color Temperature"},  # 0.0-1.0
                        "light_mode": {"value": "color", "title": "Mode"}  # color/temperature
                    },
                },
                "light2": {
                    "id": "light2", 
                    "name": "Kitchen Spots",
                    "class": "light",
                    "zoneName": "Kitchen",
                    "available": True,
                    "capabilitiesObj": {
                        "onoff": {"value": True, "title": "On/Off"},
                        "dim": {"value": 0.6, "title": "Brightness"},  # 60%
                        # Only warm/cold white, no color
                        "light_temperature": {"value": 0.3, "title": "Color Temperature"}
                    },
                },
                "sensor1": {
                    "id": "sensor1",
                    "name": "Temperature Sensor",
                    "class": "sensor", 
                    "zoneName": "Bedroom",
                    "available": True,
                    "capabilitiesObj": {
                        "measure_temperature": {"value": 21.5, "title": "Temperature"},  # °C
                        "measure_humidity": {"value": 65.2, "title": "Humidity"},  # %
                        "measure_battery": {"value": 85, "title": "Battery"},  # %
                        "alarm_battery": {"value": False, "title": "Battery Low"}  # boolean
                    },
                },
                "thermostat1": {
                    "id": "thermostat1",
                    "name": "Living Room Thermostat", 
                    "class": "thermostat",
                    "zoneName": "Living Room",
                    "available": True,
                    "capabilitiesObj": {
                        "target_temperature": {"value": 20.0, "title": "Target Temperature"},  # SETABLE
                        "measure_temperature": {"value": 19.2, "title": "Current Temperature"},  # READ-ONLY
                        "measure_battery": {"value": 92, "title": "Battery"}
                    },
                },
                "socket1": {
                    "id": "socket1",
                    "name": "Desk Socket",
                    "class": "socket", 
                    "zoneName": "Office",
                    "available": True,
                    "capabilitiesObj": {
                        "onoff": {"value": True, "title": "On/Off"},
                        "measure_power": {"value": 45.2, "title": "Power"},  # Watt
                        "meter_power": {"value": 2.34, "title": "Energy"}  # kWh
                    },
                }
            }
            logger.info(f"Demo mode: {len(demo_devices)} demo devices")
            return demo_devices

        # Check cache
        if self.client._device_cache and time.time() - self.client._cache_timestamp < self.client.config.cache_ttl:
            return self.client._device_cache

        try:
            # FIX: Voeg trailing slash toe
            response = await self.client.session.get("/api/manager/devices/device/")
            response.raise_for_status()

            devices = response.json()
            self.client._device_cache = devices
            self.client._cache_timestamp = time.time()

            logger.info(f"Devices retrieved: {len(devices)} devices")
            return devices

        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            raise

    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get specific device."""
        devices = await self.get_devices()

        if device_id not in devices:
            raise ValueError(f"Device {device_id} not found")

        return devices[device_id]

    def validate_capability_value(self, capability: str, value: Any) -> tuple[bool, Any, str]:
        """
        Validate and convert capability value to correct format.
        
        Returns:
            (is_valid, converted_value, error_message)
        """
        
        # Boolean capabilities
        if capability in ["onoff", "alarm_battery", "alarm_motion", "alarm_contact", "alarm_smoke", "alarm_co", "alarm_water", "alarm_generic"]:
            if isinstance(value, bool):
                return True, value, ""
            if isinstance(value, (int, str)):
                if isinstance(value, str) and value.lower() in ["true", "1", "on", "yes"]:
                    return True, True, ""
                elif isinstance(value, str) and value.lower() in ["false", "0", "off", "no"]:
                    return True, False, ""
                elif isinstance(value, int):
                    return True, bool(value), ""
            return False, value, f"Capability {capability} expects boolean value"
        
        # Range capabilities (0.0 - 1.0)
        if capability in ["dim", "light_hue", "light_saturation", "light_temperature", "volume_set", "windowcoverings_set", "windowcoverings_tilt_set"]:
            try:
                float_val = float(value)
                if 0.0 <= float_val <= 1.0:
                    return True, float_val, ""
                # Auto-convert percentage to fraction
                elif 0 <= float_val <= 100:
                    converted = float_val / 100.0
                    return True, converted, f"Converted {float_val}% to {converted}"
                else:
                    return False, value, f"Capability {capability} must be between 0.0-1.0 (or 0-100%)"
            except (ValueError, TypeError):
                return False, value, f"Capability {capability} expects numeric value"
        
        # Temperature capabilities  
        if capability in ["target_temperature", "measure_temperature"]:
            try:
                temp = float(value)
                if -50 <= temp <= 100:  # Reasonable temperature range
                    return True, temp, ""
                else:
                    return False, value, f"Temperature {temp}°C seems unrealistic"
            except (ValueError, TypeError):
                return False, value, f"Temperature must be numeric"
        
        # Power/energy capabilities
        if capability in ["measure_power", "meter_power", "measure_voltage", "measure_current"]:
            try:
                power = float(value)
                if power >= 0:
                    return True, power, ""
                else:
                    return False, value, "Power/energy cannot be negative"
            except (ValueError, TypeError):
                return False, value, f"Capability {capability} expects numeric value"
        
        # Percentage capabilities (0-100)
        if capability in ["measure_battery", "measure_humidity"]:
            try:
                percentage = float(value)
                if 0 <= percentage <= 100:
                    return True, percentage, ""
                else:
                    return False, value, f"Capability {capability} must be between 0-100%"
            except (ValueError, TypeError):
                return False, value, f"Capability {capability} expects numeric value"
        
        # String/enum capabilities
        if capability in ["light_mode"]:
            if capability == "light_mode" and value in ["color", "temperature"]:
                return True, value, ""
            return False, value, f"Capability {capability} has invalid value: {value}"
        
        # Default: accept as-is
        return True, value, ""

    async def set_capability_value(self, device_id: str, capability: str, value: Any) -> bool:
        """Set capability value of device."""
        # Validate value first
        is_valid, converted_value, message = self.validate_capability_value(capability, value)
        if not is_valid:
            raise ValueError(f"Invalid capability value: {message}")
        
        if message:
            logger.info(f"Capability value converted: {message}")

        # Demo mode
        if self.client.config.offline_mode or self.client.config.demo_mode:
            logger.info(
                f"Demo mode: Device {device_id} capability {capability} would be set to {converted_value}"
            )
            return True

        try:
            # MOST IMPORTANT FIX: Correct endpoint format with trailing slash
            endpoint = f"/api/manager/devices/device/{device_id}/capability/{capability}/"
            payload = {"value": converted_value}  # Use validated value!

            # CRITICAL FIX: Use PUT instead of POST!
            response = await self.client.session.put(endpoint, json=payload)
            
            # Fallback: If PUT doesn't work, try POST (for compatibility)
            if response.status_code == 405:  # Method Not Allowed
                logger.warning(f"PUT not supported for {endpoint}, trying POST...")
                response = await self.client.session.post(endpoint, json=payload)
            
            response.raise_for_status()

            # Invalidate cache for this device
            if self.client._device_cache and device_id in self.client._device_cache:
                if capability in self.client._device_cache[device_id].get("capabilitiesObj", {}):
                    self.client._device_cache[device_id]["capabilitiesObj"][capability]["value"] = converted_value

            logger.info(f"Device {device_id} capability {capability} set to {converted_value}")
            return True

        except Exception as e:
            logger.error(f"Error setting capability: {e}")
            logger.error(f"Endpoint: {endpoint}")
            logger.error(f"Payload: {payload}")
            raise