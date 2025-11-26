import json
import logging
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ...client import HomeyAPIClient
from .lighting import LightingTools
from .sensors import SensorTools


logger = logging.getLogger(__name__)


class DeviceControlTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client
        self.lighting = LightingTools(homey_client)
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
                name="get_zones",
                description="Get all available zones in Homey",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="find_devices_by_zone",
                description="Find devices in a specific zone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "zone_id": {
                            "type": "string",
                            "description": "Optional: filter by zone ID (e.g. 'f5d6…')",
                        },
                        "zone_name": {
                            "type": "string",
                            "description": "Zone name (e.g. 'Living Room', 'Bedroom')",
                        },
                        "device_class": {
                            "type": "string",
                            "description": "Optional: filter by device class (e.g. 'light', 'sensor')",
                        },
                    },
                    "required": [],
                },
            ),
        ]
        
        # Add specialized tools
        tools.extend(self.lighting.get_tools())
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
            return [TextContent(type="text", text=f"❌ Error getting devices: {str(e)}")]

    async def handle_get_zones(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_zones tool."""
        try:
            zones = await self.homey_client.get_zones()

            zone_list = []
            for zone_id, zone in zones.items():
                zone_info = {
                    "id": zone_id,
                    "name": zone.get("name"),
                    "parent": zone.get("parent"),
                    "icon": zone.get("icon"),
                    "active": zone.get("active", True),
                }
                zone_list.append(zone_info)

            # Add device count for each zone
            for zone_info in zone_list:
                try:
                    zone_devices = await self.homey_client.get_zone_devices(zone_info["id"])
                    zone_info["device_count"] = len(zone_devices)
                    
                    # Add device classes summary
                    device_classes = {}
                    for device in zone_devices:
                        device_class = device.get("class", "unknown")
                        device_classes[device_class] = device_classes.get(device_class, 0) + 1
                    zone_info["device_classes"] = device_classes
                except:
                    zone_info["device_count"] = 0
                    zone_info["device_classes"] = {}

            return [
                TextContent(
                    type="text",
                    text=f"Found {len(zone_list)} zones:\n\n"
                    + json.dumps(zone_list, indent=2, ensure_ascii=False),
                )
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting zones: {str(e)}")]

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

    async def handle_get_zones(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get all zones by extracting them from devices (like curl approach)."""
        try:
            devices = await self.homey_client.get_devices()
            zones = {}
            
            # Extract unique zones from all devices
            for device_id, device in devices.items():
                zone_id = device.get("zone")
                zone_name = device.get("zoneName") 
                
                if zone_id and zone_name:
                    if zone_id not in zones:
                        zones[zone_id] = {
                            "id": zone_id,
                            "name": zone_name,
                            "devices": []
                        }
                    zones[zone_id]["devices"].append({
                        "id": device_id,
                        "name": device.get("name"),
                        "class": device.get("class")
                    })
            
            if zones:
                zone_list = list(zones.values())
                return [TextContent(
                    type="text",
                    text=f"Found {len(zone_list)} zones:\n\n" + 
                         json.dumps(zone_list, indent=2, ensure_ascii=False)
                )]
            else:
                return [TextContent(type="text", text="No zones found")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting zones: {str(e)}")]

    async def handle_find_devices_by_zone(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for find_devices_by_zone tool - works like curl filtering."""
        try:
            zone_id = arguments.get("zone_id")
            zone_name = arguments.get("zone_name") 
            device_class = arguments.get("device_class")

            if not zone_id and not zone_name:
                return [TextContent(type="text", text="❌ Please provide either 'zone_id' or 'zone_name'")]

            # Get all devices (like curl does)
            devices = await self.homey_client.get_devices()
            matching_devices = []

            for device_id, device in devices.items():
                # Check zone match (exactly like your curl jq filter)
                zone_match = False
                
                if zone_id:
                    # Filter by zone ID: .value.zone == $zone
                    device_zone = device.get("zone")
                    zone_match = device_zone == zone_id
                elif zone_name:
                    # Filter by zone name (partial match for user-friendliness)
                    device_zone_name = device.get("zoneName", "").lower()
                    zone_match = zone_name.lower() in device_zone_name

                # Check device class filter (if provided)
                class_match = True
                if device_class:
                    class_match = device.get("class") == device_class

                # Add to results if both filters match
                if zone_match and class_match:
                    matching_devices.append({
                        "key": device_id,  # Like curl output
                        "name": device.get("name"),
                        "class": device.get("class"), 
                        "available": device.get("available"),
                        "zone": device.get("zone"),
                        "zoneName": device.get("zoneName")
                    })

            if matching_devices:
                filter_desc = f"zone_id='{zone_id}'" if zone_id else f"zone_name='{zone_name}'"
                if device_class:
                    filter_desc += f", class='{device_class}'"
                    
                return [TextContent(
                    type="text", 
                    text=f"Found {len(matching_devices)} devices ({filter_desc}):\n\n" + 
                         json.dumps(matching_devices, indent=2, ensure_ascii=False)
                )]
            else:
                return [TextContent(type="text", text=f"No devices found matching the criteria")]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error searching devices: {str(e)}")]
