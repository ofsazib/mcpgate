"""Shared fixtures: in-memory MCP servers used across the test suite."""

from __future__ import annotations

pytest_plugins = ["pytester"]

from typing import Annotated, Any

import pytest
from mcp.server.fastmcp import FastMCP
from pydantic import Field

GOOD_ADD_DESCRIPTION = (
    "Computes the sum of two integers and returns the result. "
    "Raises ValueError if either argument is not an integer."
)


def _build_good_server() -> FastMCP:
    server = FastMCP(
        "good-server",
        instructions="A well-described example MCP server used in mcpgate tests.",
    )

    @server.tool(description=GOOD_ADD_DESCRIPTION)
    def add(
        a: Annotated[int, Field(description="the first integer")] = 0,
        b: Annotated[int, Field(description="the second integer")] = 0,
    ) -> int:
        """Add two integers."""
        return a + b

    @server.resource("config://app", description="Current application configuration values.")
    def app_config() -> str:
        return "debug=false"

    @server.prompt(description="Summarize the given text into five bullet points.")
    def summarize(text: str) -> str:
        return f"Summarize: {text}"

    return server


@pytest.fixture
def good_server() -> Any:
    return _build_good_server()
