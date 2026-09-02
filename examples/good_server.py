"""A rule-clean example MCP server (passes `mcpgate lint`)."""

import logging
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP(
    "example-good-server",
    instructions="Example MCP server that passes every mcpgate rule.",
)

Int = Annotated[int, Field(description="an integer operand")]


@mcp.tool(
    description=(
        "Computes the sum of two integers and returns the result. "
        "Raises ValueError if either argument is not an integer."
    )
)
def add(a: Int = 0, b: Int = 0) -> int:
    """Add two integers."""
    return a + b


@mcp.resource("config://example", description="Current example application configuration values.")
def config() -> str:
    return "debug=false"


@mcp.prompt(description="Summarize the provided text into five concise bullet points.")
def summarize(text: str) -> str:
    return f"Summarize: {text}"


if __name__ == "__main__":
    mcp.run()
