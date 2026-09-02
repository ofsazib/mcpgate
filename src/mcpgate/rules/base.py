"""Rule protocol, registry, and shared helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from mcpgate.model import ServerSnapshot, ToolInfo

CheckResult = list[tuple[str, dict[str, Any]]]  # (source, message kwargs)


@dataclass(frozen=True)
class Rule:
    code: str
    severity: str  # "error" | "warning" | "info"
    message: str  # str.format template
    check: Callable[[ServerSnapshot], CheckResult]


_REGISTRY: dict[str, Rule] = {}


class UnknownRuleError(ValueError):
    """Raised when --select/--ignore references an undefined rule code."""


def rule(code: str, severity: str, message: str) -> Callable[[CheckFn], CheckFn]:
    """Register a rule. `check` returns (source, message-kwargs) tuples."""

    def decorator(fn: CheckFn) -> CheckFn:
        if code in _REGISTRY:
            raise ValueError(f"rule {code} registered twice")
        _REGISTRY[code] = Rule(code=code, severity=severity, message=message, check=fn)
        return fn

    return decorator


CheckFn = Callable[[ServerSnapshot], CheckResult]


def all_rules() -> list[Rule]:
    return sorted(_REGISTRY.values(), key=lambda r: r.code)


def resolve_rules(select: list[str] | None, ignore: list[str] | None) -> list[Rule]:
    """Filter registered rules by --select/--ignore; unknown codes raise."""
    unknown = [c for c in (*(select or []), *(ignore or [])) if c not in _REGISTRY]
    if unknown:
        raise UnknownRuleError(
            f"unknown rule code(s): {', '.join(sorted(unknown))}. "
            f"known codes: {', '.join(r.code for r in all_rules())}"
        )
    return [
        r
        for r in all_rules()
        if (not select or r.code in select) and not (ignore and r.code in ignore)
    ]


def tool_sources(snapshot: ServerSnapshot) -> Iterator[tuple[ToolInfo, str]]:
    for tool in snapshot.tools:
        yield tool, f"tools/{tool.name}"


def words(text: str) -> list[str]:
    return text.split()


def param_properties(tool: ToolInfo) -> dict[str, Any]:
    props = (tool.input_schema or {}).get("properties")
    return props if isinstance(props, dict) else {}


def required_params(tool: ToolInfo) -> list[str]:
    req = (tool.input_schema or {}).get("required")
    return req if isinstance(req, list) else []
