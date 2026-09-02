# AGENTS.md — mcpgate

This is the contribution contract for AI coding agents (and humans) working on `mcpgate`.
Read it fully before writing code. The build/spec source of truth is `PLAN.md`.

## Project overview

`mcpgate` is the automated quality gate for MCP (Model Context Protocol) servers —
"ruff + pytest for MCP." It lints tool/resource/prompt definitions that AI agents
consume, health-checks servers (`doctor`), and provides a pytest plugin for
contract-testing tools over the real protocol. It exists because vague tool
descriptions make agents misuse perfectly good code — a failure invisible to unit
tests (97.1% of MCP tool descriptions contain at least one quality defect).

## Non-negotiable technical constraints

- **Python ≥ 3.10**; CI matrix 3.10–3.13.
- **Layout:** `src/mcpgate/` src-layout. Build backend: `hatchling`. Env/deps: `uv`.
- **Runtime deps limited to:** `mcp`, `click`, `pydantic`. Adding any runtime
  dependency requires explicit discussion in the PR — no exceptions.
- **Typing:** full type hints; `mypy` strict must pass.
- **Lint:** `ruff` (standard aggressive ruleset). Never wemake-python-styleguide.
- **Tests:** fully offline, using the `mcp` SDK's in-memory transport. Any test that
  needs a network must be marked/skipped offline.
- **License:** MIT. All contributed code is MIT-licensed.

## Setup & commands

```bash
uv sync --all-extras     # install dev + optional deps
uv run pytest            # tests (with coverage)
uv run ruff check .      # lint
uv run ruff format .     # format
uv run mypy src          # types
uv build                 # wheel + sdist sanity check
```

## Architecture map

| Module | Responsibility |
|---|---|
| `src/mcpgate/cli.py` | click app: `mcpgate lint \| doctor`, exit codes 0/1/2 |
| `src/mcpgate/client.py` | connect via stdio command or HTTP URL using the `mcp` SDK; snapshot tool/resource/prompt definitions |
| `src/mcpgate/model.py` | normalized `ToolInfo`, `ResourceInfo`, `PromptInfo`, `Finding`, `ServerSnapshot` |
| `src/mcpgate/engine.py` | rule runner; text/json/sarif output; `--select/--ignore/--explain/--strict`; designed so a `--fix` hook can be added later without refactor |
| `src/mcpgate/doctor.py` | connectivity, handshake, protocol version, capability report, latency |
| `src/mcpgate/testing/` | pytest plugin (entry point `pytest11 = mcpgate.testing`): `mcp_server` fixture, `tool_contract` helper |
| `src/mcpgate/rules/` | rule registry + rule modules (see numbering scheme below) |

`tests/fixtures/bad_server.py` is a fixture MCP server that deliberately violates
every rule; it doubles as the source of README output examples.

## Conventions

### Rule code numbering

- `MCP1xx` — descriptions
- `MCP2xx` — schemas
- `MCP3xx` — security
- `MCP4xx` — tokens

### How to add a rule

1. Write a small **pure function** over `ServerSnapshot` returning `list[Finding]`
   in the appropriate `rules/*.py` module.
2. Register it with the decorator from `rules/base.py` (code, severity, message
   template). The registry self-accumulates; unknown codes in `--select/--ignore`
   must produce a clear CLI error.
3. Add a violating tool/resource to `tests/fixtures/bad_server.py`.
4. Add a **positive test** (rule fires) and a **negative test** (clean server does
   not fire) in `tests/test_rules.py`. One test per rule, no exceptions.
5. Update the rule table in `README.md`.

### Other conventions

- **Commits:** conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `ci:`).
- **Typing:** strict; no `# type: ignore` without a comment explaining why.
- **Comments:** only for constraints the code can't express; no narration.
- **Public API:** re-exports belong in `src/mcpgate/__init__.py`; keep the public
  surface small and documented.

## Testing policy

- Every rule: positive + negative test.
- All tests offline; in-memory transport only. `uvx mcp-server-fetch` end-to-end
  tests are marked and skipped when the network/tool is unavailable.
- Coverage gate: ≥90% on `src/mcpgate`, enforced in CI.
- Async MCP client calls use `pytest-asyncio`; plugin internals are wrapped so
  user tests stay sync-friendly.

## PR checklist

- [ ] `uv run pytest` green, coverage ≥90%
- [ ] `uv run ruff check .` and `uv run ruff format --check .` clean
- [ ] `uv run mypy src` clean
- [ ] New rule ⇒ registered + fixture entry + positive/negative tests + README rule table row
- [ ] No new runtime dependencies without prior discussion
- [ ] Conventional commit message
- [ ] README/docs updated if behavior or CLI surface changed
