import json
import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from mcp.types import TextContent, Tool

from ..homey_client import HomeyAPIClient

logger = logging.getLogger(__name__)


class InsightsTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return all insights tools."""
        return [
            Tool(
                name="get_device_insights",
                description="Get historical data for device capability over a period",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "The device ID"
                        },
                        "capability": {
                            "type": "string", 
                            "description": "Capability name (e.g. measure_temperature, dim, onoff, measure_power)"
                        },
                        "period": {
                            "type": "string",
                            "enum": ["1h", "6h", "1d", "7d", "30d", "1y"],
                            "default": "7d",
                            "description": "Time period for data"
                        },
                        "resolution": {
                            "type": "string",
                            "enum": ["1m", "5m", "1h", "1d"],
                            "default": "1h", 
                            "description": "Data resolution"
                        }
                    },
                    "required": ["device_id", "capability"]
                }
            ),
            Tool(
                name="get_energy_insights",
                description="Get energy consumption data from devices",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "period": {
                            "type": "string",
                            "enum": ["1d", "7d", "30d", "1y"],
                            "default": "7d"
                        },
                        "device_filter": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "group_by": {
                            "type": "string",
                            "enum": ["device", "zone", "type", "total"],
                            "default": "device"
                        }
                    }
                }
            ),
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
            )
        ]

    async def handle_get_device_insights(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_device_insights tool."""
        try:
            device_id = arguments["device_id"]
            capability = arguments["capability"]
            period = arguments.get("period", "7d")
            resolution = arguments.get("resolution", "1h")

            # First get the device to check if it exists and has the capability
            try:
                device = await self.homey_client.get_device(device_id)
            except ValueError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]

            # Check if capability exists on device
            capabilities = device.get("capabilitiesObj", {})
            if capability not in capabilities:
                available_caps = list(capabilities.keys())
                return [TextContent(type="text", text=f"❌ Device {device['name']} doesn't have capability '{capability}'\nAvailable capabilities: {', '.join(available_caps)}")]

            # Get insights logs to find the correct log
            logs = await self.homey_client.get_insights_logs()
            
            # Find matching log for this device + capability
            log_key = f"{device_id}.{capability}"
            matching_log = logs.get(log_key)
            
            if not matching_log:
                return [TextContent(type="text", text=f"❌ No insights log found for {device['name']} - {capability}\nThis capability might not have insights logging enabled.")]

            # Try to get log entries - if not available, show current status
            try:
                entries = await self.homey_client.get_insights_log_entries(
                    uri=device_uri,
                    log_id=capability,
                    resolution=resolution
                )
                
                if not entries:
                    # No historical data, show current value and log info
                    current_value = capabilities[capability].get("value")
                    last_value = matching_log.get("lastValue")
                    units = matching_log.get("units", "")
                    
                    response_text = f"📊 **{device['name']} - {capability.replace('_', ' ').title()}**\n\n"
                    response_text += f"📅 **Period:** {period} | **Resolution:** {resolution}\n"
                    response_text += f"📈 **Status:** Insights logging enabled, no historical data available\n\n"
                    
                    response_text += f"📍 **Current Values:**\n"
                    if current_value is not None:
                        if isinstance(current_value, bool):
                            response_text += f"• Live value: {'On' if current_value else 'Off'}\n"
                        else:
                            response_text += f"• Live value: {current_value} {units}\n"
                    
                    if last_value is not None and last_value != current_value:
                        if isinstance(last_value, bool):
                            response_text += f"• Last logged: {'On' if last_value else 'Off'}\n"
                        else:
                            response_text += f"• Last logged: {last_value} {units}\n"
                    
                    response_text += f"\n💡 **Note:** This device has insights logging enabled, but no historical entries are available for the requested period. This could mean:\n"
                    response_text += f"• Data retention period has expired\n"
                    response_text += f"• Logging was recently enabled\n"
                    response_text += f"• No data points were recorded in the selected timeframe\n"
                    
                    return [TextContent(type="text", text=response_text)]
                
            except Exception as e:
                logger.debug(f"Could not get insights entries: {e}")
                # Fallback to current value display
                current_value = capabilities[capability].get("value")
                last_value = matching_log.get("lastValue")
                units = matching_log.get("units", "")
                
                response_text = f"📊 **{device['name']} - {capability.replace('_', ' ').title()}**\n\n"
                response_text += f"📅 **Period:** {period} | **Resolution:** {resolution}\n"
                response_text += f"📈 **Status:** Insights logging detected, historical data not accessible\n\n"
                
                response_text += f"📍 **Current Values:**\n"
                if current_value is not None:
                    if isinstance(current_value, bool):
                        response_text += f"• Live value: {'On' if current_value else 'Off'}\n"
                    else:
                        response_text += f"• Live value: {current_value} {units}\n"
                
                if last_value is not None:
                    if isinstance(last_value, bool):
                        response_text += f"• Last insights value: {'On' if last_value else 'Off'}\n"
                    else:
                        response_text += f"• Last insights value: {last_value} {units}\n"
                
                response_text += f"\n💡 **Note:** While insights logging is enabled for this device, historical data entries are not accessible through the API. You can view historical charts in the Homey Web App under Insights."
                
                return [TextContent(type="text", text=response_text)]

            # Process historical data for display
            response_text = f"📊 **{device['name']} - {capability.replace('_', ' ').title()}**\n\n"
            response_text += f"📅 **Period:** {period} | **Resolution:** {resolution}\n"
            response_text += f"📈 **Data Points:** {len(entries)}\n\n"

            # Calculate statistics
            values = [entry["v"] for entry in entries if entry["v"] is not None]
            if values:
                if isinstance(values[0], bool):
                    # Boolean capability statistics
                    true_count = sum(1 for v in values if v)
                    false_count = len(values) - true_count
                    true_percentage = (true_count / len(values)) * 100
                    
                    response_text += f"🔘 **State Analysis:**\n"
                    response_text += f"• On/True: {true_count} times ({true_percentage:.1f}%)\n"
                    response_text += f"• Off/False: {false_count} times ({100-true_percentage:.1f}%)\n"
                    response_text += f"• Current: {'On' if entries[-1]['v'] else 'Off'}\n"
                    
                elif isinstance(values[0], (int, float)):
                    # Numeric capability statistics
                    avg_val = sum(values) / len(values)
                    min_val = min(values)
                    max_val = max(values)
                    current_val = entries[-1]["v"]
                    
                    # Get units from log data
                    units = matching_log.get("units", "")
                    decimals = matching_log.get("decimals", 1)
                    
                    response_text += f"📈 **Statistics:**\n"
                    response_text += f"• Average: {avg_val:.{decimals}f} {units}\n"
                    response_text += f"• Minimum: {min_val:.{decimals}f} {units}\n"
                    response_text += f"• Maximum: {max_val:.{decimals}f} {units}\n"
                    response_text += f"• Current: {current_val:.{decimals}f} {units}\n"

                # Add recent trend (last 5 entries)
                if len(entries) >= 5:
                    recent_entries = entries[-5:]
                    response_text += f"\n📉 **Recent Values:**\n"
                    for entry in reversed(recent_entries):
                        timestamp = datetime.fromisoformat(entry["t"].replace("Z", "+00:00"))
                        time_str = timestamp.strftime("%H:%M")
                        value_str = f"{entry['v']:.{decimals}f} {units}" if isinstance(entry['v'], (int, float)) else str(entry['v'])
                        response_text += f"• {time_str}: {value_str}\n"

            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting device insights: {str(e)}")]

    async def handle_get_energy_insights(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_energy_insights tool using ManagerEnergy API."""
        try:
            period = arguments.get("period", "7d")
            device_filter = arguments.get("device_filter", [])
            group_by = arguments.get("group_by", "device")
            
            response_text = f"🔋 **Energy Insights - {period}**\n\n"
            
            # Get current energy state and currency
            try:
                energy_state = await self.homey_client.get_energy_state()
                currency_info = await self.homey_client.get_energy_currency()
                currency = currency_info.get("symbol", "€")
            except Exception as e:
                logger.debug(f"Could not get energy state: {e}")
                currency = "€"
            
            # Get live energy data
            try:
                live_report = await self.homey_client.get_energy_live_report()
                
                response_text += f"⚡ **Current Power Usage:**\n"
                if "electricity" in live_report:
                    total_power = live_report["electricity"].get("total", 0)
                    response_text += f"• Total: {total_power}W\n"
                    
                    devices = live_report["electricity"].get("devices", [])
                    if devices and group_by == "device":
                        response_text += f"• Top consumers:\n"
                        for i, device in enumerate(devices[:5]):
                            name = device.get("name", "Unknown")
                            power = device.get("value", 0)
                            response_text += f"  {i+1}. {name}: {power}W\n"
                
                if "gas" in live_report:
                    gas_usage = live_report["gas"].get("total", 0)
                    if gas_usage > 0:
                        response_text += f"• Gas: {gas_usage} m³/h\n"
                        
                if "water" in live_report:
                    water_usage = live_report["water"].get("total", 0)  
                    if water_usage > 0:
                        response_text += f"• Water: {water_usage} L/min\n"
                        
                response_text += "\n"
                
            except Exception as e:
                logger.debug(f"Could not get live energy report: {e}")
            
            # Get historical reports based on period
            try:
                if period == "1d":
                    # Get today's report
                    from datetime import datetime
                    today = datetime.now().strftime("%Y-%m-%d")
                    report = await self.homey_client.get_energy_report_day(today)
                    
                    response_text += f"📊 **Today's Consumption:**\n"
                    if "electricity" in report:
                        elec = report["electricity"]
                        consumed = elec.get("consumed", 0)
                        produced = elec.get("produced", 0)
                        cost = elec.get("cost", 0)
                        response_text += f"• Electricity: {consumed:.1f} kWh"
                        if produced > 0:
                            response_text += f" (produced: {produced:.1f} kWh)"
                        response_text += f" - {currency}{cost:.2f}\n"
                    
                    if "gas" in report:
                        gas = report["gas"]
                        consumed = gas.get("consumed", 0)
                        cost = gas.get("cost", 0)
                        if consumed > 0:
                            response_text += f"• Gas: {consumed:.1f} m³ - {currency}{cost:.2f}\n"
                    
                    if "water" in report:
                        water = report["water"]
                        consumed = water.get("consumed", 0)
                        cost = water.get("cost", 0)
                        if consumed > 0:
                            response_text += f"• Water: {consumed:.0f} L - {currency}{cost:.2f}\n"
                
                elif period == "7d":
                    # Get this week's report
                    from datetime import datetime
                    today = datetime.now()
                    iso_week = f"{today.year}-W{today.isocalendar()[1]:02d}"
                    report = await self.homey_client.get_energy_report_week(iso_week)
                    
                    response_text += f"📊 **This Week's Consumption:**\n"
                    if "electricity" in report:
                        elec = report["electricity"]
                        consumed = elec.get("consumed", 0)
                        produced = elec.get("produced", 0)
                        cost = elec.get("cost", 0)
                        response_text += f"• Electricity: {consumed:.1f} kWh"
                        if produced > 0:
                            response_text += f" (produced: {produced:.1f} kWh)"
                        response_text += f" - {currency}{cost:.2f}\n"
                        
                        daily_avg = consumed / 7
                        response_text += f"  Average per day: {daily_avg:.1f} kWh\n"
                    
                    if "gas" in report:
                        gas = report["gas"]
                        consumed = gas.get("consumed", 0)
                        cost = gas.get("cost", 0)
                        if consumed > 0:
                            response_text += f"• Gas: {consumed:.1f} m³ - {currency}{cost:.2f}\n"
                    
                    if "water" in report:
                        water = report["water"]
                        consumed = water.get("consumed", 0)
                        cost = water.get("cost", 0)
                        if consumed > 0:
                            response_text += f"• Water: {consumed:.0f} L - {currency}{cost:.2f}\n"
                
                elif period == "30d":
                    # Get this month's report
                    from datetime import datetime
                    today = datetime.now()
                    year_month = today.strftime("%Y-%m")
                    report = await self.homey_client.get_energy_report_month(year_month)
                    
                    response_text += f"📊 **This Month's Consumption:**\n"
                    if "electricity" in report:
                        elec = report["electricity"]
                        consumed = elec.get("consumed", 0)
                        produced = elec.get("produced", 0)
                        cost = elec.get("cost", 0)
                        response_text += f"• Electricity: {consumed:.1f} kWh"
                        if produced > 0:
                            response_text += f" (produced: {produced:.1f} kWh)"
                        response_text += f" - {currency}{cost:.2f}\n"
                        
                        daily_avg = consumed / today.day
                        response_text += f"  Average per day: {daily_avg:.1f} kWh\n"
                    
                    if "gas" in report:
                        gas = report["gas"]
                        consumed = gas.get("consumed", 0)
                        cost = gas.get("cost", 0)
                        if consumed > 0:
                            response_text += f"• Gas: {consumed:.1f} m³ - {currency}{cost:.2f}\n"
                    
                    if "water" in report:
                        water = report["water"]
                        consumed = water.get("consumed", 0)
                        cost = water.get("cost", 0)
                        if consumed > 0:
                            response_text += f"• Water: {consumed:.0f} L - {currency}{cost:.2f}\n"
                
            except Exception as e:
                logger.debug(f"Could not get energy reports: {e}")
                response_text += f"⚠️ Historical energy reports not available\n"
            
            # Add efficiency tips
            try:
                live_report = await self.homey_client.get_energy_live_report()
                current_power = live_report.get("electricity", {}).get("total", 0)
                
                response_text += f"\n💡 **Energy Tips:**\n"
                if current_power > 1500:
                    response_text += f"• High power usage ({current_power}W) - check for energy-hungry devices\n"
                elif current_power < 300:
                    response_text += f"• Great! Low power usage ({current_power}W) - very efficient\n"
                else:
                    response_text += f"• Moderate power usage ({current_power}W) - room for improvement\n"
                
            except:
                pass
            
            response_text += f"\n🔄 *Real-time data from Homey Energy Manager*"
            
            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting energy insights: {str(e)}")]

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
