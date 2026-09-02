"""Rule registry. Importing this package registers all built-in rules."""

from __future__ import annotations

# Import for registration side effects.
from mcpgate.rules import descriptions, schemas, security, tokens  # noqa: F401
from mcpgate.rules.base import Rule, UnknownRuleError, all_rules, resolve_rules, rule

__all__ = ["Rule", "UnknownRuleError", "all_rules", "resolve_rules", "rule"]
