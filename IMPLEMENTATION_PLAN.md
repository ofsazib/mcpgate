# Implementation Plan — `mcpgate` v0.1.0 (OSS PyPI Package)

> Final, executable plan. Supersedes the build-order details in `PLAN.md` §8 and
> adds everything a public OSS PyPI package needs on day one. `PLAN.md` remains the
> spec for features, rules, and constraints; this file is the sequenced build plan
> with acceptance criteria and the release/publishing pipeline.

## 0. OSS framing — what "treat it as an OSS PyPI package" adds

Beyond the core code (spec in `PLAN.md` §3–§4), a public package ships with:

| Concern | Artifact |
|---|---|
| Licensing | `LICENSE` (MIT, copyright "mcpgate contributors") |
| Community | `CONTRIBUTING.md` (thin wrapper pointing to `AGENTS.md`), `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1), `.github/SECURITY.md`, `.github/ISSUE_TEMPLATE/` (bug report + feature request, YAML forms) |
| Changelog | `CHANGELOG.md` (Keep a Changelog format, semver) |
| Packaging metadata | Complete `pyproject.toml`: classifiers, `readme`, `license`, `license-files`, `urls` (Homepage/Changelog/Issues), `requires-python = ">=3.10"`, `[project.scripts] mcpgate = "mcpgate.cli:main"`, `[project.entry-points.pytest11] mcpgate = "mcpgate.testing.plugin"` |
| PyPI presence | README with badges (CI, PyPI version, Python versions, license, codecov), long_description rendering check in CI |
| Publishing | GitHub Actions `release.yml`: tag-push trigger → `uv build` → `twine check` → **PyPI Trusted Publishing** (OIDC, no API tokens) via `pypa/gh-action-pypi-publish` |
| Supply-chain hygiene | `.github/workflows/ci.yml` pinned to commit SHAs; optional `zizmor`/`pip-audit` step |
| Discoverability | GitHub topics (`mcp`, `model-context-protocol`, `lint`, `ai-agents`, `pytest`, `quality-gate`), pinned issue or Discussions optional |

Non-goals for v0.1 (unchanged from `PLAN.md` §5): `--fix` LLM auto-fix, YAML test
suites, baselines, custom rule plugins, pre-commit hook package, GitHub Action.

## 1. Phase 1 — Scaffold & OSS shell

Create repository layout exactly per `PLAN.md` §3, plus OSS files:

1. `git init`; src-layout dirs; `.gitignore` (uv/pytest/mypy/coverage/dist).
2. `pyproject.toml` (hatchling, deps `mcp`/`click`/`pydantic`, extras
   `test = [pytest, pytest-cov, pytest-asyncio]`, dev group: ruff, mypy,
   pre-commit; all metadata listed in §0 above).
3. `LICENSE`, `CHANGELOG.md` (`## [0.1.0] - unreleased`), `CONTRIBUTING.md`,
   `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue templates.
4. `AGENTS.md` (✅ already created — keep in sync with this file).
5. `.pre-commit-config.yaml` (ruff-format, ruff, mypy optional-stage).
6. `.github/workflows/ci.yml`: matrix 3.10–3.13; uv sync → ruff → mypy →
   pytest (coverage ≥90% gate) → `uv build` + twine check.
7. `README.md` stub with badges and the §6 section skeleton.
8. `README.md` "Contributing" section points to `CONTRIBUTING.md` → `AGENTS.md`.

**Exit criteria:** `uv sync --all-extras`, `uv run pytest` (empty suite), `uv run
ruff check .`, `uv run mypy src`, `uv build` all green.

## 2. Phase 2 — Client & models

1. `model.py`: pydantic models `ToolInfo`, `ResourceInfo`, `PromptInfo`,
   `Finding` (code, severity, message, location), `ServerSnapshot`.
2. `client.py`: async connect via `mcp` SDK — stdio command string (spawned
   subprocess) and streamable HTTP URL; snapshot all definitions; timeout
   handling. Public sync wrapper for the pytest plugin.
3. Tests: fixture server over in-memory transport (`tests/conftest.py`);
   network test against `uvx mcp-server-fetch` marked `@pytest.mark.network`,
   skipped offline.

**Exit criteria:** snapshot of the fixture server matches its definitions
exactly; offline suite stays green.

## 3. Phase 3 — Rules (15 rules, MCP101–MCP401)

1. `rules/base.py`: `Rule` protocol + decorator registry.
2. `rules/descriptions.py` (MCP101–106), `schemas.py` (MCP201–205),
   `security.py` (MCP301–303), `tokens.py` (MCP401) — exact behavior per
   `PLAN.md` §4.2.
3. Extend `tests/fixtures/bad_server.py` so every rule fires on it.
4. `tests/test_rules.py`: positive + negative test per rule.

**Exit criteria:** one test per rule, all passing; `--select/--ignore` with an
unknown code raises a clear error (tested).

## 4. Phase 4 — Engine, doctor, CLI

1. `engine.py`: run rules over snapshot; formatters `text` (ruff-style),
   `json`, `sarif`; exit codes 0/1/2; `--strict`; leave a clean seam for the
   future `--fix` hook (rule findings carry enough context to auto-fix later).
2. `doctor.py`: handshake, negotiated protocol version, server name/version,
   capabilities, counts, latency; `--format json`.
3. `cli.py`: click app `lint`/`doctor` with `--help`, `--version`; wire
   formatters and exit codes.
4. `tests/test_engine.py`, `tests/test_cli.py` (click `CliRunner`, in-memory
   transport, offline).

**Exit criteria:** `mcpgate lint` against `examples/bad_server.py` produces
output and exit code matching `PLAN.md` §4.1; `doctor` exits 0 healthy / 2
unreachable (tested with a failing command).

## 5. Phase 5 — Pytest plugin

1. `testing/plugin.py`: `pytest11` entry point; `mcp_server` fixture accepting a
   server object (in-memory) or command/URL (stdio/HTTP); `tool_contract()`
   asserting callable + valid schema + described params + well-formed result +
   `is_error` (not crash) on error path.
2. `tests/test_plugin.py`: plugin loads in a fresh pytest run via
   `pytester`/subprocess with no extra user config.

**Exit criteria:** a test file using only `mcp_server` passes without any
conftest or ini config.

## 6. Phase 6 — Docs, examples, release

1. `examples/good_server.py`, `examples/bad_server.py`; capture real CLI output
   for the README.
2. Finalize `README.md` per `PLAN.md` §6 (badges, problem + citations,
   quickstart, output, rule table, plugin example, honest comparison table,
   roadmap, contributing pointer).
3. Coverage gate ≥90% verified; `uv build` produces wheel + sdist; `twine check`
   passes.
4. `release.yml`: on tag `v*` → build → trusted-publish to PyPI.
5. Tag `v0.1.0`, fill in `CHANGELOG.md` release date, publish.

**Exit criteria (`PLAN.md` §9 + OSS):**

- [ ] Offline `uv run pytest` green, coverage ≥90%
- [ ] `ruff` + `mypy src` clean on all matrix versions
- [ ] `mcpgate lint "uvx mcp-server-fetch"` works end-to-end
- [ ] Plugin usable in a fresh project after `pip install mcpgate`
- [ ] README, AGENTS.md, CONTRIBUTING, COC, SECURITY, CHANGELOG complete
- [ ] `uv build` + `twine check` valid; CI green on the release tag
- [ ] PyPI page renders correctly (description, classifiers, links)
