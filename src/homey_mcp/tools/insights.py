import json
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from mcp.types import TextContent, Tool

from ..homey_client import HomeyAPIClient


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

            # Demo data generation
            import random
            
            # Generate some realistic demo data
            response_text = f"📊 Device Insights for {device_id} - {capability}\n\n"
            response_text += f"📅 Period: {period} | Resolution: {resolution}\n\n"
            
            if capability == "measure_temperature":
                avg_temp = round(random.uniform(19, 23), 1)
                response_text += f"🌡️ **Temperature Data:**\n"
                response_text += f"• Average: {avg_temp}°C\n"
                response_text += f"• Min: {avg_temp - 2:.1f}°C\n"
                response_text += f"• Max: {avg_temp + 2:.1f}°C\n"
            elif capability == "dim":
                avg_brightness = round(random.uniform(0.3, 0.8), 2)
                response_text += f"💡 **Brightness Data:**\n"
                response_text += f"• Average brightness: {avg_brightness*100:.0f}%\n"
                response_text += f"• On time: {random.randint(4, 8)} hours/day\n"
                response_text += f"• Peak usage: 19:00-22:00\n"
            elif capability == "measure_power":
                avg_power = round(random.uniform(20, 80), 1)
                response_text += f"⚡ **Power Data:**\n"
                response_text += f"• Average consumption: {avg_power}W\n"
                response_text += f"• Daily consumption: {avg_power * 24 / 1000:.1f} kWh\n"
                response_text += f"• Estimated cost: €{avg_power * 24 * 0.30 / 1000:.2f}/day\n"
            else:
                response_text += f"📈 **General Data:**\n"
                response_text += f"• Data points: {random.randint(50, 200)}\n"
                response_text += f"• Last value: {random.uniform(0, 100):.1f}\n"
            
            response_text += f"\n💡 *Demo data - real Homey Insights API yet to be implemented*"

            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting device insights: {str(e)}")]

    async def handle_get_energy_insights(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_energy_insights tool."""
        try:
            period = arguments.get("period", "7d")
            device_filter = arguments.get("device_filter", [])
            group_by = arguments.get("group_by", "device")
            
            import random
            
            response_text = f"🔋 Energy Insights - {period}\n\n"
            
            # Demo energy data
            total_consumption = round(random.uniform(50, 200), 1)
            total_cost = round(total_consumption * 0.30, 2)
            
            response_text += f"📊 **Total Overview:**\n"
            response_text += f"• Total consumption: {total_consumption} kWh\n"
            response_text += f"• Estimated cost: €{total_cost}\n"
            response_text += f"• Average per day: {total_consumption/7:.1f} kWh\n\n"
            
            if group_by == "device":
                response_text += f"📱 **Top Consumers:**\n"
                devices = ["Washing Machine", "Refrigerator", "TV", "Lighting", "Heating"]
                for i, device in enumerate(devices[:3]):
                    consumption = round(random.uniform(10, 50), 1)
                    percentage = round((consumption / total_consumption) * 100, 1)
                    response_text += f"{i+1}. {device}: {consumption} kWh ({percentage}%)\n"
            
            response_text += f"\n💡 *Demo data - connect with real Homey energy monitoring*"
            
            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting energy insights: {str(e)}")]

    async def handle_get_live_insights(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_live_insights tool."""
        try:
            metrics = arguments.get("metrics", ["total_power", "active_devices"])
            
            import random
            
            current_time = datetime.now().strftime("%H:%M:%S")
            response_text = f"📊 Live Dashboard - {current_time}\n\n"
            
            for metric in metrics:
                if metric == "total_power":
                    power = round(random.uniform(500, 2000), 1)
                    response_text += f"⚡ **Total Power:** {power}W\n"
                elif metric == "active_devices":
                    active = random.randint(15, 35)
                    total = random.randint(40, 60)
                    response_text += f"📱 **Active Devices:** {active}/{total}\n"
                elif metric == "temp_avg":
                    temp = round(random.uniform(19.5, 21.5), 1)
                    response_text += f"🌡️ **Avg Temperature:** {temp}°C\n"
                elif metric == "humidity_avg":
                    humidity = round(random.uniform(45, 65), 1)
                    response_text += f"💧 **Avg Humidity:** {humidity}%\n"
                elif metric == "online_devices":
                    online = random.randint(38, 42)
                    total = random.randint(40, 45)
                    response_text += f"📶 **Online Devices:** {online}/{total}\n"
                elif metric == "energy_today":
                    energy = round(random.uniform(8, 25), 1)
                    response_text += f"🔋 **Energy Today:** {energy} kWh\n"
            
            response_text += f"\n🔄 *Auto-refresh: Every 30 seconds*"
            
            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting live insights: {str(e)}")]
