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
                            "description": "De capability om te bedienen. Voorbeelden:\n" +
                                         "- onoff: true/false (aan/uit)\n" +
                                         "- dim: 0.0-1.0 of 0-100% (helderheid)\n" +
                                         "- target_temperature: number (gewenste temp in °C)\n" +
                                         "- light_hue: 0.0-1.0 (kleur)\n" +
                                         "- light_saturation: 0.0-1.0 (verzadiging)\n" +
                                         "- light_temperature: 0.0-1.0 (warm-koud wit)\n" +
                                         "- light_mode: 'color' of 'temperature'",
                        },
                        "value": {
                            "description": "De waarde om te zetten. Let op types:\n" +
                                         "- boolean voor onoff, alarm_*\n" +
                                         "- number 0.0-1.0 voor dim, light_* (of 0-100% wordt automatisch geconverteerd)\n" +
                                         "- number voor temperaturen, power, etc."
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
                            "enum": ["on", "off", "toggle"],
                            "description": "Actie: 'on', 'off' of 'toggle'",
                        },
                        "brightness": {
                            "type": "number",
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Helderheid percentage (1-100%). Werkt alleen bij 'on' actie.",
                        },
                        "color_temperature": {
                            "type": "number", 
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Optioneel: kleurtemperatuur percentage (0=warm, 100=koud wit)",
                        },
                    },
                    "required": ["zone_name", "action"],
                },
            ),
            Tool(
                name="set_thermostat_temperature",
                description="Zet de gewenste temperatuur van een thermostaat",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "Het ID van de thermostaat"},
                        "temperature": {
                            "type": "number",
                            "minimum": 5,
                            "maximum": 35,
                            "description": "Gewenste temperatuur in graden Celsius"
                        },
                    },
                    "required": ["device_id", "temperature"],
                },
            ),
            Tool(
                name="set_light_color",
                description="Zet de kleur van een lamp",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "Het ID van de lamp"},
                        "hue": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 360,
                            "description": "Kleur in graden (0=rood, 120=groen, 240=blauw)"
                        },
                        "saturation": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Verzadiging percentage (0=wit, 100=volledig verzadigd)"
                        },
                        "brightness": {
                            "type": "number",
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Optioneel: helderheid percentage"
                        },
                    },
                    "required": ["device_id", "hue", "saturation"],
                },
            ),
            Tool(
                name="get_sensor_readings",
                description="Haal sensor metingen op van specifieke zone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "zone_name": {"type": "string", "description": "Naam van de zone"},
                        "sensor_type": {
                            "type": "string",
                            "enum": ["temperature", "humidity", "battery", "power", "all"],
                            "description": "Type sensor data (optioneel, standaard 'all')"
                        },
                    },
                    "required": ["zone_name"],
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
            brightness = arguments.get("brightness")  # 0-100 percentage
            color_temperature = arguments.get("color_temperature")  # 0-100 percentage

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
                capabilities = device.get("capabilitiesObj", {})

                try:
                    # GECORRIGEERDE CAPABILITY LOGIC:
                    if action == "on":
                        # Zet brightness eerst (als opgegeven) 
                        if brightness is not None and "dim" in capabilities:
                            # KRITIEKE FIX: Converteer percentage naar 0.0-1.0 (minimum 1% om aan te blijven)
                            dim_value = max(0.01, brightness / 100.0)
                            await self.homey_client.set_capability_value(device_id, "dim", dim_value)
                            
                            # Volgens Homey regel: dim > 0 betekent automatisch onoff = True
                            await self.homey_client.set_capability_value(device_id, "onoff", True)
                            
                            result_text = f"✅ {device_name}: aangezet ({brightness}%)"
                        else:
                            # Alleen aan/uit zonder brightness
                            await self.homey_client.set_capability_value(device_id, "onoff", True)
                            result_text = f"✅ {device_name}: aangezet"
                        
                        # Zet kleurtemperatuur (als opgegeven en ondersteund)
                        if color_temperature is not None and "light_temperature" in capabilities:
                            temp_value = color_temperature / 100.0  # 0-100% naar 0.0-1.0
                            await self.homey_client.set_capability_value(device_id, "light_temperature", temp_value)
                            result_text += f" (temp: {color_temperature}%)"
                        
                        results.append(result_text)
                            
                    elif action == "off":
                        # Volgens Homey regel: onoff heeft voorrang
                        await self.homey_client.set_capability_value(device_id, "onoff", False)
                        results.append(f"✅ {device_name}: uitgezet")
                    
                    elif action == "toggle":
                        # Toggle on/off state
                        current_state = capabilities.get("onoff", {}).get("value", False)
                        new_state = not current_state
                        await self.homey_client.set_capability_value(device_id, "onoff", new_state)
                        state_text = "aangezet" if new_state else "uitgezet"
                        results.append(f"✅ {device_name}: {state_text}")

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

    async def handle_set_thermostat_temperature(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler voor set_thermostat_temperature tool."""
        try:
            device_id = arguments["device_id"]
            temperature = arguments["temperature"]

            # Haal device info op
            device = await self.homey_client.get_device(device_id)
            device_name = device.get("name", device_id)
            device_class = device.get("class")

            # Check of het een thermostaat is
            if device_class != "thermostat":
                return [TextContent(type="text", text=f"❌ Device '{device_name}' is geen thermostaat (class: {device_class})")]

            # Check of target_temperature capability bestaat
            capabilities = device.get("capabilitiesObj", {})
            if "target_temperature" not in capabilities:
                return [TextContent(type="text", text=f"❌ Thermostaat '{device_name}' heeft geen target_temperature capability")]

            # Zet de gewenste temperatuur
            await self.homey_client.set_capability_value(device_id, "target_temperature", temperature)

            # Haal huidige temperatuur op als beschikbaar
            current_temp = capabilities.get("measure_temperature", {}).get("value")
            current_text = f" (huidig: {current_temp}°C)" if current_temp is not None else ""

            return [TextContent(
                type="text",
                text=f"✅ Thermostaat '{device_name}' ingesteld op {temperature}°C{current_text}"
            )]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fout bij instellen thermostaat: {str(e)}")]

    async def handle_set_light_color(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler voor set_light_color tool."""
        try:
            device_id = arguments["device_id"]
            hue_degrees = arguments["hue"]  # 0-360
            saturation_percent = arguments["saturation"]  # 0-100
            brightness_percent = arguments.get("brightness")  # Optional 0-100

            # Haal device info op
            device = await self.homey_client.get_device(device_id)
            device_name = device.get("name", device_id)
            device_class = device.get("class")
            capabilities = device.get("capabilitiesObj", {})

            # Check of het een lamp is
            if device_class != "light":
                return [TextContent(type="text", text=f"❌ Device '{device_name}' is geen lamp (class: {device_class})")]

            # Check kleur capabilities
            missing_caps = []
            if "light_hue" not in capabilities:
                missing_caps.append("light_hue")
            if "light_saturation" not in capabilities:
                missing_caps.append("light_saturation")
            
            if missing_caps:
                return [TextContent(type="text", text=f"❌ Lamp '{device_name}' heeft geen kleur ondersteuning (missing: {', '.join(missing_caps)})")]

            # Converteer waarden naar Homey formaat
            hue_value = hue_degrees / 360.0  # 0-360° naar 0.0-1.0
            saturation_value = saturation_percent / 100.0  # 0-100% naar 0.0-1.0

            # Zet kleur mode naar color
            if "light_mode" in capabilities:
                await self.homey_client.set_capability_value(device_id, "light_mode", "color")

            # Zet kleur properties
            await self.homey_client.set_capability_value(device_id, "light_hue", hue_value)
            await self.homey_client.set_capability_value(device_id, "light_saturation", saturation_value)

            result_text = f"✅ Lamp '{device_name}' kleur ingesteld (hue: {hue_degrees}°, verzadiging: {saturation_percent}%"

            # Zet brightness als opgegeven
            if brightness_percent is not None and "dim" in capabilities:
                brightness_value = max(0.01, brightness_percent / 100.0)
                await self.homey_client.set_capability_value(device_id, "dim", brightness_value)
                await self.homey_client.set_capability_value(device_id, "onoff", True)
                result_text += f", helderheid: {brightness_percent}%"

            result_text += ")"

            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fout bij instellen lamp kleur: {str(e)}")]

    async def handle_get_sensor_readings(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler voor get_sensor_readings tool."""
        try:
            zone_name = arguments["zone_name"].lower()
            sensor_type = arguments.get("sensor_type", "all")

            devices = await self.homey_client.get_devices()

            # Zoek sensors in de zone
            sensors = []
            for device_id, device in devices.items():
                device_zone = device.get("zoneName", "").lower()
                capabilities = device.get("capabilitiesObj", {})

                if zone_name in device_zone:
                    # Check of device sensor capabilities heeft
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
                    text=f"Geen sensors gevonden in zone '{arguments['zone_name']}'"
                )]

            # Format sensor data
            result_lines = [f"Sensor metingen in '{arguments['zone_name']}':"]
            
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
                        formatted_value = "🚨 ACTIEF" if value else "✅ OK"
                    else:
                        formatted_value = str(value)
                    
                    result_lines.append(f"  • {title}: {formatted_value}")

            return [TextContent(type="text", text="\n".join(result_lines))]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fout bij ophalen sensor data: {str(e)}")]
