import json
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ...client import HomeyAPIClient


class FlowManagementTools:
    def __init__(self, homey_client: HomeyAPIClient):
        self.homey_client = homey_client

    def get_tools(self) -> List[Tool]:
        """Return all flow management tools."""
        return [
            # ================== FLOW OPERATIONS ==================
            Tool(
                name="get_flows",
                description="Get all Homey flows. Can retrieve basic flows, advanced flows, or both.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_type": {"type": "string", "enum": ["basic", "advanced", "all"], "default": "all", "description": "Type of flows to retrieve"}
                    },
                    "required": []
                },
            ),
            Tool(
                name="get_flow",
                description="Get specific flow by ID. Works for both basic and advanced flows.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "The flow ID"},
                        "flow_type": {"type": "string", "enum": ["basic", "advanced", "auto"], "default": "auto", "description": "Type of flow (auto-detect if not specified)"}
                    },
                    "required": ["flow_id"],
                },
            ),
            Tool(
                name="trigger_flow",
                description="Trigger a Homey flow. Works for both basic and advanced flows.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "The ID of the flow to trigger"},
                        "flow_type": {"type": "string", "enum": ["basic", "advanced", "auto"], "default": "auto", "description": "Type of flow (auto-detect if not specified)"}
                    },
                    "required": ["flow_id"],
                },
            ),
            Tool(
                name="get_device_flow_capabilities",
                description="Get all available flow capabilities (triggers, conditions, actions) for devices to help build flows",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "Optional: Get capabilities for specific device"},
                        "capability_type": {"type": "string", "enum": ["trigger", "condition", "action", "all"], "default": "all", "description": "Type of capabilities to get"}
                    },
                    "required": []
                }
            ),

            # ================== FLOW FOLDER OPERATIONS ==================
            Tool(
                name="get_flow_folders",
                description="Get all flow folders for organization",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),

            # ================== FLOW CARD OPERATIONS ==================
            Tool(
                name="get_flow_cards",
                description="Get available flow cards (triggers, conditions, or actions) for building flows. Supports pagination and filtering to avoid token limits.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "card_type": {"type": "string", "enum": ["trigger", "condition", "action", "all"], "default": "all", "description": "Type of flow cards to retrieve"},
                        "limit": {"type": "integer", "description": "Maximum number of results to return (default: 50, max: 200)", "default": 50},
                        "offset": {"type": "integer", "description": "Number of results to skip (for pagination)", "default": 0},
                        "summary_mode": {"type": "boolean", "description": "Return only essential fields (id, uri, title) to save tokens", "default": False},
                        "filter_uri": {"type": "string", "description": "Filter by card id prefix/pattern (e.g., 'homey:device:', 'homey:manager:logic')"},
                        "search": {"type": "string", "description": "Case-insensitive text search on card id and title"}
                    },
                    "required": []
                },
            ),

            # ================== FLOW BUILDER HELPERS ==================
            Tool(name="create_advanced_flow", description="Create an advanced flow (validated, dry_run by default)",
                 inputSchema={"type": "object", "properties": {}, "required": ["name", "cards"]}),
            Tool(name="update_advanced_flow", description="Update an advanced flow (validated, dry_run by default)",
                 inputSchema={"type": "object", "properties": {}, "required": ["flow_id"]}),
            Tool(name="delete_advanced_flow", description="Delete an advanced flow after name confirmation",
                 inputSchema={"type": "object", "properties": {}, "required": ["flow_id", "confirm_name"]}),

            # ================== FLOW TESTING ==================
            Tool(
                name="run_flow_card_action",
                description="Test run a specific flow action",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "uri": {"type": "string", "description": "Action URI"},
                        "action_id": {"type": "string", "description": "Action ID"},
                        "args": {"type": "object", "description": "Action arguments (optional)"}
                    },
                    "required": ["uri", "action_id"],
                },
            ),
        ]

    # ================== UNIFIED FLOW HANDLERS ==================

    async def handle_get_flows(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Unified handler for get_flows tool - supports basic, advanced, or both."""
        try:
            flow_type = arguments.get("flow_type", "all")

            all_flows = []

            # Fetch basic flows if requested
            if flow_type in ["basic", "all"]:
                try:
                    basic_flows = await self.homey_client.get_flows()
                    for flow_id, flow in basic_flows.items():
                        flow_info = {
                            "id": flow_id,
                            "name": flow.get("name"),
                            "type": "basic",
                            "enabled": flow.get("enabled", True),
                            "broken": flow.get("broken", False),
                            "folder": flow.get("folder"),
                        }
                        all_flows.append(flow_info)
                except Exception as e:
                    if flow_type == "basic":
                        raise
                    # If fetching all, continue even if basic flows fail
                    pass

            # Fetch advanced flows if requested
            if flow_type in ["advanced", "all"]:
                try:
                    advanced_flows = await self.homey_client.get_advanced_flows()
                    for flow_id, flow in advanced_flows.items():
                        flow_info = {
                            "id": flow_id,
                            "name": flow.get("name"),
                            "type": "advanced",
                            "enabled": flow.get("enabled", True),
                            "broken": flow.get("broken", False),
                            "folder": flow.get("folder"),
                            "cards_count": len(flow.get("cards", {}))
                        }
                        all_flows.append(flow_info)
                except Exception as e:
                    if flow_type == "advanced":
                        raise
                    # If fetching all, continue even if advanced flows fail
                    pass

            flow_type_label = {"basic": "basic", "advanced": "advanced", "all": ""}[flow_type]
            type_text = f"{flow_type_label} " if flow_type_label else ""

            return [
                TextContent(
                    type="text",
                    text=f"Found {len(all_flows)} {type_text}flows:\n\n"
                    + json.dumps(all_flows, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flows: {str(e)}")]

    async def handle_get_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Unified handler for get_flow tool - supports basic, advanced, and auto-detection."""
        try:
            flow_id = arguments["flow_id"]
            flow_type = arguments.get("flow_type", "auto")

            flow = None
            actual_type = None

            if flow_type == "auto":
                # Try basic first, then advanced
                try:
                    flow = await self.homey_client.get_flow(flow_id)
                    actual_type = "basic"
                except:
                    try:
                        flow = await self.homey_client.get_advanced_flow(flow_id)
                        actual_type = "advanced"
                    except:
                        return [TextContent(type="text", text=f"❌ Flow {flow_id} not found in basic or advanced flows")]
            elif flow_type == "basic":
                flow = await self.homey_client.get_flow(flow_id)
                actual_type = "basic"
            elif flow_type == "advanced":
                flow = await self.homey_client.get_advanced_flow(flow_id)
                actual_type = "advanced"

            return [
                TextContent(
                    type="text",
                    text=f"{actual_type.title()} Flow '{flow.get('name')}':\n\n"
                    + json.dumps(flow, indent=2, ensure_ascii=False),
                )
            ]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flow: {str(e)}")]

    async def handle_trigger_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Unified handler for trigger_flow tool - supports basic, advanced, and auto-detection."""
        try:
            flow_id = arguments["flow_id"]
            flow_type = arguments.get("flow_type", "auto")

            flow_name = flow_id
            actual_type = None
            success = False

            if flow_type == "auto":
                # Try basic first, then advanced
                try:
                    flow = await self.homey_client.get_flow(flow_id)
                    flow_name = flow.get("name", flow_id)
                    success = await self.homey_client.trigger_flow(flow_id)
                    actual_type = "basic"
                except:
                    try:
                        flow = await self.homey_client.get_advanced_flow(flow_id)
                        flow_name = flow.get("name", flow_id)
                        success = await self.homey_client.trigger_advanced_flow(flow_id)
                        actual_type = "advanced"
                    except:
                        return [TextContent(type="text", text=f"❌ Flow {flow_id} not found in basic or advanced flows")]
            elif flow_type == "basic":
                try:
                    flow = await self.homey_client.get_flow(flow_id)
                    flow_name = flow.get("name", flow_id)
                except:
                    pass
                success = await self.homey_client.trigger_flow(flow_id)
                actual_type = "basic"
            elif flow_type == "advanced":
                try:
                    flow = await self.homey_client.get_advanced_flow(flow_id)
                    flow_name = flow.get("name", flow_id)
                except:
                    pass
                success = await self.homey_client.trigger_advanced_flow(flow_id)
                actual_type = "advanced"

            if success:
                return [TextContent(type="text", text=f"✅ {actual_type.title()} flow '{flow_name}' triggered successfully")]
            else:
                return [TextContent(type="text", text=f"❌ Could not trigger {actual_type} flow '{flow_name}'")]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error triggering flow: {str(e)}")]

    async def handle_get_device_flow_capabilities(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_device_flow_capabilities tool."""
        try:
            device_id = arguments.get("device_id")
            capability_type = arguments.get("capability_type", "all")

            response_text = f"🔍 **Loading Device Flow Capabilities**\n\n"

            # Load devices first
            devices = await self.homey_client.get_devices()
            response_text += f"✅ Loaded {len(devices)} devices\n"

            # Load flow capabilities
            all_capabilities = {}
            if capability_type in ["trigger", "all"]:
                triggers = await self.homey_client.get_flow_card_triggers()
                all_capabilities["triggers"] = triggers
                response_text += f"✅ Loaded {len(triggers)} triggers\n"

            if capability_type in ["condition", "all"]:
                conditions = await self.homey_client.get_flow_card_conditions()
                all_capabilities["conditions"] = conditions
                response_text += f"✅ Loaded {len(conditions)} conditions\n"

            if capability_type in ["action", "all"]:
                actions = await self.homey_client.get_flow_card_actions()
                all_capabilities["actions"] = actions
                response_text += f"✅ Loaded {len(actions)} actions\n"

            response_text += "\n"

            # Filter by specific device if requested
            if device_id:
                if device_id in devices:
                    device = devices[device_id]
                    device_name = device.get("name", device_id)
                    response_text += f"**Device: '{device_name}' ({device_id})**\n"
                    response_text += f"Class: {device.get('class', 'unknown')}\n"
                    response_text += f"Zone: {device.get('zoneName', 'unknown')}\n\n"

                    # Find capabilities for this device
                    device_capabilities = {"triggers": [], "conditions": [], "actions": []}

                    for cap_type, capabilities in all_capabilities.items():
                        for capability in capabilities:
                            uri = capability.get("uri", "")
                            if f"homey:device:{device_id}" in uri:
                                device_capabilities[cap_type].append(capability)

                    response_text += f"**Available capabilities for {device_name}:**\n"
                    for cap_type, caps in device_capabilities.items():
                        if caps:
                            response_text += f"\n**{cap_type.title()}:**\n"
                            for cap in caps:
                                response_text += f"• {cap.get('id', 'unknown')}: {cap.get('title', 'No title')}\n"

                else:
                    return [TextContent(type="text", text=f"❌ Device {device_id} not found")]

            else:
                # Show summary of all capabilities
                response_text += "**Summary of all flow capabilities:**\n\n"

                for cap_type, capabilities in all_capabilities.items():
                    response_text += f"**{cap_type.title()} ({len(capabilities)}):**\n"

                    # Group by URI prefix
                    device_caps = {}
                    manager_caps = {}
                    app_caps = {}

                    for cap in capabilities:
                        uri = cap.get("uri", "")
                        title = cap.get("title", "No title")
                        cap_id = cap.get("id", "unknown")

                        if "homey:device:" in uri:
                            device_id_from_uri = uri.split(":")[-1] if ":" in uri else "unknown"
                            device_name = devices.get(device_id_from_uri, {}).get("name", device_id_from_uri)
                            if device_name not in device_caps:
                                device_caps[device_name] = []
                            device_caps[device_name].append(f"{cap_id}: {title}")
                        elif "homey:manager:" in uri:
                            manager_type = uri.split(":")[-1] if ":" in uri else "unknown"
                            if manager_type not in manager_caps:
                                manager_caps[manager_type] = []
                            manager_caps[manager_type].append(f"{cap_id}: {title}")
                        elif "homey:app:" in uri:
                            app_name = uri.split(":")[-1] if ":" in uri else "unknown"
                            if app_name not in app_caps:
                                app_caps[app_name] = []
                            app_caps[app_name].append(f"{cap_id}: {title}")

                    # Show device capabilities
                    if device_caps:
                        response_text += f"  **Device {cap_type}:**\n"
                        for device_name, caps in list(device_caps.items())[:5]:  # Limit to 5 devices
                            response_text += f"    {device_name}: {len(caps)} capabilities\n"
                        if len(device_caps) > 5:
                            response_text += f"    ...and {len(device_caps) - 5} more devices\n"

                    # Show manager capabilities
                    if manager_caps:
                        response_text += f"  **Manager {cap_type}:**\n"
                        for manager, caps in manager_caps.items():
                            response_text += f"    {manager}: {len(caps)} capabilities\n"

                    # Show app capabilities
                    if app_caps:
                        response_text += f"  **App {cap_type}:**\n"
                        for app, caps in list(app_caps.items())[:3]:  # Limit to 3 apps
                            response_text += f"    {app}: {len(caps)} capabilities\n"

                    response_text += "\n"

                response_text += "💡 **Tip:** Use `device_id` parameter to see specific device capabilities\n"

            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error loading device capabilities: {str(e)}")]

    # ================== FLOW FOLDER HANDLERS ==================

    async def handle_get_flow_folders(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_flow_folders tool."""
        try:
            folders = await self.homey_client.get_flow_folders()

            folder_list = []
            for folder_id, folder in folders.items():
                folder_info = {
                    "id": folder_id,
                    "name": folder.get("name"),
                    "parent": folder.get("parent")
                }
                folder_list.append(folder_info)

            return [
                TextContent(
                    type="text",
                    text=f"Found {len(folder_list)} flow folders:\n\n"
                    + json.dumps(folder_list, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flow folders: {str(e)}")]

    # ================== FLOW CARD HANDLERS ==================

    async def handle_get_flow_cards(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Unified handler for getting flow cards (triggers, conditions, or actions)."""
        try:
            # Get parameters
            card_type = arguments.get("card_type", "all")
            limit = min(arguments.get("limit", 50), 200)  # Cap at 200 max
            offset = arguments.get("offset", 0)
            summary_mode = arguments.get("summary_mode", False)
            filter_uri = arguments.get("filter_uri")
            search = (arguments.get("search") or "").lower()

            # Determine which card types to fetch
            fetch_types = []
            if card_type == "all":
                fetch_types = ["trigger", "condition", "action"]
            else:
                fetch_types = [card_type]

            all_cards = []
            type_labels = {
                "trigger": "Triggers",
                "condition": "Conditions",
                "action": "Actions"
            }

            # Fetch requested card types
            for ftype in fetch_types:
                if ftype == "trigger":
                    cards = await self.homey_client.get_flow_card_triggers()
                    card_label = "trigger"
                elif ftype == "condition":
                    cards = await self.homey_client.get_flow_card_conditions()
                    card_label = "condition"
                elif ftype == "action":
                    cards = await self.homey_client.get_flow_card_actions()
                    card_label = "action"
                else:
                    continue

                # Add type label to each card for clarity when fetching all
                for card in cards:
                    card["_type"] = card_label
                    all_cards.append(card)

            # Apply URI filter if specified
            if filter_uri:
                all_cards = [c for c in all_cards if filter_uri in c.get("id", "")]
            if search:
                all_cards = [c for c in all_cards
                             if search in c.get("id", "").lower() or search in str(c.get("title", "")).lower()]

            total_count = len(all_cards)

            # Apply pagination
            all_cards = all_cards[offset:offset + limit]

            card_list = []

            # Format cards
            for card in all_cards:
                if summary_mode:
                    # Return only essential fields
                    card_info = {
                        "id": card.get("id", "unknown"),
                        "title": card.get("title"),
                        "type": card.get("_type")
                    }
                else:
                    # Return full information
                    card_info = {
                        "id": card.get("id", "unknown"),
                        "title": card.get("title"),
                        "type": card.get("_type"),
                        "titleFormatted": card.get("titleFormatted"),
                        "args": [{k: a.get(k) for k in ("name", "type", "required", "values") if a.get(k) is not None}
                                 for a in card.get("args") or []],
                        "tokens": [t.get("id") for t in card.get("tokens") or []]
                    }
                card_list.append(card_info)

            # Build response with pagination info
            type_display = type_labels.get(card_type, "All Flow Cards") if card_type != "all" else "All Flow Cards"
            response_text = f"📋 **{type_display}** (showing {len(card_list)} of {total_count})\n"
            if offset > 0:
                response_text += f"• Offset: {offset}\n"
            if offset + limit < total_count:
                response_text += f"• More available: Use offset={offset + limit} to see next page\n"
            if filter_uri:
                response_text += f"• Filtered by id: {filter_uri}\n"
            if search:
                response_text += f"• Search: {search}\n"
            response_text += "\n"

            response_text += json.dumps(card_list, indent=2, ensure_ascii=False)

            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flow cards: {str(e)}")]

    # ================== FLOW BUILDER HANDLERS ==================

    async def handle_create_advanced_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for create_advanced_flow tool."""
        try:
            flow = {k: arguments.get(k) for k in ("name", "enabled", "folder", "cards") if arguments.get(k) is not None}
            result = await self.homey_client.create_advanced_flow(flow, dry_run=arguments.get("dry_run", True))
            return [TextContent(type="text", text=self._format_write_result("created", result))]
        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creating advanced flow: {str(e)}")]

    async def handle_update_advanced_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for update_advanced_flow tool."""
        try:
            changes = {k: arguments.get(k) for k in ("name", "enabled", "folder", "cards")}
            result = await self.homey_client.update_advanced_flow(
                arguments["flow_id"], changes, dry_run=arguments.get("dry_run", True)
            )
            return [TextContent(type="text", text=self._format_write_result("updated", result))]
        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error updating advanced flow: {str(e)}")]

    async def handle_delete_advanced_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for delete_advanced_flow tool. Deletes only when confirm_name matches the flow's name."""
        try:
            flow_id = arguments["flow_id"]
            flow = await self.homey_client.get_advanced_flow(flow_id)
            if flow.get("name") != arguments.get("confirm_name"):
                return [TextContent(type="text", text=f"❌ Not deleted: confirm_name must be exactly '{flow.get('name')}'")]
            await self.homey_client.delete_advanced_flow(flow_id)
            return [TextContent(type="text", text=f"✅ Advanced flow '{flow.get('name')}' deleted")]
        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error deleting advanced flow: {str(e)}")]

    @staticmethod
    def _format_write_result(verb: str, result: Dict[str, Any]) -> str:
        if result.get("dry_run"):
            return ("🧪 Dry run OK, nothing sent to Homey. Call again with dry_run=false to apply.\n\n"
                    + json.dumps(result["payload"], indent=2, ensure_ascii=False))
        status = "⚠️ BROKEN" if result.get("broken") else "OK"
        return (f"✅ Advanced flow '{result.get('name')}' {verb} (id: {result.get('id')}, "
                f"enabled: {result.get('enabled')}, status: {status})")



    # ================== FLOW TESTING HANDLERS ==================

    async def handle_run_flow_card_action(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for run_flow_card_action tool."""
        try:
            uri = arguments["uri"]
            action_id = arguments["action_id"]
            args = arguments.get("args", {})

            result = await self.homey_client.run_flow_card_action(uri, action_id, args)
            
            response_text = f"🧪 **Flow Action Test Results**\n\n"
            response_text += f"• Action: {uri}:{action_id}\n"
            response_text += f"• Success: {'✅' if result.get('success') else '❌'}\n"
            
            if "duration" in result:
                response_text += f"• Duration: {result['duration']:.2f}s\n"
            
            if "result" in result:
                response_text += f"• Result: {result['result']}\n"

            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error running flow action: {str(e)}")]
