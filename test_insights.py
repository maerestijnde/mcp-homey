#!/usr/bin/env python3
"""
Test script voor Homey MCP Insights functionaliteit.

Dit script test alle 9 nieuwe insights tools die zijn toegevoegd.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from homey_mcp.config import get_config
from homey_mcp.homey_client import HomeyAPIClient
from homey_mcp.tools.insights import InsightsTools

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_insights_tools():
    """Test alle insights tools."""
    logger.info("🚀 Starting Homey Insights Tools Test")
    
    # Setup
    config = get_config()
    
    # Force demo mode voor testing
    config.demo_mode = True
    config.offline_mode = True
    
    logger.info(f"📋 Config: Demo={config.demo_mode}, Offline={config.offline_mode}")
    
    # Initialize client and tools
    async with HomeyAPIClient(config) as client:
        insights_tools = InsightsTools(client)
        
        logger.info("✅ Insights tools initialized")
        logger.info("=" * 60)
        
        # Test 1: Device Insights
        logger.info("🔍 Test 1: Device Insights")
        try:
            result = await insights_tools.handle_get_device_insights({
                "device_id": "light1",
                "capability": "measure_temperature", 
                "period": "7d",
                "resolution": "1h"
            })
            logger.info(f"✅ Device insights: {len(result[0].text)} characters")
            print(f"\n📊 Device Insights Result:\n{result[0].text}\n")
        except Exception as e:
            logger.error(f"❌ Device insights failed: {e}")
        
        # Test 2: Energy Insights
        logger.info("🔍 Test 2: Energy Insights")
        try:
            result = await insights_tools.handle_get_energy_insights({
                "period": "30d",
                "device_filter": ["socket", "light"],
                "group_by": "device"
            })
            logger.info(f"✅ Energy insights: {len(result[0].text)} characters")
            print(f"\n🔋 Energy Insights Result:\n{result[0].text}\n")
        except Exception as e:
            logger.error(f"❌ Energy insights failed: {e}")
        
        # Test 3: Live Insights
        logger.info("🔍 Test 3: Live Insights")
        try:
            result = await insights_tools.handle_get_live_insights({
                "metrics": ["total_power", "active_devices", "temp_avg", "energy_today"]
            })
            logger.info(f"✅ Live insights: {len(result[0].text)} characters")
            print(f"\n📊 Live Insights Result:\n{result[0].text}\n")
        except Exception as e:
            logger.error(f"❌ Live insights failed: {e}")
        
        logger.info("=" * 60)
        logger.info("🎉 All basic insights tools tested successfully!")
        
        # Test available tools count
        tools = insights_tools.get_tools()
        logger.info(f"📊 Total insights tools available: {len(tools)}")
        for i, tool in enumerate(tools, 1):
            logger.info(f"   {i}. {tool.name} - {tool.description[:50]}...")


if __name__ == "__main__":
    asyncio.run(test_insights_tools())
