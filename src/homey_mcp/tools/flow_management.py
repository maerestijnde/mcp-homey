import json
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ..homey_client import HomeyAPIClient


class FlowManagementTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return all flow management tools."""
        return [
            Tool(
                name="get_flows",
                description="Get all Homey flows (automation)",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="trigger_flow",
                description="Start a specific Homey flow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {
                            "type": "string",
                            "description": "The ID of the flow to start",
                        }
                    },
                    "required": ["flow_id"],
                },
            ),
            Tool(
                name="find_flow_by_name",
                description="Search flows by name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_name": {
                            "type": "string",
                            "description": "Name or part of the flow name",
                        }
                    },
                    "required": ["flow_name"],
                },
            ),
        ]

    async def handle_get_flows(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_flows tool."""
        try:
            flows = await self.homey_client.get_flows()

            flow_list = []
            for flow_id, flow in flows.items():
                flow_info = {
                    "id": flow_id,
                    "name": flow.get("name"),
                    "enabled": flow.get("enabled", True),
                    "broken": flow.get("broken", False),
                }
                flow_list.append(flow_info)

            return [
                TextContent(
                    type="text",
                    text=f"Found {len(flow_list)} flows:\n\n"
                    + json.dumps(flow_list, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flows: {str(e)}")]

    async def handle_trigger_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for trigger_flow tool."""
        try:
            flow_id = arguments["flow_id"]

            # Get flow info for name
            flows = await self.homey_client.get_flows()
            if flow_id not in flows:
                return [TextContent(type="text", text=f"❌ Flow with ID '{flow_id}' not found")]

            flow_name = flows[flow_id].get("name", flow_id)

            # Trigger the flow
            success = await self.homey_client.trigger_flow(flow_id)

            if success:
                return [TextContent(type="text", text=f"✅ Flow '{flow_name}' started successfully")]
            else:
                return [TextContent(type="text", text=f"❌ Could not start flow '{flow_name}'")]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error starting flow: {str(e)}")]

    async def handle_find_flow_by_name(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for find_flow_by_name tool."""
        try:
            search_name = arguments["flow_name"].lower()
            flows = await self.homey_client.get_flows()

            matching_flows = []
            for flow_id, flow in flows.items():
                flow_name = flow.get("name", "").lower()

                if search_name in flow_name:
                    matching_flows.append(
                        {
                            "id": flow_id,
                            "name": flow.get("name"),
                            "enabled": flow.get("enabled"),
                            "broken": flow.get("broken", False),
                        }
                    )

            if matching_flows:
                return [
                    TextContent(
                        type="text",
                        text=f"Found {len(matching_flows)} flows with '{arguments['flow_name']}':\n\n"
                        + json.dumps(matching_flows, indent=2, ensure_ascii=False),
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text", text=f"No flows found with name '{arguments['flow_name']}'"
                    )
                ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error searching flows: {str(e)}")]
