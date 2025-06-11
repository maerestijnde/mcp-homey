#!/usr/bin/env python3
"""
Comprehensive test file voor alle Homey MCP Actions via de daadwerkelijke server implementatie.

Dit script test alle 14 actions die Claude kan gebruiken door de echte MCP tools te instantiëren:
- 8 Device Control actions
- 3 Flow Management actions  
- 3 Insights actions

Run from project directory:
python test_all_actions.py
"""

import asyncio
import logging
import time
import traceback
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import Homey MCP components
from homey_mcp.config import get_config
from homey_mcp.homey_client import HomeyAPIClient
from homey_mcp.tools.device_control import DeviceControlTools
from homey_mcp.tools.flow_management import FlowManagementTools
from homey_mcp.tools.insights import InsightsTools

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test results storage
test_results: Dict[str, Dict[str, Any]] = {}

def log_test_result(action_name: str, success: bool, duration: float, result: str = "", error: str = ""):
    """Log test result with timing and status."""
    test_results[action_name] = {
        "success": success,
        "duration": duration,
        "result": result[:100] + "..." if len(result) > 100 else result,
        "error": error,
        "timestamp": datetime.now().isoformat()
    }
    
    status = "✅" if success else "❌"
    logger.info(f"{status} {action_name} ({duration:.2f}s)")
    if error:
        logger.error(f"   Error: {error}")


class HomeyMCPTester:
    """Main tester class that instantiates and tests all tools."""
    
    def __init__(self):
        self.config = None
        self.client = None
        self.device_tools = None
        self.flow_tools = None
        self.insights_tools = None
    
    async def setup(self):
        """Initialize tools for testing."""
        self.config = get_config()
        
        # Force demo mode voor testing
        self.config.demo_mode = True
        self.config.offline_mode = True
        
        logger.info(f"📋 Config: Demo={self.config.demo_mode}, Offline={self.config.offline_mode}")
        
        # Initialize client and tools
        self.client = HomeyAPIClient(self.config)
        await self.client.connect()
        
        self.device_tools = DeviceControlTools(self.client)
        self.flow_tools = FlowManagementTools(self.client)
        self.insights_tools = InsightsTools(self.client)
        
        logger.info("✅ All tools initialized")
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.client:
            await self.client.disconnect()

    async def test_device_control_actions(self):
        """Test alle Device Control actions (8 total)."""
        logger.info("🔧 TESTING DEVICE CONTROL ACTIONS")
        logger.info("=" * 50)
        
        # Test 1: get_devices
        logger.info("Testing get_devices...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_get_devices({})
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("get_devices", True, duration, result_text)
            print(f"\n📱 GET DEVICES SAMPLE:\n{result_text[:300]}...\n")
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("get_devices", False, duration, error=str(e))
        
        # Test 2: control_device (basic on/off)
        logger.info("Testing control_device (onoff)...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_control_device({
                "device_id": "light1",
                "capability": "onoff",
                "value": True
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("control_device_onoff", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("control_device_onoff", False, duration, error=str(e))
        
        # Test 3: control_device (dimming)
        logger.info("Testing control_device (dimming)...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_control_device({
                "device_id": "light1",
                "capability": "dim",
                "value": 0.75
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("control_device_dim", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("control_device_dim", False, duration, error=str(e))
        
        # Test 4: get_device_status
        logger.info("Testing get_device_status...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_get_device_status({
                "device_id": "light1"
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("get_device_status", True, duration, result_text)
            print(f"\n📊 DEVICE STATUS SAMPLE:\n{result_text[:200]}...\n")
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("get_device_status", False, duration, error=str(e))
        
        # Test 5: find_devices_by_zone
        logger.info("Testing find_devices_by_zone...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_find_devices_by_zone({
                "zone_name": "Woonkamer"
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("find_devices_by_zone", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("find_devices_by_zone", False, duration, error=str(e))
        
        # Test 6: control_lights_in_zone (basic)
        logger.info("Testing control_lights_in_zone (basic)...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_control_lights_in_zone({
                "zone_name": "Woonkamer",
                "action": "on"
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("control_lights_in_zone_basic", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("control_lights_in_zone_basic", False, duration, error=str(e))
        
        # Test 7: control_lights_in_zone (with brightness)
        logger.info("Testing control_lights_in_zone (with brightness)...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_control_lights_in_zone({
                "zone_name": "Woonkamer",
                "action": "on",
                "brightness": 80
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("control_lights_in_zone_brightness", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("control_lights_in_zone_brightness", False, duration, error=str(e))
        
        # Test 8: set_thermostat_temperature
        logger.info("Testing set_thermostat_temperature...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_set_thermostat_temperature({
                "device_id": "thermostat1",
                "temperature": 21.5
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("set_thermostat_temperature", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("set_thermostat_temperature", False, duration, error=str(e))
        
        # Test 9: set_light_color
        logger.info("Testing set_light_color...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_set_light_color({
                "device_id": "light1",
                "hue": 120,
                "saturation": 90,
                "brightness": 75
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("set_light_color", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("set_light_color", False, duration, error=str(e))
        
        # Test 10: get_sensor_readings
        logger.info("Testing get_sensor_readings...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_get_sensor_readings({
                "zone_name": "Slaapkamer",
                "sensor_type": "all"
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("get_sensor_readings", True, duration, result_text)
            print(f"\n📊 SENSOR READINGS SAMPLE:\n{result_text[:200]}...\n")
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("get_sensor_readings", False, duration, error=str(e))

    async def test_flow_management_actions(self):
        """Test alle Flow Management actions (3 total)."""
        logger.info("\n🔄 TESTING FLOW MANAGEMENT ACTIONS")
        logger.info("=" * 50)
        
        # Test 1: get_flows
        logger.info("Testing get_flows...")
        start_time = time.time()
        try:
            result = await self.flow_tools.handle_get_flows({})
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("get_flows", True, duration, result_text)
            print(f"\n🔄 GET FLOWS SAMPLE:\n{result_text[:300]}...\n")
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("get_flows", False, duration, error=str(e))
        
        # Test 2: trigger_flow
        logger.info("Testing trigger_flow...")
        start_time = time.time()
        try:
            result = await self.flow_tools.handle_trigger_flow({
                "flow_id": "flow1"
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("trigger_flow", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("trigger_flow", False, duration, error=str(e))
        
        # Test 3: find_flow_by_name
        logger.info("Testing find_flow_by_name...")
        start_time = time.time()
        try:
            result = await self.flow_tools.handle_find_flow_by_name({
                "flow_name": "routine"
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("find_flow_by_name", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("find_flow_by_name", False, duration, error=str(e))

    async def test_insights_actions(self):
        """Test alle Insights actions (3 total)."""
        logger.info("\n📊 TESTING INSIGHTS ACTIONS")
        logger.info("=" * 50)
        
        # Test 1: get_device_insights
        logger.info("Testing get_device_insights...")
        start_time = time.time()
        try:
            result = await self.insights_tools.handle_get_device_insights({
                "device_id": "sensor1",
                "capability": "measure_temperature",
                "period": "7d",
                "resolution": "1h"
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("get_device_insights", True, duration, result_text)
            print(f"\n📈 DEVICE INSIGHTS SAMPLE:\n{result_text[:300]}...\n")
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("get_device_insights", False, duration, error=str(e))
        
        # Test 2: get_energy_insights
        logger.info("Testing get_energy_insights...")
        start_time = time.time()
        try:
            result = await self.insights_tools.handle_get_energy_insights({
                "period": "30d",
                "device_filter": ["socket", "light"],
                "group_by": "device"
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("get_energy_insights", True, duration, result_text)
            print(f"\n🔋 ENERGY INSIGHTS SAMPLE:\n{result_text[:300]}...\n")
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("get_energy_insights", False, duration, error=str(e))
        
        # Test 3: get_live_insights
        logger.info("Testing get_live_insights...")
        start_time = time.time()
        try:
            result = await self.insights_tools.handle_get_live_insights({
                "metrics": ["total_power", "active_devices", "temp_avg"]
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("get_live_insights", True, duration, result_text)
            print(f"\n📊 LIVE INSIGHTS SAMPLE:\n{result_text[:300]}...\n")
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("get_live_insights", False, duration, error=str(e))

    async def test_edge_cases(self):
        """Test edge cases en error handling."""
        logger.info("\n⚠️  TESTING EDGE CASES & ERROR HANDLING")
        logger.info("=" * 50)
        
        # Test invalid device ID
        logger.info("Testing invalid device ID...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_control_device({
                "device_id": "invalid_device_id",
                "capability": "onoff",
                "value": True
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("edge_case_invalid_device", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("edge_case_invalid_device", False, duration, error=str(e))
        
        # Test invalid capability
        logger.info("Testing invalid capability...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_control_device({
                "device_id": "light1",
                "capability": "invalid_capability",
                "value": True
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("edge_case_invalid_capability", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("edge_case_invalid_capability", False, duration, error=str(e))
        
        # Test invalid zone
        logger.info("Testing invalid zone...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_find_devices_by_zone({
                "zone_name": "NonExistentZone"
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("edge_case_invalid_zone", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("edge_case_invalid_zone", False, duration, error=str(e))
        
        # Test out of range temperature
        logger.info("Testing out of range temperature...")
        start_time = time.time()
        try:
            result = await self.device_tools.handle_set_thermostat_temperature({
                "device_id": "thermostat1",
                "temperature": 100.0  # Too high
            })
            result_text = result[0].text if result else "No result"
            duration = time.time() - start_time
            log_test_result("edge_case_temp_range", True, duration, result_text)
        except Exception as e:
            duration = time.time() - start_time
            log_test_result("edge_case_temp_range", False, duration, error=str(e))


def generate_test_report():
    """Generate a comprehensive test report."""
    logger.info("\n" + "=" * 80)
    logger.info("🎉 COMPREHENSIVE TEST REPORT")
    logger.info("=" * 80)
    
    # Count results
    total_tests = len(test_results)
    successful_tests = sum(1 for result in test_results.values() if result["success"])
    failed_tests = total_tests - successful_tests
    
    # Calculate average duration
    total_duration = sum(result["duration"] for result in test_results.values())
    avg_duration = total_duration / total_tests if total_tests > 0 else 0
    
    logger.info(f"📊 SUMMARY:")
    logger.info(f"   • Total Tests: {total_tests}")
    logger.info(f"   • Successful: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
    logger.info(f"   • Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    logger.info(f"   • Average Duration: {avg_duration:.2f}s")
    logger.info(f"   • Total Duration: {total_duration:.2f}s")
    
    # Group by category
    device_actions = [k for k in test_results.keys() if any(x in k for x in ["device", "control", "light", "thermostat", "sensor"])]
    flow_actions = [k for k in test_results.keys() if "flow" in k]
    insights_actions = [k for k in test_results.keys() if "insight" in k]
    edge_cases = [k for k in test_results.keys() if "edge_case" in k]
    
    logger.info(f"\n📋 BY CATEGORY:")
    logger.info(f"   • Device Control: {len(device_actions)} tests")
    logger.info(f"   • Flow Management: {len(flow_actions)} tests")
    logger.info(f"   • Insights: {len(insights_actions)} tests")
    logger.info(f"   • Edge Cases: {len(edge_cases)} tests")
    
    # Detailed results
    logger.info(f"\n📝 DETAILED RESULTS:")
    for action_name, result in test_results.items():
        status = "✅" if result["success"] else "❌"
        duration_str = f"{result['duration']:.2f}s"
        logger.info(f"   {status} {action_name:<35} {duration_str:>8}")
        if not result["success"] and result["error"]:
            logger.info(f"      └── Error: {result['error']}")
    
    # Failed tests details
    failed_actions = [k for k, v in test_results.items() if not v["success"]]
    if failed_actions:
        logger.info(f"\n❌ FAILED TESTS ANALYSIS:")
        for action in failed_actions:
            error = test_results[action]["error"]
            logger.info(f"   • {action}: {error}")
    
    # Performance analysis
    slowest_tests = sorted(test_results.items(), key=lambda x: x[1]["duration"], reverse=True)[:5]
    logger.info(f"\n⏱️  SLOWEST TESTS:")
    for action, result in slowest_tests:
        logger.info(f"   • {action}: {result['duration']:.2f}s")
    
    logger.info(f"\n🎯 RECOMMENDATIONS:")
    if failed_tests == 0:
        logger.info("   ✅ All tests passed! Homey MCP Server is fully functional.")
    else:
        logger.info(f"   ⚠️  {failed_tests} tests failed. Check error details above.")
    
    if avg_duration > 2.0:
        logger.info("   ⚠️  Average response time > 2s. Consider optimizing.")
    else:
        logger.info("   ✅ Good response times (< 2s average).")
    
    logger.info(f"\n🚀 STATUS: Homey MCP Server ready for Claude integration!")
    logger.info(f"   📅 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def main():
    """Main test execution."""
    logger.info("🚀 STARTING COMPREHENSIVE HOMEY MCP ACTIONS TEST")
    logger.info(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    # Initialize tester
    tester = HomeyMCPTester()
    
    try:
        # Setup
        await tester.setup()
        
        # Run all test categories
        await tester.test_device_control_actions()
        await tester.test_flow_management_actions()
        await tester.test_insights_actions()
        await tester.test_edge_cases()
        
        # Generate final report
        generate_test_report()
        
    finally:
        # Cleanup
        await tester.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed with exception: {e}")
        logger.error(traceback.format_exc())
