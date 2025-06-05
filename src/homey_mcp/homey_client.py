import httpx
import asyncio
import logging
from typing import Dict, Any, Optional, List
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
            "Content-Type": "application/json"
        }
        
        self.session = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.config.request_timeout)
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
        
        # Demo mode data
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
                        "dim": {"value": 0.8, "title": "Helderheid"}
                    }
                },
                "sensor1": {
                    "id": "sensor1",
                    "name": "Temperatuur Sensor",
                    "class": "sensor",
                    "zoneName": "Slaapkamer",
                    "available": True,
                    "capabilitiesObj": {
                        "measure_temperature": {"value": 21.5, "title": "Temperatuur"}
                    }
                }
            }
            logger.info(f"Demo mode: {len(demo_devices)} demo devices")
            return demo_devices
        
        # Check cache
        if (self._device_cache and 
            time.time() - self._cache_timestamp < self.config.cache_ttl):
            return self._device_cache
        
        try:
            response = await self.session.get("/api/manager/devices/device")
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
    
    async def set_capability_value(self, device_id: str, capability: str, value: Any) -> bool:
        """Zet capability waarde van device."""
        # Demo mode
        if self.config.offline_mode or self.config.demo_mode:
            logger.info(f"Demo mode: Device {device_id} capability {capability} zou worden gezet naar {value}")
            return True
            
        try:
            endpoint = f"/api/manager/devices/device/{device_id}/state"
            payload = {capability: value}
            
            response = await self.session.put(endpoint, json=payload)
            response.raise_for_status()
            
            # Cache invalideren voor dit device
            if self._device_cache and device_id in self._device_cache:
                if capability in self._device_cache[device_id].get('capabilitiesObj', {}):
                    self._device_cache[device_id]['capabilitiesObj'][capability]['value'] = value
            
            logger.info(f"Device {device_id} capability {capability} set to {value}")
            return True
            
        except Exception as e:
            logger.error(f"Fout bij zetten capability: {e}")
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
                    "broken": False
                },
                "flow2": {
                    "id": "flow2",
                    "name": "Avond Routine",
                    "enabled": True,
                    "broken": False
                }
            }
            logger.info(f"Demo mode: {len(demo_flows)} demo flows")
            return demo_flows
            
        try:
            response = await self.session.get("/api/manager/flow/flow")
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
            endpoint = f"/api/manager/flow/flow/{flow_id}/trigger"
            response = await self.session.post(endpoint)
            response.raise_for_status()
            
            logger.info(f"Flow {flow_id} getriggerd")
            return True
        except Exception as e:
            logger.error(f"Fout bij triggeren flow: {e}")
            raise
