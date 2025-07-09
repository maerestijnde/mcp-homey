import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from ..config import HomeyMCPConfig
from .devices import DeviceAPI
from .flows import FlowAPI
from .insights import InsightsAPI
from .energy import EnergyAPI

logger = logging.getLogger(__name__)


class HomeyAPIClient:
    def __init__(self, config: HomeyMCPConfig):
        self.config = config
        self.base_url = f"http://{config.homey_local_address}"
        self.session: Optional[httpx.AsyncClient] = None
        self._device_cache: Dict[str, Any] = {}
        self._cache_timestamp = 0

        # Initialize API modules
        self.devices = DeviceAPI(self)
        self.flows = FlowAPI(self)
        self.insights = InsightsAPI(self)
        self.energy = EnergyAPI(self)

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

    # Delegate methods to maintain compatibility
    async def get_devices(self) -> Dict[str, Any]:
        return await self.devices.get_devices()

    async def get_device(self, device_id: str) -> Dict[str, Any]:
        return await self.devices.get_device(device_id)

    def validate_capability_value(self, capability: str, value: Any) -> tuple[bool, Any, str]:
        return self.devices.validate_capability_value(capability, value)

    async def set_capability_value(self, device_id: str, capability: str, value: Any) -> bool:
        return await self.devices.set_capability_value(device_id, capability, value)

    async def get_flows(self) -> Dict[str, Any]:
        return await self.flows.get_flows()

    async def trigger_flow(self, flow_id: str) -> bool:
        return await self.flows.trigger_flow(flow_id)

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