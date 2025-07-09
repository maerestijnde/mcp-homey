import logging
from typing import Any, Dict, List, Optional
import urllib.parse

logger = logging.getLogger(__name__)


class InsightsAPI:
    def __init__(self, client):
        self.client = client

    async def get_insights_logs(self) -> Dict[str, Any]:
        """Get all insights logs."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            # Demo data for insights logs
            return {
                "light1.onoff": {
                    "id": "onoff",
                    "uri": "homey:device:light1",
                    "name": "Living Room Lamp - On/Off",
                    "type": "boolean",
                    "units": "",
                    "decimals": 0
                },
                "light1.dim": {
                    "id": "dim", 
                    "uri": "homey:device:light1",
                    "name": "Living Room Lamp - Brightness",
                    "type": "number",
                    "units": "%",
                    "decimals": 1
                },
                "sensor1.measure_temperature": {
                    "id": "measure_temperature",
                    "uri": "homey:device:sensor1", 
                    "name": "Temperature Sensor - Temperature",
                    "type": "number",
                    "units": "°C",
                    "decimals": 1
                },
                "socket1.measure_power": {
                    "id": "measure_power",
                    "uri": "homey:device:socket1",
                    "name": "Desk Socket - Power",
                    "type": "number", 
                    "units": "W",
                    "decimals": 1
                }
            }

        try:
            # Try both V2 and V3 API endpoints
            endpoints_to_try = [
                "/api/manager/insights/log",      # V3 format
                "/api/manager/insights/log/"      # V2 format
            ]
            
            raw_data = None
            for endpoint in endpoints_to_try:
                try:
                    response = await self.client.session.get(endpoint)
                    if response.status_code == 200:
                        raw_data = response.json()
                        logger.debug(f"Successfully got insights logs from {endpoint}")
                        break
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint} failed: {e}")
                    continue
            
            if raw_data is None:
                logger.warning("No insights log endpoint worked")
                return {}
            
            # Handle both list and dict responses
            if isinstance(raw_data, list):
                # Convert list to dict format for consistent handling using NEW format
                logs_dict = {}
                for log in raw_data:
                    if isinstance(log, dict) and "id" in log and "ownerUri" in log:
                        # NEW FORMAT: Extract device ID and capability from the structured data
                        full_id = log.get("id", "")
                        owner_uri = log.get("ownerUri", "")
                        capability = log.get("ownerId", "")
                        device_name = log.get("ownerName", "Unknown")
                        
                        # Extract device ID from ownerUri (homey:device:xxxxx)
                        uri_parts = owner_uri.split(":")
                        device_id = uri_parts[-1] if len(uri_parts) > 2 else "unknown"
                        
                        # Create a simple key for easier access
                        key = f"{device_id}.{capability}"
                        
                        logs_dict[key] = {
                            "id": capability,  # Just the capability name
                            "full_id": full_id,  # Full insights ID for API calls
                            "uri": owner_uri,  # Device URI
                            "name": f"{device_name} - {log.get('title', capability)}",
                            "type": log.get("type", "unknown"),
                            "units": log.get("units", ""),
                            "decimals": log.get("decimals", 1),
                            "lastValue": log.get("lastValue", None)
                        }
                        
                return logs_dict
            else:
                # Already a dict
                return raw_data
                
        except Exception as e:
            logger.error(f"Error getting insights logs: {e}")
            raise

    async def get_insights_state(self) -> Dict[str, Any]:
        """Get insights manager state."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            return {
                "enabled": True,
                "version": "1.0.0",
                "storage": {
                    "used": 1024 * 1024 * 50,  # 50MB
                    "total": 1024 * 1024 * 1024,  # 1GB
                }
            }

        try:
            response = await self.client.session.get("/api/manager/insights/state")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting insights state: {e}")
            raise

    async def get_insights_log(self, log_id: str) -> Dict[str, Any]:
        """Get specific insights log by ID."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            logs = await self.get_insights_logs()
            return logs.get(log_id, {})

        try:
            response = await self.client.session.get(f"/api/manager/insights/log/{log_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting insights log {log_id}: {e}")
            raise

    async def get_insights_log_entries(self, uri: str, log_id: str, resolution: str = "1h", from_timestamp: Optional[str] = None, to_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get log entries for a specific insight log."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            # Generate demo data based on log type
            import random
            from datetime import datetime, timedelta
            
            entries = []
            
            # Generate last 24 hours of data
            now = datetime.now()
            hours_back = 24 if resolution == "1h" else 7 * 24
            interval_minutes = 60 if resolution == "1h" else 60 * 24
            
            for i in range(hours_back):
                timestamp = now - timedelta(minutes=i * interval_minutes)
                
                if "temperature" in log_id:
                    value = round(random.uniform(18.0, 24.0), 1)
                elif "dim" in log_id:
                    value = round(random.uniform(0.0, 1.0), 2)
                elif "power" in log_id:
                    value = round(random.uniform(10.0, 100.0), 1)
                elif "onoff" in log_id:
                    value = random.choice([True, False])
                else:
                    value = round(random.uniform(0, 100), 1)
                
                entries.append({
                    "t": timestamp.isoformat(),
                    "v": value
                })
            
            return sorted(entries, key=lambda x: x["t"])

        try:
            # NEW CORRECT FORMAT: Use the full insights log ID
            # First, we need to find the full_id for this device/capability combo
            logs = await self.get_insights_logs()
            
            # Find the matching log
            device_id = uri.split(":")[-1] if ":" in uri else uri
            search_key = f"{device_id}.{log_id}"
            
            if search_key not in logs:
                logger.warning(f"No insights log found for {search_key}")
                return []
            
            log_info = logs[search_key]
            full_log_id = log_info.get("full_id")
            
            if not full_log_id:
                logger.warning(f"No full_id found for log {search_key}")
                return []
            
            # Use the correct endpoint with full insights log ID (URL encoded)
            encoded_log_id = urllib.parse.quote(full_log_id, safe='')
            endpoint = f"/api/manager/insights/log/{encoded_log_id}/entry"
            params = {}
            
            if resolution:
                params["resolution"] = resolution
            if from_timestamp:
                params["from"] = from_timestamp
            if to_timestamp:
                params["to"] = to_timestamp
                
            response = await self.client.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting insights log entries for {uri}/{log_id}: {e}")
            raise

    async def get_insights_storage_info(self) -> Dict[str, Any]:
        """Get insights storage information."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            return {
                "used": 1024 * 1024 * 50,  # 50MB
                "total": 1024 * 1024 * 1024,  # 1GB
                "entries": 125000,
                "logs": 25
            }

        try:
            # Try different possible endpoints for storage info
            endpoints = [
                "/api/manager/insights/storage",
                "/api/manager/insights/",
                "/api/manager/insights"
            ]
            
            for endpoint in endpoints:
                try:
                    response = await self.client.session.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        # Check if this looks like storage info
                        if isinstance(data, dict) and any(key in data for key in ["used", "total", "storage", "size"]):
                            return data
                except:
                    continue
            
            # If no storage endpoint works, return estimated info based on logs
            logs = await self.get_insights_logs()
            return {
                "used": len(logs) * 1024 * 100,  # Estimate: 100KB per log
                "total": 1024 * 1024 * 1024,  # Estimate: 1GB total
                "entries": len(logs) * 1000,  # Estimate: 1000 entries per log
                "logs": len(logs)
            }
            
        except Exception as e:
            logger.error(f"Error getting insights storage info: {e}")
            # Return fallback data
            return {
                "used": 0,
                "total": 1024 * 1024 * 1024,  # 1GB
                "entries": 0,
                "logs": 0
            }