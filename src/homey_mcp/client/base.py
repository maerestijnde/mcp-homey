import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from ..config import HomeyMCPConfig
from .devices import DeviceAPI
from .flows import FlowAPI
from .insights import InsightsAPI
from .energy import EnergyAPI
from .zones import ZonesAPI

logger = logging.getLogger(__name__)


class HomeyAPIClient:
    def __init__(self, config: HomeyMCPConfig):
        self.config = config
        self._scheme = "https" if config.homey_use_https else "http"
        self.base_url = f"{self._scheme}://{config.homey_local_address}"
        self.session: Optional[httpx.AsyncClient] = None
        self._device_cache: Dict[str, Any] = {}
        self._cache_timestamp = 0

        # Initialize API modules
        self.devices = DeviceAPI(self)
        self.flows = FlowAPI(self)
        self.insights = InsightsAPI(self)
        self.energy = EnergyAPI(self)
        self.zones = ZonesAPI(self)

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

        if self.session is None:
            verify_ssl = self.config.homey_verify_ssl if self._scheme == "https" else True

            self.session = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.config.request_timeout),
                verify=verify_ssl,
            )

            if self._scheme == "https" and not self.config.homey_verify_ssl:
                logger.debug("HTTPS certificate verification disabled for Homey local API (self-signed cert)")

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

    # Delegate methods to maintain compatibility
    async def get_devices(self) -> Dict[str, Any]:
        return await self.devices.get_devices()

    async def get_device(self, device_id: str) -> Dict[str, Any]:
        return await self.devices.get_device(device_id)

    async def get_zones(self) -> Dict[str, Any]:
        """Get all zones by extracting them from devices."""
        devices = await self.get_devices()
        zones = {}
        
        for device_id, device in devices.items():
            zone_id = device.get("zone")
            zone_name = device.get("zoneName")
            
            if zone_id and zone_name and zone_id not in zones:
                zones[zone_id] = {
                    "id": zone_id,
                    "name": zone_name
                }
        
        return zones

    async def get_zone(self, zone_id: str) -> Dict[str, Any]:
        """Get specific zone by ID."""
        zones = await self.get_zones()
        if zone_id not in zones:
            raise ValueError(f"Zone {zone_id} not found")
        return zones[zone_id]

    async def find_zone_by_name(self, zone_name: str) -> Dict[str, Any]:
        """Find zone by name (partial match)."""
        zones = await self.get_zones()
        zone_name_lower = zone_name.lower()
        
        for zone_id, zone in zones.items():
            if zone_name_lower in zone.get("name", "").lower():
                return zone
        return None

    def validate_capability_value(self, capability: str, value: Any) -> tuple[bool, Any, str]:
        return self.devices.validate_capability_value(capability, value)

    async def set_capability_value(self, device_id: str, capability: str, value: Any) -> bool:
        return await self.devices.set_capability_value(device_id, capability, value)

    # ================== REGULAR FLOWS ==================
    async def get_flows(self) -> Dict[str, Any]:
        return await self.flows.get_flows()

    async def get_flow(self, flow_id: str) -> Dict[str, Any]:
        return await self.flows.get_flow(flow_id)

    async def trigger_flow(self, flow_id: str) -> bool:
        return await self.flows.trigger_flow(flow_id)

    async def create_flow(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.flows.create_flow(flow_data)

    async def update_flow(self, flow_id: str, **kwargs) -> Dict[str, Any]:
        return await self.flows.update_flow(flow_id, **kwargs)

    async def delete_flow(self, flow_id: str) -> bool:
        return await self.flows.delete_flow(flow_id)

    async def test_flow(self, flow_data: Dict[str, Any], tokens: Dict[str, Any] = None) -> Dict[str, Any]:
        return await self.flows.test_flow(flow_data, tokens)

    # ================== ADVANCED FLOWS ==================
    async def get_advanced_flows(self) -> Dict[str, Any]:
        return await self.flows.get_advanced_flows()

    async def get_advanced_flow(self, flow_id: str) -> Dict[str, Any]:
        return await self.flows.get_advanced_flow(flow_id)

    async def trigger_advanced_flow(self, flow_id: str) -> bool:
        return await self.flows.trigger_advanced_flow(flow_id)

    async def create_advanced_flow(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.flows.create_advanced_flow(flow_data)

    async def update_advanced_flow(self, flow_id: str, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.flows.update_advanced_flow(flow_id, flow_data)

    async def delete_advanced_flow(self, flow_id: str) -> bool:
        return await self.flows.delete_advanced_flow(flow_id)

    # ================== FLOW FOLDERS ==================
    async def get_flow_folders(self) -> Dict[str, Any]:
        return await self.flows.get_flow_folders()

    async def get_flow_folder(self, folder_id: str) -> Dict[str, Any]:
        return await self.flows.get_flow_folder(folder_id)

    async def create_flow_folder(self, name: str, parent: str = None) -> Dict[str, Any]:
        return await self.flows.create_flow_folder(name, parent)

    # ================== FLOW CARDS ==================
    async def get_flow_card_triggers(self) -> Dict[str, Any]:
        return await self.flows.get_flow_card_triggers()

    async def get_flow_card_conditions(self) -> Dict[str, Any]:
        return await self.flows.get_flow_card_conditions()

    async def get_flow_card_actions(self) -> Dict[str, Any]:
        return await self.flows.get_flow_card_actions()

    # ================== FLOW UTILITIES ==================
    async def get_flow_state(self) -> Dict[str, Any]:
        return await self.flows.get_flow_state()

    async def run_flow_card_action(self, uri: str, action_id: str, args: Dict[str, Any] = None, 
                                  tokens: Dict[str, Any] = None) -> Dict[str, Any]:
        return await self.flows.run_flow_card_action(uri, action_id, args, tokens)

    async def get_insights_logs(self) -> Dict[str, Any]:
        return await self.insights.get_insights_logs()

    async def get_insights_state(self) -> Dict[str, Any]:
        return await self.insights.get_insights_state()

    async def get_insights_log(self, log_id: str) -> Dict[str, Any]:
        return await self.insights.get_insights_log(log_id)

    async def get_insights_log_entries(self, uri: str, log_id: str, resolution: str = "1h", from_timestamp: Optional[str] = None, to_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self.insights.get_insights_log_entries(uri, log_id, resolution, from_timestamp, to_timestamp)

    async def get_insights_storage_info(self) -> Dict[str, Any]:
        return await self.insights.get_insights_storage_info()

    async def get_energy_state(self) -> Dict[str, Any]:
        return await self.energy.get_energy_state()

    async def get_energy_live_report(self, zone: Optional[str] = None) -> Dict[str, Any]:
        return await self.energy.get_energy_live_report(zone)

    async def get_energy_report_day(self, date: str, cache: Optional[str] = None) -> Dict[str, Any]:
        return await self.energy.get_energy_report_day(date, cache)

    async def get_energy_report_week(self, iso_week: str, cache: Optional[str] = None) -> Dict[str, Any]:
        return await self.energy.get_energy_report_week(iso_week, cache)

    async def get_energy_report_month(self, year_month: str, cache: Optional[str] = None) -> Dict[str, Any]:
        return await self.energy.get_energy_report_month(year_month, cache)

    async def get_energy_reports_available(self) -> Dict[str, Any]:
        return await self.energy.get_energy_reports_available()

    async def get_energy_report_hour(self, date_hour: str, cache: Optional[str] = None) -> Dict[str, Any]:
        return await self.energy.get_energy_report_hour(date_hour, cache)

    async def get_energy_report_year(self, year: str, cache: Optional[str] = None) -> Dict[str, Any]:
        return await self.energy.get_energy_report_year(year, cache)

    async def get_energy_currency(self) -> Dict[str, Any]:
        return await self.energy.get_energy_currency()

    # Zones delegate methods  
    async def get_zones(self) -> Dict[str, Any]:
        return await self.devices.get_zones()

    async def get_zone(self, zone_id: str) -> Dict[str, Any]:
        return await self.zones.get_zone(zone_id)

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
            "/api/manager/zones/zone/",  # CORRECT endpoint for Local API v3
            "/api/manager/zones/state",
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
