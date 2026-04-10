# Change Validation Report: improve-ado-backlog-refine-error-logging

**Validation Date**: 2026-01-29  
**Change Proposal**: [proposal.md](./proposal.md)  
**Validation Method**: Dry-run simulation and production-grade UX review  
**Source**: [GitHub Issue #162](https://github.com/nold-ai/specfact-cli/issues/162)

## Executive Summary

- **Breaking Changes**: 0 detected
- **Dependent Files**: Limited to `src/specfact_cli/adapters/ado.py` and optionally `runtime.py`; no public API changes
- **Impact Level**: Low
- **Validation Result**: Pass
- **Production-grade UX**: Reviewed; recommendations below for implementation phase

## Breaking Changes Detected

None. Change only extends failure paths (capture response, log in debug, surface message + hint). Success paths and public method signatures unchanged.

## Dependencies Affected

- **Critical**: None
- **Recommended**: Ensure all ADO PATCH call sites (backlog refine body, status update, comment, create work item) use the same helper so behavior is consistent
- **Optional**: Extend `debug-logging` main spec with a short “API failure logging” requirement so future adapters follow the same pattern

## Impact Assessment

- **Code Impact**: ADO adapter only; internal helper and extended exception handling
- **Test Impact**: New unit tests for helper and for user message content; optional integration test for debug log content
- **Documentation Impact**: Optional: add a doc link in the user-facing hint (e.g. ADO custom mapping) and/or one line “Run with --debug and check ~/.specfact/logs for full response and patch paths”
- **Release Impact**: Patch (fix + improved UX)

## Production-Grade UX Review

### What the change gets right (strong)

1. **User sees cause without --debug**: ADO message (e.g. “Cannot find field System.AcceptanceCriteria”) and mapping hint are required in the console message, so users can act without enabling debug.
2. **Debug log has full context**: Response body snippet (redacted, truncated) and list of patch paths make the failing field obvious and support custom templates and future improvements.
3. **Consistency**: Same behavior at all ADO PATCH sites (refine body, status, comment, create) avoids inconsistent UX.
4. **Safe logging**: Truncation and redaction avoid leaking secrets and huge payloads.

### Recommendations for implementation (make it “really good”)

1. **Actionable hint with doc link**: In implementation, include a concrete link in the hint when available (e.g. “See <https://github.com/nold-ai/specfact-cli/docs/>... or ado_custom.yaml”) so corporate users can resolve mapping issues without searching.
2. **Optional --debug pointer**: Consider appending to the hint: “Run with --debug and check ~/.specfact/logs for full response and patch paths.” so users know how to get more detail when needed.
3. **Log every failed attempt**: In the backlog-refine PATCH path there are multiple retries (omit multilineFieldsFormat, replace add with replace, HTML fallback). Call the logging helper before each retry and on final failure so the debug log shows the sequence of attempts and the final response/paths.
4. **Highlight field name in message**: When the ADO message contains a field reference (e.g. “System.AcceptanceCriteria”), consider quoting or emphasizing it in the user message (e.g. “Field ‘System.AcceptanceCriteria’ not found. Check custom field mapping…”) so the failing field is obvious at a glance.

### Production readiness

The change is sufficient to fix issue #162 and is suitable for production. Applying the four recommendations above will make error UX and debug usefulness “really good” for all customer sizes and complex infrastructures, and will make future bug reports (e.g. other custom templates) easier to diagnose.

## Format Validation

- **proposal.md Format**: Pass  
  - Title: `# Change: ...`  
  - Sections: Why, What Changes, Capabilities, Impact, Source Tracking  
  - Capabilities: api-error-diagnostics with spec file
- **tasks.md Format**: Pass  
  - Branch creation first (task 1), PR creation last (task 5)  
  - Numbered tasks and sub-tasks; quality gates (format, type-check, tests)
- **specs/api-error-diagnostics/spec.md Format**: Pass  
  - Delta header: `## ADDED Requirements`  
  - Requirements with `#### Scenario:` blocks
- **design.md Format**: Pass  
  - Bridge adapter integration, error handling strategy, sequence diagram

## OpenSpec Validation

- **Status**: Pass
- **Validation Command**: `openspec validate improve-ado-backlog-refine-error-logging --strict`
- **Issues Found**: 0 (after adding `## ADDED Requirements` to spec)
- **Re-validated**: Yes

## Validation Artifacts

- Change directory: `openspec/changes/improve-ado-backlog-refine-error-logging/`
- Plan source: `specfact-cli-internal/docs/internal/implementation/2026-01-29-ado-backlog-refine-error-logging-plan.md`

## Next Steps

1. Review this validation report and the production-grade UX recommendations.
2. Implement the change (branch `bugfix/improve-ado-backlog-refine-error-logging`, then code and tests).
3. During implementation, apply the four “really good” recommendations where feasible (doc link, --debug pointer, log each attempt, highlight field name).
4. Run full test suite and create PR to `dev` with Fixes nold-ai/specfact-cli#162.
