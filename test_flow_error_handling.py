#!/usr/bin/env python3
"""
Test error handling for all flow operations.

This script tests various error scenarios to ensure proper error handling:
- Invalid flow IDs (404 errors)
- Invalid data (400/422 errors)
- Network failures
- Malformed requests
- Edge cases
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from homey_mcp.config import get_config
from homey_mcp.client import HomeyAPIClient
from homey_mcp.tools.flow import FlowManagementTools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlowErrorTester:
    def __init__(self):
        self.config = get_config()
        self.client = None
        self.flow_tools = None

    async def setup(self):
        """Initialize for testing."""
        # Force offline mode to avoid real API calls during error testing
        self.config.offline_mode = True
        self.config.demo_mode = False

        self.client = HomeyAPIClient(self.config)
        await self.client.connect()

        self.flow_tools = FlowManagementTools(self.client)
        logger.info("✅ Test environment setup complete")

    async def test_invalid_flow_ids(self):
        """Test error handling for invalid flow IDs."""
        logger.info("🧪 Testing invalid flow IDs...")

        invalid_ids = ["", "nonexistent", "null", None, 12345, [], {}]

        for invalid_id in invalid_ids:
            try:
                logger.info(f"Testing get_flow with invalid ID: {invalid_id}")
                result = await self.flow_tools.handle_get_flow({"flow_id": str(invalid_id) if invalid_id is not None else "null"})
                logger.info(f"Result: {result[0].text}")

                logger.info(f"Testing trigger_flow with invalid ID: {invalid_id}")
                result = await self.flow_tools.handle_trigger_flow({"flow_id": str(invalid_id) if invalid_id is not None else "null"})
                logger.info(f"Result: {result[0].text}")

            except Exception as e:
                logger.error(f"Unexpected exception with {invalid_id}: {e}")

    async def test_invalid_flow_data(self):
        """Test error handling for invalid flow creation data."""
        logger.info("🧪 Testing invalid flow creation data...")

        invalid_flow_data_sets = [
            # Missing name
            {"trigger": {"id": "test"}, "actions": []},
            # Null name
            {"name": None, "trigger": {"id": "test"}, "actions": []},
            # Empty name
            {"name": "", "trigger": {"id": "test"}, "actions": []},
            # Invalid name type
            {"name": 123, "trigger": {"id": "test"}, "actions": []},
            # Missing trigger
            {"name": "Test", "actions": []},
            # Missing actions
            {"name": "Test", "trigger": {"id": "test"}},
            # Invalid trigger type
            {"name": "Test", "trigger": "invalid", "actions": []},
            # Invalid actions type
            {"name": "Test", "trigger": {"id": "test"}, "actions": "invalid"},
        ]

        for i, invalid_data in enumerate(invalid_flow_data_sets):
            try:
                logger.info(f"Testing create_flow with invalid data set {i+1}: {invalid_data}")
                result = await self.flow_tools.handle_create_flow(invalid_data)
                logger.info(f"Result: {result[0].text}")
            except Exception as e:
                logger.error(f"Unexpected exception with data set {i+1}: {e}")

    async def test_invalid_advanced_flow_data(self):
        """Test error handling for invalid advanced flow data."""
        logger.info("🧪 Testing invalid advanced flow creation data...")

        invalid_advanced_data_sets = [
            # Missing name
            {"cards": []},
            # Null name
            {"name": None, "cards": []},
            # Empty name
            {"name": "", "cards": []},
            # Invalid name type
            {"name": [], "cards": []},
            # Missing cards
            {"name": "Test"},
            # Invalid cards type
            {"name": "Test", "cards": "invalid"},
            # Invalid card structure
            {"name": "Test", "cards": [{"invalid": "card"}]},
            # Cards with null values
            {"name": "Test", "cards": [{"type": None, "id": None}]},
        ]

        for i, invalid_data in enumerate(invalid_advanced_data_sets):
            try:
                logger.info(f"Testing create_advanced_flow with invalid data set {i+1}: {invalid_data}")
                result = await self.flow_tools.handle_create_advanced_flow(invalid_data)
                logger.info(f"Result: {result[0].text}")
            except Exception as e:
                logger.error(f"Unexpected exception with data set {i+1}: {e}")

    async def test_update_operations(self):
        """Test error handling for update operations."""
        logger.info("🧪 Testing update operations...")

        # Test update with no parameters
        try:
            logger.info("Testing update_flow with no parameters")
            result = await self.flow_tools.handle_update_flow({"flow_id": "test"})
            logger.info(f"Result: {result[0].text}")
        except Exception as e:
            logger.error(f"Unexpected exception: {e}")

        # Test update with invalid flow ID
        try:
            logger.info("Testing update_flow with invalid ID")
            result = await self.flow_tools.handle_update_flow({
                "flow_id": "nonexistent",
                "enabled": True,
                "name": "New Name"
            })
            logger.info(f"Result: {result[0].text}")
        except Exception as e:
            logger.error(f"Unexpected exception: {e}")

    async def test_search_operations(self):
        """Test error handling for search operations."""
        logger.info("🧪 Testing search operations...")

        search_terms = ["", None, 12345, [], {}, "nonexistent_flow_xyz"]

        for term in search_terms:
            try:
                logger.info(f"Testing find_flow_by_name with: {term}")
                result = await self.flow_tools.handle_find_flow_by_name({
                    "flow_name": str(term) if term is not None else "null"
                })
                logger.info(f"Result: {result[0].text}")
            except Exception as e:
                logger.error(f"Unexpected exception with {term}: {e}")

    async def test_folder_operations(self):
        """Test error handling for folder operations."""
        logger.info("🧪 Testing folder operations...")

        invalid_folder_data = [
            # Missing name
            {},
            # Empty name
            {"name": ""},
            # Null name
            {"name": None},
            # Invalid name type
            {"name": 123},
            # Invalid parent
            {"name": "Test", "parent": 123},
        ]

        for i, invalid_data in enumerate(invalid_folder_data):
            try:
                logger.info(f"Testing create_flow_folder with invalid data set {i+1}: {invalid_data}")
                result = await self.flow_tools.handle_create_flow_folder(invalid_data)
                logger.info(f"Result: {result[0].text}")
            except Exception as e:
                logger.error(f"Unexpected exception with data set {i+1}: {e}")

    async def test_action_testing(self):
        """Test error handling for flow action testing."""
        logger.info("🧪 Testing flow action operations...")

        invalid_action_data = [
            # Missing URI
            {"action_id": "test"},
            # Missing action ID
            {"uri": "homey:device:test"},
            # Empty values
            {"uri": "", "action_id": ""},
            # Invalid types
            {"uri": 123, "action_id": []},
            # Null values
            {"uri": None, "action_id": None},
        ]

        for i, invalid_data in enumerate(invalid_action_data):
            try:
                logger.info(f"Testing run_flow_card_action with invalid data set {i+1}: {invalid_data}")
                result = await self.flow_tools.handle_run_flow_card_action(invalid_data)
                logger.info(f"Result: {result[0].text}")
            except Exception as e:
                logger.error(f"Unexpected exception with data set {i+1}: {e}")

    async def cleanup(self):
        """Cleanup resources."""
        if self.client:
            await self.client.disconnect()

async def main():
    """Main test function."""
    logger.info("🚨 FLOW ERROR HANDLING TESTS")
    logger.info("=" * 50)

    tester = FlowErrorTester()

    try:
        await tester.setup()

        # Run all error handling tests
        await tester.test_invalid_flow_ids()
        await tester.test_invalid_flow_data()
        await tester.test_invalid_advanced_flow_data()
        await tester.test_update_operations()
        await tester.test_search_operations()
        await tester.test_folder_operations()
        await tester.test_action_testing()

        logger.info("✅ All error handling tests completed!")

    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())