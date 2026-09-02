"""Connect to MCP servers and snapshot their definitions over the protocol."""

from __future__ import annotations

import shlex
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.memory import create_connected_server_and_client_session

from mcpgate.model import PromptInfo, ResourceInfo, ServerSnapshot, ToolInfo

# A running server object (FastMCP / lowlevel Server) usable over in-memory transport.
ServerObject = Any

_HTTP_PREFIXES = ("http://", "https://")


@asynccontextmanager
async def open_session(target: str | ServerObject) -> AsyncIterator[ClientSession]:
    """Open a ClientSession to a server object (in-memory), command string (stdio) or URL (HTTP)."""
    if isinstance(target, str):
        if target.startswith(_HTTP_PREFIXES):
            async with (
                streamablehttp_client(target) as (read, write, _),
                ClientSession(read, write) as session,
            ):
                yield session
        else:
            parts = shlex.split(target)
            if not parts:
                raise ValueError(f"empty server command: {target!r}")
            params = StdioServerParameters(command=parts[0], args=parts[1:])
            async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
                yield session
    else:
        async with create_connected_server_and_client_session(
            target, raise_exceptions=True
        ) as session:
            yield session


async def snapshot(target: str | ServerObject) -> ServerSnapshot:
    """Connect to an MCP server and capture its full definition snapshot."""
    async with open_session(target) as session:
        start = time.perf_counter()
        init = await session.initialize()
        latency_ms = (time.perf_counter() - start) * 1000

        tools_result = await session.list_tools()
        resources_result = await session.list_resources()
        prompts_result = await session.list_prompts()

        server_info = init.serverInfo
        capabilities = sorted(init.capabilities.model_dump(exclude_none=True, exclude_unset=True))
        return ServerSnapshot(
            server_name=server_info.name,
            server_version=server_info.version or "",
            protocol_version=str(init.protocolVersion),
            instructions=init.instructions or "",
            capabilities=capabilities,
            tools=[
                ToolInfo(
                    name=t.name,
                    description=t.description or "",
                    input_schema=t.inputSchema,
                    output_schema=t.outputSchema,
                )
                for t in tools_result.tools
            ],
            resources=[
                ResourceInfo(
                    uri=str(r.uri),
                    name=r.name or "",
                    description=r.description or "",
                    mime_type=r.mimeType,
                )
                for r in resources_result.resources
            ],
            prompts=[
                PromptInfo(
                    name=p.name,
                    description=p.description or "",
                    arguments=[a.name for a in p.arguments or []],
                )
                for p in prompts_result.prompts
            ],
            latency_ms=round(latency_ms, 1),
        )


def snapshot_sync(target: str | ServerObject, timeout: float | None = None) -> ServerSnapshot:
    """Synchronous wrapper around :func:`snapshot` (used by the pytest plugin)."""
    import anyio

    async def run() -> ServerSnapshot:
        if timeout is None:
            return await snapshot(target)
        with anyio.fail_after(timeout):
            return await snapshot(target)

    return anyio.run(run)
