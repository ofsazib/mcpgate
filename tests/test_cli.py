"""CLI tests via click's CliRunner, offline over in-memory/stdio transports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from click.testing import CliRunner

from mcpgate.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"
GOOD = f"{sys.executable} {Path('examples/good_server.py').resolve()}"
BAD = f"{sys.executable} {FIXTURES / 'bad_server.py'}"


def test_version() -> None:
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "mcpgate" in result.output


def test_lint_bad_server_exit_1() -> None:
    result = CliRunner().invoke(cli, ["lint", BAD])
    assert result.exit_code == 1
    assert "MCP101" in result.output
    assert "problems" in result.output


def test_lint_json_format() -> None:
    result = CliRunner().invoke(cli, ["lint", BAD, "--format", "json"])
    assert result.exit_code == 1
    findings = json.loads(result.output)
    assert findings
    assert {"code", "severity", "message", "source"} <= findings[0].keys()


def test_lint_sarif_format() -> None:
    result = CliRunner().invoke(cli, ["lint", BAD, "--format", "sarif"])
    assert result.exit_code == 1
    sarif = json.loads(result.output)
    assert sarif["runs"][0]["tool"]["driver"]["name"] == "mcpgate"


def test_lint_good_server_exit_0() -> None:
    result = CliRunner().invoke(cli, ["lint", GOOD])
    assert result.exit_code == 0, result.output


def test_lint_select_unknown_code_exit_2() -> None:
    result = CliRunner().invoke(cli, ["lint", BAD, "--select", "MCP999"])
    assert result.exit_code == 2
    assert "unknown rule code" in result.output


def test_lint_select_limits_rules() -> None:
    result = CliRunner().invoke(cli, ["lint", BAD, "--select", "MCP101"])
    assert result.exit_code == 1
    assert "MCP102" not in result.output


def test_lint_unreachable_target_exit_2() -> None:
    result = CliRunner().invoke(
        cli, ["lint", "definitely-not-a-real-command-xyz", "--timeout", "5"]
    )
    assert result.exit_code == 2


def test_explain() -> None:
    result = CliRunner().invoke(cli, ["lint", "--explain", "MCP101"])
    assert result.exit_code == 0
    assert "MCP101" in result.output
    assert "warning" in result.output


def test_explain_unknown_exit_2() -> None:
    result = CliRunner().invoke(cli, ["lint", "--explain", "MCP999"])
    assert result.exit_code == 2


def test_lint_missing_target_exit_error() -> None:
    result = CliRunner().invoke(cli, ["lint"])
    assert result.exit_code != 0


def test_doctor_healthy_exit_0() -> None:
    result = CliRunner().invoke(cli, ["doctor", GOOD])
    assert result.exit_code == 0, result.output
    assert "healthy" in result.output


def test_doctor_json() -> None:
    result = CliRunner().invoke(cli, ["doctor", GOOD, "--format", "json"])
    assert result.exit_code == 0
    report = json.loads(result.output)
    assert report["healthy"] is True
    assert report["server_name"] == "example-good-server"


def test_doctor_unreachable_exit_2() -> None:
    result = CliRunner().invoke(
        cli, ["doctor", "definitely-not-a-real-command-xyz", "--timeout", "5"]
    )
    assert result.exit_code == 2
