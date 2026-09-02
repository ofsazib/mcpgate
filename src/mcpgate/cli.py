"""mcpgate command-line interface: `lint` and `doctor`."""

from __future__ import annotations

import json
import sys
from typing import Any

import click

from mcpgate import __version__
from mcpgate.client import snapshot_sync
from mcpgate.doctor import health_report, print_report
from mcpgate.engine import exit_code, format_json, format_sarif, format_text, get_rule, run_rules
from mcpgate.rules import UnknownRuleError

_DEFAULT_TIMEOUT = 30.0


@click.group()
@click.version_option(__version__, prog_name="mcpgate")
def cli() -> None:
    """mcpgate — automated quality gate for MCP servers."""


@cli.command()
@click.argument("target", required=False)
@click.option("--format", "fmt", type=click.Choice(["text", "json", "sarif"]), default="text")
@click.option("--select", multiple=True, help="Rule codes to run (repeatable).")
@click.option("--ignore", multiple=True, help="Rule codes to skip (repeatable).")
@click.option(
    "--explain", "explain_code", default=None, metavar="CODE", help="Explain a rule code and exit."
)
@click.option("--strict", is_flag=True, help="Treat warnings as failures.")
@click.option("--timeout", type=float, default=_DEFAULT_TIMEOUT, show_default=True)
def lint(
    target: str | None,
    fmt: str,
    select: tuple[str, ...],
    ignore: tuple[str, ...],
    explain_code: str | None,
    strict: bool,
    timeout: float,
) -> None:
    """Lint an MCP server's tool/resource/prompt definitions.

    TARGET is a server command string (stdio), an http(s) URL, or omitted
    when --explain is used.
    """
    if explain_code:
        _explain(explain_code)
        return
    if not target:
        raise click.UsageError("TARGET is required unless --explain is used")

    try:
        snapshot = snapshot_sync(target, timeout=timeout)
        findings = run_rules(snapshot, select=list(select), ignore=list(ignore))
    except UnknownRuleError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(2)
    except Exception as exc:
        click.echo(f"error: failed to connect to {target!r}: {exc}", err=True)
        sys.exit(2)

    if fmt == "json":
        format_json(findings)
    elif fmt == "sarif":
        format_sarif(findings)
    else:
        format_text(findings)
    sys.exit(exit_code(findings, strict=strict))


def _explain(code: str) -> None:
    rule = get_rule(code)
    if rule is None:
        click.echo(f"error: unknown rule code {code!r}", err=True)
        sys.exit(2)
    click.echo(f"{rule.code} [{rule.severity}] {rule.message}")
    click.echo(f"\nUse --ignore {rule.code} to skip this rule.")


@cli.command()
@click.argument("target")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--timeout", type=float, default=_DEFAULT_TIMEOUT, show_default=True)
def doctor(target: str, fmt: str, timeout: float) -> None:
    """Health-check an MCP server: handshake, capabilities, latency."""
    try:
        report: dict[str, Any] = health_report(target, timeout=timeout)
    except Exception as exc:
        click.echo(f"error: server {target!r} unreachable: {exc}", err=True)
        sys.exit(2)
    if fmt == "json":
        click.echo(json.dumps(report, indent=2))
    else:
        print_report(report, sys.stdout)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
