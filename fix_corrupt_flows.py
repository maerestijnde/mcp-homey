#!/usr/bin/env python3
"""
Fix corrupt flows in Homey that are causing the localeCompare error.

This script:
1. Detects flows with null/missing names or other required fields
2. Provides options to fix or remove corrupt flows
3. Validates flow structure before API calls

Run: python fix_corrupt_flows.py
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from homey_mcp.config import get_config
from homey_mcp.client import HomeyAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlowCorruptionFixer:
    def __init__(self):
        self.config = get_config()
        self.client = None
        self.corrupt_flows = []
        self.corrupt_advanced_flows = []

    async def connect(self):
        """Connect to Homey."""
        self.client = HomeyAPIClient(self.config)
        await self.client.connect()
        logger.info("✅ Connected to Homey")

    async def disconnect(self):
        """Disconnect from Homey."""
        if self.client:
            await self.client.disconnect()

    def validate_flow_structure(self, flow_id: str, flow: Dict[str, Any], flow_type: str = "regular") -> List[str]:
        """Validate flow structure and return list of issues."""
        issues = []

        # Check for null/missing name (main cause of localeCompare error)
        name = flow.get("name")
        if name is None:
            issues.append(f"Missing name (null)")
        elif not isinstance(name, str):
            issues.append(f"Name is not a string: {type(name)} - {name}")
        elif name.strip() == "":
            issues.append(f"Empty name string")

        # Check other critical fields that could cause sorting issues
        if flow.get("id") is None:
            issues.append("Missing id")

        if flow.get("enabled") is None:
            issues.append("Missing enabled field")

        # Check flow-type specific fields
        if flow_type == "regular":
            if flow.get("trigger") is None:
                issues.append("Missing trigger")
            if flow.get("actions") is None:
                issues.append("Missing actions")
        elif flow_type == "advanced":
            if flow.get("cards") is None:
                issues.append("Missing cards")

        return issues

    async def scan_for_corrupt_flows(self):
        """Scan all flows for corruption issues."""
        logger.info("🔍 Scanning for corrupt flows...")

        # Check regular flows
        try:
            flows = await self.client.get_flows()
            logger.info(f"Checking {len(flows)} regular flows...")

            for flow_id, flow in flows.items():
                issues = self.validate_flow_structure(flow_id, flow, "regular")
                if issues:
                    self.corrupt_flows.append({
                        "id": flow_id,
                        "flow": flow,
                        "issues": issues
                    })
                    logger.warning(f"❌ Corrupt regular flow {flow_id}: {', '.join(issues)}")
        except Exception as e:
            logger.error(f"Error scanning regular flows: {e}")

        # Check advanced flows
        try:
            advanced_flows = await self.client.get_advanced_flows()
            logger.info(f"Checking {len(advanced_flows)} advanced flows...")

            for flow_id, flow in advanced_flows.items():
                issues = self.validate_flow_structure(flow_id, flow, "advanced")
                if issues:
                    self.corrupt_advanced_flows.append({
                        "id": flow_id,
                        "flow": flow,
                        "issues": issues
                    })
                    logger.warning(f"❌ Corrupt advanced flow {flow_id}: {', '.join(issues)}")
        except Exception as e:
            logger.error(f"Error scanning advanced flows: {e}")

    def display_corrupt_flows(self):
        """Display all found corrupt flows."""
        total_corrupt = len(self.corrupt_flows) + len(self.corrupt_advanced_flows)

        if total_corrupt == 0:
            logger.info("✅ No corrupt flows found!")
            return False

        logger.info(f"\n🚨 Found {total_corrupt} corrupt flows:")
        logger.info("=" * 60)

        # Regular flows
        for i, corrupt in enumerate(self.corrupt_flows, 1):
            logger.info(f"\n{i}. REGULAR FLOW: {corrupt['id']}")
            logger.info(f"   Name: {corrupt['flow'].get('name', 'NULL')}")
            logger.info(f"   Issues: {', '.join(corrupt['issues'])}")

        # Advanced flows
        for i, corrupt in enumerate(self.corrupt_advanced_flows, len(self.corrupt_flows) + 1):
            logger.info(f"\n{i}. ADVANCED FLOW: {corrupt['id']}")
            logger.info(f"   Name: {corrupt['flow'].get('name', 'NULL')}")
            logger.info(f"   Issues: {', '.join(corrupt['issues'])}")

        return True

    async def fix_flow_name(self, flow_id: str, flow: Dict[str, Any], flow_type: str):
        """Fix a flow with null/invalid name."""
        current_name = flow.get("name")

        # Generate a safe name
        if current_name is None or not isinstance(current_name, str) or current_name.strip() == "":
            safe_name = f"Fixed Flow {flow_id[:8]}"
            logger.info(f"Fixing {flow_type} flow {flow_id}: '{current_name}' -> '{safe_name}'")

            try:
                if flow_type == "regular":
                    await self.client.update_flow(flow_id, name=safe_name)
                else:  # advanced
                    # Advanced flows need different update approach
                    flow_data = flow.copy()
                    flow_data["name"] = safe_name
                    await self.client.update_advanced_flow(flow_id, flow_data)

                logger.info(f"✅ Fixed {flow_type} flow {flow_id}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to fix {flow_type} flow {flow_id}: {e}")
                return False
        return True

    async def delete_corrupt_flow(self, flow_id: str, flow_type: str):
        """Delete a corrupt flow that cannot be fixed."""
        try:
            if flow_type == "regular":
                await self.client.delete_flow(flow_id)
            else:  # advanced
                await self.client.delete_advanced_flow(flow_id)

            logger.info(f"✅ Deleted corrupt {flow_type} flow {flow_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete {flow_type} flow {flow_id}: {e}")
            return False

    async def interactive_fix(self):
        """Interactive flow fixing session."""
        all_corrupt = []

        # Combine all corrupt flows
        for corrupt in self.corrupt_flows:
            all_corrupt.append((corrupt, "regular"))
        for corrupt in self.corrupt_advanced_flows:
            all_corrupt.append((corrupt, "advanced"))

        logger.info(f"\n🔧 INTERACTIVE FIX SESSION")
        logger.info("=" * 40)

        for corrupt, flow_type in all_corrupt:
            flow_id = corrupt["id"]
            flow = corrupt["flow"]
            issues = corrupt["issues"]

            logger.info(f"\n📋 {flow_type.upper()} FLOW: {flow_id}")
            logger.info(f"Name: {flow.get('name', 'NULL')}")
            logger.info(f"Issues: {', '.join(issues)}")

            # Check if this is primarily a name issue
            name_issues = [i for i in issues if "name" in i.lower()]
            if name_issues:
                print(f"\nOptions for {flow_id}:")
                print("1. Fix name automatically")
                print("2. Delete flow")
                print("3. Skip")

                choice = input("Choose option (1-3): ").strip()

                if choice == "1":
                    await self.fix_flow_name(flow_id, flow, flow_type)
                elif choice == "2":
                    confirm = input(f"Are you sure you want to DELETE flow {flow_id}? (yes/no): ").strip().lower()
                    if confirm == "yes":
                        await self.delete_corrupt_flow(flow_id, flow_type)
                    else:
                        logger.info("Skipped deletion")
                else:
                    logger.info("Skipped")
            else:
                print(f"\nComplex issues found for {flow_id}. Recommend deletion.")
                print("1. Delete flow")
                print("2. Skip")

                choice = input("Choose option (1-2): ").strip()
                if choice == "1":
                    confirm = input(f"Are you sure you want to DELETE flow {flow_id}? (yes/no): ").strip().lower()
                    if confirm == "yes":
                        await self.delete_corrupt_flow(flow_id, flow_type)

async def main():
    """Main function."""
    logger.info("🚨 HOMEY FLOW CORRUPTION FIXER")
    logger.info("=" * 50)

    fixer = FlowCorruptionFixer()

    try:
        # Connect to Homey
        await fixer.connect()

        # Scan for corrupt flows
        await fixer.scan_for_corrupt_flows()

        # Display results
        has_corrupt = fixer.display_corrupt_flows()

        if has_corrupt:
            logger.info("\n" + "=" * 60)
            logger.info("🔧 FIXING OPTIONS:")
            logger.info("The 'localeCompare' error is typically caused by flows with null names.")
            logger.info("We can fix this by giving them proper names or deleting them.")

            choice = input("\nStart interactive fixing? (y/n): ").strip().lower()
            if choice == 'y':
                await fixer.interactive_fix()

                # Rescan to verify fixes
                logger.info("\n🔍 Rescanning after fixes...")
                fixer.corrupt_flows = []
                fixer.corrupt_advanced_flows = []
                await fixer.scan_for_corrupt_flows()
                fixer.display_corrupt_flows()

        logger.info("\n✅ Flow corruption check completed!")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        await fixer.disconnect()

if __name__ == "__main__":
    asyncio.run(main())