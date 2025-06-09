#!/bin/bash
# Homey MCP Server startup script for Claude Desktop

# Set environment
export PATH="/Users/yourname/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export OFFLINE_MODE="true"
export DEMO_MODE="true"
export LOG_LEVEL="DEBUG"
export HOMEY_LOCAL_ADDRESS="YOUR_HOMEY_IP"
export HOMEY_LOCAL_TOKEN="your-token-here"

# Change to project directory
cd "/Users/yourname/Projects/mcp-homey"

# Run the server
exec /Users/yourname/.local/bin/uv run python src/homey_mcp/__main__.py
