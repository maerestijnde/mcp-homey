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
        """Handler for get_sensor_readings tool - FIXED WITH ZONE UUID SUPPORT."""
        try:
            zone_input = arguments["zone_name"]  # Can be name OR UUID
            sensor_type = arguments.get("sensor_type", "all")

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

            # Find sensors in the zone (improved filtering)
            sensors = []
            for device_id, device in devices.items():
                # Check zone match (UUID preferred, fallback to name)
                zone_match = False
                if zone_uuid and device.get("zone") == zone_uuid:
                    zone_match = True
                elif zone_name and zone_name.lower() in device.get("zoneName", "").lower():
                    zone_match = True
                elif zone_input.lower() in device.get("zoneName", "").lower():
                    zone_match = True

                if zone_match:
                    capabilities = device.get("capabilitiesObj", {})
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
                    text=f"No sensors found in zone '{zone_input}'"
                )]

            # Format sensor data
            result_lines = [f"Sensor readings in '{zone_input}':"]
            
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