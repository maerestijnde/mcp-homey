import logging
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class FlowAPI:
    def __init__(self, client):
        self.client = client

    async def get_flows(self) -> Dict[str, Any]:
        """Get all flows."""
        # Demo mode data
        if self.client.config.offline_mode or self.client.config.demo_mode:
            demo_flows = {
                "flow1": {
                    "id": "flow1",
                    "name": "Good Morning Routine",
                    "enabled": True,
                    "broken": False,
                },
                "flow2": {"id": "flow2", "name": "Evening Routine", "enabled": True, "broken": False},
            }
            logger.info(f"Demo mode: {len(demo_flows)} demo flows")
            return demo_flows

        try:
            # FIX: Add trailing slash
            response = await self.client.session.get("/api/manager/flow/flow/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting flows: {e}")
            raise

    async def trigger_flow(self, flow_id: str) -> bool:
        """Start a flow."""
        # Demo mode
        if self.client.config.offline_mode or self.client.config.demo_mode:
            logger.info(f"Demo mode: Flow {flow_id} would be started")
            return True

        try:
            # Try different endpoint variants
            endpoints_to_try = [
                f"/api/manager/flow/flow/{flow_id}/trigger",
                f"/api/manager/flow/flow/{flow_id}/start", 
                f"/api/manager/flow/flow/{flow_id}/run",
                f"/api/manager/flow/flow/{flow_id}/"
            ]
            
            last_error = None
            
            for endpoint in endpoints_to_try:
                try:
                    logger.debug(f"Trying flow trigger endpoint: {endpoint}")
                    response = await self.client.session.post(endpoint)
                    response.raise_for_status()
                    
                    logger.info(f"✅ Flow {flow_id} triggered via {endpoint}")
                    return True
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        logger.debug(f"Endpoint {endpoint} not found, trying next...")
                        last_error = e
                        continue
                    else:
                        # Other HTTP error, stop trying
                        raise e
                except Exception as e:
                    last_error = e
                    continue
            
            # If we get here, none of the endpoints worked
            logger.error(f"No working flow trigger endpoint found for flow {flow_id}")
            if last_error:
                raise last_error
            else:
                raise Exception("All flow trigger endpoints failed")

        except Exception as e:
            logger.error(f"Error triggering flow: {e}")
            raise