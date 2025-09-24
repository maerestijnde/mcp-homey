#!/usr/bin/env python3
"""
Test script om de zones fix te testen.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from homey_mcp.config import get_config
from homey_mcp.client import HomeyAPIClient

async def test_zones_fix():
    """Test de zones en devices met zone namen."""
    print("🧪 Testing Zones Fix")
    print("=" * 50)
    
    config = get_config()
    config.demo_mode = True
    config.offline_mode = True
    
    async with HomeyAPIClient(config) as client:
        
        # Test 1: Get zones
        print("1. Testing get_zones()...")
        zones = await client.get_zones()
        print(f"   Found {len(zones)} zones:")
        for zone_id, zone in zones.items():
            print(f"   • {zone_id}: {zone.get('name')}")
        print()
        
        # Test 2: Get devices with zone names
        print("2. Testing get_devices() with zone enrichment...")
        devices = await client.get_devices()
        print(f"   Found {len(devices)} devices:")
        for device_id, device in devices.items():
            zone_name = device.get("zoneName", "No Zone")
            zone_id = device.get("zone", "no-zone")
            device_name = device.get("name", device_id)
            print(f"   • {device_name} ({device_id})")
            print(f"     └── Zone: {zone_name} (ID: {zone_id})")
        print()
        
        # Test 3: Verify zone name resolution works correctly
        print("3. Verifying zone name resolution...")
        devices_with_zones = []
        devices_without_zones = []
        
        for device_id, device in devices.items():
            zone_name = device.get("zoneName")
            if zone_name and zone_name != "No Zone":
                devices_with_zones.append(device.get("name"))
            else:
                devices_without_zones.append(device.get("name"))
        
        print(f"   ✅ Devices with zones: {len(devices_with_zones)}")
        print(f"   ❌ Devices without zones: {len(devices_without_zones)}")
        
        if len(devices_with_zones) > 0:
            print("   🎉 Zone enrichment working correctly!")
        else:
            print("   ⚠️ Zone enrichment may not be working")
        
        print()
        print("🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_zones_fix())
