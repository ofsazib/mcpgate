"""Shared fixtures: in-memory MCP servers used across the test suite."""

from __future__ import annotations

from typing import Any

import pytest
from mcp.server.fastmcp import FastMCP

GOOD_ADD_DESCRIPTION = (
    "Add two integers together and return their sum. "
    "Raises ValueError if either argument is not an integer."
)


def _build_good_server() -> FastMCP:
    server = FastMCP(
        "good-server",
        instructions="A well-described example MCP server used in mcpgate tests.",
    )

    @server.tool(description=GOOD_ADD_DESCRIPTION)
    def add(a: int = 0, b: int = 0) -> int:
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
