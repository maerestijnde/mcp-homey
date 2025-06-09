#!/bin/bash
# Bulletproof Homey MCP Server launcher
# This script ensures everything works regardless of Claude Desktop's environment

# Debug: Log bash script debugging to a file (not stderr to avoid JSON-RPC interference)
exec 2>/Users/yourname/Projects/mcp-homey/homey_mcp_debug.log

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

# Run the server with explicit paths and error handling
exec "/Users/yourname/.local/bin/uv" run python "src/homey_mcp/__main__.py"
