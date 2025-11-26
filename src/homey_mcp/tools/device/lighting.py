from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ...client import HomeyAPIClient


class LightingTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return lighting-specific tools."""
        return [
            Tool(
                name="control_lights_in_zone",
                description="Control all lights in a zone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "zone_name": {"type": "string", "description": "Zone name"},
                        "action": {
                            "type": "string",
                            "enum": ["on", "off", "toggle"],
                            "description": "Action: 'on', 'off' or 'toggle'",
                        },
                        "brightness": {
                            "type": "number",
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Brightness percentage (1-100%). Only works with 'on' action.",
                        },
                        "color_temperature": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Optional: color temperature percentage (0=warm, 100=cold white)",
                        },
                    },
                    "required": ["zone_name", "action"],
                },
            ),
        ]

    async def handle_control_lights_in_zone(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for control_lights_in_zone tool - FIXED WITH ZONE UUID SUPPORT."""
        try:
            zone_input = arguments["zone_name"]  # Can be name OR UUID
            action = arguments["action"]
            brightness = arguments.get("brightness")  # 0-100 percentage
            color_temperature = arguments.get("color_temperature")  # 0-100 percentage

            devices = await self.homey_client.get_devices()
            
            # Get all zones to support both name and UUID lookup
            try:
                zones = await self.homey_client.get_zones()
            except:
                zones = {}

            # Determine if input is UUID or name
            zone_uuid = None
            zone_name = None
            
            if zone_input in zones:
                # Input is UUID
                zone_uuid = zone_input
                zone_name = zones[zone_input].get("name", "")
            else:
                # Input is name - find matching zone
                zone_input_lower = zone_input.lower()
                for zid, zdata in zones.items():
                    if zdata.get("name", "").lower() == zone_input_lower:
                        zone_uuid = zid
                        zone_name = zdata.get("name")
                        break

            # Find lights in the zone (improved filtering)
            lights = []
            for device_id, device in devices.items():
                device_class = device.get("class")
                
                if device_class == "light":
                    # Check zone match (UUID preferred, fallback to name)
                    zone_match = False
                    if zone_uuid and device.get("zone") == zone_uuid:
                        zone_match = True
                    elif zone_name and zone_name.lower() in device.get("zoneName", "").lower():
                        zone_match = True
                    elif zone_input.lower() in device.get("zoneName", "").lower():
                        zone_match = True
                    
                    if zone_match:
                        lights.append((device_id, device))

            if not lights:
                return [
                    TextContent(
                        type="text",
                        text=f"No lights found in zone '{zone_input}'",
                    )
                ]

            results = []
            for device_id, device in lights:
                device_name = device.get("name")
                capabilities = device.get("capabilitiesObj", {})

                try:
                    if action == "on":
                        # Set brightness first (if specified) 
                        if brightness is not None and "dim" in capabilities:
                            # Convert percentage to 0.0-1.0 (minimum 1% to stay on)
                            dim_value = max(0.01, brightness / 100.0)
                            await self.homey_client.set_capability_value(device_id, "dim", dim_value)
                            
                            # According to Homey rule: dim > 0 means onoff = True automatically
                            await self.homey_client.set_capability_value(device_id, "onoff", True)
                            
                            result_text = f"✅ {device_name}: turned on ({brightness}%)"
                        else:
                            # Only on/off without brightness
                            await self.homey_client.set_capability_value(device_id, "onoff", True)
                            result_text = f"✅ {device_name}: turned on"
                        
                        # Set color temperature (if specified and supported)
                        if color_temperature is not None and "light_temperature" in capabilities:
                            temp_value = color_temperature / 100.0  # 0-100% to 0.0-1.0
                            await self.homey_client.set_capability_value(device_id, "light_temperature", temp_value)
                            result_text += f" (temp: {color_temperature}%)"
                        
                        results.append(result_text)
                            
                    elif action == "off":
                        # According to Homey rule: onoff takes precedence
                        await self.homey_client.set_capability_value(device_id, "onoff", False)
                        results.append(f"✅ {device_name}: turned off")
                    
                    elif action == "toggle":
                        # Toggle on/off state
                        current_state = capabilities.get("onoff", {}).get("value", False)
                        new_state = not current_state
                        await self.homey_client.set_capability_value(device_id, "onoff", new_state)
                        state_text = "turned on" if new_state else "turned off"
                        results.append(f"✅ {device_name}: {state_text}")

                except Exception as e:
                    results.append(f"❌ {device_name}: error - {str(e)}")

            return [
                TextContent(
                    type="text",
                    text=f"Lights in '{zone_input}' controlled:\n\n" + "\n".join(results),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error controlling lights: {str(e)}")]
