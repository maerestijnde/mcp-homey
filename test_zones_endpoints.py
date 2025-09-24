#!/usr/bin/env python3
"""
Test script om endpoints te testen voor zones op een echte Homey.

Run met echte Homey configuratie:
OFFLINE_MODE=false DEMO_MODE=false python test_zones_endpoints.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from homey_mcp.config import get_config
from homey_mcp.client import HomeyAPIClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_real_homey_endpoints():
    """Test zones endpoints op een echte Homey."""
    
    config = get_config()
    
    logger.info("🔍 Testing Real Homey Zones Endpoints")
    logger.info("=" * 60)
    logger.info(f"📋 Mode: Demo={config.demo_mode}, Offline={config.offline_mode}")
    logger.info(f"📋 Address: {config.homey_local_address}")
    
    if config.offline_mode or config.demo_mode:
        logger.warning("⚠️  Not testing real endpoints - demo/offline mode active")
        logger.info("To test real endpoints, set: OFFLINE_MODE=false DEMO_MODE=false")
        return
    
    async with HomeyAPIClient(config) as client:
        logger.info("✅ Connected to Homey")
        
        # Test all endpoints systematically
        endpoint_results = await client.test_endpoints()
        
        logger.info("\n🌐 ENDPOINT TEST RESULTS:")
        zones_endpoints = [k for k, v in endpoint_results.items() if 'zone' in k.lower() or 'geolocation' in k.lower()]
        
        for endpoint in zones_endpoints:
            status = "✅" if endpoint_results[endpoint] else "❌"
            logger.info(f"   {status} {endpoint}")
        
        # Try to get zones using working endpoints
        logger.info("\n🏠 TRYING TO GET ZONES:")
        try:
            zones = await client.get_zones()
            if zones:
                logger.info(f"✅ Found {len(zones)} zones:")
                for zone_id, zone_data in zones.items():
                    zone_name = zone_data.get('name', 'Unknown')
                    logger.info(f"   • {zone_name} (ID: {zone_id})")
                    
                    # Try to get devices for this zone
                    try:
                        zone_devices = await client.get_zone_devices(zone_id)
                        logger.info(f"     └── {len(zone_devices)} devices")
                    except Exception as e:
                        logger.debug(f"     └── Could not get zone devices: {e}")
            else:
                logger.warning("❌ No zones returned")
        except Exception as e:
            logger.error(f"❌ Error getting zones: {e}")
        
        # Test zone lookup
        logger.info("\n🔍 TESTING ZONE LOOKUP:")
        try:
            # Test common zone names
            test_names = ["Living Room", "Kitchen", "Bedroom", "Bathroom", "Office", "Woonkamer", "Keuken", "Slaapkamer"]
            
            for zone_name in test_names:
                try:
                    zone = await client.find_zone_by_name(zone_name)
                    if zone:
                        logger.info(f"✅ Found zone: '{zone_name}' → {zone['name']} (ID: {zone['id']})")
                    else:
                        logger.debug(f"   No zone found for: '{zone_name}'")
                except Exception as e:
                    logger.debug(f"   Error looking up '{zone_name}': {e}")
        except Exception as e:
            logger.error(f"❌ Error testing zone lookup: {e}")
        
        logger.info("\n📊 RECOMMENDATION:")
        working_endpoints = [k for k, v in endpoint_results.items() if v and ('zone' in k.lower() or 'geolocation' in k.lower())]
        if working_endpoints:
            logger.info(f"✅ Use these endpoints for zones: {working_endpoints}")
        else:
            logger.warning("❌ No working zone endpoints found - zones might not be supported on this Homey version")


if __name__ == "__main__":
    asyncio.run(test_real_homey_endpoints())
