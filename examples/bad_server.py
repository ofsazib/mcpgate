"""An example MCP server that violates many mcpgate rules (for docs).

Run: uv run mcpgate lint "python3 examples/bad_server.py"
"""

import logging

from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP("example-bad-server")

TOOLS = {
    "search": "Search stuff.",
    "run_command": "Runs any shell command you pass it.",
    "delete_record": "Removes a record from the database permanently.",
}


def _register() -> None:
    for name, desc in TOOLS.items():
        mcp.tool(name=name, description=desc)(lambda: None)


_register()

if __name__ == "__main__":
    mcp.run()
