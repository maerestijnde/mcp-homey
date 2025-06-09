#!/usr/bin/env python3
"""
Entry point voor Homey MCP Server.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Setup logging first - redirect to file to avoid interfering with JSON-RPC stdio
log_file = "/Users/yourname/Projects/mcp-homey/homey_mcp_server.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        # Don't log to stderr/stdout as it interferes with JSON-RPC
    ]
)

# Add src to path voor development
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from homey_mcp.server import main


async def run_server():
    """Main entry point."""
    try:
        logger = logging.getLogger(__name__)
        logger.info("Starting Homey MCP Server...")

        # Start server
        await main()

    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("Server gestopt door gebruiker")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_server())
