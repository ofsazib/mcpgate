"""MCP3xx — security-oriented definition rules."""

from __future__ import annotations

import re

from mcpgate.model import ServerSnapshot
from mcpgate.rules.base import CheckResult, param_properties, rule, tool_sources

_EXEC_PATTERN = re.compile(r"(shell|exec|execute|command|cmd|terminal|subprocess)", re.I)
_SAFETY_WORDS = (
    "sandbox",
    "allowlist",
    "allow-list",
    "confirm",
    "caution",
    "warning",
    "safe",
    "do not",
    "only runs",
)
_SECRET_PATTERN = re.compile(
    r"(password|passwd|secret|token|api_?key|credential|private_?key)", re.I
)
_DESTRUCTIVE_PATTERN = re.compile(r"(delete|drop|remove|purge|destroy)", re.I)
_CONFIRM_PARAMS = ("confirm", "confirmation", "acknowledge", "sure", "force")


@rule("MCP301", "error", "Tool `{name}`: suggests command execution without a safety note")
def check_exec_without_safety(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        blob = f"{tool.name} {tool.description}"
        if not _EXEC_PATTERN.search(blob):
            continue
        if not any(w in tool.description.lower() for w in _SAFETY_WORDS):
            out.append((src, {"name": tool.name}))
    return out


@rule(
    "MCP302", "warning", "Tool `{name}`: parameter `{param}` looks like a secret — review handling"
)
def check_secret_params(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        for param in param_properties(tool):
            if _SECRET_PATTERN.search(param):
                out.append((src, {"name": tool.name, "param": param}))
    return out


@rule("MCP303", "warning", "Tool `{name}`: destructive operation without a confirmation parameter")
def check_destructive_no_confirm(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        if not _DESTRUCTIVE_PATTERN.search(tool.name):
            continue
        params = {p.lower() for p in param_properties(tool)}
        if not params & set(_CONFIRM_PARAMS):
            out.append((src, {"name": tool.name}))
    return out
