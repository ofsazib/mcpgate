# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-02

### Added
- feat: automated release script with semver bump decision
- feat: pytest plugin with mcp_server fixture and tool_contract
- feat: lint/doctor CLI with text, json and sarif output
- feat: 15 lint rules with decorator registry (MCP101-MCP401)
- feat: protocol client and normalized snapshot models

### Fixed
- fix: rename PyPI distribution to mcp-gatekeeper
- fix: rename PyPI package to mcp-gate (mcpgate is taken)
- fix: snapshot servers that lack resources/prompts capabilities

### Changed
- docs: drop AGENTS.md link from README
- docs: self-contained public CONTRIBUTING guide
- docs: full README with rule table, comparison and examples; coverage gate at 90%

### Other
- chore: keep AI and planning docs untracked
- chore: scaffold package, OSS files, CI and release workflows

## [0.1.0] - 2026-09-02

### Added
- `mcpgate lint` with 15 rules (MCP101–MCP401), text/json/sarif output, CI-friendly exit codes.
- `mcpgate doctor` health report.
- Pytest plugin: `mcp_server` fixture + `tool_contract` helper.
