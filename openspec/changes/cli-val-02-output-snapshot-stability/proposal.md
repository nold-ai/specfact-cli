# Change: Output Snapshot Stability

## Why

Users who script SpecFact in CI/CD pipelines rely on stable output: help text format, error message wording, JSON/YAML structured output shapes. Today, a refactoring PR can silently change help text or error phrasing with no test catching it. A user's `specfact validate --help | grep "spec"` pipeline step breaks without warning. Snapshot testing makes output changes explicit, reviewable, and intentional — treating help text and structured output as versioned contracts.

## What Changes

- **NEW**: `syrupy` added as a dev/test dependency for pytest snapshot testing
- **NEW**: Snapshot tests for all top-level and subcommand `--help` outputs in `tests/snapshots/`
- **NEW**: Snapshot tests for structured output shapes (JSON/YAML from commands that produce machine output)
- **NEW**: Snapshot tests for key error message templates (ensuring consistent user-facing error phrasing)
- **EXTEND**: CI pipeline to reject unreviewed snapshot changes (snapshot mismatches fail CI; updates require explicit `--snapshot-update` flag)
- **EXTEND**: `pyproject.toml` with syrupy configuration and hatch script for snapshot updates

## Capabilities

### New Capabilities

- `output-snapshot-stability`: Pytest snapshot tests using syrupy that freeze help text, structured output shapes, and error message templates as versioned contracts. Any output change requires explicit snapshot update and PR review.

## Impact

- **Affected specs**: No existing specs modified; new spec delta defines snapshot testing requirements
- **Affected code**: No production CLI code changes; new test files and dev dependency only
- **Integration points**: Consumed by cli-val-05 (CI integration — snapshot mismatch becomes a hard gate)
- **Documentation impact**: Developer guide update in `docs/` describing snapshot update workflow

## Dependencies

- No hard blockers — can develop in parallel with cli-val-01
- Downstream dependents: cli-val-05-ci-integration

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #280
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/280
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
