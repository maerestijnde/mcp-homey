#!/usr/bin/env python3
"""
Test script om de MCP server te testen zonder asyncio conflicts.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from homey_mcp.server import initialize_server, get_devices, control_device, get_flows
import logging

async def test_server():
    """Test de complete server functionaliteit."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    
    print("🧪 Testing Homey MCP Server...")
    
    try:
        # Initialize server
        print("🚀 Initializing server...")
        await initialize_server()
        
        print("\n📱 Testing device tools...")
        
        # Test get devices
        devices_result = await get_devices()
        print(f"✅ get_devices: {devices_result[:100]}...")
        
        # Test device control
        control_result = await control_device("light1", "onoff", True)
        print(f"✅ control_device: {control_result}")
        
        # Test device status
        from homey_mcp.server import get_device_status
        status_result = await get_device_status("light1")
        print(f"✅ get_device_status: {status_result[:100]}...")
        
        print("\n🔄 Testing flow tools...")
        
        # Test get flows
        flows_result = await get_flows()
        print(f"✅ get_flows: {flows_result[:100]}...")
        
        # Test trigger flow
        from homey_mcp.server import trigger_flow
        trigger_result = await trigger_flow("flow1")
        print(f"✅ trigger_flow: {trigger_result}")
        
        print("\n🎉 All tests passed! Server is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
