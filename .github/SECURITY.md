# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a vulnerability

Do **not** open a public issue for security vulnerabilities. Use GitHub's
"Report a vulnerability" (Security → Advisories → New draft security advisory),
or open a minimal issue pointing to a draft advisory. You will get a response
within 7 days.

## Scope

`mcpgate` connects to MCP servers you point it at. Vulnerabilities of interest
include: command injection via server command strings, unsafe deserialization of
server responses, and SARIF/JSON output injection.
