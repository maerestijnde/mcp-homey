import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ZonesAPI:
    def __init__(self, client):
        self.client = client
        self._zone_cache: Dict[str, Any] = {}
        self._zone_cache_timestamp = 0

    async def get_zones(self) -> Dict[str, Any]:
        """Get all zones (with caching)."""
        # Demo mode data - Realistic zone structure
        if self.client.config.offline_mode or self.client.config.demo_mode:
            demo_zones = {
                "living-room-uuid": {
                    "id": "living-room-uuid",
                    "name": "Living Room",
                    "icon": "home",
                    "parent": None,
                    "active": True
                },
                "kitchen-uuid": {
                    "id": "kitchen-uuid", 
                    "name": "Kitchen",
                    "icon": "kitchen",
                    "parent": None,
                    "active": True
                },
                "bedroom-uuid": {
                    "id": "bedroom-uuid",
                    "name": "Bedroom", 
                    "icon": "bed",
                    "parent": None,
                    "active": True
                },
                "office-uuid": {
                    "id": "office-uuid",
                    "name": "Office",
                    "icon": "office",
                    "parent": None,
                    "active": True
                },
                "bathroom-uuid": {
                    "id": "bathroom-uuid",
                    "name": "Bathroom",
                    "icon": "bathroom", 
                    "parent": None,
                    "active": True
                },
                "garage-uuid": {
                    "id": "garage-uuid",
                    "name": "Garage",
                    "icon": "garage",
                    "parent": None,
                    "active": True
                }
            }
            logger.info(f"Demo mode: {len(demo_zones)} demo zones")
            return demo_zones

        # Check cache first
        if self._zone_cache and time.time() - self._zone_cache_timestamp < self.client.config.cache_ttl:
            logger.info(f"Returning cached zones: {len(self._zone_cache)} zones")
            return self._zone_cache

        try:
            # Try different endpoint variations for zones
            endpoints_to_try = [
                "/api/manager/zones/zone/",      # With trailing slash
                "/api/manager/zones/zone",       # Without trailing slash
                "/api/manager/zones/"            # Alternative endpoint
            ]
            
            zones_data = None
            for endpoint in endpoints_to_try:
                try:
                    logger.info(f"Trying zones endpoint: {endpoint}")
                    response = await self.client.session.get(endpoint)
                    logger.info(f"Response status: {response.status_code}")
                    if response.status_code == 200:
                        zones_data = response.json()
                        logger.info(f"✅ Zones retrieved from {endpoint}: {len(zones_data)} zones")
                        logger.info(f"Sample zone data: {list(zones_data.keys())[:3] if zones_data else 'None'}")
                        break
                except Exception as e:
                    logger.error(f"Endpoint {endpoint} failed: {e}")
                    continue
            
            if zones_data is None:
                logger.warning("No zones endpoint worked, returning empty zones")
                return {}

            # Cache the result
            self._zone_cache = zones_data
            self._zone_cache_timestamp = time.time()
            
            logger.info(f"Cached {len(zones_data)} zones successfully")
            return zones_data

        except Exception as e:
            logger.error(f"Error getting zones: {e}")
            raise

    async def get_zone(self, zone_id: str) -> Dict[str, Any]:
        """Get specific zone by ID."""
        zones = await self.get_zones()
        
        if zone_id not in zones:
            raise ValueError(f"Zone {zone_id} not found")
        
        return zones[zone_id]

    def find_zone_by_name(self, zones: Dict[str, Any], zone_name: str) -> tuple[str, Dict[str, Any]]:
        """
        Find zone by name (case-insensitive).
        
        Returns:
            (zone_id, zone_data) or (None, None) if not found
        """
        zone_name_lower = zone_name.lower()
        
        for zone_id, zone_data in zones.items():
            if zone_data.get("name", "").lower() == zone_name_lower:
                return zone_id, zone_data
        
        # Try partial matching
        for zone_id, zone_data in zones.items():
            if zone_name_lower in zone_data.get("name", "").lower():
                return zone_id, zone_data
        
        return None, None

    def invalidate_cache(self):
        """Invalidate zones cache."""
        self._zone_cache = {}
        self._zone_cache_timestamp = 0
