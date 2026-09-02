# Contributing to mcpgate

Thanks for helping make MCP servers better for the agents that use them!

## Getting started

```bash
git clone https://github.com/mcpgate/mcpgate
cd mcpgate
uv sync --all-extras     # install deps (dev + test extras)

uv run coverage run -m pytest   # tests (fully offline)
uv run coverage report          # coverage, gate at 90%
uv run ruff check .             # lint
uv run ruff format .            # format
uv run mypy src                 # strict type check
```

Requires Python 3.10–3.13 and [uv](https://docs.astral.sh/uv/).

## Project layout

| Module | Responsibility |
|---|---|
| `src/mcpgate/cli.py` | click app: `mcpgate lint \| doctor` |
| `src/mcpgate/client.py` | connect over in-memory/stdio/HTTP; snapshot definitions |
| `src/mcpgate/model.py` | pydantic models: `ToolInfo`, `Finding`, `ServerSnapshot`, … |
| `src/mcpgate/engine.py` | rule runner, text/json/sarif formatters, exit codes |
| `src/mcpgate/doctor.py` | health report |
| `src/mcpgate/testing/plugin.py` | pytest plugin (`mcp_server` fixture, `tool_contract`) |
| `src/mcpgate/rules/` | rule registry + rule modules |

## Adding a lint rule

Rule codes are grouped by prefix: `MCP1xx` descriptions, `MCP2xx` schemas,
`MCP3xx` security, `MCP4xx` token cost.

1. Write a small pure function over `ServerSnapshot` returning
   `(source, message-kwargs)` tuples, in the right `rules/*.py` module.
2. Register it with the `@rule("MCPxxx", "severity", "message template")` decorator
   from `rules/base.py`.
3. Add a positive and a negative test in `tests/test_rules.py` — one of each per
   rule, no exceptions.
4. If it is user-visible, add a row to the rule table in `README.md`.

## Ground rules

- **Runtime dependencies** are frozen at `mcp`, `click`, `pydantic` — anything else
  needs prior discussion in an issue.
- **Tests are offline.** Use the `mcp` SDK's in-memory transport; mark network
  tests with `@pytest.mark.network` (deselected by default).
- **Typing is strict.** No `# type: ignore` without a comment explaining why.
- **Commits** follow Conventional Commits (`feat:`, `fix:`, `docs:`, …).
- Every PR must keep `pytest`, `ruff` and `mypy src` green.

## Reporting bugs and security issues

Bugs and feature requests: open a GitHub issue using the templates.
Security vulnerabilities: **never** in a public issue — see
[SECURITY.md](.github/SECURITY.md).

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
