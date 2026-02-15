# Change: MCP Server — Programmatic Tool Interface for Agentic Workflows

## Why




While the Agent Skill handles 90% of developer interactions via CLI invocation, agentic workflows (CI/CD pipelines, autonomous coding agents, multi-step validation loops) need programmatic tool access with structured inputs and outputs. MCP (Model Context Protocol) — adopted by every major AI platform with 97M+ monthly SDK downloads — provides the standard interface. An MCP server exposing 3-5 high-level tools with compressed, summarized results gives SpecFact programmatic accessibility without the context bloat of naive MCP implementations.

## What Changes




- **NEW**: MCP server in `src/specfact_cli/mcp/` exposing high-level tools:
  - `validate_spec(spec_path, options)` — run validation (spec-only or full-chain), return compressed summary
  - `check_compatibility(base_spec, revision_spec)` — breaking change detection between spec versions
  - `get_requirement_coverage(requirement_id)` — traceability status for a specific requirement
  - `suggest_fixes(validation_report_path)` — actionable fix recommendations for validation failures
- **NEW**: Server-side summarization — tools never return raw specs or full diffs; only compressed, actionable summaries suitable for LLM context windows
- **NEW**: Dual-response pattern: concise text summary for LLM reasoning + ResourceLink URI for full reports that agents can fetch on demand
- **NEW**: `specfact mcp serve` — start the MCP server (stdio transport for IDE integration, HTTP/SSE for CI/CD)
- **NEW**: `specfact mcp install` — generate MCP server configuration for Claude Desktop, Cursor, VS Code, etc.
- **NEW**: Tool count disciplined to 3-5 tools per MCP best practices (Phil Schmid: 5-15 maximum)
- **DESIGN DECISION**: MCP server wraps CLI commands internally — the CLI remains the source of truth, MCP is a thin adapter layer

## Capabilities
### New Capabilities

- `mcp-server`: MCP server exposing 3-5 high-level specification intelligence tools with server-side summarization, dual-response pattern, stdio and HTTP/SSE transports. Wraps CLI commands as thin adapter layer.

### Modified Capabilities

(none)


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #252
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/252>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 83b763280fc0b831 -->