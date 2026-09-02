# mcpgate

> Automated quality gate for MCP servers — **ruff + pytest for MCP**.

[![CI](https://github.com/ofsazib/mcpgate/actions/workflows/ci.yml/badge.svg)](https://github.com/ofsazib/mcpgate/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/mcpgate)](https://pypi.org/project/mcp-gatekeeper/)
[![Python](https://img.shields.io/pypi/pyversions/mcpgate)](https://pypi.org/project/mcp-gatekeeper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Coverage](https://codecov.io/gh/ofsazib/mcpgate/branch/main/graph/badge.svg)](https://codecov.io/gh/ofsazib/mcpgate)

## The problem

When an MCP tool description is vague, the AI agent misuses the tool — even though
the code behind it is perfect. This failure is invisible to unit tests because it
happens at the AI-interpretation layer. Research documents the scale:

- An arXiv study of 103 major MCP servers (856 tools) found tool descriptions
  systematically "smelly and costly" ([arXiv:2602.14878](https://arxiv.org/abs/2602.14878)).
- An AWS-led study found **97.1% of MCP tool descriptions contain at least one
  quality defect**.

`mcpgate` catches these defects before agents hit them in production. It speaks the
real protocol, so it works with any server — FastMCP, the official Python SDK, or
TypeScript servers — over stdio or HTTP.

## Quickstart

```bash
uv tool install mcp-gatekeeper    # or: pip install mcp-gatekeeper

mcpgate lint "uvx mcp-server-fetch"
mcpgate doctor "uvx mcp-server-fetch"
```

Exit codes are CI-friendly: `0` clean, `1` findings (fail the build), `2` connection
or protocol error.

## Example output

```text
    warning  MCP101  Tool `delete_record`: description too short (7 words; minimum 8)  src: tools/delete_record
    warning  MCP105  Tool `delete_record`: description does not state error/return behavior  src: tools/delete_record
    warning  MCP303  Tool `delete_record`: destructive operation without a confirmation parameter  src: tools/delete_record
    error    MCP301  Tool `run_command`: suggests command execution without a safety note  src: tools/run_command
    warning  MCP101  Tool `run_command`: description too short (7 words; minimum 8)  src: tools/run_command
    warning  MCP105  Tool `run_command`: description does not state error/return behavior  src: tools/run_command
    warning  MCP101  Tool `search`: description too short (2 words; minimum 8)  src: tools/search
    warning  MCP105  Tool `search`: description does not state error/return behavior  src: tools/search
    info     MCP204  Tool `search`: description repeats the tool name (wasted tokens)  src: tools/search
    ———
    found 9 problems (1 errors, 7 warnings)
    run `mcpgate lint --explain CODE` for details
```

Formats: `--format text|json|sarif` (SARIF plugs into GitHub code scanning).
Filter with `--select MCP3xx --ignore MCP401`; inspect a rule with
`--explain MCP101`; fail on warnings with `--strict`.

## Rules (v0.1)

| Code | Severity | What it checks |
|------|----------|----------------|
| MCP101 | warning | Tool description missing or shorter than 8 words |
| MCP102 | warning | Description is vague ("does stuff", "handles things", "various") |
| MCP103 | warning | Description just restates the tool name |
| MCP104 | warning | Tools with 2+ parameters where parameters lack descriptions |
| MCP105 | warning | Description does not state error/return behavior |
| MCP106 | warning | Description longer than 1024 chars (token bloat) |
| MCP201 | error | Input schema missing or not a JSON object schema |
| MCP202 | warning | Required parameter is not described |
| MCP203 | info | `additionalProperties: false` schema but description states no constraints |
| MCP204 | info | Description repeats the tool name (wasted tokens) |
| MCP205 | error | Declared output schema is invalid |
| MCP301 | error | Command-execution tool without a safety note |
| MCP302 | warning | Parameter name looks like a secret (`api_key`, `token`, …) |
| MCP303 | warning | Destructive operation without a confirmation parameter |
| MCP401 | info | Full definition snapshot costs more than ~10k tokens |

## Pytest plugin

Install with the `test` extra, then contract-test your tools over the real protocol:

```bash
pip install "mcp-gatekeeper[test]"
```

```python
import pytest
from my_server import mcp  # your FastMCP / MCP server object


@pytest.mark.parametrize("mcp_server", [mcp], indirect=True)
def test_search(mcp_server):
    result = mcp_server.call_tool("search", {"query": "hello"})
    assert result.is_error is False


@pytest.mark.parametrize("mcp_server", [mcp], indirect=True)
def test_contract(mcp_server):
    mcp_server.tool_contract("search")
    # asserts: described, valid object schema, described required params,
    # and the error path returns is_error instead of crashing
```

Or point a whole suite at one server: `pytest --mcp-server "uvx mcp-server-fetch"`.
Works in-memory for server objects (fully offline), stdio/HTTP for commands and URLs.

## How it compares

| | MCP Inspector | mcplint-cli | mcp-doctor | **mcpgate** |
|---|---|---|---|---|
| Purpose | interactive debugger | description lint | diagnostics | unified quality gate |
| CLI-first, CI exit codes | ✗ | ✓ | partial | ✓ (0/1/2) |
| Definition lint rules | ✗ | ✓ | ✗ | ✓ (15 rules) |
| Doctor / health check | ✓ | ✗ | ✓ | ✓ |
| pytest plugin | ✗ | ✗ | ✗ | ✓ |
| JSON + SARIF output | ✗ | ✗ | ✗ | ✓ |
| Framework-agnostic (speaks MCP) | ✓ | ✓ | ✓ | ✓ |

## Roadmap

- **v0.2** — `--fix`: LLM-assisted rewriting of weak descriptions (the engine already
  carries the context needed per finding)
- Declarative YAML test suites and `--baseline` files
- Custom user rule plugins and a pre-commit hook package
- GitHub Action and official MCP servers registry integration

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). MIT licensed — see [LICENSE](LICENSE).
