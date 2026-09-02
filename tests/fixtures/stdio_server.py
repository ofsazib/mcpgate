"""Runnable stdio MCP server used to test the stdio transport path offline."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("stdio-fixture")


@mcp.tool(description="Add two integers together and return their integer sum.")
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    mcp.run()
