from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ...client import HomeyAPIClient


class ZoneManagementTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return zone management tools."""
        return [
            Tool(
                name="get_zones",
                description="Get all available zones in Homey",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
        ]

    async def handle_get_zones(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_zones tool."""
        try:
            zones = await self.homey_client.get_zones()

            # Format zones data nicely
            zone_list = []
            parent_zones = []
            sub_zones = []

            for zone_id, zone in zones.items():
                zone_info = {
                    "id": zone_id,
                    "name": zone.get("name"),
                    "parent": zone.get("parent"),
                    "icon": zone.get("icon"),
                    "active": zone.get("active", True),
                }
                
                if zone.get("parent"):
                    sub_zones.append(zone_info)
                else:
                    parent_zones.append(zone_info)
                    
                zone_list.append(zone_info)

            response_text = f"🏠 **Available Zones ({len(zones)} total)**\n\n"
            
            # Show parent zones first
            if parent_zones:
                response_text += "📍 **Main Zones:**\n"
                for zone in parent_zones:
                    icon = zone.get("icon", "📍")
                    name = zone.get("name", "Unknown")
                    zone_id = zone.get("id")
                    status = "✅" if zone.get("active") else "❌"
                    response_text += f"  {status} {name} (ID: {zone_id})\n"
                response_text += "\n"
            
            # Show sub-zones
            if sub_zones:
                response_text += "📂 **Sub-zones:**\n"
                for zone in sub_zones:
                    icon = zone.get("icon", "📂")
                    name = zone.get("name", "Unknown")
                    zone_id = zone.get("id")
                    parent_id = zone.get("parent")
                    
                    # Find parent name
                    parent_name = "Unknown"
                    for parent_zone in parent_zones:
                        if parent_zone.get("id") == parent_id:
                            parent_name = parent_zone.get("name", "Unknown")
                            break
                    
                    status = "✅" if zone.get("active") else "❌"
                    response_text += f"  {status} {name} → {parent_name} (ID: {zone_id})\n"

            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting zones: {str(e)}")]
