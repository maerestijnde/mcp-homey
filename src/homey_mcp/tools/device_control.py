import json
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ..homey_client import HomeyAPIClient


class DeviceControlTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return all device control tools."""
        return [
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
            Tool(
                name="get_sensor_readings",
                description="Get sensor readings from a specific zone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "zone_name": {"type": "string", "description": "Zone name"},
                        "sensor_type": {
                            "type": "string",
                            "enum": ["temperature", "humidity", "battery", "power", "all"],
                            "description": "Sensor data type (optional, defaults to 'all')"
                        },
                    },
                    "required": ["zone_name"],
                },
            ),
        ]

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

    async def handle_get_sensor_readings(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_sensor_readings tool."""
        try:
            zone_name = arguments["zone_name"].lower()
            sensor_type = arguments.get("sensor_type", "all")

            devices = await self.homey_client.get_devices()

            # Find sensors in the zone
            sensors = []
            for device_id, device in devices.items():
                device_zone = device.get("zoneName", "").lower()
                capabilities = device.get("capabilitiesObj", {})

                if zone_name in device_zone:
                    # Check if device has sensor capabilities
                    sensor_caps = {}
                    for cap_name, cap_data in capabilities.items():
                        if cap_name.startswith("measure_") or cap_name.startswith("alarm_"):
                            if sensor_type == "all" or sensor_type in cap_name:
                                sensor_caps[cap_name] = cap_data

                    if sensor_caps:
                        sensors.append({
                            "device_id": device_id,
                            "name": device.get("name"),
                            "class": device.get("class"),
                            "capabilities": sensor_caps
                        })

            if not sensors:
                return [TextContent(
                    type="text",
                    text=f"No sensors found in zone '{arguments['zone_name']}'"
                )]

            # Format sensor data
            result_lines = [f"Sensor readings in '{arguments['zone_name']}':"]
            
            for sensor in sensors:
                result_lines.append(f"\n📊 {sensor['name']} ({sensor['class']}):")
                
                for cap_name, cap_data in sensor["capabilities"].items():
                    value = cap_data.get("value")
                    title = cap_data.get("title", cap_name)
                    
                    # Format value based on capability type
                    if cap_name.startswith("measure_temperature"):
                        formatted_value = f"{value}°C"
                    elif cap_name.startswith("measure_humidity"):
                        formatted_value = f"{value}%"
                    elif cap_name.startswith("measure_battery"):
                        formatted_value = f"{value}%"
                    elif cap_name.startswith("measure_power"):
                        formatted_value = f"{value}W"
                    elif cap_name.startswith("alarm_"):
                        formatted_value = "🚨 ACTIVE" if value else "✅ OK"
                    else:
                        formatted_value = str(value)
                    
                    result_lines.append(f"  • {title}: {formatted_value}")

            return [TextContent(type="text", text="\n".join(result_lines))]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting sensor data: {str(e)}")]
