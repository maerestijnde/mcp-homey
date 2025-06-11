import asyncio
import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, Tool

from .config import get_config
from .homey_client import HomeyAPIClient
from .tools import DeviceControlTools, FlowManagementTools
from .tools.insights import InsightsTools

# Get logger (logging is configured in __main__.py)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("Homey Integration Server")

# Global variables for tools
homey_client = None
device_tools = None
flow_tools = None
insights_tools = None


async def initialize_server():
    """Initialize the server and tools."""
    global homey_client, device_tools, flow_tools, insights_tools

    logger.info("🚀 Initializing Homey MCP Server...")

    # Setup configuration
    config = get_config()
    logger.info(f"📋 Configuration loaded:")
    logger.info(f"   - Homey IP: {config.homey_local_address}")
    logger.info(f"   - Token: {config.homey_local_token[:20]}...")
    logger.info(f"   - Offline mode: {config.offline_mode}")
    logger.info(f"   - Demo mode: {config.demo_mode}")

    # Setup Homey client
    homey_client = HomeyAPIClient(config)

    try:
        await homey_client.connect()
    except Exception as e:
        if config.offline_mode or config.demo_mode:
            logger.warning("⚠️  Homey connection failed, but demo/offline mode active")
        else:
            logger.error("❌ Homey connection failed! Try:")
            logger.error("   1. Check your .env file configuration")
            logger.error(
                "   2. Test manually: curl -H 'Authorization: Bearer TOKEN' http://IP/api/manager/system"
            )
            logger.error("   3. Or use offline mode: OFFLINE_MODE=true")
            raise

    # Setup tools
    device_tools = DeviceControlTools(homey_client)
    flow_tools = FlowManagementTools(homey_client)
    insights_tools = InsightsTools(homey_client)

    logger.info("✅ Homey MCP Server initialized with 15 tools (12 device/flow + 3 insights)")


@mcp.tool()
async def get_devices() -> str:
    """Get all Homey devices with their current status."""
    try:
        result = await device_tools.handle_get_devices({})
        return result[0].text if result else "No devices found"
    except Exception as e:
        logger.error(f"Error in get_devices: {e}")
        return f"Error getting devices: {str(e)}"


@mcp.tool()
async def control_device(device_id: str, capability: str, value: str | int | float | bool) -> str:
    """Control a Homey device by setting a capability value."""
    try:
        arguments = {"device_id": device_id, "capability": capability, "value": value}
        result = await device_tools.handle_control_device(arguments)
        return result[0].text if result else "No result"
    except Exception as e:
        logger.error(f"Error in control_device: {e}")
        return f"Error controlling device: {str(e)}"


@mcp.tool()
async def get_device_status(device_id: str) -> str:
    """Get the status of a specific device."""
    try:
        arguments = {"device_id": device_id}
        result = await device_tools.handle_get_device_status(arguments)
        return result[0].text if result else "No status found"
    except Exception as e:
        logger.error(f"Error in get_device_status: {e}")
        return f"Error getting device status: {str(e)}"


@mcp.tool()
async def find_devices_by_zone(zone_name: str, device_class: str = None) -> str:
    """Find devices in a specific zone."""
    try:
        arguments = {"zone_name": zone_name}
        if device_class:
            arguments["device_class"] = device_class
        result = await device_tools.handle_find_devices_by_zone(arguments)
        return result[0].text if result else "No devices found"
    except Exception as e:
        logger.error(f"Error in find_devices_by_zone: {e}")
        return f"Error searching devices: {str(e)}"


@mcp.tool()
async def control_lights_in_zone(zone_name: str, action: str, brightness: int = None) -> str:
    """Control all lights in a zone."""
    try:
        arguments = {"zone_name": zone_name, "action": action}
        if brightness is not None:
            arguments["brightness"] = brightness
        result = await device_tools.handle_control_lights_in_zone(arguments)
        return result[0].text if result else "No lights found"
    except Exception as e:
        logger.error(f"Error in control_lights_in_zone: {e}")
        return f"Error controlling lights: {str(e)}"


@mcp.tool()
async def get_flows() -> str:
    """Get all Homey flows (automation)."""
    try:
        result = await flow_tools.handle_get_flows({})
        return result[0].text if result else "No flows found"
    except Exception as e:
        logger.error(f"Error in get_flows: {e}")
        return f"Error getting flows: {str(e)}"


@mcp.tool()
async def trigger_flow(flow_id: str) -> str:
    """Start a specific Homey flow."""
    try:
        arguments = {"flow_id": flow_id}
        result = await flow_tools.handle_trigger_flow(arguments)
        return result[0].text if result else "Flow not started"
    except Exception as e:
        logger.error(f"Error in trigger_flow: {e}")
        return f"Error starting flow: {str(e)}"


@mcp.tool()
async def find_flow_by_name(flow_name: str) -> str:
    """Search flows by name."""
    try:
        arguments = {"flow_name": flow_name}
        result = await flow_tools.handle_find_flow_by_name(arguments)
        return result[0].text if result else "No flows found"
    except Exception as e:
        logger.error(f"Error in find_flow_by_name: {e}")
        return f"Error searching flows: {str(e)}"


@mcp.tool()
async def set_thermostat_temperature(device_id: str, temperature: float) -> str:
    """Set the desired temperature of a thermostat."""
    try:
        arguments = {"device_id": device_id, "temperature": temperature}
        result = await device_tools.handle_set_thermostat_temperature(arguments)
        return result[0].text if result else "Thermostat not set"
    except Exception as e:
        logger.error(f"Error in set_thermostat_temperature: {e}")
        return f"Error setting thermostat: {str(e)}"


@mcp.tool()
async def set_light_color(device_id: str, hue: float, saturation: float, brightness: float = None) -> str:
    """Set the color of a light."""
    try:
        arguments = {"device_id": device_id, "hue": hue, "saturation": saturation}
        if brightness is not None:
            arguments["brightness"] = brightness
        result = await device_tools.handle_set_light_color(arguments)
        return result[0].text if result else "Light color not set"
    except Exception as e:
        logger.error(f"Error in set_light_color: {e}")
        return f"Error setting light color: {str(e)}"


@mcp.tool()
async def get_sensor_readings(zone_name: str, sensor_type: str = "all") -> str:
    """Get sensor readings from a specific zone."""
    try:
        arguments = {"zone_name": zone_name, "sensor_type": sensor_type}
        result = await device_tools.handle_get_sensor_readings(arguments)
        return result[0].text if result else "No sensor data found"
    except Exception as e:
        logger.error(f"Error in get_sensor_readings: {e}")
        return f"Error getting sensor data: {str(e)}"


# ====== INSIGHTS TOOLS ======

@mcp.tool()
async def get_device_insights(device_id: str, capability: str, period: str = "7d", resolution: str = "1h") -> str:
    """Get historical data for device capability over a period."""
    try:
        arguments = {
            "device_id": device_id, 
            "capability": capability, 
            "period": period, 
            "resolution": resolution
        }
        result = await insights_tools.handle_get_device_insights(arguments)
        return result[0].text if result else "No insights data found"
    except Exception as e:
        logger.error(f"Error in get_device_insights: {e}")
        return f"Error getting device insights: {str(e)}"


@mcp.tool()
async def get_energy_insights(period: str = "7d", device_filter: list = None, group_by: str = "device") -> str:
    """Get energy consumption data from devices."""
    try:
        arguments = {"period": period, "group_by": group_by}
        if device_filter:
            arguments["device_filter"] = device_filter
        result = await insights_tools.handle_get_energy_insights(arguments)
        return result[0].text if result else "No energy data found"
    except Exception as e:
        logger.error(f"Error in get_energy_insights: {e}")
        return f"Error getting energy insights: {str(e)}"


@mcp.tool()
async def get_live_insights(metrics: list = None) -> str:
    """Real-time dashboard data for monitoring."""
    try:
        arguments = {}
        if metrics:
            arguments["metrics"] = metrics
        result = await insights_tools.handle_get_live_insights(arguments)
        return result[0].text if result else "No live data available"
    except Exception as e:
        logger.error(f"Error in get_live_insights: {e}")
        return f"Error getting live insights: {str(e)}"


async def cleanup():
    """Cleanup resources."""
    global homey_client
    if homey_client:
        await homey_client.disconnect()
    logger.info("Homey MCP Server stopped")


async def main():
    """Main entry point."""
    try:
        logger.info("🚀 Starting Homey MCP Server main()")
        await initialize_server()
        logger.info("✅ Server initialized, starting stdio...")

        # Use stdio async to avoid event loop conflicts
        await mcp.run_stdio_async()

    except Exception as e:
        logger.error(f"❌ Error in main(): {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        await cleanup()


def get_server():
    """Get server instance."""
    return mcp
