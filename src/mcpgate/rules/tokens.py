"""MCP4xx — token-cost rules."""

from __future__ import annotations

import json

from mcpgate.model import ServerSnapshot
from mcpgate.rules.base import rule

CHARS_PER_TOKEN = 4
SERVER_BUDGET_TOKENS = 10_000


def estimate_tokens(snapshot: ServerSnapshot) -> int:
    chars = len(snapshot.instructions)
    for tool in snapshot.tools:
        chars += len(tool.name) + len(tool.description)
        chars += len(_schema_text(tool.input_schema)) + len(_schema_text(tool.output_schema))
    chars += sum(len(r.uri) + len(r.description) for r in snapshot.resources)
    chars += sum(len(p.name) + len(p.description) for p in snapshot.prompts)
    return chars // CHARS_PER_TOKEN


def _schema_text(schema: object) -> str:
    return json.dumps(schema) if schema else ""


@rule("MCP401", "info", "Server definition snapshot costs ~{tokens} tokens (budget {budget})")
def check_server_token_cost(snapshot: ServerSnapshot) -> list[tuple[str, dict[str, object]]]:
    tokens = estimate_tokens(snapshot)
    if tokens <= SERVER_BUDGET_TOKENS:
        return []
    return [("server", {"tokens": tokens, "budget": SERVER_BUDGET_TOKENS})]
