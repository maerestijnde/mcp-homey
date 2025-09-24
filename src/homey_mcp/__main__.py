#!/usr/bin/env python3
"""
Entry point for Homey MCP Server v3.0 with insights support.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Setup logging - use stderr for errors so Claude can see them, file for info
log_file = Path(__file__).parent.parent.parent / "homey_mcp_server.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        # Add stderr handler for errors so Claude can see startup issues
        logging.StreamHandler(sys.stderr)
    ]
)

# Set stderr handler to only show warnings and errors
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)
logging.getLogger().addHandler(stderr_handler)

# Add src to path for development (this should be set by the shell script)
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from homey_mcp.server import main


async def run_server():
    """Main entry point."""
    try:
        logger = logging.getLogger(__name__)
        logger.info("🚀 Starting Homey MCP Server v3.0 from __main__.py...")

        # Start server
        await main()

    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("Server stopped by user")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Server error in __main__.py: {e}", exc_info=True)
        # Don't sys.exit(1) as it can cause issues with MCP
        raise


if __name__ == "__main__":
    asyncio.run(run_server())
