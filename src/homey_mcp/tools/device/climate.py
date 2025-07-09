from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ...client import HomeyAPIClient


class ClimateTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return climate control tools."""
        return [
            Tool(
                name="set_thermostat_temperature",
                description="Set the desired temperature of a thermostat",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "The thermostat device ID"},
                        "temperature": {
                            "type": "number",
                            "minimum": 5,
                            "maximum": 35,
                            "description": "Desired temperature in degrees Celsius"
                        },
                    },
                    "required": ["device_id", "temperature"],
                },
            ),
        ]

    async def handle_set_thermostat_temperature(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for set_thermostat_temperature tool."""
        try:
            device_id = arguments["device_id"]
            temperature = arguments["temperature"]

            # Get device info
            device = await self.homey_client.get_device(device_id)
            device_name = device.get("name", device_id)
            device_class = device.get("class")

            # Check if it's a thermostat
            if device_class != "thermostat":
                return [TextContent(type="text", text=f"❌ Device '{device_name}' is not a thermostat (class: {device_class})")]

            # Check if target_temperature capability exists
            capabilities = device.get("capabilitiesObj", {})
            if "target_temperature" not in capabilities:
                return [TextContent(type="text", text=f"❌ Thermostat '{device_name}' has no target_temperature capability")]

            # Set the desired temperature
            await self.homey_client.set_capability_value(device_id, "target_temperature", temperature)

            # Get current temperature if available
            current_temp = capabilities.get("measure_temperature", {}).get("value")
            current_text = f" (current: {current_temp}°C)" if current_temp is not None else ""

            return [TextContent(
                type="text",
                text=f"✅ Thermostat '{device_name}' set to {temperature}°C{current_text}"
            )]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error setting thermostat: {str(e)}")]