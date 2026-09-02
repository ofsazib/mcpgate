"""MCP1xx — tool description quality rules (ported from the arXiv quality rubric)."""

from __future__ import annotations

from mcpgate.model import ServerSnapshot
from mcpgate.rules.base import CheckResult, rule, tool_sources, words

MIN_WORDS = 8
MAX_CHARS = 1024
_VAGUE = ("does stuff", "handles things", "various", "and stuff", "things like that")
_ERROR_WORDS = ("error", "fail", "raise", "exception", "invalid", "returns")
_ECHO_STOP = {"the", "a", "an", "tool", "to", "for", "and", "of", "given"}


@rule("MCP101", "warning", "Tool `{name}`: description too short ({n} words; minimum {min})")
def check_too_short(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: list[tuple[str, dict[str, object]]] = []
    for tool, src in tool_sources(snapshot):
        n = len(words(tool.description))
        if not tool.description.strip():
            out.append((src, {"name": tool.name, "n": 0, "min": MIN_WORDS}))
        elif n < MIN_WORDS:
            out.append((src, {"name": tool.name, "n": n, "min": MIN_WORDS}))
    return out


@rule("MCP102", "warning", "Tool `{name}`: description too vague (`{phrase}`)")
def check_vague(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        low = tool.description.lower()
        for phrase in _VAGUE:
            if phrase in low:
                out.append((src, {"name": tool.name, "phrase": phrase}))
                break
    return out


@rule("MCP103", "warning", "Tool `{name}`: description just restates the tool name")
def check_name_echo(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        if not tool.description.strip():
            continue
        name_tokens = {
            t for t in tool.name.lower().replace("_", " ").split() if t not in _ECHO_STOP
        }
        desc_tokens = {t.strip(".,;:!?") for t in tool.description.lower().split()} - _ECHO_STOP
        if name_tokens and desc_tokens and desc_tokens <= name_tokens:
            out.append((src, {"name": tool.name}))
    return out


@rule("MCP104", "warning", "Tool `{name}`: parameter `{param}` has no description")
def check_param_descriptions(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        props = tool.input_schema.get("properties", {}) if tool.input_schema else {}
        if len(props) <= 1:
            continue
        for param, spec in props.items():
            if not (isinstance(spec, dict) and spec.get("description")):
                out.append((src, {"name": tool.name, "param": param}))
    return out


@rule("MCP105", "warning", "Tool `{name}`: description does not state error/return behavior")
def check_error_behavior(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        low = tool.description.lower()
        if not any(w in low for w in _ERROR_WORDS):
            out.append((src, {"name": tool.name}))
    return out


@rule("MCP106", "warning", "Tool `{name}`: description too long ({n} chars; maximum {max})")
def check_too_long(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    out: CheckResult = []
    for tool, src in tool_sources(snapshot):
        n = len(tool.description)
        if n > MAX_CHARS:
            out.append((src, {"name": tool.name, "n": n, "max": MAX_CHARS}))
    return out
