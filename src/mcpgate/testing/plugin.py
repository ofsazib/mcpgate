"""Pytest plugin: `mcp_server` fixture and `tool_contract` helper.

Register via the `pytest11` entry point (installed with the package).

Usage — parametrize with a server object (in-memory) or a command/URL:

    @pytest.mark.parametrize("mcp_server", [MyFastMcpServer], indirect=True)
    def test_add(mcp_server):
        result = mcp_server.call_tool("add", {"a": 1, "b": 2})
        assert result.is_error is False
        mcp_server.tool_contract("add")

Or point every test at one server with `--mcp-server "uvx mcp-server-fetch"`.
"""

from __future__ import annotations

from typing import Any

import anyio
import pytest

from mcpgate.client import ServerObject, open_session, snapshot_sync
from mcpgate.model import ServerSnapshot, ToolInfo
from mcpgate.rules.base import param_properties, required_params


class ToolResult:
    """Sync-friendly wrapper around the SDK's CallToolResult."""

    def __init__(self, is_error: bool, content: list[Any]) -> None:
        self.is_error = is_error
        self.content = content


class McpTestClient:
    """Synchronous test client over a live MCP server."""

    def __init__(self, target: str | ServerObject) -> None:
        self._target = target
        self._snapshot: ServerSnapshot | None = None

    @property
    def snapshot(self) -> ServerSnapshot:
        if self._snapshot is None:
            self._snapshot = snapshot_sync(self._target)
        return self._snapshot

    def tool(self, name: str) -> ToolInfo:
        for t in self.snapshot.tools:
            if t.name == name:
                return t
        raise AssertionError(
            f"tool {name!r} not found; available: {[t.name for t in self.snapshot.tools]}"
        )

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> ToolResult:
        async def run() -> ToolResult:
            async with open_session(self._target) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments or {})
                return ToolResult(is_error=bool(result.isError), content=list(result.content))

        return anyio.run(run)

    def tool_contract(self, name: str) -> None:
        """Assert the tool is well-formed: described, valid schema, safe error path."""
        t = self.tool(name)
        assert t.description.strip(), f"tool {name!r} has an empty description"
        assert len(t.description.split()) >= 8, f"tool {name!r} description too short"

        schema = t.input_schema
        assert isinstance(schema, dict), f"tool {name!r} has no input schema"
        assert schema.get("type") == "object", f"tool {name!r} input schema is not an object"

        props = param_properties(t)
        for param in required_params(t):
            spec = props.get(param)
            assert isinstance(spec, dict) and spec.get("description"), (
                f"tool {name!r} required parameter {param!r} is not described"
            )

        # Error path: an under-specified call must yield is_error, not a crash.
        result = self.call_tool(name, {})
        if not required_params(t):
            return
        assert result.is_error, (
            f"tool {name!r} accepted an empty call; expected an error result "
            f"(content: {result.content!r})"
        )


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addini(
        "mcp_server",
        help="Default MCP server (command string or URL) for the mcp_server fixture.",
        default="",
    )
    parser.addoption(
        "--mcp-server",
        dest="mcp_server",
        default=None,
        help="MCP server (command string or URL) for the mcp_server fixture.",
    )


@pytest.fixture
def mcp_server(request: pytest.FixtureRequest) -> McpTestClient:
    """An McpTestClient for the parametrized server, --mcp-server option, or mcp_server ini."""
    target = getattr(request, "param", None)
    if target is None:
        target = request.config.getoption("--mcp-server") or request.config.getini("mcp_server")
    if not target:
        pytest.fail(
            "mcp_server fixture needs a server: parametrize indirectly "
            '(@pytest.mark.parametrize("mcp_server", [server], indirect=True)), '
            "pass --mcp-server, or set the mcp_server ini setting"
        )
    return McpTestClient(target)
