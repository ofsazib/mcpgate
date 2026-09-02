# Project Plan: `mcpgate` — Quality & Testing Toolkit for MCP Servers

> **For the AI agent executing this plan:** This document is self-contained. Build the
> project described below: generate `AGENTS.md`, `README.md`, the full package source,
> tests, and CI. Do not skip sections labeled "REQUIRED".

---

## 1. Mission Statement

`mcpgate` is the automated quality gate for MCP (Model Context Protocol) servers —
"**ruff + pytest for MCP**." It lints the tool/resource/prompt definitions that AI
agents consume, health-checks servers, and lets developers contract-test their tools
through the real protocol.

**Core insight this package is built on:** when an MCP tool description is vague, the
AI agent misuses the tool even though the code behind it is perfect. This failure is
invisible to unit tests because it happens at the AI-interpretation layer. Research
documents this is a mass problem: an arXiv study of 103 major MCP servers (856 tools)
found tool descriptions systematically "smelly and costly" (arXiv:2602.14878), and an
AWS-led study found **97.1% of MCP tool descriptions contain at least one quality
defect**. `mcpgate` catches these defects before agents hit them in production.

**Positioning:** first-party tools (MCP Inspector) are interactive debuggers;
existing third-party tools (mcplint-cli, mcp-doctor, pytest-mcp, mcp-eval) are small
and single-feature. `mcpgate` is the unified, CI-first, framework-agnostic standard:
lint + doctor + pytest plugin + JSON/SARIF output, cited against published research.

**Target users:**
- Developers shipping production MCP servers (FastMCP, official Python SDK, TypeScript servers via stdio/HTTP)
- Platform/enterprise teams vetting third-party MCP servers before wiring them into agents
- Solo developers who want pytest-native testing of their MCP tools

---

## 2. Deliverables

1. **Installable PyPI package** `mcpgate` with console script `mcpgate`.
2. **`README.md`** — problem statement (cite the two studies above), 30-second quickstart,
   rule table, output examples, comparison table, roadmap.
3. **`AGENTS.md`** — contribution contract for AI coding agents (see §7 for required content).
4. Full test suite (≥90% coverage of `mcpgate` code), CI workflow, and docs.

---

## 3. Technical Requirements (REQUIRED — do not deviate)

- **Python ≥ 3.10**, support 3.10–3.13 in CI matrix.
- **Pure Python.** Runtime dependencies kept minimal: `mcp` (official Model Context
  Protocol Python SDK — provides client + in-memory transport), `click` (CLI),
  `pydantic` (models — already transitive via `mcp`). Optional extra: `pytest` for the plugin.
- **Build backend:** `hatchling`. **Dependency/env management:** `uv`
  (`uv`-style `pyproject.toml`, lockfile committed).
- **Layout:** `src/mcpgate/` src-layout.
- **Typing:** full type hints, `mypy` strict in CI.
- **Lint:** `ruff` (aggressive but standard ruleset — do NOT use wemake-python-styleguide).
- **Tests:** `pytest` + `pytest-cov` + `pytest-asyncio` (MCP client calls are async).
  Tests must run offline using the official SDK's **in-memory transport** — no network.
- **License:** MIT.
- **Pre-commit:** ruff-format, ruff, mypy (optional-stage).
- **CI:** GitHub Actions — uv install, ruff, mypy, pytest with coverage gate,
  build check (`uv build`), on 3.10/3.11/3.12/3.13.

### Repository layout to generate

```
mcpgate/
├── AGENTS.md
├── README.md
├── LICENSE                       # MIT
├── pyproject.toml                # hatchling, console script, optional pytest extra
├── uv.lock
├── .gitignore
├── .pre-commit-config.yaml
├── .github/workflows/ci.yml
├── src/mcpgate/
│   ├── __init__.py               # version, public re-exports
│   ├── cli.py                    # click app: `mcpgate lint | doctor`
│   ├── client.py                 # connect to servers (stdio & streamable HTTP) via mcp SDK;
│   │                             #   snapshot tool/resource/prompt definitions
│   ├── model.py                  # normalized ToolInfo, ResourceInfo, PromptInfo, Finding, ServerSnapshot
│   ├── engine.py                 # rule runner: run rules, ruff-style text output,
│   │                             #   --format text|json|sarif, exit codes (0 clean / 1 findings / 2 error)
│   ├── doctor.py                 # connectivity, handshake, protocol version, capability report
│   ├── testing/
│   │   ├── __init__.py           # pytest plugin registration (entry point: pytest11 = mcpgate.testing)
│   │   └── plugin.py             # `mcp_server` fixture, `tool_contract` helper
│   └── rules/
│       ├── __init__.py           # rule registry (dataclass + decorator-based registration)
│       ├── base.py               # Rule protocol: code, severity, message template, check(snapshot)->list[Finding]
│       ├── descriptions.py       # MCP1xx rules
│       ├── schemas.py            # MCP2xx rules
│       ├── security.py           # MCP3xx rules
│       └── tokens.py             # MCP4xx rules
├── tests/
│   ├── conftest.py               # fixture MCP server (built with mcp SDK/FastMCP API) with
│   │                             #   deliberately good and bad tools for rule testing
│   ├── fixtures/bad_server.py    # server violating every rule (used in tests + README examples)
│   ├── test_client.py
│   ├── test_engine.py
│   ├── test_cli.py               # click CliRunner, offline, in-memory transport
│   ├── test_rules.py             # one test per rule
│   └── test_plugin.py
├── examples/
│   ├── good_server.py            # clean example server
│   └── bad_server.py             # example showing lint output for docs
└── docs/                         # optional at v0.1; mkdocs-material scaffold ok
```

---

## 4. Features to Implement

### 4.1 `mcpgate lint <server-command-or-url>` (core feature)

Connects to **any** MCP server (spawned via stdio command string, or HTTP URL), pulls
its full definition snapshot, and runs all rules. Works regardless of framework
(FastMCP, official SDK, TS servers) because it speaks the protocol.

Output: ruff-style diagnostics.

```text
mcpgate lint "uvx mcp-server-fetch"
warning  MCP101  Tool `search`: description too short (3 words; minimum 8)  src: tools/search
warning  MCP201  Tool `search`: parameter `query` missing description        src: tools/search
error    MCP301  Tool `run_cmd`: executes shell commands without declaring destructive side effects
———
found 12 problems (2 errors, 10 warnings)
run `mcpgate lint --explain MCP101` for details
```

Flags: `--format text|json|sarif`, `--select`/`--ignore` (rule codes),
`--explain CODE`, `--strict` (warnings become exit-code failures), `--timeout`.
Exit codes: `0` = clean, `1` = findings (fail CI), `2` = connection/protocol error.

### 4.2 Lint rules — v0.1 set (REQUIRED minimum: these 15)

Codes `MCP###`; severity `error`/`warning`/`info`.

**Descriptions (MCP1xx) — port the arXiv quality rubric:**
- `MCP101` description too short (< 8 words) or missing
- `MCP102` description too vague: contains vague verbs without object ("does stuff", "handles things", "various")
- `MCP103` description is a bare name-echo (description ≈ function name restated)
- `MCP104` tool has > 1 parameters but parameter descriptions missing
- `MCP105` description doesn't state error/failure behavior for tools that return results (warning)
- `MCP106` description excessively long (> 1024 chars — token bloat)

**Schemas (MCP2xx):**
- `MCP201` input schema invalid JSON Schema or missing `type: object`
- `MCP202` required parameter not described
- `MCP203` schema declares properties with `additionalProperties: false` but tool description doesn't mention constraints (info)
- `MCP204` duplicate meaning between tool name and description (wasted tokens)
- `MCP205` output schema (if declared) invalid

**Security (MCP3xx):**
- `MCP301` tool name/description suggests shell/exec/command execution without a safety note
- `MCP302` parameter names suggesting secrets (password, token, api_key, secret) — flag for review (warning)
- `MCP303` destructive verbs (delete, drop, remove, purge) without confirmation/flag parameter (warning)

**Tokens (MCP4xx):**
- `MCP401` full snapshot cost estimate: report total approximate token count of all
  tool definitions; warn above 10k tokens for a single server (info; never fails by default)

Each rule is a small pure function over the snapshot — easy to test and extend.
Implement a registry so rules self-register by decorator; unknown rule codes in
`--select/--ignore` produce a clear error.

### 4.3 `mcpgate doctor <server-command-or-url>`

Human-readable health report: connects, completes handshake, prints protocol version
negotiated, server name/version from `initialize`, capability list, tool/resource/prompt
counts, and latency. Exit 0 healthy / 2 unreachable. `--format json` for scripting.

### 4.4 Pytest plugin

Entry point group `pytest11` named `mcpgate.testing`. Provides:

```python
def test_search(mcp_server):          # fixture: takes an MCP server object or command
    result = mcp_server.call_tool("search", {"query": "hello"})
    assert result.is_error is False

def test_contract(mcp_server):
    mcp_server.tool_contract("search")  # asserts: callable, schema valid, described params,
                                        # result well-formed, error path returns is_error not crash
```

Implementation: in-memory transport via the `mcp` SDK when given a server object;
stdio/HTTP when given a command/URL. Async internals wrapped so tests stay sync-friendly.

### 4.5 `mcpgate --version` and sensible `--help` for every command.

---

## 5. Explicitly Out of Scope for v0.1 (do NOT build now)

- LLM-powered auto-fix of descriptions (planned v0.2 — the killer differentiator; design
  `engine.py` so a `--fix` hook can be added without refactor)
- Declarative YAML test suites; `--baseline` files; custom user rule plugins;
  pre-commit hook package; GitHub Action marketplace entry (roadmap items only)

## 6. README.md — required sections

1. One-line tagline + badges (CI, PyPI, Python versions, license, codecov)
2. **The problem** — with the two research citations (arXiv:2602.14878; 97.1% defect study)
3. 30-second quickstart (install with uv/pip; lint a real popular server like `mcp-server-fetch`)
4. Example output block (from `examples/bad_server.py`)
5. Full rule table (code, severity, what it checks)
6. Pytest plugin example
7. Comparison table vs MCP Inspector / mcplint-cli / mcp-doctor / pytest-mcp (honest)
8. Roadmap (v0.2 auto-fix, YAML suites, baselines, plugin API)
9. Contributing + AGENTS.md pointer

## 7. AGENTS.md — required content

- Project overview in 3 sentences (§1) and the non-negotiable technical constraints (§3)
- Setup: `uv sync --all-extras`, run tests `uv run pytest`, lint `uv run ruff check .`,
  types `uv run mypy src`
- Architecture map: which module does what (mirror §3 layout with one-line responsibilities)
- Conventions: rule code numbering scheme (MCP1xx descriptions, MCP2xx schemas, MCP3xx
  security, MCP4xx tokens); how to add a rule (write pure function, register decorator,
  add fixture-violating server entry, add test); commit style (conventional commits);
  typing strictness; "no runtime deps beyond mcp/click/pydantic without discussion"
- Testing policy: every rule needs a positive and negative test; tests offline only
- PR checklist

## 8. Build Order for the Implementing Agent

1. Scaffold repo (layout, pyproject, uv lock, CI, AGENTS.md, README stub) → verify `uv sync` + `uv run pytest` (empty) green
2. `model.py` + `client.py`: connect to in-memory and stdio servers; snapshot definitions. Test against a fixture server and one real server (`uvx mcp-server-fetch`) behind a network-skipped test
3. `rules/base.py` + registry + `descriptions.py` (MCP1xx) with tests
4. `schemas.py`, `security.py`, `tokens.py` with tests
5. `engine.py` (formats, exit codes) + `cli.py` (`lint`, `doctor`) with CliRunner tests
6. Pytest plugin + tests
7. `examples/good_server.py` + `bad_server.py`; generate real output for README
8. README final; coverage gate ≥90%; `uv build` sanity; tag `v0.1.0`

## 9. Definition of Done

- [ ] `uv run pytest` green with ≥90% coverage, fully offline
- [ ] `uv run ruff check .` and `uv run mypy src` clean
- [ ] `mcpgate lint` produces correct output and exit codes against `examples/bad_server.py`
- [ ] `mcpgate lint "uvx mcp-server-fetch"` works end-to-end
- [ ] Pytest plugin fixture `mcp_server` usable in a fresh test file without extra config
- [ ] README and AGENTS.md complete per §6/§7
- [ ] `uv build` produces a valid wheel + sdist
