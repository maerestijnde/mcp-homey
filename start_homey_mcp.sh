#!/bin/bash
# Bulletproof Homey MCP Server launcher v3.0
# This script ensures everything works regardless of Claude Desktop's environment
# Now with full insights support!

# Debug: Log bash script debugging to a file (not stderr to avoid JSON-RPC interference)
exec 2>/Users/yourname/Projects/mcp-homey/homey_mcp_debug.log

# Log startup with timestamp
echo "$(date): Starting Homey MCP Server v3.0..." >&2

# Set working directory
cd "/Users/yourname/Projects/mcp-homey" || {
    echo "ERROR: Cannot find project directory" >&2
    exit 1
}

# Check if uv exists
if [ ! -f "/Users/yourname/.local/bin/uv" ]; then
    echo "ERROR: uv not found at /Users/yourname/.local/bin/uv" >&2
    exit 1
fi

# Check if Python script exists
if [ ! -f "src/homey_mcp/__main__.py" ]; then
    echo "ERROR: Python script not found" >&2
    exit 1
fi

# Set all environment variables explicitly
export PATH="/Users/yourname/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="/Users/yourname/Projects/mcp-homey/src"

# Set Homey configuration (load from .env or use defaults for fallback)
export HOMEY_LOCAL_ADDRESS="${HOMEY_LOCAL_ADDRESS:-YOUR_HOMEY_IP}"
export HOMEY_LOCAL_TOKEN="${HOMEY_LOCAL_TOKEN:-your-token-here}"
export OFFLINE_MODE="${OFFLINE_MODE:-false}"
export DEMO_MODE="${DEMO_MODE:-false}"

# Log configuration
echo "$(date): Configuration:" >&2
echo "  - Homey IP: $HOMEY_LOCAL_ADDRESS" >&2
echo "  - Offline Mode: $OFFLINE_MODE" >&2
echo "  - Demo Mode: $DEMO_MODE" >&2
echo "  - Python Path: $PYTHONPATH" >&2

# Log that we're starting the server
echo "$(date): Executing: uv run python src/homey_mcp/__main__.py" >&2

# Run the server with explicit paths and error handling
exec "/Users/yourname/.local/bin/uv" run python "src/homey_mcp/__main__.py"
