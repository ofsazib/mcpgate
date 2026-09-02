"""One positive + one negative test per rule, plus registry behavior."""

from __future__ import annotations

from typing import Any

import pytest

from mcpgate.model import ServerSnapshot, ToolInfo
from mcpgate.rules import (  # noqa: F401
    UnknownRuleError,
    all_rules,
    descriptions,
    resolve_rules,
    schemas,
    security,
    tokens,
)

GOOD_DESC = (
    "Add two integers together and return their sum. "
    "Raises ValueError if either argument is not an integer."
)


def tool(
    name: str = "search",
    description: str = GOOD_DESC,
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
    output_schema: dict[str, Any] | None = None,
) -> ToolInfo:
    schema = None
    if properties is not None:
        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
    return ToolInfo(
        name=name, description=description, input_schema=schema, output_schema=output_schema
    )


def snap(*tools: ToolInfo, **kw: Any) -> ServerSnapshot:
    return ServerSnapshot(tools=list(tools), **kw)


def codes(snapshot: ServerSnapshot) -> set[str]:
    from mcpgate.rules.base import _REGISTRY

    return {r.code for r in _REGISTRY.values() if (findings := r.check(snapshot))}


def described_props(**specs: Any) -> dict[str, Any]:
    return {
        name: (spec if isinstance(spec, dict) else {"type": "string", "description": spec})
        for name, spec in specs.items()
    }


class TestDescriptions:
    def test_mcp101_fires_on_short(self) -> None:
        assert "MCP101" in codes(snap(tool(description="Search stuff.")))

    def test_mcp101_quiet_on_good(self) -> None:
        assert "MCP101" not in codes(snap(tool()))

    def test_mcp102_fires_on_vague(self) -> None:
        assert "MCP102" in codes(snap(tool(description="Does stuff and handles things.")))

    def test_mcp102_quiet_on_good(self) -> None:
        assert "MCP102" not in codes(snap(tool()))

    def test_mcp103_fires_on_name_echo(self) -> None:
        assert "MCP103" in codes(snap(tool(name="search_web", description="Search the web.")))

    def test_mcp103_quiet_on_good(self) -> None:
        assert "MCP103" not in codes(snap(tool()))

    def test_mcp104_fires_on_undescribed_params(self) -> None:
        props = {"a": {"type": "integer"}, "b": {"type": "integer", "description": "second"}}
        assert "MCP104" in codes(snap(tool(properties=props)))

    def test_mcp104_quiet_when_described(self) -> None:
        props = described_props(a="first", b="second")
        assert "MCP104" not in codes(snap(tool(properties=props)))

    def test_mcp105_fires_without_behavior(self) -> None:
        assert "MCP105" in codes(
            snap(tool(description="Add two integers together and return the result."))
        )

    def test_mcp105_quiet_with_behavior(self) -> None:
        assert "MCP105" not in codes(snap(tool()))

    def test_mcp106_fires_on_long(self) -> None:
        assert "MCP106" in codes(snap(tool(description="x" * 1100)))

    def test_mcp106_quiet_on_good(self) -> None:
        assert "MCP106" not in codes(snap(tool()))


class TestSchemas:
    def test_mcp201_fires_on_non_object(self) -> None:
        t = tool()
        t = t.model_copy(update={"input_schema": {"type": "string"}})
        assert "MCP201" in codes(snap(t))

    def test_mcp201_quiet_on_object(self) -> None:
        assert "MCP201" not in codes(snap(tool(properties={})))

    def test_mcp202_fires_on_undescribed_required(self) -> None:
        assert "MCP202" in codes(snap(tool(properties={"q": {"type": "string"}}, required=["q"])))

    def test_mcp202_quiet_when_described(self) -> None:
        props = described_props(q="the query")
        assert "MCP202" not in codes(snap(tool(properties=props, required=["q"])))

    def test_mcp203_fires_without_constraint_note(self) -> None:
        t = tool(
            description="Add two integers together and gives the sum. Raises ValueError on bad input."
        )
        schema = dict(t.input_schema or {}, additionalProperties=False)
        assert "MCP203" in codes(snap(t.model_copy(update={"input_schema": schema})))

    def test_mcp203_quiet_with_constraint_note(self) -> None:
        t = tool(description=f"{GOOD_DESC} Only accepts two integers.")
        schema = dict(t.input_schema or {}, additionalProperties=False)
        assert "MCP203" not in codes(snap(t.model_copy(update={"input_schema": schema})))

    def test_mcp204_fires_on_repetition(self) -> None:
        assert "MCP204" in codes(
            snap(tool(name="search_web", description="search web and return the results."))
        )

    def test_mcp204_quiet_on_good(self) -> None:
        assert "MCP204" not in codes(snap(tool()))

    def test_mcp205_fires_on_invalid_output(self) -> None:
        assert "MCP205" in codes(snap(tool(output_schema={"properties": {}})))

    def test_mcp205_quiet_without_output(self) -> None:
        assert "MCP205" not in codes(snap(tool()))


class TestSecurity:
    def test_mcp301_fires_without_safety(self) -> None:
        assert "MCP301" in codes(snap(tool(name="run_command", description="Runs any command.")))

    def test_mcp301_quiet_with_safety(self) -> None:
        desc = "Runs one allowlisted command in a sandbox."
        assert "MCP301" not in codes(snap(tool(name="run_command", description=desc)))

    def test_mcp302_fires_on_secret_param(self) -> None:
        props = described_props(api_key="your key")
        assert "MCP302" in codes(snap(tool(properties=props)))

    def test_mcp302_quiet_on_normal_param(self) -> None:
        props = described_props(query="the query")
        assert "MCP302" not in codes(snap(tool(properties=props)))

    def test_mcp303_fires_without_confirm(self) -> None:
        assert "MCP303" in codes(snap(tool(name="delete_record")))

    def test_mcp303_quiet_with_confirm(self) -> None:
        props = described_props(confirm="set true to proceed")
        assert "MCP303" not in codes(snap(tool(name="delete_record", properties=props)))


class TestTokens:
    def test_mcp401_fires_over_budget(self) -> None:
        assert "MCP401" in codes(snap(instructions="x" * 50_000))

    def test_mcp401_quiet_under_budget(self) -> None:
        assert "MCP401" not in codes(snap())


class TestRegistry:
    def test_all_15_rules_registered(self) -> None:
        assert len(all_rules()) == 15

    def test_unknown_code_raises(self) -> None:
        with pytest.raises(UnknownRuleError, match="MCP999"):
            resolve_rules(["MCP999"], None)

    def test_select_filters(self) -> None:
        assert [r.code for r in resolve_rules(["MCP101", "MCP301"], None)] == ["MCP101", "MCP301"]

    def test_ignore_filters(self) -> None:
        assert all(r.code != "MCP101" for r in resolve_rules(None, ["MCP101"]))
