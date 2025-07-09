import json
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ...client import HomeyAPIClient
from .lighting import LightingTools
from .climate import ClimateTools
from .sensors import SensorTools


class DeviceControlTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client
        self.lighting = LightingTools(homey_client)
        self.climate = ClimateTools(homey_client)
        self.sensors = SensorTools(homey_client)

    def get_tools(self) -> List[Tool]:
        """Return all device control tools."""
        tools = [
            Tool(
                name="get_devices",
                description="Get all Homey devices with their current status",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="control_device",
                description="Control a Homey device by setting a capability value",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "The device ID"},
                        "capability": {
                            "type": "string", 
                            "description": "The capability to control. Examples:\n" +
                                         "- onoff: true/false (on/off)\n" +
                                         "- dim: 0.0-1.0 or 0-100% (brightness)\n" +
                                         "- target_temperature: number (desired temp in °C)\n" +
                                         "- light_hue: 0.0-1.0 (color)\n" +
                                         "- light_saturation: 0.0-1.0 (saturation)\n" +
                                         "- light_temperature: 0.0-1.0 (warm-cold white)\n" +
                                         "- light_mode: 'color' or 'temperature'",
                        },
                        "value": {
                            "description": "The value to set. Note types:\n" +
                                         "- boolean for onoff, alarm_*\n" +
                                         "- number 0.0-1.0 for dim, light_* (or 0-100% will be auto-converted)\n" +
                                         "- number for temperatures, power, etc."
                        },
                    },
                    "required": ["device_id", "capability", "value"],
                },
            ),
            Tool(
                name="get_device_status",
                description="Get the status of a specific device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "The device ID"}
                    },
                    "required": ["device_id"],
                },
            ),
            Tool(
                name="find_devices_by_zone",
                description="Find devices in a specific zone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "zone_name": {
                            "type": "string",
                            "description": "Zone name (e.g. 'Living Room', 'Bedroom')",
                        },
                        "device_class": {
                            "type": "string",
                            "description": "Optional: filter by device class (e.g. 'light', 'sensor')",
                        },
                    },
                    "required": ["zone_name"],
                },
            ),
        ]
        
        # Add specialized tools
        tools.extend(self.lighting.get_tools())
        tools.extend(self.climate.get_tools())
        tools.extend(self.sensors.get_tools())
        
        return tools

    async def handle_get_devices(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_devices tool."""
        try:
            devices = await self.homey_client.get_devices()

            # Format for nice output
            device_list = []
            for device_id, device in devices.items():
                device_info = {
                    "id": device_id,
                    "name": device.get("name"),
                    "class": device.get("class"),
                    "zone": device.get("zoneName"),
                    "capabilities": list(device.get("capabilitiesObj", {}).keys()),
                    "available": device.get("available", True),
                }
                device_list.append(device_info)

            return [
                TextContent(
                    type="text",
                    text=f"Found {len(device_list)} devices:\n\n"
                    + json.dumps(device_list, indent=2, ensure_ascii=False),
                )
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting devices: {str(e)}")]

    async def handle_control_device(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for control_device tool."""
        try:
            device_id = arguments["device_id"]
            capability = arguments["capability"]
            value = arguments["value"]

            # Get device info for name
            device = await self.homey_client.get_device(device_id)
            device_name = device.get("name", device_id)

            # Set capability
            success = await self.homey_client.set_capability_value(device_id, capability, value)

            if success:
                return [
                    TextContent(
                        type="text",
                        text=f"✅ Device '{device_name}' capability '{capability}' set to '{value}'",
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text", text=f"❌ Could not set capability of '{device_name}'"
                    )
                ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error controlling device: {str(e)}")]

    async def handle_get_device_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_device_status tool."""
        try:
            device_id = arguments["device_id"]
            device = await self.homey_client.get_device(device_id)

            status = {
                "name": device.get("name"),
                "class": device.get("class"),
                "zone": device.get("zoneName"),
                "available": device.get("available"),
                "capabilities": {},
            }

            # Get capability values
            capabilities_obj = device.get("capabilitiesObj", {})
            for cap_name, cap_data in capabilities_obj.items():
                if isinstance(cap_data, dict) and "value" in cap_data:
                    status["capabilities"][cap_name] = {
                        "value": cap_data["value"],
                        "title": cap_data.get("title", cap_name),
                    }

            return [
                TextContent(
                    type="text",
                    text=f"Status of '{device.get('name')}':\n\n"
                    + json.dumps(status, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting device status: {str(e)}")]

    async def handle_find_devices_by_zone(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for find_devices_by_zone tool."""
        try:
            zone_name = arguments["zone_name"].lower()
            device_class = arguments.get("device_class")

            devices = await self.homey_client.get_devices()

            matching_devices = []
            for device_id, device in devices.items():
                device_zone = device.get("zoneName", "").lower()

                if zone_name in device_zone:
                    if device_class is None or device.get("class") == device_class:
                        matching_devices.append(
                            {
                                "id": device_id,
                                "name": device.get("name"),
                                "class": device.get("class"),
                                "zone": device.get("zoneName"),
                            }
                        )

            if matching_devices:
                return [
                    TextContent(
                        type="text",
                        text=f"Found {len(matching_devices)} devices in '{arguments['zone_name']}':\n\n"
                        + json.dumps(matching_devices, indent=2, ensure_ascii=False),
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text=f"No devices found in zone '{arguments['zone_name']}'",
                    )
                ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error searching devices: {str(e)}")]