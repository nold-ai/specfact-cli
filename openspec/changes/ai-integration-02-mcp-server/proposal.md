# Change: MCP Adapter for Validation Tools

## Why

An MCP server may be useful after the CLI validation loop has real pull, but it
should remain a thin adapter over trusted CLI behavior. Shipping a broad MCP
surface early would distract from the flagship validation and AI-bloat defense
path.

## Gate

This change is gated until `ai-integration-01-agent-skill` has shipped and at
least one real user or dogfooding workflow shows pull for programmatic
validation access.

## What Changes

- **NEW**: MCP server exposing only 2-3 high-value validation tools:
  `run_validation`, `read_evidence`, and optionally `prepare_remediation`.
- **NEW**: Server-side summarization that returns bounded evidence summaries and
  resource links instead of raw specs, raw diffs, or full reports.
- **NEW**: `specfact mcp serve` starts stdio transport for IDE integration.
- **NEW**: `specfact mcp install` generates minimal IDE configuration.
- **DESIGN DECISION**: MCP wraps CLI commands internally. The CLI remains the
  source of truth.

## Capabilities

### New Capabilities

- `mcp-validation-adapter`: Thin MCP adapter exposing a minimal validation and
  evidence-reading surface after CLI demand is proven.

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
