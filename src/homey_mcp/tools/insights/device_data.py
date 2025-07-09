import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ...client import HomeyAPIClient

logger = logging.getLogger(__name__)


class DeviceInsightsTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return device insights tools."""
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
                    uri=matching_log.get("uri", ""),
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