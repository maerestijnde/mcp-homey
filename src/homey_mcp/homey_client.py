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
        """Maak verbinding met Homey API."""
        # Check voor offline mode
        if self.config.offline_mode:
            logger.info("Offline mode - skip Homey verbinding")
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

        # Test connectie
        try:
            logger.info(f"Proberen te verbinden met Homey op {self.base_url}...")
            response = await self.session.get("/api/manager/system")
            response.raise_for_status()
            logger.info("✅ Successvol verbonden met Homey")
        except httpx.ConnectTimeout:
            logger.error(f"❌ Connection timeout naar {self.base_url}")
            logger.error("💡 Check of:")
            logger.error("   - Homey IP adres correct is")
            logger.error("   - Homey bereikbaar is op het netwerk")
            logger.error("   - Firewall settings")
            raise ConnectionError(f"Kan niet verbinden met Homey op {self.base_url}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("❌ Unauthorized - check je Personal Access Token")
            else:
                logger.error(f"❌ HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ Onbekende fout bij verbinden met Homey: {e}")
            raise

    async def disconnect(self):
        """Sluit verbinding."""
        if self.session:
            await self.session.aclose()

    async def get_devices(self) -> Dict[str, Any]:
        """Haal alle devices op (met caching)."""
        import time

        # Demo mode data - UITGEBREID EN GECORRIGEERD
        if self.config.offline_mode or self.config.demo_mode:
            demo_devices = {
                "light1": {
                    "id": "light1",
                    "name": "Woonkamer Lamp",
                    "class": "light",
                    "zoneName": "Woonkamer", 
                    "available": True,
                    "capabilitiesObj": {
                        "onoff": {"value": False, "title": "Aan/Uit"},
                        "dim": {"value": 0.8, "title": "Helderheid"},  # 0.0-1.0 (80%)
                        "light_hue": {"value": 0.2, "title": "Kleur"},  # 0.0-1.0 (hue)
                        "light_saturation": {"value": 0.9, "title": "Verzadiging"},  # 0.0-1.0
                        "light_temperature": {"value": 0.5, "title": "Kleurtemperatuur"},  # 0.0-1.0
                        "light_mode": {"value": "color", "title": "Modus"}  # color/temperature
                    },
                },
                "light2": {
                    "id": "light2", 
                    "name": "Keuken Spots",
                    "class": "light",
                    "zoneName": "Keuken",
                    "available": True,
                    "capabilitiesObj": {
                        "onoff": {"value": True, "title": "Aan/Uit"},
                        "dim": {"value": 0.6, "title": "Helderheid"},  # 60%
                        # Alleen warm/koud wit, geen kleur
                        "light_temperature": {"value": 0.3, "title": "Kleurtemperatuur"}
                    },
                },
                "sensor1": {
                    "id": "sensor1",
                    "name": "Temperatuur Sensor",
                    "class": "sensor", 
                    "zoneName": "Slaapkamer",
                    "available": True,
                    "capabilitiesObj": {
                        "measure_temperature": {"value": 21.5, "title": "Temperatuur"},  # °C
                        "measure_humidity": {"value": 65.2, "title": "Luchtvochtigheid"},  # %
                        "measure_battery": {"value": 85, "title": "Batterij"},  # %
                        "alarm_battery": {"value": False, "title": "Batterij Leeg"}  # boolean
                    },
                },
                "thermostat1": {
                    "id": "thermostat1",
                    "name": "Woonkamer Thermostaat", 
                    "class": "thermostat",
                    "zoneName": "Woonkamer",
                    "available": True,
                    "capabilitiesObj": {
                        "target_temperature": {"value": 20.0, "title": "Gewenste Temperatuur"},  # SETABLE
                        "measure_temperature": {"value": 19.2, "title": "Huidige Temperatuur"},  # READ-ONLY
                        "measure_battery": {"value": 92, "title": "Batterij"}
                    },
                },
                "socket1": {
                    "id": "socket1",
                    "name": "Bureau Stopcontact",
                    "class": "socket", 
                    "zoneName": "Kantoor",
                    "available": True,
                    "capabilitiesObj": {
                        "onoff": {"value": True, "title": "Aan/Uit"},
                        "measure_power": {"value": 45.2, "title": "Vermogen"},  # Watt
                        "meter_power": {"value": 2.34, "title": "Energieverbruik"}  # kWh
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

            logger.info(f"Devices opgehaald: {len(devices)} devices")
            return devices

        except Exception as e:
            logger.error(f"Fout bij ophalen devices: {e}")
            raise

    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """Haal specifiek device op."""
        devices = await self.get_devices()

        if device_id not in devices:
            raise ValueError(f"Device {device_id} niet gevonden")

        return devices[device_id]

    def validate_capability_value(self, capability: str, value: Any) -> tuple[bool, Any, str]:
        """
        Valideer en converteer capability waarde naar correct formaat.
        
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
            return False, value, f"Capability {capability} verwacht boolean waarde"
        
        # Range capabilities (0.0 - 1.0)
        if capability in ["dim", "light_hue", "light_saturation", "light_temperature", "volume_set", "windowcoverings_set", "windowcoverings_tilt_set"]:
            try:
                float_val = float(value)
                if 0.0 <= float_val <= 1.0:
                    return True, float_val, ""
                # Auto-convert percentage naar fractie
                elif 0 <= float_val <= 100:
                    converted = float_val / 100.0
                    return True, converted, f"Converted {float_val}% to {converted}"
                else:
                    return False, value, f"Capability {capability} moet tussen 0.0-1.0 zijn (of 0-100%)"
            except (ValueError, TypeError):
                return False, value, f"Capability {capability} verwacht numerieke waarde"
        
        # Temperature capabilities  
        if capability in ["target_temperature", "measure_temperature"]:
            try:
                temp = float(value)
                if -50 <= temp <= 100:  # Redelijke temperatuur range
                    return True, temp, ""
                else:
                    return False, value, f"Temperatuur {temp}°C lijkt onrealistisch"
            except (ValueError, TypeError):
                return False, value, f"Temperatuur moet numeriek zijn"
        
        # Power/energy capabilities
        if capability in ["measure_power", "meter_power", "measure_voltage", "measure_current"]:
            try:
                power = float(value)
                if power >= 0:
                    return True, power, ""
                else:
                    return False, value, "Power/energie kan niet negatief zijn"
            except (ValueError, TypeError):
                return False, value, f"Capability {capability} verwacht numerieke waarde"
        
        # Percentage capabilities (0-100)
        if capability in ["measure_battery", "measure_humidity"]:
            try:
                percentage = float(value)
                if 0 <= percentage <= 100:
                    return True, percentage, ""
                else:
                    return False, value, f"Capability {capability} moet tussen 0-100% zijn"
            except (ValueError, TypeError):
                return False, value, f"Capability {capability} verwacht numerieke waarde"
        
        # String/enum capabilities
        if capability in ["light_mode"]:
            if capability == "light_mode" and value in ["color", "temperature"]:
                return True, value, ""
            return False, value, f"Capability {capability} heeft ongeldige waarde: {value}"
        
        # Default: accept as-is
        return True, value, ""

    async def set_capability_value(self, device_id: str, capability: str, value: Any) -> bool:
        """Zet capability waarde van device."""
        # Valideer waarde eerst
        is_valid, converted_value, message = self.validate_capability_value(capability, value)
        if not is_valid:
            raise ValueError(f"Ongeldige capability waarde: {message}")
        
        if message:
            logger.info(f"Capability waarde geconverteerd: {message}")

        # Demo mode
        if self.config.offline_mode or self.config.demo_mode:
            logger.info(
                f"Demo mode: Device {device_id} capability {capability} zou worden gezet naar {converted_value}"
            )
            return True

        try:
            # BELANGRIJKSTE FIX: Correct endpoint format met trailing slash
            endpoint = f"/api/manager/devices/device/{device_id}/capability/{capability}/"
            payload = {"value": converted_value}  # Gebruik gevalideerde waarde!

            # KRITIEKE FIX: Gebruik PUT in plaats van POST!
            response = await self.session.put(endpoint, json=payload)
            
            # Fallback: Als PUT niet werkt, probeer POST (voor compatibiliteit)
            if response.status_code == 405:  # Method Not Allowed
                logger.warning(f"PUT niet ondersteund voor {endpoint}, probeer POST...")
                response = await self.session.post(endpoint, json=payload)
            
            response.raise_for_status()

            # Cache invalideren voor dit device
            if self._device_cache and device_id in self._device_cache:
                if capability in self._device_cache[device_id].get("capabilitiesObj", {}):
                    self._device_cache[device_id]["capabilitiesObj"][capability]["value"] = converted_value

            logger.info(f"Device {device_id} capability {capability} set to {converted_value}")
            return True

        except Exception as e:
            logger.error(f"Fout bij zetten capability: {e}")
            logger.error(f"Endpoint: {endpoint}")
            logger.error(f"Payload: {payload}")
            raise

    async def get_flows(self) -> Dict[str, Any]:
        """Haal alle flows op."""
        # Demo mode data
        if self.config.offline_mode or self.config.demo_mode:
            demo_flows = {
                "flow1": {
                    "id": "flow1",
                    "name": "Goedemorgen Routine",
                    "enabled": True,
                    "broken": False,
                },
                "flow2": {"id": "flow2", "name": "Avond Routine", "enabled": True, "broken": False},
            }
            logger.info(f"Demo mode: {len(demo_flows)} demo flows")
            return demo_flows

        try:
            # FIX: Voeg trailing slash toe
            response = await self.session.get("/api/manager/flow/flow/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Fout bij ophalen flows: {e}")
            raise

    async def trigger_flow(self, flow_id: str) -> bool:
        """Start een flow."""
        # Demo mode
        if self.config.offline_mode or self.config.demo_mode:
            logger.info(f"Demo mode: Flow {flow_id} zou worden gestart")
            return True

        try:
            # Probeer verschillende endpoint varianten
            endpoints_to_try = [
                f"/api/manager/flow/flow/{flow_id}/trigger",
                f"/api/manager/flow/flow/{flow_id}/start", 
                f"/api/manager/flow/flow/{flow_id}/run",
                f"/api/manager/flow/flow/{flow_id}/"
            ]
            
            last_error = None
            
            for endpoint in endpoints_to_try:
                try:
                    logger.debug(f"Probeer flow trigger endpoint: {endpoint}")
                    response = await self.session.post(endpoint)
                    response.raise_for_status()
                    
                    logger.info(f"✅ Flow {flow_id} getriggerd via {endpoint}")
                    return True
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        logger.debug(f"Endpoint {endpoint} niet gevonden, probeer volgende...")
                        last_error = e
                        continue
                    else:
                        # Andere HTTP error, stop proberen
                        raise e
                except Exception as e:
                    last_error = e
                    continue
            
            # Als we hier komen, werkte geen van de endpoints
            logger.error(f"Geen werkend flow trigger endpoint gevonden voor flow {flow_id}")
            if last_error:
                raise last_error
            else:
                raise Exception("Alle flow trigger endpoints faalden")

        except Exception as e:
            logger.error(f"Fout bij triggeren flow: {e}")
            raise

    async def test_endpoints(self) -> Dict[str, bool]:
        """Test verschillende endpoint varianten."""
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
        ]
        
        for endpoint in test_endpoints:
            try:
                response = await self.session.get(endpoint)
                results[endpoint] = response.status_code == 200
            except Exception as e:
                results[endpoint] = False
                logger.debug(f"Endpoint {endpoint} faal: {e}")
        
        return results
