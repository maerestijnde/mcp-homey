"""Call one MCP tool on a fresh server process, so code changes are picked up without restarting Claude.

    uv run python scripts/mcp_call.py                          # list tools
    uv run python scripts/mcp_call.py get_flows '{"flow_type": "advanced"}'
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).parent.parent


async def main(argv: list[str]) -> None:
    server = StdioServerParameters(command=sys.executable, args=["-m", "homey_mcp"], cwd=str(ROOT))
    async with stdio_client(server) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        if not argv:
            for tool in (await session.list_tools()).tools:
                print(f"{tool.name:32} {(tool.description or '').splitlines()[0][:80]}")
            return
        result = await session.call_tool(argv[0], json.loads(argv[1]) if len(argv) > 1 else {})
        for block in result.content:
            print(getattr(block, "text", block))
        if result.isError:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
