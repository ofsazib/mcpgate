"""Runnable stdio MCP server used to test the stdio transport path offline."""

import logging

from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP("stdio-fixture")


@mcp.tool(description="Add two integers together and return their integer sum.")
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    mcp.run()
