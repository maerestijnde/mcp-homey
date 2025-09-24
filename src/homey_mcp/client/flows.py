import logging
from typing import Any, Dict, Optional, List, Union
from datetime import datetime
import uuid
import re

import httpx

logger = logging.getLogger(__name__)


class FlowAPI:
    def __init__(self, client):
        self.client = client

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

    async def create_flow(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new flow."""
        # Validate and sanitize flow_data to prevent corruption
        sanitized_data = await self._sanitize_flow_data(flow_data)

        if self.client.config.offline_mode or self.client.config.demo_mode:
            new_flow = {
                "id": str(uuid.uuid4()),
                "name": sanitized_data["name"],
                "enabled": sanitized_data["enabled"],
                "broken": False,
                "folder": sanitized_data.get("folder"),
                "trigger": sanitized_data["trigger"],
                "conditions": sanitized_data["conditions"],
                "actions": sanitized_data["actions"]
            }
            logger.info(f"Demo mode: Flow '{new_flow['name']}' would be created")
            return new_flow

        try:
            payload = {"flow": sanitized_data}
            response = await self.client.session.post("/api/manager/flow/flow", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise ValueError(f"Invalid flow data: {e.response.text}")
            elif e.response.status_code == 422:
                raise ValueError(f"Flow validation failed: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error creating flow: {e}")
            raise

    async def update_flow(self, flow_id: str, enabled: Optional[bool] = None,
                        name: Optional[str] = None, folder: Optional[str] = None,
                        trigger: Optional[Dict] = None, conditions: Optional[List] = None,
                        actions: Optional[List] = None) -> Dict[str, Any]:
        """Update flow properties."""
        if not flow_id or not isinstance(flow_id, str) or not flow_id.strip():
            raise ValueError("Flow ID must be a non-empty string")

        if self.client.config.offline_mode or self.client.config.demo_mode:
            logger.info(f"Demo mode: Flow {flow_id} would be updated")
            flows = await self.get_flows()
            if flow_id in flows:
                flow = flows[flow_id].copy()
                if enabled is not None:
                    flow["enabled"] = bool(enabled)
                if name is not None and isinstance(name, str) and name.strip():
                    flow["name"] = name.strip()
                if folder is not None and isinstance(folder, str) and folder.strip():
                    flow["folder"] = folder.strip()
                if trigger is not None:
                    flow["trigger"] = self._sanitize_dict(trigger)
                if conditions is not None:
                    flow["conditions"] = [self._sanitize_dict(c) for c in conditions if isinstance(c, dict)]
                if actions is not None:
                    flow["actions"] = [self._sanitize_dict(a) for a in actions if isinstance(a, dict)]
                return flow
            raise ValueError(f"Flow {flow_id} not found")

        try:
            # Build update payload - only include non-null values
            payload = {}
            if enabled is not None:
                payload["enabled"] = bool(enabled)
            if name is not None and isinstance(name, str) and name.strip():
                payload["name"] = name.strip()
            if folder is not None and isinstance(folder, str) and folder.strip():
                payload["folder"] = folder.strip()
            if trigger is not None and isinstance(trigger, dict):
                payload["trigger"] = self._sanitize_dict(trigger)
            if conditions is not None and isinstance(conditions, list):
                payload["conditions"] = [self._sanitize_dict(c) for c in conditions if isinstance(c, dict)]
            if actions is not None and isinstance(actions, list):
                payload["actions"] = [self._sanitize_dict(a) for a in actions if isinstance(a, dict)]

            if not payload:
                raise ValueError("At least one valid field must be specified for update")

            response = await self.client.session.put(f"/api/manager/flow/flow/{flow_id}",json={"flow": payload})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Flow {flow_id} not found")
            elif e.response.status_code == 400:
                raise ValueError(f"Invalid flow update data: {e.response.text}")
            elif e.response.status_code == 422:
                raise ValueError(f"Flow update validation failed: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error updating flow {flow_id}: {e}")
            raise

    async def delete_flow(self, flow_id: str) -> bool:
        """Delete a flow."""
        if not flow_id or not isinstance(flow_id, str) or not flow_id.strip():
            raise ValueError("Flow ID must be a non-empty string")

        flow_id = flow_id.strip()
        if self.client.config.offline_mode or self.client.config.demo_mode:
            logger.info(f"Demo mode: Flow {flow_id} would be deleted")
            return True

        try:
            response = await self.client.session.delete(f"/api/manager/flow/flow/{flow_id}")
            response.raise_for_status()
            logger.info(f"✅ Flow {flow_id} deleted")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Flow {flow_id} not found")
            elif e.response.status_code == 409:
                raise ValueError(f"Flow {flow_id} cannot be deleted (may be in use)")
            raise
        except Exception as e:
            logger.error(f"Error deleting flow {flow_id}: {e}")
            raise

    async def test_flow(self, flow_data: Dict[str, Any], tokens: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test a flow before saving/triggering."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            logger.info("Demo mode: Flow test would be executed")
            return {
                "success": True,
                "results": ["All conditions passed", "All actions executed successfully"],
                "duration": 1.23,
                "errors": [],
                "warnings": []
            }

        try:
            # According to API documentation, test endpoint expects flow data directly
            payload = {
                "flow": flow_data,
                "tokens": tokens or {}
            }

            response = await self.client.session.post("/api/manager/flow/flow/test", json=payload)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error testing flow: {e}")
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

                logger.info(f"Cleaned {len(cleaned_flows)} advanced flows from API response")
                return cleaned_flows

            return flows_data
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
            flow_data = response.json()

            # CRITICAL: Apply bulletproof null filtering to prevent UI crashes
            cleaned_flow = self._ultra_clean_for_api(flow_data)
            logger.info(f"Cleaned single advanced flow {flow_id} from API response")
            return cleaned_flow

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

    async def create_advanced_flow(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new advanced flow."""
        # Handle array to object conversion for cards if needed
        flow_data = self._convert_cards_array_to_object(flow_data)

        # Debug: log the flow data before sanitization
        logger.info(f"Creating advanced flow with data: {flow_data}")

        # Validate and sanitize flow_data to prevent corruption
        sanitized_data = await self._sanitize_advanced_flow_data(flow_data)

        # Debug: log the sanitized data
        logger.info(f"Sanitized flow data: {sanitized_data}")

        if self.client.config.offline_mode or self.client.config.demo_mode:
            new_flow = {
                "id": str(uuid.uuid4()),
                "name": sanitized_data["name"],
                "enabled": sanitized_data["enabled"],
                "broken": False,
                "folder": sanitized_data.get("folder"),
                "cards": sanitized_data["cards"]
            }
            logger.info(f"Demo mode: Advanced flow '{new_flow['name']}' would be created")
            return new_flow

        try:
            # BULLETPROOF null filtering - multiple layers of protection
            clean_data = self._ultra_clean_for_api(sanitized_data)
            final_payload = {"advancedflow": clean_data}

            # Log the cleaned payload for debugging
            logger.info(f"Sending ultra-clean API payload: {final_payload}")

            response = await self.client.session.post("/api/manager/flow/advancedflow", json=final_payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise ValueError(f"Invalid advanced flow data: {e.response.text}")
            elif e.response.status_code == 422:
                raise ValueError(f"Advanced flow validation failed: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error creating advanced flow: {e}")
            raise

    async def update_advanced_flow(self, flow_id: str, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an advanced flow."""
        if not flow_id or not isinstance(flow_id, str) or not flow_id.strip():
            raise ValueError("Advanced flow ID must be a non-empty string")

        # Sanitize the update data
        sanitized_data = self._sanitize_dict(flow_data)
        if not sanitized_data:
            raise ValueError("Update data must contain valid fields")

        if self.client.config.offline_mode or self.client.config.demo_mode:
            logger.info(f"Demo mode: Advanced flow {flow_id} would be updated")
            flows = await self.get_advanced_flows()
            if flow_id in flows:
                flow = flows[flow_id].copy()
                flow.update(sanitized_data)
                return flow
            raise ValueError(f"Advanced flow {flow_id} not found")

        try:
            payload = {"advancedflow": sanitized_data}
            response = await self.client.session.put(f"/api/manager/flow/advancedflow/{flow_id}",
            json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Advanced flow {flow_id} not found")
            elif e.response.status_code == 400:
                raise ValueError(f"Invalid advanced flow update data: {e.response.text}")
            elif e.response.status_code == 422:
                raise ValueError(f"Advanced flow update validation failed: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error updating advanced flow {flow_id}: {e}")
            raise

    async def delete_advanced_flow(self, flow_id: str) -> bool:
        """Delete an advanced flow."""
        if not flow_id or not isinstance(flow_id, str) or not flow_id.strip():
            raise ValueError("Advanced flow ID must be a non-empty string")

        flow_id = flow_id.strip()
        if self.client.config.offline_mode or self.client.config.demo_mode:
            logger.info(f"Demo mode: Advanced flow {flow_id} would be deleted")
            return True

        try:
            response = await self.client.session.delete(f"/api/manager/flow/advancedflow/{flow_id}")
            response.raise_for_status()
            logger.info(f"✅ Advanced flow {flow_id} deleted")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Advanced flow {flow_id} not found")
            elif e.response.status_code == 409:
                raise ValueError(f"Advanced flow {flow_id} cannot be deleted (may be in use)")
            raise
        except Exception as e:
            logger.error(f"Error deleting advanced flow {flow_id}: {e}")
            raise

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

    async def create_flow_folder(self, name: str, parent: Optional[str] = None) -> Dict[str, Any]:
        """Create a new flow folder."""
        # Sanitize folder data to prevent null values
        sanitized_data = self._sanitize_folder_data(name, parent)

        if self.client.config.offline_mode or self.client.config.demo_mode:
            new_folder = {
                "id": str(uuid.uuid4()),
                "name": sanitized_data["name"],
                "parent": sanitized_data.get("parent")
            }
            logger.info(f"Demo mode: Flow folder '{sanitized_data['name']}' would be created")
            return new_folder

        try:
            # According to API documentation - only send non-null values
            payload = {"flowfolder": sanitized_data}

            response = await self.client.session.post("/api/manager/flow/flowfolder", json=payload)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise ValueError(f"Invalid folder data: {e.response.text}")
            elif e.response.status_code == 409:
                raise ValueError(f"Folder with name '{sanitized_data['name']}' already exists")
            raise
        except Exception as e:
            logger.error(f"Error creating flow folder: {e}")
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

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove null values and sanitize dictionary data."""
        if not isinstance(data, dict):
            return {}

        sanitized = {}
        for key, value in data.items():
            if value is None:
                continue  # Skip null values completely
            elif isinstance(value, str):
                if value.strip():  # Only include non-empty strings
                    sanitized[key] = value.strip()
            elif isinstance(value, dict):
                sanitized_sub = self._sanitize_dict(value)
                if sanitized_sub:  # Only include non-empty dicts
                    sanitized[key] = sanitized_sub
            elif isinstance(value, list):
                sanitized_list = []
                for item in value:
                    if item is not None:
                        if isinstance(item, dict):
                            sanitized_item = self._sanitize_dict(item)
                            if sanitized_item:
                                sanitized_list.append(sanitized_item)
                        elif isinstance(item, str) and item.strip():
                            sanitized_list.append(item.strip())
                        elif not isinstance(item, str):
                            sanitized_list.append(item)
                if sanitized_list:  # Only include non-empty lists
                    sanitized[key] = sanitized_list
            else:
                sanitized[key] = value  # Include other types as-is (booleans, numbers, etc.)

        return sanitized

    async def _sanitize_flow_data(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and validate flow data to prevent corruption issues and null values."""
        if not flow_data or not isinstance(flow_data, dict):
            raise ValueError("Flow data must be a valid dictionary")

        sanitized = {}

        # Ensure name is a non-empty string (main cause of localeCompare error)
        name = flow_data.get("name")
        if not isinstance(name, str) or not name or not name.strip():
            sanitized["name"] = f"Flow {str(uuid.uuid4())[:8]}"
            logger.warning(f"Fixed invalid flow name: {name} -> {sanitized['name']}")
        else:
            sanitized["name"] = name.strip()

        # Ensure enabled is boolean (never null)
        enabled = flow_data.get("enabled")
        sanitized["enabled"] = bool(enabled) if enabled is not None else True

        # Validate and sanitize trigger (required)
        trigger = flow_data.get("trigger")
        if not isinstance(trigger, dict) or not trigger:
            raise ValueError("Flow trigger must be a valid dictionary")
        sanitized["trigger"] = await self._validate_trigger(trigger)

        # Validate and sanitize actions (required)
        actions = flow_data.get("actions")
        if not isinstance(actions, list) or not actions:
            raise ValueError("Flow must have at least one action")

        sanitized_actions = []
        for action in actions:
            if isinstance(action, dict):
                sanitized_actions.append(await self._validate_action(action))

        if not sanitized_actions:
            raise ValueError("Flow must have at least one valid action")
        sanitized["actions"] = sanitized_actions

        # Validate and sanitize conditions (optional)
        conditions = flow_data.get("conditions", [])
        sanitized_conditions = []
        if isinstance(conditions, list):
            for condition in conditions:
                if isinstance(condition, dict):
                    sanitized_conditions.append(await self._validate_condition(condition))
        sanitized["conditions"] = sanitized_conditions

        # Optional fields (only include if not null)
        folder = flow_data.get("folder")
        if folder is not None and isinstance(folder, str) and folder.strip():
            sanitized["folder"] = folder.strip()

        return sanitized

    async def _sanitize_advanced_flow_data(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and validate advanced flow data to prevent corruption issues and null values."""
        if not flow_data or not isinstance(flow_data, dict):
            raise ValueError("Advanced flow data must be a valid dictionary")

        sanitized = {}

        # Ensure name is a non-empty string (main cause of localeCompare error)
        name = flow_data.get("name")
        logger.info(f"Processing flow name: {repr(name)} (type: {type(name)})")

        if name is None or not isinstance(name, str) or not name or not name.strip():
            sanitized["name"] = f"Advanced Flow {str(uuid.uuid4())[:8]}"
            logger.warning(f"Fixed invalid advanced flow name: {repr(name)} -> {sanitized['name']}")
        else:
            sanitized["name"] = name.strip()
            logger.info(f"Using valid flow name: {sanitized['name']}")

        # Ensure enabled is boolean (never null)
        enabled = flow_data.get("enabled")
        sanitized["enabled"] = bool(enabled) if enabled is not None else True

        # Optional boolean fields
        triggerable = flow_data.get("triggerable")
        if triggerable is not None:
            sanitized["triggerable"] = bool(triggerable)

        broken = flow_data.get("broken")
        if broken is not None:
            sanitized["broken"] = bool(broken)

        # Validate and sanitize cards - now expecting object structure
        cards = flow_data.get("cards")
        if not isinstance(cards, dict) or not cards:
            raise ValueError("Advanced flow must have at least one card as object with card IDs as keys")

        sanitized_cards = {}
        for card_id, card in cards.items():
            if isinstance(card, dict):
                # Validate required fields for advanced flow cards
                validated_card = self._validate_advanced_flow_card(card)
                sanitized_cards[card_id] = validated_card

        if not sanitized_cards:
            raise ValueError("Advanced flow must have at least one valid card")

        sanitized["cards"] = sanitized_cards

        # Optional fields (only include if not null)
        folder = flow_data.get("folder")
        if folder is not None and isinstance(folder, str) and folder.strip():
            sanitized["folder"] = folder.strip()

        return sanitized

    def _sanitize_folder_data(self, name: str, parent: Optional[str] = None) -> Dict[str, Any]:
        """Sanitize folder creation data."""
        if not isinstance(name, str) or not name or not name.strip():
            raise ValueError("Folder name must be a non-empty string")

        sanitized = {
            "name": name.strip()
        }

        # Only include parent if it's a valid non-empty string
        if parent is not None and isinstance(parent, str) and parent.strip():
            sanitized["parent"] = parent.strip()

        return sanitized

    # ================== FLOW CARD VALIDATION ==================

    async def _get_available_cards(self) -> Dict[str, Dict[str, Any]]:
        """Get all available flow cards for validation."""
        if not hasattr(self, '_cached_cards') or self._cached_cards is None:
            try:
                triggers = await self.get_flow_card_triggers()
                conditions = await self.get_flow_card_conditions()
                actions = await self.get_flow_card_actions()

                self._cached_cards = {
                    'triggers': {card.get('id', card.get('uri', f'trigger_{i}')): card for i, card in enumerate(triggers)},
                    'conditions': {card.get('id', card.get('uri', f'condition_{i}')): card for i, card in enumerate(conditions)},
                    'actions': {card.get('id', card.get('uri', f'action_{i}')): card for i, card in enumerate(actions)}
                }
            except Exception as e:
                logger.warning(f"Could not load available flow cards: {e}")
                self._cached_cards = {'triggers': {}, 'conditions': {}, 'actions': {}}

        return self._cached_cards

    async def _validate_flow_card(self, card: Dict[str, Any], card_type: str) -> Dict[str, Any]:
        """Validate a flow card against available cards."""
        if not isinstance(card, dict):
            raise ValueError(f"Flow {card_type} must be a dictionary")

        available_cards = await self._get_available_cards()
        available_type_cards = available_cards.get(f"{card_type}s", {})

        # Get card identifier (id or uri)
        card_id = card.get('id')
        card_uri = card.get('uri')

        if not card_id and not card_uri:
            raise ValueError(f"Flow {card_type} must have either 'id' or 'uri' field")

        # Find matching available card
        matching_card = None
        if card_id and card_id in available_type_cards:
            matching_card = available_type_cards[card_id]
        elif card_uri and card_uri in available_type_cards:
            matching_card = available_type_cards[card_uri]

        # If not found in available cards, still allow but warn
        if not matching_card:
            logger.warning(f"Unknown {card_type} card: {card_id or card_uri}. This may cause flow issues.")
            return self._sanitize_dict(card)

        # Validate card structure based on available card
        validated_card = {
            'id': card_id or matching_card.get('id', 'unknown'),
            'uri': card_uri or matching_card.get('uri', '')
        }

        # Copy other properties, ensuring no nulls
        for key, value in card.items():
            if key not in ['id', 'uri'] and value is not None:
                validated_card[key] = value

        return validated_card

    async def _validate_trigger(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a flow trigger."""
        return await self._validate_flow_card(trigger, 'trigger')

    async def _validate_condition(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a flow condition."""
        return await self._validate_flow_card(condition, 'condition')

    async def _validate_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a flow action."""
        return await self._validate_flow_card(action, 'action')

    def _validate_advanced_flow_card(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an advanced flow card with position and connection data."""
        if not isinstance(card, dict):
            raise ValueError("Advanced flow card must be a dictionary")

        validated_card = {}

        # Always required fields
        required_fields = ["type", "x", "y"]
        for field in required_fields:
            if field not in card:
                raise ValueError(f"Advanced flow card missing required field: {field}")
            validated_card[field] = card[field]

        # Validate type
        card_type = card["type"]
        if card_type not in ["trigger", "condition", "action", "delay", "any", "all", "note", "start"]:
            raise ValueError(f"Invalid card type: {card_type}")

        # Validate coordinates
        for coord in ["x", "y"]:
            if not isinstance(card[coord], (int, float)):
                raise ValueError(f"Card coordinate {coord} must be a number")

        # ownerUri and id requirements by card type
        builtin_cards = ["delay", "any", "all", "note", "start"]

        if card_type not in builtin_cards:
            # Device/app cards require ownerUri and id
            if "ownerUri" not in card:
                raise ValueError(f"Advanced flow card of type '{card_type}' missing required field: ownerUri")
            if "id" not in card:
                raise ValueError(f"Advanced flow card of type '{card_type}' missing required field: id")
            validated_card["ownerUri"] = card["ownerUri"]
            validated_card["id"] = card["id"]
        else:
            # Builtin cards: ownerUri and id are optional
            if "ownerUri" in card and card["ownerUri"] is not None:
                validated_card["ownerUri"] = card["ownerUri"]
            if "id" in card and card["id"] is not None:
                validated_card["id"] = card["id"]

        # Optional fields - only include if present and valid
        optional_fields = ["args", "outputSuccess", "outputTrue", "outputFalse", "outputError",
                          "droptoken", "inverted", "input", "value", "color", "width", "height"]
        for field in optional_fields:
            if field in card and card[field] is not None:
                if field in ["outputSuccess", "outputTrue", "outputFalse", "outputError", "input"]:
                    # Connection arrays and input arrays
                    if isinstance(card[field], list):
                        validated_card[field] = [str(item) for item in card[field] if item is not None]
                elif field == "args":
                    # Card arguments
                    if isinstance(card[field], dict):
                        validated_card[field] = self._sanitize_dict(card[field])
                elif field in ["droptoken", "value", "color"]:
                    # String fields
                    if isinstance(card[field], str) and card[field].strip():
                        validated_card[field] = card[field].strip()
                elif field == "inverted":
                    # Boolean field
                    if isinstance(card[field], bool):
                        validated_card[field] = card[field]
                elif field in ["width", "height"]:
                    # Number fields
                    if isinstance(card[field], (int, float)):
                        validated_card[field] = card[field]

        return validated_card

    def _convert_cards_array_to_object(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert cards array to object structure if needed."""
        if not isinstance(flow_data, dict):
            return flow_data

        cards = flow_data.get('cards')
        if not isinstance(cards, list):
            return flow_data  # Already object or not present

        # Convert array to object structure
        cards_object = {}
        card_ids = []

        # Generate unique card IDs first
        for i, card in enumerate(cards):
            card_type = card.get('type', 'card')
            card_id = f"{card_type}_{i}_{uuid.uuid4().hex[:6]}"
            card_ids.append(card_id)

        # Build cards object with connections
        for i, card in enumerate(cards):
            card_id = card_ids[i]
            card_copy = card.copy()

            # Add required position fields if missing
            if 'x' not in card_copy:
                card_copy['x'] = 50 + (i * 200)  # Spread cards horizontally
            if 'y' not in card_copy:
                card_copy['y'] = 100  # Fixed Y position

            # Add connections between consecutive cards (except for last card)
            if i < len(cards) - 1 and card_copy.get('type') not in ['end', 'note']:
                next_card_id = card_ids[i + 1]
                # Use appropriate output connection based on card type
                if card_copy.get('type') == 'condition':
                    # For conditions, default to outputTrue
                    if 'outputTrue' not in card_copy:
                        card_copy['outputTrue'] = [next_card_id]
                else:
                    # For triggers, actions, etc., use outputSuccess
                    if 'outputSuccess' not in card_copy:
                        card_copy['outputSuccess'] = [next_card_id]

            cards_object[card_id] = card_copy

        # Return updated flow_data with object structure
        flow_data_copy = flow_data.copy()
        flow_data_copy['cards'] = cards_object
        return flow_data_copy

    def _remove_all_nulls(self, data: Any) -> Any:
        """Recursively remove all null values from nested structures."""
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if value is not None:
                    cleaned_value = self._remove_all_nulls(value)
                    if cleaned_value is not None:
                        cleaned[key] = cleaned_value
            return cleaned if cleaned else None
        elif isinstance(data, list):
            cleaned = []
            for item in data:
                if item is not None:
                    cleaned_item = self._remove_all_nulls(item)
                    if cleaned_item is not None:
                        cleaned.append(cleaned_item)
            return cleaned if cleaned else None
        else:
            return data

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

    def _parse_wait_time(self, description: str) -> int:
        """Parse wait time from description like 'wait 30 seconds' or 'delay 5 minutes'."""

        # Look for number followed by time unit
        time_pattern = r'(\d+)\s*(second|minute|hour|sec|min|hr)s?'
        match = re.search(time_pattern, description.lower())

        if match:
            number = int(match.group(1))
            unit = match.group(2)

            # Convert to seconds
            if unit in ['minute', 'min']:
                return number * 60
            elif unit in ['hour', 'hr']:
                return number * 3600
            else:  # seconds
                return number

        # Default to 10 seconds if no time found
        return 10

    def _find_device_from_description(self, description: str) -> Dict[str, Any]:
        """Find device info from description like 'turn on living room lights'."""
        # This is a simplified implementation
        # In a real implementation, you'd query actual devices

        if "turn on" in description.lower():
            return {
                "action_id": "turn_on_device",
                "uri": "homey:manager:device",
                "args": {}
            }
        elif "turn off" in description.lower():
            return {
                "action_id": "turn_off_device",
                "uri": "homey:manager:device",
                "args": {}
            }
        else:
            return {
                "action_id": "generic_action",
                "uri": "homey:manager:device",
                "args": {}
            }

    # ================== FLOW BUILDER HELPERS ==================

    async def find_trigger_by_name(self, name: str) -> Dict[str, Any]:
        """Find a trigger card by name or title."""
        available_cards = await self._get_available_cards()
        triggers = available_cards.get('triggers', {})

        name_lower = name.lower()
        for trigger_id, trigger in triggers.items():
            title = trigger.get('title', '').lower()
            if name_lower in title or title in name_lower:
                return trigger

        raise ValueError(f"No trigger found matching '{name}'. Available triggers: {list(triggers.keys())}")

    async def find_condition_by_name(self, name: str) -> Dict[str, Any]:
        """Find a condition card by name or title."""
        available_cards = await self._get_available_cards()
        conditions = available_cards.get('conditions', {})

        name_lower = name.lower()
        for condition_id, condition in conditions.items():
            title = condition.get('title', '').lower()
            if name_lower in title or title in name_lower:
                return condition

        raise ValueError(f"No condition found matching '{name}'. Available conditions: {list(conditions.keys())}")

    async def find_action_by_name(self, name: str) -> Dict[str, Any]:
        """Find an action card by name or title."""
        available_cards = await self._get_available_cards()
        actions = available_cards.get('actions', {})

        name_lower = name.lower()
        for action_id, action in actions.items():
            title = action.get('title', '').lower()
            if name_lower in title or title in name_lower:
                return action

        raise ValueError(f"No action found matching '{name}'. Available actions: {list(actions.keys())}")




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
