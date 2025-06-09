import json
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ..homey_client import HomeyAPIClient


class DeviceControlTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Geef alle device control tools terug."""
        return [
            Tool(
                name="get_devices",
                description="Haal alle Homey devices op met hun huidige status",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="control_device",
                description="Bedien een Homey device door een capability waarde te zetten",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "Het ID van het device"},
                        "capability": {
                            "type": "string",
                            "description": "De capability om te bedienen (bv. 'onoff', 'dim', 'target_temperature')",
                        },
                        "value": {
                            "description": "De waarde om te zetten (boolean, number, of string)"
                        },
                    },
                    "required": ["device_id", "capability", "value"],
                },
            ),
            Tool(
                name="get_device_status",
                description="Haal de status op van een specifiek device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "Het ID van het device"}
                    },
                    "required": ["device_id"],
                },
            ),
            Tool(
                name="find_devices_by_zone",
                description="Zoek devices in een specifieke zone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "zone_name": {
                            "type": "string",
                            "description": "Naam van de zone (bv. 'Woonkamer', 'Slaapkamer')",
                        },
                        "device_class": {
                            "type": "string",
                            "description": "Optioneel: filter op device class (bv. 'light', 'sensor')",
                        },
                    },
                    "required": ["zone_name"],
                },
            ),
            Tool(
                name="control_lights_in_zone",
                description="Bedien alle lichten in een zone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "zone_name": {"type": "string", "description": "Naam van de zone"},
                        "action": {
                            "type": "string",
                            "enum": ["on", "off"],
                            "description": "Actie: 'on' of 'off'",
                        },
                        "brightness": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Optioneel: helderheid percentage (0-100)",
                        },
                    },
                    "required": ["zone_name", "action"],
                },
            ),
        ]

    async def handle_get_devices(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler voor get_devices tool."""
        try:
            devices = await self.homey_client.get_devices()

            # Format voor mooie output
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
                    text=f"Gevonden {len(device_list)} devices:\n\n"
                    + json.dumps(device_list, indent=2, ensure_ascii=False),
                )
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Fout bij ophalen devices: {str(e)}")]

    async def handle_control_device(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler voor control_device tool."""
        try:
            device_id = arguments["device_id"]
            capability = arguments["capability"]
            value = arguments["value"]

            # Haal device info op voor naam
            device = await self.homey_client.get_device(device_id)
            device_name = device.get("name", device_id)

            # Zet capability
            success = await self.homey_client.set_capability_value(device_id, capability, value)

            if success:
                return [
                    TextContent(
                        type="text",
                        text=f"✅ Device '{device_name}' capability '{capability}' is gezet naar '{value}'",
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text", text=f"❌ Kon capability van '{device_name}' niet zetten"
                    )
                ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fout bij bedienen device: {str(e)}")]

    async def handle_get_device_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler voor get_device_status tool."""
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

            # Haal capability values op
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
                    text=f"Status van '{device.get('name')}':\n\n"
                    + json.dumps(status, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fout bij ophalen device status: {str(e)}")]

    async def handle_find_devices_by_zone(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler voor find_devices_by_zone tool."""
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
                        text=f"Gevonden {len(matching_devices)} devices in '{arguments['zone_name']}':\n\n"
                        + json.dumps(matching_devices, indent=2, ensure_ascii=False),
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text=f"Geen devices gevonden in zone '{arguments['zone_name']}'",
                    )
                ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fout bij zoeken devices: {str(e)}")]

    async def handle_control_lights_in_zone(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler voor control_lights_in_zone tool."""
        try:
            zone_name = arguments["zone_name"].lower()
            action = arguments["action"]
            brightness = arguments.get("brightness")

            devices = await self.homey_client.get_devices()

            # Zoek lichten in de zone
            lights = []
            for device_id, device in devices.items():
                device_zone = device.get("zoneName", "").lower()
                device_class = device.get("class")

                if zone_name in device_zone and device_class == "light":
                    lights.append((device_id, device))

            if not lights:
                return [
                    TextContent(
                        type="text",
                        text=f"Geen lichten gevonden in zone '{arguments['zone_name']}'",
                    )
                ]

            results = []
            for device_id, device in lights:
                device_name = device.get("name")

                try:
                    # Zet on/off
                    if action == "on":
                        await self.homey_client.set_capability_value(device_id, "onoff", True)

                        # Zet brightness als opgegeven
                        if brightness is not None and "dim" in device.get("capabilitiesObj", {}):
                            await self.homey_client.set_capability_value(
                                device_id, "dim", brightness / 100
                            )

                        results.append(
                            f"✅ {device_name}: aangezet"
                            + (f" ({brightness}%)" if brightness else "")
                        )
                    else:  # off
                        await self.homey_client.set_capability_value(device_id, "onoff", False)
                        results.append(f"✅ {device_name}: uitgezet")

                except Exception as e:
                    results.append(f"❌ {device_name}: fout - {str(e)}")

            return [
                TextContent(
                    type="text",
                    text=f"Lichten in '{arguments['zone_name']}' bediend:\n\n" + "\n".join(results),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fout bij bedienen lichten: {str(e)}")]
