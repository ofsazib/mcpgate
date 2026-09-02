# mcpgate

> Automated quality gate for MCP servers — **ruff + pytest for MCP**.

[![CI](https://github.com/mcpgate/mcpgate/actions/workflows/ci.yml/badge.svg)](https://github.com/mcpgate/mcpgate/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/mcpgate)](https://pypi.org/project/mcpgate/)
[![Python](https://img.shields.io/pypi/pyversions/mcpgate)](https://pypi.org/project/mcpgate/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

When an MCP tool description is vague, the AI agent misuses the tool — even though
the code behind it is perfect. Research on 103 major MCP servers found tool
descriptions systematically "smelly and costly" (arXiv:2602.14878); an AWS-led
study found **97.1% of MCP tool descriptions contain at least one quality defect**.
`mcpgate` catches these defects before agents hit them in production.

- `mcpgate lint <server>` — ruff-style linting of tool/resource/prompt definitions
- `mcpgate doctor <server>` — health check: handshake, capabilities, latency
- pytest plugin — contract-test your tools over the real protocol

Status: under active development. Full docs, rule table, and quickstart land with v0.1.0.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md).
