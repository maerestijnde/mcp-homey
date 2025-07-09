import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ...client import HomeyAPIClient

logger = logging.getLogger(__name__)


class EnergyInsightsTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return energy insights tools."""
        return [
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
                name="get_energy_report_hourly",
                description="Get hourly energy consumption report for a specific hour",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date_hour": {
                            "type": "string",
                            "description": "Date and hour in format YYYY-MM-DD-HH (e.g. 2024-01-15-14)"
                        },
                        "cache": {
                            "type": "string",
                            "description": "Cache control parameter (optional)"
                        }
                    },
                    "required": ["date_hour"]
                }
            ),
            Tool(
                name="get_energy_report_yearly", 
                description="Get yearly energy consumption report for a specific year",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "string",
                            "description": "Year in format YYYY (e.g. 2024)"
                        },
                        "cache": {
                            "type": "string",
                            "description": "Cache control parameter (optional)"
                        }
                    },
                    "required": ["year"]
                }
            )
        ]

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

    async def handle_get_energy_report_hourly(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_energy_report_hourly tool."""
        try:
            date_hour = arguments["date_hour"]
            cache = arguments.get("cache")
            
            result = await self.homey_client.get_energy_report_hour(date_hour, cache)
            
            # Format the response nicely
            response_text = f"⏰ **Hourly Energy Report - {date_hour}**\n\n"
            
            if "electricity" in result:
                elec = result["electricity"]
                response_text += f"⚡ **Electricity:**\n"
                response_text += f"  • Consumed: {elec.get('consumed', 0)} kWh\n"
                response_text += f"  • Produced: {elec.get('produced', 0)} kWh\n"
                response_text += f"  • Cost: €{elec.get('cost', 0)}\n\n"
            
            if "gas" in result:
                gas = result["gas"]
                response_text += f"🔥 **Gas:**\n"
                response_text += f"  • Consumed: {gas.get('consumed', 0)} m³\n"
                response_text += f"  • Cost: €{gas.get('cost', 0)}\n\n"
            
            if "water" in result:
                water = result["water"]
                response_text += f"💧 **Water:**\n"
                response_text += f"  • Consumed: {water.get('consumed', 0)} L\n"
                response_text += f"  • Cost: €{water.get('cost', 0)}\n"
            
            response_text += f"\n🔄 *Data from Homey Energy Manager*"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting hourly energy report: {str(e)}")]

    async def handle_get_energy_report_yearly(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_energy_report_yearly tool."""
        try:
            year = arguments["year"]
            cache = arguments.get("cache")
            
            result = await self.homey_client.get_energy_report_year(year, cache)
            
            # Format the response nicely
            response_text = f"📅 **Yearly Energy Report - {year}**\n\n"
            
            if "electricity" in result:
                elec = result["electricity"]
                response_text += f"⚡ **Electricity:**\n"
                response_text += f"  • Consumed: {elec.get('consumed', 0):,.1f} kWh\n"
                response_text += f"  • Produced: {elec.get('produced', 0):,.1f} kWh\n"
                response_text += f"  • Cost: €{elec.get('cost', 0):,.2f}\n"
                
                # Add monthly average
                consumed = elec.get('consumed', 0)
                if consumed > 0:
                    monthly_avg = consumed / 12
                    response_text += f"  • Monthly average: {monthly_avg:,.1f} kWh\n"
                response_text += "\n"
            
            if "gas" in result:
                gas = result["gas"]
                response_text += f"🔥 **Gas:**\n"
                response_text += f"  • Consumed: {gas.get('consumed', 0):,.1f} m³\n"
                response_text += f"  • Cost: €{gas.get('cost', 0):,.2f}\n"
                
                # Add monthly average
                consumed = gas.get('consumed', 0)
                if consumed > 0:
                    monthly_avg = consumed / 12
                    response_text += f"  • Monthly average: {monthly_avg:,.1f} m³\n"
                response_text += "\n"
            
            if "water" in result:
                water = result["water"]
                response_text += f"💧 **Water:**\n"
                response_text += f"  • Consumed: {water.get('consumed', 0):,.0f} L\n"
                response_text += f"  • Cost: €{water.get('cost', 0):,.2f}\n"
                
                # Add monthly average
                consumed = water.get('consumed', 0)
                if consumed > 0:
                    monthly_avg = consumed / 12
                    response_text += f"  • Monthly average: {monthly_avg:,.0f} L\n"
            
            response_text += f"\n🔄 *Data from Homey Energy Manager*"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting yearly energy report: {str(e)}")]