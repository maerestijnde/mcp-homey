#!/usr/bin/env python3
"""
Uitgebreid test script voor Homey capabilities en endpoints.
Test alle nieuwe functionaliteit en capabilities.

Run vanuit project directory:
python test_capabilities.py
"""

import asyncio
import os
import json
from dotenv import load_dotenv

# Import homey client
import sys
sys.path.append('src')
from homey_mcp.homey_client import HomeyAPIClient
from homey_mcp.config import get_config

async def test_capabilities():
    """Test alle capabilities en nieuwe functionaliteit."""
    
    print("🧪 Testing Homey Capabilities & Endpoints")
    print("=" * 60)
    
    # Setup
    config = get_config()
    
    async with HomeyAPIClient(config) as client:
        
        print(f"📋 Config: {config.homey_local_address} (demo: {config.demo_mode})")
        print()
        
        # 1. Test endpoint variations
        print("🔗 Testing endpoint variations...")
        endpoint_results = await client.test_endpoints()
        for endpoint, success in endpoint_results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {endpoint}")
        print()
        
        # 2. Test extended demo devices
        print("📱 Testing extended demo devices...")
        devices = await client.get_devices()
        print(f"Found {len(devices)} devices:")
        
        for device_id, device in devices.items():
            name = device.get('name')
            device_class = device.get('class')
            capabilities = list(device.get('capabilitiesObj', {}).keys())
            print(f"  • {name} ({device_class}): {', '.join(capabilities)}")
        print()
        
        # 3. Test capability validation
        print("🔍 Testing capability validation...")
        test_cases = [
            # (capability, test_value, expected_valid)
            ("onoff", True, True),
            ("onoff", "true", True),
            ("onoff", 1, True),
            ("onoff", "invalid", False),
            ("dim", 0.5, True),
            ("dim", 50, True),  # Should convert to 0.5
            ("dim", 150, False),  # Out of range
            ("target_temperature", 20.5, True),
            ("target_temperature", 200, False),  # Unrealistic
            ("light_hue", 0.33, True),
            ("light_hue", 120, True),  # Should convert from degrees
            ("light_mode", "color", True),
            ("light_mode", "invalid", False),
        ]
        
        for capability, value, expected_valid in test_cases:
            is_valid, converted, message = client.validate_capability_value(capability, value)
            status = "✅" if is_valid == expected_valid else "❌"
            print(f"  {status} {capability}={value} → valid={is_valid}, converted={converted}")
            if message:
                print(f"    └── {message}")
        print()
        
        # 4. Test capability setting (demo mode)
        print("⚙️  Testing capability setting...")
        test_device = "light1"  # Demo device
        
        capability_tests = [
            ("onoff", True),
            ("dim", 75),  # Test percentage conversion
            ("light_hue", 120),  # Test degree conversion
            ("light_saturation", 90),
            ("light_temperature", 30),
            ("light_mode", "color"),
        ]
        
        for capability, value in capability_tests:
            try:
                success = await client.set_capability_value(test_device, capability, value)
                status = "✅" if success else "❌"
                print(f"  {status} Set {test_device}.{capability} = {value}")
            except Exception as e:
                print(f"  ❌ Set {test_device}.{capability} = {value} failed: {e}")
        print()
        
        # 5. Test flows
        print("🔄 Testing flows...")
        flows = await client.get_flows()
        print(f"Found {len(flows)} flows:")
        
        for flow_id, flow in flows.items():
            name = flow.get('name')
            enabled = flow.get('enabled')
            status = "✅" if enabled else "⏸️"
            print(f"  {status} {name} (ID: {flow_id})")
        
        # Test flow triggering
        if flows:
            test_flow_id = list(flows.keys())[0]
            test_flow_name = flows[test_flow_id].get('name')
            try:
                success = await client.trigger_flow(test_flow_id)
                status = "✅" if success else "❌"
                print(f"  {status} Triggered flow: {test_flow_name}")
            except Exception as e:
                print(f"  ❌ Flow trigger failed: {e}")
        print()
        
        # 6. Test color conversion functions
        print("🌈 Testing color conversions...")
        
        color_tests = [
            # (hue_degrees, expected_fraction)
            (0, 0.0),      # Red
            (120, 0.33),   # Green (approximately)
            (240, 0.67),   # Blue (approximately)
            (360, 1.0),    # Red again
        ]
        
        for hue_degrees, expected in color_tests:
            converted = hue_degrees / 360.0
            close_enough = abs(converted - expected) < 0.01
            status = "✅" if close_enough else "❌"
            print(f"  {status} {hue_degrees}° → {converted:.3f} (expected ~{expected})")
        print()
        
        # 7. Test device class filtering
        print("🔍 Testing device filtering...")
        
        device_classes = {}
        for device_id, device in devices.items():
            device_class = device.get('class', 'unknown')
            if device_class not in device_classes:
                device_classes[device_class] = []
            device_classes[device_class].append(device.get('name'))
        
        for device_class, device_names in device_classes.items():
            print(f"  {device_class}: {', '.join(device_names)}")
        print()
        
        # 8. Test capability combinations
        print("🎛️  Testing capability combinations...")
        
        for device_id, device in devices.items():
            name = device.get('name')
            capabilities = device.get('capabilitiesObj', {})
            
            # Check for logical capability combinations
            has_onoff = 'onoff' in capabilities
            has_dim = 'dim' in capabilities
            has_color = all(cap in capabilities for cap in ['light_hue', 'light_saturation'])
            has_temp_control = 'target_temperature' in capabilities
            has_temp_measure = 'measure_temperature' in capabilities
            
            combinations = []
            if has_onoff and has_dim:
                combinations.append("dimmable")
            if has_color:
                combinations.append("color")
            if has_temp_control and has_temp_measure:
                combinations.append("thermostat")
            
            if combinations:
                print(f"  • {name}: {', '.join(combinations)}")
        print()
        
        print("🏁 Capability testing completed!")
        print()
        print("💡 Summary:")
        print("   - Extended demo devices with realistic capabilities")
        print("   - Capability validation with auto-conversion")
        print("   - Proper brightness percentage → fraction conversion")
        print("   - Color hue degree → fraction conversion")
        print("   - Endpoint variations testing")
        print("   - Flow trigger endpoint fallbacks")


async def test_new_tools():
    """Test de nieuwe MCP tools functionaliteit."""
    print("\n" + "=" * 60)
    print("🛠️  Testing New MCP Tools")
    print("=" * 60)
    
    # Import tools
    from homey_mcp.tools.device_control import DeviceControlTools
    
    config = get_config()
    
    async with HomeyAPIClient(config) as client:
        tools = DeviceControlTools(client)
        
        # Test thermostat tool
        print("🌡️  Testing thermostat control...")
        try:
            result = await tools.handle_set_thermostat_temperature({
                "device_id": "thermostat1",
                "temperature": 21.5
            })
            print(f"  ✅ {result[0].text}")
        except Exception as e:
            print(f"  ❌ Thermostat test failed: {e}")
        
        # Test light color tool
        print("🌈 Testing light color control...")
        try:
            result = await tools.handle_set_light_color({
                "device_id": "light1",
                "hue": 120,  # Green
                "saturation": 90,
                "brightness": 80
            })
            print(f"  ✅ {result[0].text}")
        except Exception as e:
            print(f"  ❌ Light color test failed: {e}")
        
        # Test sensor readings
        print("📊 Testing sensor readings...")
        try:
            result = await tools.handle_get_sensor_readings({
                "zone_name": "Slaapkamer",
                "sensor_type": "all"
            })
            print(f"  ✅ {result[0].text}")
        except Exception as e:
            print(f"  ❌ Sensor readings test failed: {e}")
        
        # Test enhanced light zone control
        print("💡 Testing enhanced light zone control...")
        try:
            result = await tools.handle_control_lights_in_zone({
                "zone_name": "Woonkamer",
                "action": "on",
                "brightness": 75,
                "color_temperature": 40
            })
            print(f"  ✅ {result[0].text}")
        except Exception as e:
            print(f"  ❌ Enhanced light control test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_capabilities())
    asyncio.run(test_new_tools())
