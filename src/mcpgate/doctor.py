"""Health report for an MCP server: handshake, capabilities, latency."""

from __future__ import annotations

from typing import Any, TextIO

from mcpgate.client import ServerObject, snapshot_sync
from mcpgate.model import ServerSnapshot


def health_report(target: str | ServerObject, timeout: float | None = None) -> dict[str, Any]:
    snap = snapshot_sync(target, timeout=timeout)
    report: dict[str, Any] = _report_from(snap)
    report["healthy"] = True
    return report


def _report_from(snap: ServerSnapshot) -> dict[str, Any]:
    return {
        "server_name": snap.server_name,
        "server_version": snap.server_version,
        "protocol_version": snap.protocol_version,
        "capabilities": snap.capabilities,
        "tools": len(snap.tools),
        "resources": len(snap.resources),
        "prompts": len(snap.prompts),
        "latency_ms": snap.latency_ms,
    }


def print_report(report: dict[str, Any], stream: TextIO) -> None:
    stream.write(f"server      {report['server_name']} v{report['server_version']}\n")
    stream.write(f"protocol    {report['protocol_version']}\n")
    stream.write(f"latency     {report['latency_ms']} ms\n")
    stream.write(f"capabilities {', '.join(report['capabilities']) or 'none'}\n")
    stream.write(
        f"definitions {report['tools']} tools, {report['resources']} resources, "
        f"{report['prompts']} prompts\n"
    )
    stream.write("status      healthy\n")
