"""Rule runner and output formatters (text/json/sarif) with CI exit codes."""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from mcpgate.model import Finding, ServerSnapshot
from mcpgate.rules import Rule, all_rules, resolve_rules

_SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


def run_rules(
    snapshot: ServerSnapshot,
    select: list[str] | None = None,
    ignore: list[str] | None = None,
) -> list[Finding]:
    """Run the selected rules over a snapshot and return sorted findings."""
    findings: list[Finding] = []
    for r in resolve_rules(select, ignore):
        for source, kwargs in r.check(snapshot):
            findings.append(
                Finding(
                    code=r.code,
                    severity=r.severity,
                    message=r.message.format(**kwargs),
                    source=source,
                )
            )
    findings.sort(key=lambda f: (f.source, _SEVERITY_ORDER.get(f.severity, 9), f.code))
    return findings


def exit_code(findings: list[Finding], strict: bool = False) -> int:
    """0 clean, 1 findings (warnings count under --strict)."""
    if not findings:
        return 0
    if strict:
        return 1
    return 0 if all(f.severity == "info" for f in findings) else 1


def format_text(findings: list[Finding], stream: TextIO | None = None) -> None:
    if stream is None:
        stream = sys.stdout
    for f in findings:
        stream.write(f"{f.severity:<8} {f.code}  {f.message}  src: {f.source}\n")
    if findings:
        errors = sum(1 for f in findings if f.severity == "error")
        warnings = sum(1 for f in findings if f.severity == "warning")
        stream.write(
            f"———\nfound {len(findings)} problems ({errors} errors, {warnings} warnings)\n"
        )
        stream.write("run `mcpgate lint --explain CODE` for details\n")


def format_json(findings: list[Finding], stream: TextIO | None = None) -> None:
    if stream is None:
        stream = sys.stdout
    json.dump([f.model_dump() for f in findings], stream, indent=2)
    stream.write("\n")


def format_sarif(findings: list[Finding], stream: TextIO | None = None) -> None:
    if stream is None:
        stream = sys.stdout
    rules = all_rules()
    sarif: dict[str, Any] = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "mcpgate",
                        "informationUri": "https://github.com/mcpgate/mcpgate",
                        "rules": [
                            {
                                "id": r.code,
                                "shortDescription": {"text": r.message},
                                "defaultConfiguration": {"level": r.severity},
                            }
                            for r in rules
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": f.code,
                        "level": "note" if f.severity == "info" else f.severity,
                        "message": {"text": f.message},
                        "locations": [
                            {"physicalLocation": {"artifactLocation": {"uri": f"mcp://{f.source}"}}}
                        ],
                    }
                    for f in findings
                ],
            }
        ],
    }
    json.dump(sarif, stream, indent=2)
    stream.write("\n")


def get_rule(code: str) -> Rule | None:
    for r in all_rules():
        if r.code == code:
            return r
    return None
