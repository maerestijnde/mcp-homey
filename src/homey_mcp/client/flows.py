import logging
import time
import uuid
from typing import Any, Dict, Optional, List, Union
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

WRITABLE_FLOW_FIELDS = ("name", "enabled", "folder", "cards")
CATALOG_CARD_TYPES = ("trigger", "condition", "action")
BUILTIN_CARD_TYPES = ("start", "delay", "all", "any", "note")
OUTPUT_FIELDS = ("outputSuccess", "outputTrue", "outputFalse", "outputError")


def _is_uuid(value: Any) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def validate_advanced_flow(flow: Dict[str, Any], catalog: Dict[str, Dict[str, Any]]) -> List[str]:
    """Return every problem that would make Homey store a broken or empty advanced flow.

    The API accepts almost anything with 200, so this is the only guard.
    """
    errors = []
    name = flow.get("name")
    if not isinstance(name, str) or not name.strip() or name.strip().strip('"') == "null":
        errors.append("name must be a non-empty string")

    cards = flow.get("cards")
    if not isinstance(cards, dict) or not cards:
        return errors + ["cards must be a non-empty object keyed by card UUID"]

    for key, card in cards.items():
        where = f"card {key}"
        if not _is_uuid(key):
            errors.append(f"{where}: key must be a UUID")
        if not isinstance(card, dict):
            errors.append(f"{where}: must be an object")
            continue

        ctype = card.get("type")
        if ctype not in CATALOG_CARD_TYPES + BUILTIN_CARD_TYPES:
            errors.append(f"{where}: unknown type {ctype!r}")
            continue
        if not all(isinstance(card.get(axis), (int, float)) for axis in ("x", "y")):
            errors.append(f"{where}: x and y must be numbers")

        if ctype in CATALOG_CARD_TYPES:
            known = catalog.get(card.get("id"))
            if known is None:
                errors.append(f"{where}: no {ctype} card with id {card.get('id')!r} (use the full id from get_flow_cards)")
            elif known["_kind"] != ctype:
                errors.append(f"{where}: {card['id']!r} is a {known['_kind']} card, not a {ctype}")
            else:
                args = card.get("args") or {}
                for arg in known.get("args") or []:
                    if arg.get("required", True) is not False and arg["name"] not in args:
                        errors.append(f"{where}: missing required arg {arg['name']!r} ({arg.get('type')})")
        elif ctype == "delay":
            delay = (card.get("args") or {}).get("delay") or {}
            if "number" not in delay or delay.get("multiplier") not in (1, 60):
                errors.append(f"{where}: delay needs args.delay = {{number, multiplier: 1|60}}")
        elif ctype == "note" and not isinstance(card.get("value"), str):
            errors.append(f"{where}: note needs a string value")

        for field in OUTPUT_FIELDS:
            for target in card.get(field) or []:
                if target not in cards:
                    errors.append(f"{where}: {field} points to unknown card {target}")
        for source in card.get("input") or []:
            source_key, _, output = str(source).partition("::")
            if source_key not in cards or output not in OUTPUT_FIELDS:
                errors.append(f"{where}: input {source!r} must be '<card UUID>::<output field>' of an existing card")

    if not any(isinstance(c, dict) and c.get("type") in ("trigger", "start") for c in cards.values()):
        errors.append("flow needs at least one trigger or start card")
    return errors


class FlowAPI:
    def __init__(self, client):
        self.client = client
        self._catalog: Dict[str, Dict[str, Any]] = {}
        self._catalog_at = 0.0

    # ================== REGULAR FLOWS ==================
    
    async def get_flows(self) -> Dict[str, Any]:
        """Get all regular flows."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            demo_flows = {
                "flow1": {
                    "id": "flow1",
                    "name": "Good Morning Routine",
                    "enabled": True,
                    "broken": False,
                    "folder": "routines",
                    "trigger": {
                        "id": "time_schedule", 
                        "uri": "homey:app:com.athom.scheduler",
                        "args": {"time": "07:00"}
                    },
                    "conditions": [],
                    "actions": [
                        {"id": "turn_on_lights", "uri": "homey:device:light1"},
                        {"id": "set_thermostat", "uri": "homey:device:thermostat1"}
                    ]
                },
                "flow2": {
                    "id": "flow2", 
                    "name": "Evening Routine",
                    "enabled": True, 
                    "broken": False,
                    "folder": "routines",
                    "trigger": {
                        "id": "sunset", 
                        "uri": "homey:app:com.athom.sun"
                    },
                    "conditions": [
                        {"id": "presence", "uri": "homey:app:com.athom.presence"}
                    ],
                    "actions": [
                        {"id": "dim_lights", "uri": "homey:device:light1"}
                    ]
                },
                "flow3": {
                    "id": "flow3",
                    "name": "Security Check", 
                    "enabled": False,  # Disabled flow
                    "broken": True,   # Broken flow
                    "folder": "security",
                    "trigger": {
                        "id": "motion", 
                        "uri": "homey:device:sensor1"
                    },
                    "conditions": [],
                    "actions": [
                        {"id": "send_notification", "uri": "homey:app:com.athom.notifications"}
                    ]
                },
                "flow4": {
                    "id": "flow4",
                    "name": "Bedtime Lights",
                    "enabled": True,
                    "broken": False,
                    "folder": "routines",
                    "trigger": {
                        "id": "time_schedule",
                        "uri": "homey:app:com.athom.scheduler", 
                        "args": {"time": "22:00"}
                    },
                    "conditions": [],
                    "actions": [
                        {"id": "turn_off_lights", "uri": "homey:device:light1"},
                        {"id": "turn_off_lights", "uri": "homey:device:light2"}
                    ]
                }
            }
            logger.info(f"Demo mode: {len(demo_flows)} demo flows")
            return demo_flows

        try:
            # CORRECT: No trailing slash needed for GET
            response = await self.client.session.get("/api/manager/flow/flow")
            response.raise_for_status()
            flows_data = response.json()

            # CRITICAL: Apply bulletproof null filtering to ALL returned flows
            # This prevents "null is not an object (evaluating 'v.name.toLowerCase')" crashes
            if isinstance(flows_data, dict):
                cleaned_flows = {}
                for flow_id, flow_data in flows_data.items():
                    if flow_data is None:
                        continue

                    # Apply ultra-defensive cleaning to each flow
                    cleaned_flow = self._ultra_clean_for_api(flow_data)
                    if cleaned_flow:  # Only add if we got valid data back
                        cleaned_flows[flow_id] = cleaned_flow

                logger.info(f"Cleaned {len(cleaned_flows)} regular flows from API response")
                return cleaned_flows

            return flows_data
        except Exception as e:
            logger.error(f"Error getting flows: {e}")
            raise

    async def get_flow(self, flow_id: str) -> Dict[str, Any]:
        """Get specific flow by ID."""
        if not flow_id or not isinstance(flow_id, str) or not flow_id.strip():
            raise ValueError("Flow ID must be a non-empty string")

        flow_id = flow_id.strip()
        if self.client.config.offline_mode or self.client.config.demo_mode:
            flows = await self.get_flows()
            if flow_id not in flows:
                raise ValueError(f"Flow {flow_id} not found")
            return flows[flow_id]

        try:
            response = await self.client.session.get(f"/api/manager/flow/flow/{flow_id}")
            response.raise_for_status()
            flow_data = response.json()

            # CRITICAL: Apply bulletproof null filtering to prevent UI crashes
            cleaned_flow = self._ultra_clean_for_api(flow_data)
            logger.info(f"Cleaned single flow {flow_id} from API response")
            return cleaned_flow

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Flow {flow_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error getting flow {flow_id}: {e}")
            raise

    async def trigger_flow(self, flow_id: str) -> bool:
        """Trigger a regular flow."""
        if not flow_id or not isinstance(flow_id, str) or not flow_id.strip():
            raise ValueError("Flow ID must be a non-empty string")

        flow_id = flow_id.strip()
        if self.client.config.offline_mode or self.client.config.demo_mode:
            logger.info(f"Demo mode: Flow {flow_id} would be triggered")
            return True

        try:
            # CORRECT endpoint according to API docs
            response = await self.client.session.post(f"/api/manager/flow/flow/{flow_id}/trigger")
            response.raise_for_status()
            logger.info(f"✅ Flow {flow_id} triggered successfully")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Flow {flow_id} not found")
            elif e.response.status_code == 422:
                raise ValueError(f"Flow {flow_id} cannot be triggered (may be disabled or broken)")
            raise
        except Exception as e:
            logger.error(f"Error triggering flow {flow_id}: {e}")
            raise

    # ================== ADVANCED FLOWS ==================

    async def get_advanced_flows(self) -> Dict[str, Any]:
        """Get all advanced flows."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            return {
                "advanced1": {
                    "id": "advanced1",
                    "name": "Smart Home Orchestration",
                    "enabled": True,
                    "broken": False,
                    "folder": "advanced",
                    "cards": {
                        "trigger_1": {
                            "type": "trigger",
                            "id": "multiple_sensors",
                            "ownerUri": "homey:app:com.athom.logic",
                            "x": 50,
                            "y": 100,
                            "outputSuccess": ["condition_1"]
                        },
                        "condition_1": {
                            "type": "condition",
                            "id": "time_range",
                            "ownerUri": "homey:app:com.athom.time",
                            "x": 300,
                            "y": 100,
                            "outputTrue": ["action_1"],
                            "outputFalse": []
                        },
                        "action_1": {
                            "type": "action",
                            "id": "scene_control",
                            "ownerUri": "homey:app:com.athom.scenes",
                            "x": 550,
                            "y": 100
                        }
                    }
                },
                "advanced2": {
                    "id": "advanced2",
                    "name": "Climate Control Logic",
                    "enabled": True,
                    "broken": False,
                    "folder": "climate",
                    "cards": {
                        "trigger_2": {
                            "type": "trigger",
                            "id": "temp_change",
                            "ownerUri": "homey:device:sensor1",
                            "x": 50,
                            "y": 100,
                            "outputSuccess": ["condition_2"]
                        },
                        "condition_2": {
                            "type": "condition",
                            "id": "presence_check",
                            "ownerUri": "homey:app:com.athom.presence",
                            "x": 300,
                            "y": 100,
                            "outputTrue": ["action_2"],
                            "outputFalse": []
                        },
                        "action_2": {
                            "type": "action",
                            "id": "adjust_thermostat",
                            "ownerUri": "homey:device:thermostat1",
                            "x": 550,
                            "y": 100
                        }
                    }
                }
            }

        try:
            response = await self.client.session.get("/api/manager/flow/advancedflow")
            response.raise_for_status()
            flows_data = response.json()

            return {fid: f for fid, f in flows_data.items() if f is not None}
        except Exception as e:
            logger.error(f"Error getting advanced flows: {e}")
            raise

    async def get_advanced_flow(self, flow_id: str) -> Dict[str, Any]:
        """Get specific advanced flow."""
        if not flow_id or not isinstance(flow_id, str) or not flow_id.strip():
            raise ValueError("Advanced flow ID must be a non-empty string")

        flow_id = flow_id.strip()
        if self.client.config.offline_mode or self.client.config.demo_mode:
            flows = await self.get_advanced_flows()
            if flow_id not in flows:
                raise ValueError(f"Advanced flow {flow_id} not found")
            return flows[flow_id]

        try:
            response = await self.client.session.get(f"/api/manager/flow/advancedflow/{flow_id}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Advanced flow {flow_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error getting advanced flow {flow_id}: {e}")
            raise

    async def trigger_advanced_flow(self, flow_id: str) -> bool:
        """Trigger an advanced flow."""
        if not flow_id or not isinstance(flow_id, str) or not flow_id.strip():
            raise ValueError("Advanced flow ID must be a non-empty string")

        flow_id = flow_id.strip()
        if self.client.config.offline_mode or self.client.config.demo_mode:
            logger.info(f"Demo mode: Advanced flow {flow_id} would be triggered")
            return True

        try:
            response = await self.client.session.post(f"/api/manager/flow/advancedflow/{flow_id}/trigger")
            response.raise_for_status()
            logger.info(f"✅ Advanced flow {flow_id} triggered")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Advanced flow {flow_id} not found")
            elif e.response.status_code == 422:
                raise ValueError(f"Advanced flow {flow_id} cannot be triggered (may be disabled or broken)")
            raise
        except Exception as e:
            logger.error(f"Error triggering advanced flow {flow_id}: {e}")
            raise

    async def get_card_catalog(self) -> Dict[str, Dict[str, Any]]:
        """All flow cards by full id, each tagged with its kind (trigger/condition/action)."""
        if self._catalog and time.monotonic() - self._catalog_at < self.client.config.cache_ttl:
            return self._catalog
        catalog = {}
        for kind, fetch in (("trigger", self.get_flow_card_triggers),
                            ("condition", self.get_flow_card_conditions),
                            ("action", self.get_flow_card_actions)):
            cards = await fetch()
            for card in cards.values() if isinstance(cards, dict) else cards:
                catalog[card["id"]] = {**card, "_kind": kind}
        self._catalog, self._catalog_at = catalog, time.monotonic()
        return catalog

    async def create_advanced_flow(self, flow_data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Validate and create an advanced flow. The flow object itself is the request body."""
        self._refuse_in_demo()
        flow = {k: v for k, v in flow_data.items() if k in WRITABLE_FLOW_FIELDS}
        flow.setdefault("enabled", False)
        self._raise_if_invalid(flow, await self.get_card_catalog())
        if dry_run:
            return {"dry_run": True, "payload": flow}

        response = await self.client.session.post("/api/manager/flow/advancedflow", json=flow)
        self._raise_for_flow_error(response)
        return response.json()

    async def update_advanced_flow(self, flow_id: str, changes: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Merge top-level changes (name/enabled/folder/cards) into the current flow and PUT the whole flow."""
        self._refuse_in_demo()
        current = await self.get_advanced_flow(flow_id)
        flow = {k: v for k, v in current.items() if k in WRITABLE_FLOW_FIELDS}
        flow.update({k: v for k, v in changes.items() if k in WRITABLE_FLOW_FIELDS and v is not None})
        self._raise_if_invalid(flow, await self.get_card_catalog())
        if dry_run:
            return {"dry_run": True, "payload": flow}

        response = await self.client.session.put(f"/api/manager/flow/advancedflow/{flow_id}", json=flow)
        self._raise_for_flow_error(response)
        return response.json()

    async def delete_advanced_flow(self, flow_id: str) -> bool:
        """Delete an advanced flow."""
        self._refuse_in_demo()
        response = await self.client.session.delete(f"/api/manager/flow/advancedflow/{flow_id}")
        if response.status_code == 404:
            raise ValueError(f"Advanced flow {flow_id} not found")
        response.raise_for_status()
        return True

    def _refuse_in_demo(self) -> None:
        # a fake success here would hide that nothing reached the Homey
        if self.client.config.offline_mode or self.client.config.demo_mode:
            raise ValueError("Flow writes are disabled in demo/offline mode (Homey not connected?)")

    @staticmethod
    def _raise_if_invalid(flow: Dict[str, Any], catalog: Dict[str, Dict[str, Any]]) -> None:
        errors = validate_advanced_flow(flow, catalog)
        if errors:
            raise ValueError("Invalid advanced flow:\n- " + "\n- ".join(errors))

    @staticmethod
    def _raise_for_flow_error(response: httpx.Response) -> None:
        if response.status_code in (400, 404, 422):
            raise ValueError(f"Homey rejected the flow ({response.status_code}): {response.text}")
        response.raise_for_status()

    # ================== FLOW FOLDERS ==================

    async def get_flow_folders(self) -> Dict[str, Any]:
        """Get all flow folders for organization."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            return {
                "routines": {
                    "id": "routines",
                    "name": "Daily Routines", 
                    "parent": None
                },
                "security": {
                    "id": "security",
                    "name": "Security & Safety",
                    "parent": None
                },
                "climate": {
                    "id": "climate", 
                    "name": "Climate Control",
                    "parent": None
                },
                "advanced": {
                    "id": "advanced",
                    "name": "Advanced Automations",
                    "parent": None
                }
            }

        try:
            response = await self.client.session.get("/api/manager/flow/flowfolder")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting flow folders: {e}")
            raise

    async def get_flow_folder(self, folder_id: str) -> Dict[str, Any]:
        """Get specific flow folder."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            folders = await self.get_flow_folders()
            if folder_id not in folders:
                raise ValueError(f"Flow folder {folder_id} not found")
            return folders[folder_id]

        try:
            response = await self.client.session.get(f"/api/manager/flow/flowfolder/{folder_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Flow folder {folder_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error getting flow folder {folder_id}: {e}")
            raise

    # ================== FLOW CARDS ==================

    async def get_flow_card_triggers(self) -> List[Dict[str, Any]]:
        """Get all available flow card triggers."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            return [
                {
                    "id": "time_schedule",
                    "uri": "homey:app:com.athom.scheduler",
                    "title": "Time Schedule",
                    "titleFormatted": "When the time is {{time}}",
                    "args": [{"name": "time", "type": "time", "required": True}]
                },
                {
                    "id": "device_turned_on",
                    "uri": "homey:manager:device",
                    "title": "Device turned on",
                    "titleFormatted": "When {{device}} is turned on",
                    "args": [{"name": "device", "type": "device", "required": True}]
                },
                {
                    "id": "sunset",
                    "uri": "homey:app:com.athom.sun",
                    "title": "Sunset",
                    "titleFormatted": "When the sun sets",
                    "args": []
                },
                {
                    "id": "motion_detected",
                    "uri": "homey:device:sensor",
                    "title": "Motion detected",
                    "titleFormatted": "When {{device}} detects motion",
                    "args": [{"name": "device", "type": "device", "filter": "class=sensor"}]
                }
            ]

        try:
            response = await self.client.session.get("/api/manager/flow/flowcardtrigger")
            response.raise_for_status()
            # API returns a list of flow card triggers
            return response.json()
        except Exception as e:
            logger.error(f"Error getting flow triggers: {e}")
            raise

    async def get_flow_card_conditions(self) -> List[Dict[str, Any]]:
        """Get all available flow card conditions."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            return [
                {
                    "id": "time_between",
                    "uri": "homey:app:com.athom.time",
                    "title": "Time is between",
                    "titleFormatted": "Time is between {{from}} and {{to}}",
                    "args": [
                        {"name": "from", "type": "time", "required": True},
                        {"name": "to", "type": "time", "required": True}
                    ]
                },
                {
                    "id": "device_is_on",
                    "uri": "homey:manager:device",
                    "title": "Device is on",
                    "titleFormatted": "{{device}} is turned on",
                    "args": [{"name": "device", "type": "device", "required": True}]
                },
                {
                    "id": "presence_home",
                    "uri": "homey:app:com.athom.presence",
                    "title": "Someone is home",
                    "titleFormatted": "Someone is home",
                    "args": []
                }
            ]

        try:
            response = await self.client.session.get("/api/manager/flow/flowcardcondition")
            response.raise_for_status()
            # API returns a list of flow card conditions
            return response.json()
        except Exception as e:
            logger.error(f"Error getting flow conditions: {e}")
            raise

    async def get_flow_card_actions(self) -> List[Dict[str, Any]]:
        """Get all available flow card actions."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            return [
                {
                    "id": "turn_on_device",
                    "uri": "homey:manager:device",
                    "title": "Turn device on",
                    "titleFormatted": "Turn {{device}} on",
                    "args": [{"name": "device", "type": "device", "required": True}]
                },
                {
                    "id": "turn_off_device",
                    "uri": "homey:manager:device",
                    "title": "Turn device off",
                    "titleFormatted": "Turn {{device}} off",
                    "args": [{"name": "device", "type": "device", "required": True}]
                },
                {
                    "id": "send_notification",
                    "uri": "homey:app:com.athom.notifications",
                    "title": "Send notification",
                    "titleFormatted": "Send notification: {{message}}",
                    "args": [{"name": "message", "type": "text", "required": True}]
                },
                {
                    "id": "set_thermostat",
                    "uri": "homey:device:thermostat",
                    "title": "Set thermostat temperature",
                    "titleFormatted": "Set {{device}} to {{temperature}}°C",
                    "args": [
                        {"name": "device", "type": "device", "filter": "class=thermostat", "required": True},
                        {"name": "temperature", "type": "number", "min": 5, "max": 35, "required": True}
                    ]
                }
            ]

        try:
            response = await self.client.session.get("/api/manager/flow/flowcardaction")
            response.raise_for_status()
            # API returns a list of flow card actions
            return response.json()
        except Exception as e:
            logger.error(f"Error getting flow actions: {e}")
            raise

    # ================== SANITIZATION METHODS ==================

    def _ultra_clean_for_api(self, data: Any) -> Any:
        """Bulletproof null filtering - multiple layers of protection against UI crashes."""
        def is_valid_value(value):
            """Check if value is valid for API (not null, undefined, or empty string)."""
            if value is None:
                return False
            if isinstance(value, str) and not value.strip():
                return False
            if isinstance(value, (dict, list)) and not value:
                return False
            return True

        def clean_recursively(obj):
            """Recursively clean object with aggressive filtering."""
            if isinstance(obj, dict):
                cleaned = {}
                for key, value in obj.items():
                    # Skip keys that are None or empty
                    if not key or key is None:
                        continue

                    # Clean the value recursively
                    cleaned_value = clean_recursively(value)

                    # Only keep valid values
                    if is_valid_value(cleaned_value):
                        cleaned[key] = cleaned_value

                return cleaned if cleaned else {}

            elif isinstance(obj, list):
                cleaned = []
                for item in obj:
                    cleaned_item = clean_recursively(item)
                    if is_valid_value(cleaned_item):
                        cleaned.append(cleaned_item)
                return cleaned

            else:
                # Primitive values - return if valid, otherwise None
                return obj if is_valid_value(obj) else None

        # Start cleaning process
        result = clean_recursively(data)

        # Final safety check - ensure critical fields exist with fallbacks
        if isinstance(result, dict):
            # Ensure name exists and is non-empty
            if not result.get('name'):
                result['name'] = 'Unnamed Flow'

            # Ensure cards exist and is an object
            if 'cards' not in result or not isinstance(result['cards'], dict):
                result['cards'] = {}

            # Clean each card thoroughly
            cleaned_cards = {}
            for card_id, card_data in result.get('cards', {}).items():
                if not card_id or not isinstance(card_data, dict):
                    continue

                # Ensure required card fields
                cleaned_card = {
                    'type': card_data.get('type', 'action'),
                    'id': card_data.get('id', 'unknown'),
                    'ownerUri': card_data.get('ownerUri', 'homey:app:unknown')
                }

                # Add optional fields only if they have valid values
                for field in ['x', 'y', 'outputSuccess', 'outputTrue', 'outputFalse']:
                    if field in card_data and is_valid_value(card_data[field]):
                        cleaned_card[field] = card_data[field]

                cleaned_cards[card_id] = cleaned_card

            result['cards'] = cleaned_cards

        return result

    # ================== UTILITY METHODS ==================

    async def get_flow_state(self) -> Dict[str, Any]:
        """Get overall flow manager state."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            flows = await self.get_flows()
            advanced_flows = await self.get_advanced_flows()
            
            total_flows = len(flows) + len(advanced_flows)
            enabled_flows = sum(1 for f in flows.values() if f.get("enabled", True)) + \
                        sum(1 for f in advanced_flows.values() if f.get("enabled", True))
            broken_flows = sum(1 for f in flows.values() if f.get("broken", False)) + \
                        sum(1 for f in advanced_flows.values() if f.get("broken", False))
            
            return {
                "enabled": True,
                "version": "3.0.0",
                "total_flows": total_flows,
                "enabled_flows": enabled_flows, 
                "broken_flows": broken_flows,
                "regular_flows": len(flows),
                "advanced_flows": len(advanced_flows)
            }

        try:
            response = await self.client.session.get("/api/manager/flow/state")
            response.raise_for_status()
            # API should return flow manager state
            return response.json()
        except Exception as e:
            logger.error(f"Error getting flow state: {e}")
            raise

    async def run_flow_card_action(self, uri: str, action_id: str, args: Dict[str, Any] = None,
                                tokens: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a specific flow card action for testing."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            logger.info(f"Demo mode: Action {uri}:{action_id} would be executed with args {args}")
            return {
                "success": True,
                "result": "Action executed successfully in demo mode",
                "duration": 0.5
            }

        try:
            payload = {
                "args": args or {},
                "tokens": tokens or {},
                "state": {},
                "droptoken": None
            }

            # Fix endpoint format - encode URI properly
            import urllib.parse
            encoded_uri = urllib.parse.quote(uri, safe='')
            endpoint = f"/api/manager/flow/flowcardaction/{encoded_uri}/{action_id}/run"
            response = await self.client.session.post(endpoint, json=payload)
            response.raise_for_status()
            logger.info(f"✅ Flow action {uri}:{action_id} executed")
            return response.json()

        except Exception as e:
            logger.error(f"Error running flow action {uri}:{action_id}: {e}")
            raise
