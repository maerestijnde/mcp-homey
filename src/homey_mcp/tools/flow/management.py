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
            # ================== BASIC FLOW OPERATIONS ==================
            Tool(
                name="get_flows",
                description="Get all Homey flows (automation)",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="get_flow",
                description="Get specific flow by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "The flow ID"}
                    },
                    "required": ["flow_id"],
                },
            ),
            Tool(
                name="trigger_flow",
                description="Start a specific Homey flow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "The ID of the flow to start"}
                    },
                    "required": ["flow_id"],
                },
            ),
            Tool(
                name="create_flow",
                description="Create a new flow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Flow name"},
                        "trigger": {"type": "object", "description": "Flow trigger configuration"},
                        "actions": {"type": "array", "items": {"type": "object"}, "description": "Flow actions"},
                        "conditions": {"type": "array", "items": {"type": "object"}, "description": "Flow conditions (optional)"},
                        "folder": {"type": "string", "description": "Flow folder ID (optional)"},
                        "enabled": {"type": "boolean", "default": True, "description": "Enable flow"}
                    },
                    "required": ["name", "trigger", "actions"],
                },
            ),
            Tool(
                name="update_flow",
                description="Update flow properties (enable/disable, rename, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "The flow ID"},
                        "enabled": {"type": "boolean", "description": "Enable/disable flow"},
                        "name": {"type": "string", "description": "New flow name"},
                        "folder": {"type": "string", "description": "New folder ID"},
                    },
                    "required": ["flow_id"],
                },
            ),
            Tool(
                name="delete_flow",
                description="Delete a flow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "The flow ID"}
                    },
                    "required": ["flow_id"],
                },
            ),
            Tool(
                name="test_flow",
                description="Test a flow before saving/triggering",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_data": {"type": "object", "description": "Flow configuration to test"},
                        "tokens": {"type": "object", "description": "Test tokens (optional)"}
                    },
                    "required": ["flow_data"],
                },
            ),

            # ================== ADVANCED FLOW OPERATIONS ==================
            Tool(
                name="get_advanced_flows",
                description="Get all advanced flows (complex automations)",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="get_advanced_flow",
                description="Get specific advanced flow by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "The advanced flow ID"}
                    },
                    "required": ["flow_id"],
                },
            ),
            Tool(
                name="trigger_advanced_flow",
                description="Trigger an advanced flow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "The advanced flow ID"}
                    },
                    "required": ["flow_id"],
                },
            ),
            Tool(
                name="create_advanced_flow",
                description="Create a new advanced flow with proper card structure including positions and connections. Supports all card types: trigger, condition, action, delay (wait), any (OR gate), all (AND gate), note (documentation). Advanced features: inverted conditions, outputError for error handling, input arrays for ALL cards.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Flow name"},
                        "cards": {
                            "oneOf": [
                                {
                                    "type": "object",
                                    "description": "Flow cards as object with unique IDs as keys"
                                },
                                {
                                    "type": "array",
                                    "description": "Flow cards as array (will be converted to object automatically)",
                                    "items": {"type": "object"}
                                }
                            ],
                            "description": "Flow cards. Can be either an object with card IDs as keys, or an array of cards (which will be automatically converted). Each card must have: type, and for non-builtin cards: id, ownerUri. Position (x, y) will be auto-generated if missing.",
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "ownerUri": {"type": "string", "description": "Owner URI (e.g., homey:device:uuid) - not required for delay cards"},
                                    "id": {"type": "string", "description": "Card capability ID - not required for delay cards"},
                                    "type": {"type": "string", "enum": ["trigger", "condition", "action", "delay", "any", "all", "note", "start"], "description": "Card type"},
                                    "x": {"type": "number", "description": "X coordinate in flow editor"},
                                    "y": {"type": "number", "description": "Y coordinate in flow editor"},
                                    "args": {"type": "object", "description": "Card arguments/parameters"},
                                    "outputSuccess": {"type": "array", "items": {"type": "string"}, "description": "Card IDs to connect on success"},
                                    "outputTrue": {"type": "array", "items": {"type": "string"}, "description": "Card IDs to connect on true condition"},
                                    "outputFalse": {"type": "array", "items": {"type": "string"}, "description": "Card IDs to connect on false condition"},
                                    "outputError": {"type": "array", "items": {"type": "string"}, "description": "Card IDs to connect on error"},
                                    "droptoken": {"type": "string", "description": "Droptoken for conditions"},
                                    "inverted": {"type": "boolean", "description": "Invert condition logic (NOT)"},
                                    "input": {"type": "array", "items": {"type": "string"}, "description": "Input card references for ALL cards (format: card-id::outputType)"},
                                    "value": {"type": "string", "description": "Text content for NOTE cards"},
                                    "color": {"type": "string", "description": "Color for NOTE cards"},
                                    "width": {"type": "number", "description": "Width for NOTE cards"},
                                    "height": {"type": "number", "description": "Height for NOTE cards"}
                                },
                                "required": ["type", "x", "y"]
                            }
                        },
                        "enabled": {"type": "boolean", "default": True, "description": "Enable flow"},
                        "folder": {"type": "string", "description": "Flow folder ID (optional)"},
                        "triggerable": {"type": "boolean", "default": False, "description": "Whether flow can be triggered manually"},
                        "broken": {"type": "boolean", "default": False, "description": "Whether flow is broken"}
                    },
                    "required": ["name", "cards"],
                },
            ),
            Tool(
                name="create_advanced_flow_with_validation",
                description="Create advanced flow with full device capability validation. First loads all available triggers, conditions and actions from devices to ensure flow is valid before creation.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Flow name"},
                        "cards": {
                            "type": "object",
                            "description": "Flow cards - will be validated against actual device capabilities"
                        },
                        "enabled": {"type": "boolean", "default": True, "description": "Enable flow"},
                        "folder": {"type": "string", "description": "Flow folder ID (optional)"},
                        "triggerable": {"type": "boolean", "default": False, "description": "Whether flow can be triggered manually"},
                        "validate_devices": {"type": "boolean", "default": True, "description": "Validate device capabilities before creation"},
                        "auto_fix_positions": {"type": "boolean", "default": True, "description": "Automatically fix card positioning"}
                    },
                    "required": ["name", "cards"]
                }
            ),
            Tool(
                name="update_advanced_flow",
                description="Update an existing advanced flow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "The advanced flow ID to update"},
                        "name": {"type": "string", "description": "New flow name"},
                        "enabled": {"type": "boolean", "description": "Enable/disable flow"},
                        "folder": {"type": "string", "description": "Flow folder ID"},
                        "cards": {"type": "object", "description": "Updated flow cards configuration"},
                        "triggerable": {"type": "boolean", "description": "Whether flow can be triggered manually"}
                    },
                    "required": ["flow_id"]
                }
            ),
            Tool(
                name="delete_advanced_flow",
                description="Delete an advanced flow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "The advanced flow ID to delete"}
                    },
                    "required": ["flow_id"]
                }
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
            Tool(
                name="get_flow_folder",
                description="Get a specific flow folder by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "The folder ID"}
                    },
                    "required": ["folder_id"]
                }
            ),
            Tool(
                name="create_flow_folder",
                description="Create a new flow folder for organization",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Folder name"},
                        "parent": {"type": "string", "description": "Parent folder ID (optional)"}
                    },
                    "required": ["name"],
                },
            ),

            # ================== FLOW CARD OPERATIONS ==================
            Tool(
                name="get_flow_card_triggers",
                description="Get available flow triggers for building flows",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="get_flow_card_conditions",
                description="Get available flow conditions for building flows",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="get_flow_card_actions",
                description="Get available flow actions for building flows",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),

            # ================== FLOW BUILDER HELPERS ==================

            # ================== FLOW STATE & TESTING ==================
            Tool(
                name="get_flow_state",
                description="Get overall flow manager statistics",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
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

    # ================== BASIC FLOW HANDLERS ==================

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
                    "folder": flow.get("folder"),
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

    async def handle_get_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_flow tool."""
        try:
            flow_id = arguments["flow_id"]
            flow = await self.homey_client.get_flow(flow_id)

            return [
                TextContent(
                    type="text",
                    text=f"Flow '{flow.get('name')}':\n\n"
                    + json.dumps(flow, indent=2, ensure_ascii=False),
                )
            ]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flow: {str(e)}")]

    async def handle_trigger_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for trigger_flow tool."""
        try:
            flow_id = arguments["flow_id"]

            # Get flow info for name
            try:
                flow = await self.homey_client.get_flow(flow_id)
                flow_name = flow.get("name", flow_id)
            except:
                flow_name = flow_id

            # Trigger the flow
            success = await self.homey_client.trigger_flow(flow_id)

            if success:
                return [TextContent(type="text", text=f"✅ Flow '{flow_name}' started successfully")]
            else:
                return [TextContent(type="text", text=f"❌ Could not start flow '{flow_name}'")]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error starting flow: {str(e)}")]

    async def handle_create_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for create_flow tool."""
        try:
            flow_data = {
                "name": arguments["name"],
                "trigger": arguments["trigger"],
                "actions": arguments["actions"],
                "conditions": arguments.get("conditions", []),
                "folder": arguments.get("folder"),
                "enabled": arguments.get("enabled", True)
            }

            new_flow = await self.homey_client.create_flow(flow_data)
            
            return [TextContent(
                type="text", 
                text=f"✅ Flow '{new_flow.get('name')}' created successfully (ID: {new_flow.get('id')})"
            )]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creating flow: {str(e)}")]

    async def handle_update_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for update_flow tool."""
        try:
            flow_id = arguments["flow_id"]
            
            # Extract update parameters
            update_params = {}
            if "enabled" in arguments:
                update_params["enabled"] = arguments["enabled"]
            if "name" in arguments:
                update_params["name"] = arguments["name"]
            if "folder" in arguments:
                update_params["folder"] = arguments["folder"]

            updated_flow = await self.homey_client.update_flow(flow_id, **update_params)
            
            return [TextContent(
                type="text",
                text=f"✅ Flow '{updated_flow.get('name')}' updated successfully"
            )]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error updating flow: {str(e)}")]

    async def handle_delete_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for delete_flow tool."""
        try:
            flow_id = arguments["flow_id"]
            
            # Get flow name before deletion
            try:
                flow = await self.homey_client.get_flow(flow_id)
                flow_name = flow.get("name", flow_id)
            except:
                flow_name = flow_id

            success = await self.homey_client.delete_flow(flow_id)
            
            if success:
                return [TextContent(type="text", text=f"✅ Flow '{flow_name}' deleted successfully")]
            else:
                return [TextContent(type="text", text=f"❌ Could not delete flow '{flow_name}'")]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error deleting flow: {str(e)}")]

    async def handle_test_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for test_flow tool."""
        try:
            flow_data = arguments["flow_data"]
            tokens = arguments.get("tokens", {})

            result = await self.homey_client.test_flow(flow_data, tokens)
            
            response_text = f"🧪 **Flow Test Results**\n\n"
            response_text += f"• Success: {'✅' if result.get('success') else '❌'}\n"
            
            if "duration" in result:
                response_text += f"• Duration: {result['duration']:.2f}s\n"
            
            if result.get("results"):
                response_text += f"• Results: {', '.join(result['results'])}\n"
            
            if result.get("errors"):
                response_text += f"• Errors: {', '.join(result['errors'])}\n"
            
            if result.get("warnings"):
                response_text += f"• Warnings: {', '.join(result['warnings'])}\n"

            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error testing flow: {str(e)}")]


    # ================== ADVANCED FLOW HANDLERS ==================

    async def handle_get_advanced_flows(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_advanced_flows tool."""
        try:
            flows = await self.homey_client.get_advanced_flows()

            flow_list = []
            for flow_id, flow in flows.items():
                flow_info = {
                    "id": flow_id,
                    "name": flow.get("name"),
                    "enabled": flow.get("enabled", True),
                    "broken": flow.get("broken", False),
                    "folder": flow.get("folder"),
                    "cards_count": len(flow.get("cards", {}))
                }
                flow_list.append(flow_info)

            return [
                TextContent(
                    type="text",
                    text=f"Found {len(flow_list)} advanced flows:\n\n"
                    + json.dumps(flow_list, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting advanced flows: {str(e)}")]

    async def handle_get_advanced_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_advanced_flow tool."""
        try:
            flow_id = arguments["flow_id"]
            flow = await self.homey_client.get_advanced_flow(flow_id)

            return [
                TextContent(
                    type="text",
                    text=f"Advanced Flow '{flow.get('name')}':\n\n"
                    + json.dumps(flow, indent=2, ensure_ascii=False),
                )
            ]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting advanced flow: {str(e)}")]

    async def handle_trigger_advanced_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for trigger_advanced_flow tool."""
        try:
            flow_id = arguments["flow_id"]

            # Get flow info for name
            try:
                flow = await self.homey_client.get_advanced_flow(flow_id)
                flow_name = flow.get("name", flow_id)
            except:
                flow_name = flow_id

            success = await self.homey_client.trigger_advanced_flow(flow_id)
            
            if success:
                return [TextContent(type="text", text=f"✅ Advanced flow '{flow_name}' triggered successfully")]
            else:
                return [TextContent(type="text", text=f"❌ Could not trigger advanced flow '{flow_name}'")]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error triggering advanced flow: {str(e)}")]

    async def handle_create_advanced_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for create_advanced_flow tool."""
        try:
            flow_data = {
                "name": arguments["name"],
                "cards": arguments["cards"],  # Now expects object structure
                "enabled": arguments.get("enabled", True),
                "folder": arguments.get("folder"),
                "triggerable": arguments.get("triggerable", False),
                "broken": arguments.get("broken", False)
            }

            new_flow = await self.homey_client.create_advanced_flow(flow_data)

            card_count = len(flow_data["cards"]) if isinstance(flow_data["cards"], dict) else 0

            return [TextContent(
                type="text",
                text=f"✅ Advanced flow '{new_flow.get('name')}' created successfully (ID: {new_flow.get('id')}) with {card_count} cards"
            )]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creating advanced flow: {str(e)}")]

    async def handle_create_advanced_flow_with_validation(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for create_advanced_flow_with_validation tool."""
        try:
            name = arguments["name"]
            cards = arguments["cards"]
            enabled = arguments.get("enabled", True)
            folder = arguments.get("folder")
            triggerable = arguments.get("triggerable", False)
            validate_devices = arguments.get("validate_devices", True)
            auto_fix_positions = arguments.get("auto_fix_positions", True)

            response_text = f"🔄 **Creating Advanced Flow: '{name}'**\n\n"

            # Step 1: Pre-load all device capabilities if validation enabled
            if validate_devices:
                response_text += "**Step 1: Loading device capabilities...**\n"
                try:
                    # Load all devices first
                    devices = await self.homey_client.get_devices()
                    response_text += f"✅ Loaded {len(devices)} devices\n"

                    # Load all available flow cards
                    triggers = await self.homey_client.get_flow_card_triggers()
                    conditions = await self.homey_client.get_flow_card_conditions()
                    actions = await self.homey_client.get_flow_card_actions()

                    response_text += f"✅ Loaded {len(triggers)} triggers\n"
                    response_text += f"✅ Loaded {len(conditions)} conditions\n"
                    response_text += f"✅ Loaded {len(actions)} actions\n\n"

                except Exception as e:
                    return [TextContent(type="text", text=f"❌ Error loading capabilities: {str(e)}")]

            # Step 2: Validate each card against available capabilities
            if validate_devices:
                response_text += "**Step 2: Validating flow cards...**\n"
                validation_errors = []
                validation_warnings = []

                for card_id, card in cards.items():
                    card_type = card.get("type", "unknown")
                    owner_uri = card.get("ownerUri", "")
                    capability_id = card.get("id", "")

                    # Skip builtin cards
                    if card_type in ["delay", "any", "all", "note"]:
                        response_text += f"✅ {card_id}: Builtin card '{card_type}'\n"
                        continue

                    # Check if device exists
                    if owner_uri.startswith("homey:device:"):
                        device_id = owner_uri.split(":")[-1]
                        if device_id not in devices:
                            validation_errors.append(f"Device {device_id} not found for card {card_id}")
                            continue

                        device_name = devices[device_id].get("name", device_id)
                        response_text += f"✅ {card_id}: Device '{device_name}' found\n"

                    # Validate capability exists
                    capability_found = False
                    if card_type == "trigger":
                        capability_found = any(t.get("id") == capability_id for t in triggers)
                    elif card_type == "condition":
                        capability_found = any(c.get("id") == capability_id for c in conditions)
                    elif card_type == "action":
                        capability_found = any(a.get("id") == capability_id for a in actions)

                    if not capability_found:
                        validation_warnings.append(f"Capability '{capability_id}' not found in available {card_type}s for card {card_id}")

                if validation_errors:
                    response_text += f"\n❌ **Validation Errors:**\n"
                    for error in validation_errors:
                        response_text += f"• {error}\n"
                    return [TextContent(type="text", text=response_text)]

                if validation_warnings:
                    response_text += f"\n⚠️ **Validation Warnings:**\n"
                    for warning in validation_warnings:
                        response_text += f"• {warning}\n"

                response_text += "\n"

            # Step 3: Auto-fix positions if enabled
            if auto_fix_positions:
                response_text += "**Step 3: Optimizing card positions...**\n"
                cards = self._optimize_card_positions(cards)
                response_text += "✅ Card positions optimized\n\n"

            # Step 4: Create the flow
            response_text += "**Step 4: Creating advanced flow...**\n"
            flow_data = {
                "name": name,
                "cards": cards,
                "enabled": enabled,
                "folder": folder,
                "triggerable": triggerable
            }

            new_flow = await self.homey_client.create_advanced_flow(flow_data)
            card_count = len(cards) if isinstance(cards, dict) else 0

            response_text += f"✅ **Advanced flow '{new_flow.get('name')}' created successfully!**\n"
            response_text += f"• Flow ID: {new_flow.get('id')}\n"
            response_text += f"• Cards: {card_count}\n"
            response_text += f"• Enabled: {'Yes' if enabled else 'No'}\n"

            return [TextContent(type="text", text=response_text)]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creating validated advanced flow: {str(e)}")]

    async def handle_update_advanced_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for update_advanced_flow tool."""
        try:
            flow_id = arguments["flow_id"]

            # Build update data from provided arguments
            update_data = {}
            if "name" in arguments:
                update_data["name"] = arguments["name"]
            if "enabled" in arguments:
                update_data["enabled"] = arguments["enabled"]
            if "folder" in arguments:
                update_data["folder"] = arguments["folder"]
            if "cards" in arguments:
                update_data["cards"] = arguments["cards"]
            if "triggerable" in arguments:
                update_data["triggerable"] = arguments["triggerable"]

            updated_flow = await self.homey_client.update_advanced_flow(flow_id, update_data)

            return [TextContent(
                type="text",
                text=f"✅ Advanced flow '{updated_flow.get('name')}' updated successfully"
            )]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error updating advanced flow: {str(e)}")]

    async def handle_delete_advanced_flow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for delete_advanced_flow tool."""
        try:
            flow_id = arguments["flow_id"]

            # Get flow name before deletion
            try:
                flow = await self.homey_client.get_advanced_flow(flow_id)
                flow_name = flow.get("name", flow_id)
            except:
                flow_name = flow_id

            success = await self.homey_client.delete_advanced_flow(flow_id)

            if success:
                return [TextContent(type="text", text=f"✅ Advanced flow '{flow_name}' deleted successfully")]
            else:
                return [TextContent(type="text", text=f"❌ Could not delete advanced flow '{flow_name}'")]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error deleting advanced flow: {str(e)}")]

    def _optimize_card_positions(self, cards: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize card positions for better flow layout."""
        optimized_cards = cards.copy()

        # Simple optimization: organize by type
        triggers = []
        conditions = []
        actions = []
        others = []

        for card_id, card in cards.items():
            card_type = card.get("type", "action")
            if card_type == "trigger":
                triggers.append((card_id, card))
            elif card_type == "condition":
                conditions.append((card_id, card))
            elif card_type == "action":
                actions.append((card_id, card))
            else:
                others.append((card_id, card))

        # Layout: triggers left, conditions center, actions right
        y_offset = 40
        spacing = 100

        # Position triggers
        for i, (card_id, card) in enumerate(triggers):
            optimized_cards[card_id]["x"] = 50
            optimized_cards[card_id]["y"] = y_offset + (i * spacing)

        # Position conditions
        for i, (card_id, card) in enumerate(conditions):
            optimized_cards[card_id]["x"] = 400
            optimized_cards[card_id]["y"] = y_offset + (i * spacing)

        # Position actions
        for i, (card_id, card) in enumerate(actions):
            optimized_cards[card_id]["x"] = 800
            optimized_cards[card_id]["y"] = y_offset + (i * spacing)

        # Position others
        for i, (card_id, card) in enumerate(others):
            optimized_cards[card_id]["x"] = 600
            optimized_cards[card_id]["y"] = y_offset + (i * spacing)

        return optimized_cards

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

    async def handle_get_flow_folder(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_flow_folder tool."""
        try:
            folder_id = arguments["folder_id"]
            folder = await self.homey_client.get_flow_folder(folder_id)

            return [
                TextContent(
                    type="text",
                    text=f"Flow folder '{folder.get('name')}':\n\n"
                    + json.dumps(folder, indent=2, ensure_ascii=False),
                )
            ]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flow folder: {str(e)}")]

    async def handle_create_flow_folder(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for create_flow_folder tool."""
        try:
            name = arguments["name"]
            parent = arguments.get("parent")

            new_folder = await self.homey_client.create_flow_folder(name, parent)
            
            return [TextContent(
                type="text", 
                text=f"✅ Flow folder '{new_folder.get('name')}' created successfully (ID: {new_folder.get('id')})"
            )]

        except ValueError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creating flow folder: {str(e)}")]

    # ================== FLOW CARD HANDLERS ==================

    async def handle_get_flow_card_triggers(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_flow_card_triggers tool."""
        try:
            triggers = await self.homey_client.get_flow_card_triggers()

            trigger_list = []

            # API returns a list of triggers
            for trigger in triggers:
                trigger_info = {
                    "id": trigger.get("id", "unknown"),
                    "uri": trigger.get("uri"),
                    "title": trigger.get("title"),
                    "titleFormatted": trigger.get("titleFormatted"),
                    "args": trigger.get("args", [])
                }
                trigger_list.append(trigger_info)

            return [
                TextContent(
                    type="text",
                    text=f"Found {len(trigger_list)} flow triggers:\n\n"
                    + json.dumps(trigger_list, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flow triggers: {str(e)}")]

    async def handle_get_flow_card_conditions(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_flow_card_conditions tool."""
        try:
            conditions = await self.homey_client.get_flow_card_conditions()

            condition_list = []

            # API returns a list of conditions
            for condition in conditions:
                condition_info = {
                    "id": condition.get("id", "unknown"),
                    "uri": condition.get("uri"),
                    "title": condition.get("title"),
                    "titleFormatted": condition.get("titleFormatted"),
                    "args": condition.get("args", [])
                }
                condition_list.append(condition_info)

            return [
                TextContent(
                    type="text",
                    text=f"Found {len(condition_list)} flow conditions:\n\n"
                    + json.dumps(condition_list, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flow conditions: {str(e)}")]

    async def handle_get_flow_card_actions(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_flow_card_actions tool."""
        try:
            actions = await self.homey_client.get_flow_card_actions()

            action_list = []

            # API returns a list of actions
            for action in actions:
                action_info = {
                    "id": action.get("id", "unknown"),
                    "uri": action.get("uri"),
                    "title": action.get("title"),
                    "titleFormatted": action.get("titleFormatted"),
                    "args": action.get("args", [])
                }
                action_list.append(action_info)

            return [
                TextContent(
                    type="text",
                    text=f"Found {len(action_list)} flow actions:\n\n"
                    + json.dumps(action_list, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flow actions: {str(e)}")]

    # ================== FLOW BUILDER HANDLERS ==================




    # ================== FLOW STATE HANDLERS ==================

    async def handle_get_flow_state(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handler for get_flow_state tool."""
        try:
            state = await self.homey_client.get_flow_state()

            response_text = f"🔄 **Flow Manager State**\n\n"
            response_text += f"• Status: {'✅ Enabled' if state.get('enabled') else '❌ Disabled'}\n"
            
            if "version" in state:
                response_text += f"• Version: {state['version']}\n"
            
            if "total_flows" in state:
                response_text += f"• Total Flows: {state['total_flows']}\n"
            
            if "enabled_flows" in state:
                response_text += f"• Enabled Flows: {state['enabled_flows']}\n"
            
            if "broken_flows" in state:
                response_text += f"• Broken Flows: {state['broken_flows']}\n"
            
            if "regular_flows" in state:
                response_text += f"• Regular Flows: {state['regular_flows']}\n"
            
            if "advanced_flows" in state:
                response_text += f"• Advanced Flows: {state['advanced_flows']}\n"

            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error getting flow state: {str(e)}")]

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
