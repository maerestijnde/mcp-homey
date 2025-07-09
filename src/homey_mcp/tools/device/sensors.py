from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ...client import HomeyAPIClient


class SensorTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return sensor reading tools."""
        return [
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