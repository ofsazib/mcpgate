"""Tests for the client snapshot over in-memory and stdio transports."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from mcpgate.client import open_session, snapshot, snapshot_sync

FIXTURES = Path(__file__).parent / "fixtures"


async def test_snapshot_in_memory(good_server) -> None:
    snap = await snapshot(good_server)
    assert snap.server_name == "good-server"
    assert snap.protocol_version
    assert [t.name for t in snap.tools] == ["add"]
    assert snap.tools[0].input_schema is not None
    assert [r.uri for r in snap.resources] == ["config://app"]
    assert [p.name for p in snap.prompts] == ["summarize"]
    assert "tools" in snap.capabilities
    assert snap.latency_ms >= 0


async def test_snapshot_stdio() -> None:
    snap = await snapshot(f"{sys.executable} {FIXTURES / 'stdio_server.py'}")
    assert snap.server_name == "stdio-fixture"
    assert [t.name for t in snap.tools] == ["add"]


async def test_open_session_rejects_empty_command() -> None:
    with pytest.raises(ValueError, match="empty server command"):
        async with open_session("   "):
            pass


def test_snapshot_sync(good_server) -> None:
    snap = snapshot_sync(good_server)
    assert snap.server_name == "good-server"


@pytest.mark.network
async def test_snapshot_real_server() -> None:
    snap = await snapshot("uvx mcp-server-fetch")
    assert snap.server_name
