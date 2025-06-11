import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import HomeyMCPConfig

logger = logging.getLogger(__name__)


class HomeyAPIClient:
    def __init__(self, config: HomeyMCPConfig):
        self.config = config
        self.base_url = f"http://{config.homey_local_address}"
        self.session: Optional[httpx.AsyncClient] = None
        self._device_cache: Dict[str, Any] = {}
        self._cache_timestamp = 0

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        """Connect to Homey API."""
        # Check for offline mode
        if self.config.offline_mode:
            logger.info("Offline mode - skip Homey connection")
            return

        headers = {
            "Authorization": f"Bearer {self.config.homey_local_token}",
            "Content-Type": "application/json",
        }

        self.session = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.config.request_timeout),
        )

        # Test connection
        try:
            logger.info(f"Trying to connect to Homey at {self.base_url}...")
            response = await self.session.get("/api/manager/system")
            response.raise_for_status()
            logger.info("✅ Successfully connected to Homey")
        except httpx.ConnectTimeout:
            logger.warning(f"❌ Connection timeout to {self.base_url}")
            logger.warning("💡 Check if:")
            logger.warning("   - Homey IP address is correct")
            logger.warning("   - Homey is reachable on the network")
            logger.warning("   - Firewall settings")
            logger.warning("🔄 Switching to demo mode automatically...")
            # Auto-enable demo mode for connection failures
            self.config.offline_mode = True
            self.config.demo_mode = True
            return  # Continue in demo mode
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning("❌ Unauthorized - check your Personal Access Token")
                logger.warning("🔄 Switching to demo mode automatically...")
                # Auto-enable demo mode for authentication failures
                self.config.offline_mode = True
                self.config.demo_mode = True
                return  # Continue in demo mode
            else:
                logger.error(f"❌ HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.warning(f"❌ Cannot connect to Homey: {e}")
            logger.warning("🔄 Switching to demo mode automatically...")
            # Auto-enable demo mode for any connection failures
            self.config.offline_mode = True
            self.config.demo_mode = True
            return  # Continue in demo mode

    async def disconnect(self):
        """Close connection."""
        if self.session:
            await self.session.aclose()

    async def get_devices(self) -> Dict[str, Any]:
        """Get all devices (with caching)."""
        import time

        # Demo mode data - EXTENDED AND CORRECTED
        if self.config.offline_mode or self.config.demo_mode:
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
        if self._device_cache and time.time() - self._cache_timestamp < self.config.cache_ttl:
            return self._device_cache

        try:
            # FIX: Voeg trailing slash toe
            response = await self.session.get("/api/manager/devices/device/")
            response.raise_for_status()

            devices = response.json()
            self._device_cache = devices
            self._cache_timestamp = time.time()

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
        if self.config.offline_mode or self.config.demo_mode:
            logger.info(
                f"Demo mode: Device {device_id} capability {capability} would be set to {converted_value}"
            )
            return True

        try:
            # MOST IMPORTANT FIX: Correct endpoint format with trailing slash
            endpoint = f"/api/manager/devices/device/{device_id}/capability/{capability}/"
            payload = {"value": converted_value}  # Use validated value!

            # CRITICAL FIX: Use PUT instead of POST!
            response = await self.session.put(endpoint, json=payload)
            
            # Fallback: If PUT doesn't work, try POST (for compatibility)
            if response.status_code == 405:  # Method Not Allowed
                logger.warning(f"PUT not supported for {endpoint}, trying POST...")
                response = await self.session.post(endpoint, json=payload)
            
            response.raise_for_status()

            # Invalidate cache for this device
            if self._device_cache and device_id in self._device_cache:
                if capability in self._device_cache[device_id].get("capabilitiesObj", {}):
                    self._device_cache[device_id]["capabilitiesObj"][capability]["value"] = converted_value

            logger.info(f"Device {device_id} capability {capability} set to {converted_value}")
            return True

        except Exception as e:
            logger.error(f"Error setting capability: {e}")
            logger.error(f"Endpoint: {endpoint}")
            logger.error(f"Payload: {payload}")
            raise

    async def get_flows(self) -> Dict[str, Any]:
        """Get all flows."""
        # Demo mode data
        if self.config.offline_mode or self.config.demo_mode:
            demo_flows = {
                "flow1": {
                    "id": "flow1",
                    "name": "Good Morning Routine",
                    "enabled": True,
                    "broken": False,
                },
                "flow2": {"id": "flow2", "name": "Evening Routine", "enabled": True, "broken": False},
            }
            logger.info(f"Demo mode: {len(demo_flows)} demo flows")
            return demo_flows

        try:
            # FIX: Add trailing slash
            response = await self.session.get("/api/manager/flow/flow/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting flows: {e}")
            raise

    async def trigger_flow(self, flow_id: str) -> bool:
        """Start a flow."""
        # Demo mode
        if self.config.offline_mode or self.config.demo_mode:
            logger.info(f"Demo mode: Flow {flow_id} would be started")
            return True

        try:
            # Try different endpoint variants
            endpoints_to_try = [
                f"/api/manager/flow/flow/{flow_id}/trigger",
                f"/api/manager/flow/flow/{flow_id}/start", 
                f"/api/manager/flow/flow/{flow_id}/run",
                f"/api/manager/flow/flow/{flow_id}/"
            ]
            
            last_error = None
            
            for endpoint in endpoints_to_try:
                try:
                    logger.debug(f"Trying flow trigger endpoint: {endpoint}")
                    response = await self.session.post(endpoint)
                    response.raise_for_status()
                    
                    logger.info(f"✅ Flow {flow_id} triggered via {endpoint}")
                    return True
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        logger.debug(f"Endpoint {endpoint} not found, trying next...")
                        last_error = e
                        continue
                    else:
                        # Other HTTP error, stop trying
                        raise e
                except Exception as e:
                    last_error = e
                    continue
            
            # If we get here, none of the endpoints worked
            logger.error(f"No working flow trigger endpoint found for flow {flow_id}")
            if last_error:
                raise last_error
            else:
                raise Exception("All flow trigger endpoints failed")

        except Exception as e:
            logger.error(f"Error triggering flow: {e}")
            raise

    async def get_insights_logs(self) -> Dict[str, Any]:
        """Get all insights logs."""
        if self.config.offline_mode or self.config.demo_mode:
            # Demo data for insights logs
            return {
                "light1.onoff": {
                    "id": "onoff",
                    "uri": "homey:device:light1",
                    "name": "Living Room Lamp - On/Off",
                    "type": "boolean",
                    "units": "",
                    "decimals": 0
                },
                "light1.dim": {
                    "id": "dim", 
                    "uri": "homey:device:light1",
                    "name": "Living Room Lamp - Brightness",
                    "type": "number",
                    "units": "%",
                    "decimals": 1
                },
                "sensor1.measure_temperature": {
                    "id": "measure_temperature",
                    "uri": "homey:device:sensor1", 
                    "name": "Temperature Sensor - Temperature",
                    "type": "number",
                    "units": "°C",
                    "decimals": 1
                },
                "socket1.measure_power": {
                    "id": "measure_power",
                    "uri": "homey:device:socket1",
                    "name": "Desk Socket - Power",
                    "type": "number", 
                    "units": "W",
                    "decimals": 1
                }
            }

        try:
            # Try both V2 and V3 API endpoints
            endpoints_to_try = [
                "/api/manager/insights/log",      # V3 format
                "/api/manager/insights/log/"      # V2 format
            ]
            
            raw_data = None
            for endpoint in endpoints_to_try:
                try:
                    response = await self.session.get(endpoint)
                    if response.status_code == 200:
                        raw_data = response.json()
                        logger.debug(f"Successfully got insights logs from {endpoint}")
                        break
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint} failed: {e}")
                    continue
            
            if raw_data is None:
                logger.warning("No insights log endpoint worked")
                return {}
            
            # Handle both list and dict responses
            if isinstance(raw_data, list):
                # Convert list to dict format for consistent handling using NEW format
                logs_dict = {}
                for log in raw_data:
                    if isinstance(log, dict) and "id" in log and "ownerUri" in log:
                        # NEW FORMAT: Extract device ID and capability from the structured data
                        full_id = log.get("id", "")
                        owner_uri = log.get("ownerUri", "")
                        capability = log.get("ownerId", "")
                        device_name = log.get("ownerName", "Unknown")
                        
                        # Extract device ID from ownerUri (homey:device:xxxxx)
                        uri_parts = owner_uri.split(":")
                        device_id = uri_parts[-1] if len(uri_parts) > 2 else "unknown"
                        
                        # Create a simple key for easier access
                        key = f"{device_id}.{capability}"
                        
                        logs_dict[key] = {
                            "id": capability,  # Just the capability name
                            "full_id": full_id,  # Full insights ID for API calls
                            "uri": owner_uri,  # Device URI
                            "name": f"{device_name} - {log.get('title', capability)}",
                            "type": log.get("type", "unknown"),
                            "units": log.get("units", ""),
                            "decimals": log.get("decimals", 1),
                            "lastValue": log.get("lastValue", None)
                        }
                        
                return logs_dict
            else:
                # Already a dict
                return raw_data
                
        except Exception as e:
            logger.error(f"Error getting insights logs: {e}")
            raise

    async def get_insights_state(self) -> Dict[str, Any]:
        """Get insights manager state."""
        if self.config.offline_mode or self.config.demo_mode:
            return {
                "enabled": True,
                "version": "1.0.0",
                "storage": {
                    "used": 1024 * 1024 * 50,  # 50MB
                    "total": 1024 * 1024 * 1024,  # 1GB
                }
            }

        try:
            response = await self.session.get("/api/manager/insights/state")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting insights state: {e}")
            raise

    async def get_insights_log(self, log_id: str) -> Dict[str, Any]:
        """Get specific insights log by ID."""
        if self.config.offline_mode or self.config.demo_mode:
            logs = await self.get_insights_logs()
            return logs.get(log_id, {})

        try:
            response = await self.session.get(f"/api/manager/insights/log/{log_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting insights log {log_id}: {e}")
            raise

    async def get_insights_log_entries(self, uri: str, log_id: str, resolution: str = "1h", from_timestamp: Optional[str] = None, to_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get log entries for a specific insight log."""
        if self.config.offline_mode or self.config.demo_mode:
            # Generate demo data based on log type
            import random
            from datetime import datetime, timedelta
            
            entries = []
            
            # Generate last 24 hours of data
            now = datetime.now()
            hours_back = 24 if resolution == "1h" else 7 * 24
            interval_minutes = 60 if resolution == "1h" else 60 * 24
            
            for i in range(hours_back):
                timestamp = now - timedelta(minutes=i * interval_minutes)
                
                if "temperature" in log_id:
                    value = round(random.uniform(18.0, 24.0), 1)
                elif "dim" in log_id:
                    value = round(random.uniform(0.0, 1.0), 2)
                elif "power" in log_id:
                    value = round(random.uniform(10.0, 100.0), 1)
                elif "onoff" in log_id:
                    value = random.choice([True, False])
                else:
                    value = round(random.uniform(0, 100), 1)
                
                entries.append({
                    "t": timestamp.isoformat(),
                    "v": value
                })
            
            return sorted(entries, key=lambda x: x["t"])

        try:
            # NEW CORRECT FORMAT: Use the full insights log ID
            # First, we need to find the full_id for this device/capability combo
            logs = await self.get_insights_logs()
            
            # Find the matching log
            device_id = uri.split(":")[-1] if ":" in uri else uri
            search_key = f"{device_id}.{log_id}"
            
            if search_key not in logs:
                logger.warning(f"No insights log found for {search_key}")
                return []
            
            log_info = logs[search_key]
            full_log_id = log_info.get("full_id")
            
            if not full_log_id:
                logger.warning(f"No full_id found for log {search_key}")
                return []
            
            # Use the correct endpoint with full insights log ID (URL encoded)
            import urllib.parse
            encoded_log_id = urllib.parse.quote(full_log_id, safe='')
            endpoint = f"/api/manager/insights/log/{encoded_log_id}/entry"
            params = {}
            
            if resolution:
                params["resolution"] = resolution
            if from_timestamp:
                params["from"] = from_timestamp
            if to_timestamp:
                params["to"] = to_timestamp
                
            response = await self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting insights log entries for {uri}/{log_id}: {e}")
            raise

    async def get_insights_storage_info(self) -> Dict[str, Any]:
        """Get insights storage information."""
        if self.config.offline_mode or self.config.demo_mode:
            return {
                "used": 1024 * 1024 * 50,  # 50MB
                "total": 1024 * 1024 * 1024,  # 1GB
                "entries": 125000,
                "logs": 25
            }

        try:
            # Try different possible endpoints for storage info
            endpoints = [
                "/api/manager/insights/storage",
                "/api/manager/insights/",
                "/api/manager/insights"
            ]
            
            for endpoint in endpoints:
                try:
                    response = await self.session.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        # Check if this looks like storage info
                        if isinstance(data, dict) and any(key in data for key in ["used", "total", "storage", "size"]):
                            return data
                except:
                    continue
            
            # If no storage endpoint works, return estimated info based on logs
            logs = await self.get_insights_logs()
            return {
                "used": len(logs) * 1024 * 100,  # Estimate: 100KB per log
                "total": 1024 * 1024 * 1024,  # Estimate: 1GB total
                "entries": len(logs) * 1000,  # Estimate: 1000 entries per log
                "logs": len(logs)
            }
            
        except Exception as e:
            logger.error(f"Error getting insights storage info: {e}")
            # Return fallback data
            return {
                "used": 0,
                "total": 1024 * 1024 * 1024,  # 1GB
                "entries": 0,
                "logs": 0
            }

    async def get_energy_state(self) -> Dict[str, Any]:
        """Get energy manager state."""
        if self.config.offline_mode or self.config.demo_mode:
            return {
                "available": True,
                "currency": "EUR",
                "electricityPriceFixed": 0.30,
                "gasPriceFixed": 1.20,
                "waterPriceFixed": 2.50
            }

        try:
            response = await self.session.get("/api/manager/energy/state")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting energy state: {e}")
            raise

    async def get_energy_live_report(self, zone: Optional[str] = None) -> Dict[str, Any]:
        """Get live energy report."""
        if self.config.offline_mode or self.config.demo_mode:
            import random
            return {
                "electricity": {
                    "total": round(random.uniform(500, 2000), 1),
                    "devices": [
                        {"id": "device1", "name": "Washing Machine", "value": round(random.uniform(100, 500), 1)},
                        {"id": "device2", "name": "Refrigerator", "value": round(random.uniform(50, 150), 1)},
                        {"id": "device3", "name": "TV", "value": round(random.uniform(20, 80), 1)}
                    ]
                },
                "gas": {"total": round(random.uniform(0, 20), 1)},
                "water": {"total": round(random.uniform(0, 5), 1)}
            }

        try:
            params = {"zone": zone} if zone else {}
            response = await self.session.get("/api/manager/energy/live", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting live energy report: {e}")
            raise

    async def get_energy_report_day(self, date: str, cache: Optional[str] = None) -> Dict[str, Any]:
        """Get daily energy report."""
        if self.config.offline_mode or self.config.demo_mode:
            import random
            return {
                "date": date,
                "electricity": {
                    "consumed": round(random.uniform(15, 35), 2),
                    "produced": round(random.uniform(0, 10), 2),
                    "cost": round(random.uniform(4, 12), 2)
                },
                "gas": {
                    "consumed": round(random.uniform(5, 25), 2),
                    "cost": round(random.uniform(6, 30), 2)
                },
                "water": {
                    "consumed": round(random.uniform(100, 300), 1),
                    "cost": round(random.uniform(0.25, 0.75), 2)
                }
            }

        try:
            params = {"date": date}
            if cache:
                params["cache"] = cache
            response = await self.session.get("/api/manager/energy/report/day", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting daily energy report: {e}")
            raise

    async def get_energy_report_week(self, iso_week: str, cache: Optional[str] = None) -> Dict[str, Any]:
        """Get weekly energy report."""
        if self.config.offline_mode or self.config.demo_mode:
            import random
            return {
                "week": iso_week,
                "electricity": {
                    "consumed": round(random.uniform(100, 250), 2),
                    "produced": round(random.uniform(0, 70), 2),
                    "cost": round(random.uniform(30, 80), 2)
                },
                "gas": {
                    "consumed": round(random.uniform(35, 175), 2),
                    "cost": round(random.uniform(42, 210), 2)
                },
                "water": {
                    "consumed": round(random.uniform(700, 2100), 1),
                    "cost": round(random.uniform(1.75, 5.25), 2)
                }
            }

        try:
            params = {"isoWeek": iso_week}
            if cache:
                params["cache"] = cache
            response = await self.session.get("/api/manager/energy/report/week", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting weekly energy report: {e}")
            raise

    async def get_energy_report_month(self, year_month: str, cache: Optional[str] = None) -> Dict[str, Any]:
        """Get monthly energy report."""
        if self.config.offline_mode or self.config.demo_mode:
            import random
            return {
                "month": year_month,
                "electricity": {
                    "consumed": round(random.uniform(400, 1000), 2),
                    "produced": round(random.uniform(0, 300), 2),
                    "cost": round(random.uniform(120, 320), 2)
                },
                "gas": {
                    "consumed": round(random.uniform(150, 750), 2),
                    "cost": round(random.uniform(180, 900), 2)
                },
                "water": {
                    "consumed": round(random.uniform(3000, 9000), 1),
                    "cost": round(random.uniform(7.5, 22.5), 2)
                }
            }

        try:
            params = {"yearMonth": year_month}
            if cache:
                params["cache"] = cache
            response = await self.session.get("/api/manager/energy/report/month", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting monthly energy report: {e}")
            raise

    async def get_energy_reports_available(self) -> Dict[str, Any]:
        """Get available energy reports."""
        if self.config.offline_mode or self.config.demo_mode:
            from datetime import datetime, timedelta
            today = datetime.now()
            return {
                "days": [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)],
                "weeks": [f"{(today - timedelta(weeks=i)).isocalendar()[0]}-W{(today - timedelta(weeks=i)).isocalendar()[1]:02d}" for i in range(12)],
                "months": [(today - timedelta(days=30*i)).strftime("%Y-%m") for i in range(12)]
            }

        try:
            response = await self.session.get("/api/manager/energy/reports/available")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting available reports: {e}")
            raise

    async def get_energy_currency(self) -> Dict[str, Any]:
        """Get energy currency settings."""
        if self.config.offline_mode or self.config.demo_mode:
            return {"currency": "EUR", "symbol": "€"}

        try:
            response = await self.session.get("/api/manager/energy/currency")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting energy currency: {e}")
            raise

    async def test_endpoints(self) -> Dict[str, bool]:
        """Test different endpoint variants."""
        if self.config.offline_mode or self.config.demo_mode:
            return {"demo_mode": True}
        
        results = {}
        test_endpoints = [
            "/api/manager/system",
            "/api/manager/devices/device",
            "/api/manager/devices/device/", 
            "/api/manager/flow/flow",
            "/api/manager/flow/flow/",
            "/api/manager/geolocation/",
            "/api/manager/cloud/state/",
            "/api/manager/insights/log",
            "/api/manager/insights/log/", 
            "/api/manager/insights/state",
            "/api/manager/insights/storage",
            "/api/manager/energy/state",
            "/api/manager/energy/live",
            "/api/manager/energy/currency",
        ]
        
        for endpoint in test_endpoints:
            try:
                response = await self.session.get(endpoint)
                results[endpoint] = response.status_code == 200
            except Exception as e:
                results[endpoint] = False
                logger.debug(f"Endpoint {endpoint} failed: {e}")
        
        return results
