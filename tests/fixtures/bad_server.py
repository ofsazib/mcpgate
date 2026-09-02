"""MCP server deliberately violating description/security rules.

Used by engine/CLI tests and as the source of README output examples.
FastMCP always emits object-typed schemas, so MCP2xx violations are covered
by hand-built snapshots in test_rules.py instead.
"""

import logging

from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP("bad-server")

SHORT = "Search stuff."
VAGUE = "This tool does stuff and handles things."
ECHO = "Search the web."
LONG = "x" * 1100
NO_BEHAVIOR = "Add two integers together and give back the final answer."

TOOLS = {
    "short": SHORT,
    "vague": VAGUE,
    "echo": ECHO,
    "long": LONG,
    "no_behavior": NO_BEHAVIOR,
    "run_command": "Runs any shell command you pass it.",
    "delete_record": "Removes a record from the database permanently.",
}


def _register() -> None:
    for name, desc in TOOLS.items():
        mcp.tool(name=name, description=desc)(lambda: None)


_register()

if __name__ == "__main__":
    mcp.run()
