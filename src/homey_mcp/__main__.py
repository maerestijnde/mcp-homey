#!/usr/bin/env python3
"""
Entry point voor Homey MCP Server.
"""
import asyncio
import sys
import logging
from pathlib import Path

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
        logger.info("Server gestopt door gebruiker")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_server())
