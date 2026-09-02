"""MCP2xx — input/output schema rules."""

from __future__ import annotations

from typing import Any

from mcpgate.model import ServerSnapshot
from mcpgate.rules.base import CheckResult, param_properties, required_params, rule, tool_sources

_CONSTRAINT_WORDS = (
    "must",
    "only",
    "exactly",
    "no more than",
    "at most",
    "additional",
    "either",
)


@rule("MCP201", "error", "Tool `{name}`: input schema {problem}")
def check_input_schema(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        schema = tool.input_schema
        if schema is None:
            out.append((src, {"name": tool.name, "problem": "missing"}))
        elif not isinstance(schema, dict) or schema.get("type") != "object":
            out.append((src, {"name": tool.name, "problem": "is not a JSON object schema"}))
    return out


@rule("MCP202", "warning", "Tool `{name}`: required parameter `{param}` is not described")
def check_required_described(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        props: dict[str, Any] = param_properties(tool)
        for param in required_params(tool):
            spec = props.get(param)
            if not (isinstance(spec, dict) and spec.get("description")):
                out.append((src, {"name": tool.name, "param": param}))
    return out


@rule("MCP203", "info", "Tool `{name}`: strict schema but description states no constraints")
def check_constraints_mentioned(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        if (tool.input_schema or {}).get("additionalProperties") is not False:
            continue
        low = tool.description.lower()
        if not any(w in low for w in _CONSTRAINT_WORDS):
            out.append((src, {"name": tool.name}))
    return out


@rule("MCP204", "info", "Tool `{name}`: description repeats the tool name (wasted tokens)")
def check_name_repetition(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        name_spaced = tool.name.lower().replace("_", " ").replace("-", " ")
        if (
            name_spaced in tool.description.lower()
            and name_spaced != tool.description.lower().strip()
        ):
            out.append((src, {"name": tool.name}))
    return out


@rule("MCP205", "error", "Tool `{name}`: output schema is declared but invalid")
def check_output_schema(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        schema = tool.output_schema
        if schema is None:
            continue
        if not isinstance(schema, dict) or "type" not in schema:
            out.append((src, {"name": tool.name}))
    return out
