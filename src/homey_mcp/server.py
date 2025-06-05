import asyncio
import logging
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent

from .config import get_config
from .homey_client import HomeyAPIClient
from .tools import DeviceControlTools, FlowManagementTools

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("Homey Integration Server")

# Global variables voor tools
homey_client = None
device_tools = None
flow_tools = None

async def initialize_server():
    """Initialiseer de server en tools."""
    global homey_client, device_tools, flow_tools
    
    logger.info("🚀 Initialiseren Homey MCP Server...")
    
    # Setup configuratie
    config = get_config()
    logger.info(f"📋 Configuratie geladen:")
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
            logger.warning("⚠️  Homey verbinding gefaald, maar demo/offline mode actief")
        else:
            logger.error("❌ Homey verbinding gefaald! Probeer:")
            logger.error("   1. Check je .env file configuratie")
            logger.error("   2. Test handmatig: curl -H 'Authorization: Bearer TOKEN' http://IP/api/manager/system")
            logger.error("   3. Of gebruik offline mode: OFFLINE_MODE=true")
            raise
    
    # Setup tools
    device_tools = DeviceControlTools(homey_client)
    flow_tools = FlowManagementTools(homey_client)
    
    logger.info("✅ Homey MCP Server geïnitialiseerd met 8 tools")

@mcp.tool()
async def get_devices() -> str:
    """Haal alle Homey devices op met hun huidige status."""
    try:
        result = await device_tools.handle_get_devices({})
        return result[0].text if result else "Geen devices gevonden"
    except Exception as e:
        logger.error(f"Fout in get_devices: {e}")
        return f"Fout bij ophalen devices: {str(e)}"

@mcp.tool()
async def control_device(device_id: str, capability: str, value: str | int | float | bool) -> str:
    """Bedien een Homey device door een capability waarde te zetten."""
    try:
        arguments = {
            "device_id": device_id,
            "capability": capability,
            "value": value
        }
        result = await device_tools.handle_control_device(arguments)
        return result[0].text if result else "Geen resultaat"
    except Exception as e:
        logger.error(f"Fout in control_device: {e}")
        return f"Fout bij bedienen device: {str(e)}"

@mcp.tool()
async def get_device_status(device_id: str) -> str:
    """Haal de status op van een specifiek device."""
    try:
        arguments = {"device_id": device_id}
        result = await device_tools.handle_get_device_status(arguments)
        return result[0].text if result else "Geen status gevonden"
    except Exception as e:
        logger.error(f"Fout in get_device_status: {e}")
        return f"Fout bij ophalen device status: {str(e)}"

@mcp.tool()
async def find_devices_by_zone(zone_name: str, device_class: str = None) -> str:
    """Zoek devices in een specifieke zone."""
    try:
        arguments = {"zone_name": zone_name}
        if device_class:
            arguments["device_class"] = device_class
        result = await device_tools.handle_find_devices_by_zone(arguments)
        return result[0].text if result else "Geen devices gevonden"
    except Exception as e:
        logger.error(f"Fout in find_devices_by_zone: {e}")
        return f"Fout bij zoeken devices: {str(e)}"

@mcp.tool()
async def control_lights_in_zone(zone_name: str, action: str, brightness: int = None) -> str:
    """Bedien alle lichten in een zone."""
    try:
        arguments = {
            "zone_name": zone_name,
            "action": action
        }
        if brightness is not None:
            arguments["brightness"] = brightness
        result = await device_tools.handle_control_lights_in_zone(arguments)
        return result[0].text if result else "Geen lichten gevonden"
    except Exception as e:
        logger.error(f"Fout in control_lights_in_zone: {e}")
        return f"Fout bij bedienen lichten: {str(e)}"

@mcp.tool()
async def get_flows() -> str:
    """Haal alle Homey flows (automation) op."""
    try:
        result = await flow_tools.handle_get_flows({})
        return result[0].text if result else "Geen flows gevonden"
    except Exception as e:
        logger.error(f"Fout in get_flows: {e}")
        return f"Fout bij ophalen flows: {str(e)}"

@mcp.tool()
async def trigger_flow(flow_id: str) -> str:
    """Start een specifieke Homey flow."""
    try:
        arguments = {"flow_id": flow_id}
        result = await flow_tools.handle_trigger_flow(arguments)
        return result[0].text if result else "Flow niet gestart"
    except Exception as e:
        logger.error(f"Fout in trigger_flow: {e}")
        return f"Fout bij starten flow: {str(e)}"

@mcp.tool()
async def find_flow_by_name(flow_name: str) -> str:
    """Zoek flows op basis van naam."""
    try:
        arguments = {"flow_name": flow_name}
        result = await flow_tools.handle_find_flow_by_name(arguments)
        return result[0].text if result else "Geen flows gevonden"
    except Exception as e:
        logger.error(f"Fout in find_flow_by_name: {e}")
        return f"Fout bij zoeken flows: {str(e)}"

async def cleanup():
    """Cleanup resources."""
    global homey_client
    if homey_client:
        await homey_client.disconnect()
    logger.info("Homey MCP Server gestopt")

async def main():
    """Main entry point."""
    try:
        await initialize_server()
        
        # Use stdio async to avoid event loop conflicts
        await mcp.run_stdio_async()
            
    finally:
        await cleanup()

def get_server():
    """Krijg server instance."""
    return mcp
