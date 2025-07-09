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
            Tool(
                name="set_light_color",
                description="Set the color of a light",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "The light device ID"},
                        "hue": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 360,
                            "description": "Color in degrees (0=red, 120=green, 240=blue)"
                        },
                        "saturation": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Saturation percentage (0=white, 100=fully saturated)"
                        },
                        "brightness": {
                            "type": "number",
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Optional: brightness percentage"
                        },
                    },
                    "required": ["device_id", "hue", "saturation"],
                },
            ),
        ]

    async def handle_control_lights_in_zone(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for control_lights_in_zone tool."""
        try:
            zone_name = arguments["zone_name"].lower()
            action = arguments["action"]
            brightness = arguments.get("brightness")  # 0-100 percentage
            color_temperature = arguments.get("color_temperature")  # 0-100 percentage

            devices = await self.homey_client.get_devices()

            # Find lights in the zone
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
                        text=f"No lights found in zone '{arguments['zone_name']}'",
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
                    text=f"Lights in '{arguments['zone_name']}' controlled:\n\n" + "\n".join(results),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error controlling lights: {str(e)}")]

    async def handle_set_light_color(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for set_light_color tool."""
        try:
            device_id = arguments["device_id"]
            hue_degrees = arguments["hue"]  # 0-360
            saturation_percent = arguments["saturation"]  # 0-100
            brightness_percent = arguments.get("brightness")  # Optional 0-100

            # Get device info
            device = await self.homey_client.get_device(device_id)
            device_name = device.get("name", device_id)
            device_class = device.get("class")
            capabilities = device.get("capabilitiesObj", {})

            # Check if it's a light
            if device_class != "light":
                return [TextContent(type="text", text=f"❌ Device '{device_name}' is not a light (class: {device_class})")]

            # Check color capabilities
            missing_caps = []
            if "light_hue" not in capabilities:
                missing_caps.append("light_hue")
            if "light_saturation" not in capabilities:
                missing_caps.append("light_saturation")
            
            if missing_caps:
                return [TextContent(type="text", text=f"❌ Light '{device_name}' has no color support (missing: {', '.join(missing_caps)})")]

            # Convert values to Homey format
            hue_value = hue_degrees / 360.0  # 0-360° to 0.0-1.0
            saturation_value = saturation_percent / 100.0  # 0-100% to 0.0-1.0

            # Set color mode to color
            if "light_mode" in capabilities:
                await self.homey_client.set_capability_value(device_id, "light_mode", "color")

            # Set color properties
            await self.homey_client.set_capability_value(device_id, "light_hue", hue_value)
            await self.homey_client.set_capability_value(device_id, "light_saturation", saturation_value)

            result_text = f"✅ Light '{device_name}' color set (hue: {hue_degrees}°, saturation: {saturation_percent}%"

            # Set brightness if specified
            if brightness_percent is not None and "dim" in capabilities:
                brightness_value = max(0.01, brightness_percent / 100.0)
                await self.homey_client.set_capability_value(device_id, "dim", brightness_value)
                await self.homey_client.set_capability_value(device_id, "onoff", True)
                result_text += f", brightness: {brightness_percent}%"

            result_text += ")"

            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error setting light color: {str(e)}")]