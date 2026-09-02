"""Tests for the pytest plugin: fixture wiring and contract checks."""

import sys
from pathlib import Path

import pytest

from mcpgate.testing.plugin import McpTestClient

FIXTURES = Path(__file__).parent / "fixtures"
STDIO = f"{sys.executable} {FIXTURES / 'stdio_server.py'}"


def test_client_call_tool(good_server) -> None:
    client = McpTestClient(good_server)
    result = client.call_tool("add", {"a": 2, "b": 3})
    assert result.is_error is False


def test_contract_passes_on_good_server(good_server) -> None:
    McpTestClient(good_server).tool_contract("add")


def test_contract_fails_on_bad_server() -> None:
    sys.path.insert(0, str(FIXTURES))
    bad_server = __import__("bad_server").mcp
    client = McpTestClient(bad_server)
    with pytest.raises(AssertionError):
        client.tool_contract("short")


def test_tool_unknown_raises_helpful(good_server) -> None:
    with pytest.raises(AssertionError, match="not found"):
        McpTestClient(good_server).tool("nope")


def test_plugin_in_fresh_pytest_run(pytester: pytest.Pytester) -> None:
    pytester.makeini(f"[pytest]\nmcp_server = {STDIO}\n")
    pytester.makepyfile(
        """
        def test_add(mcp_server):
            result = mcp_server.call_tool("add", {"a": 1, "b": 2})
            assert result.is_error is False
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
