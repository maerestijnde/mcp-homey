import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ...client import HomeyAPIClient

logger = logging.getLogger(__name__)


class LiveInsightsTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return live insights tools."""
        return [
            Tool(
                name="get_live_insights",
                description="Real-time dashboard data for monitoring",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "metrics": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["total_power", "active_devices", "temp_avg", "humidity_avg", "online_devices", "energy_today"]
                            },
                            "default": ["total_power", "active_devices"]
                        }
                    }
                }
            ),
        ]

    async def handle_get_live_insights(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_live_insights tool."""
        try:
            metrics = arguments.get("metrics", ["total_power", "active_devices"])
            
            current_time = datetime.now().strftime("%H:%M:%S")
            response_text = f"📊 **Live Dashboard - {current_time}**\n\n"
            
            # Get all devices for general metrics
            devices = await self.homey_client.get_devices()
            total_devices = len(devices)
            online_devices = sum(1 for device in devices.values() if device.get("available", False))
            
            for metric in metrics:
                if metric == "total_power":
                    # Sum current power consumption from all power-measuring devices
                    total_power = 0.0
                    power_devices = 0
                    
                    for device_id, device in devices.items():
                        capabilities = device.get("capabilitiesObj", {})
                        if "measure_power" in capabilities:
                            power_value = capabilities["measure_power"].get("value", 0)
                            if power_value and isinstance(power_value, (int, float)):
                                total_power += power_value
                                power_devices += 1
                    
                    response_text += f"⚡ **Total Power:** {total_power:.1f}W"
                    if power_devices > 0:
                        response_text += f" ({power_devices} devices)\n"
                    else:
                        response_text += " (No power monitoring devices found)\n"
                
                elif metric == "active_devices":
                    # Count devices that are currently "on" or active
                    active_devices = 0
                    for device_id, device in devices.items():
                        capabilities = device.get("capabilitiesObj", {})
                        if "onoff" in capabilities:
                            if capabilities["onoff"].get("value", False):
                                active_devices += 1
                        elif "dim" in capabilities:
                            dim_value = capabilities["dim"].get("value", 0)
                            if dim_value and dim_value > 0:
                                active_devices += 1
                    
                    response_text += f"📱 **Active Devices:** {active_devices}/{total_devices}\n"
                
                elif metric == "temp_avg":
                    # Average temperature from all temperature sensors
                    temp_values = []
                    for device_id, device in devices.items():
                        capabilities = device.get("capabilitiesObj", {})
                        if "measure_temperature" in capabilities:
                            temp_value = capabilities["measure_temperature"].get("value")
                            if temp_value and isinstance(temp_value, (int, float)):
                                temp_values.append(temp_value)
                    
                    if temp_values:
                        avg_temp = sum(temp_values) / len(temp_values)
                        response_text += f"🌡️ **Avg Temperature:** {avg_temp:.1f}°C ({len(temp_values)} sensors)\n"
                    else:
                        response_text += f"🌡️ **Avg Temperature:** No sensors found\n"
                
                elif metric == "humidity_avg":
                    # Average humidity from all humidity sensors
                    humidity_values = []
                    for device_id, device in devices.items():
                        capabilities = device.get("capabilitiesObj", {})
                        if "measure_humidity" in capabilities:
                            humidity_value = capabilities["measure_humidity"].get("value")
                            if humidity_value and isinstance(humidity_value, (int, float)):
                                humidity_values.append(humidity_value)
                    
                    if humidity_values:
                        avg_humidity = sum(humidity_values) / len(humidity_values)
                        response_text += f"💧 **Avg Humidity:** {avg_humidity:.1f}% ({len(humidity_values)} sensors)\n"
                    else:
                        response_text += f"💧 **Avg Humidity:** No sensors found\n"
                
                elif metric == "online_devices":
                    response_text += f"📶 **Online Devices:** {online_devices}/{total_devices}\n"
                
                elif metric == "energy_today":
                    # Calculate today's energy consumption from meter readings
                    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    now = datetime.now()
                    
                    total_energy_today = 0.0
                    energy_devices = 0
                    
                    # Get insights logs for energy meters
                    logs = await self.homey_client.get_insights_logs()
                    
                    for log_id, log_data in logs.items():
                        if log_data.get("id") == "meter_power":
                            try:
                                uri = log_data.get("uri", "")
                                entries = await self.homey_client.get_insights_log_entries(
                                    uri=uri,
                                    log_id="meter_power",
                                    resolution="1h",
                                    from_timestamp=today_start.isoformat(),
                                    to_timestamp=now.isoformat()
                                )
                                
                                if len(entries) >= 2:
                                    # Calculate consumption as difference between first and last reading
                                    start_value = entries[0]["v"]
                                    end_value = entries[-1]["v"]
                                    if isinstance(start_value, (int, float)) and isinstance(end_value, (int, float)):
                                        daily_consumption = end_value - start_value
                                        if daily_consumption >= 0:  # Sanity check
                                            total_energy_today += daily_consumption
                                            energy_devices += 1
                            except Exception as e:
                                logger.debug(f"Error calculating daily energy for {log_id}: {e}")
                                continue
                    
                    if energy_devices > 0:
                        response_text += f"🔋 **Energy Today:** {total_energy_today:.1f} kWh ({energy_devices} meters)\n"
                    else:
                        response_text += f"🔋 **Energy Today:** No energy meters found\n"
            
            # Add storage info if available
            try:
                storage_info = await self.homey_client.get_insights_storage_info()
                used_mb = storage_info.get("used", 0) / (1024 * 1024)
                total_mb = storage_info.get("total", 0) / (1024 * 1024)
                usage_percent = (used_mb / total_mb * 100) if total_mb > 0 else 0
                
                response_text += f"\n💾 **Insights Storage:** {used_mb:.1f}MB / {total_mb:.1f}MB ({usage_percent:.1f}%)\n"
                response_text += f"📈 **Log Entries:** {storage_info.get('entries', 0):,}\n"
            except Exception as e:
                logger.debug(f"Could not get storage info: {e}")
            
            response_text += f"\n🔄 *Real-time data from Homey Pro*"
            
            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting live insights: {str(e)}")]