# Change: CLI Validation CI Integration

## Why

Validation only has value if it runs automatically. Today, `pr-orchestrator.yml` runs a `cli-validation` job that only checks `specfact --help` — a single smoke test. The new validation layers (snapshots from cli-val-02, anti-patterns from cli-val-03, acceptance tests from cli-val-04) need to slot into CI with clear gating rules so broken CLI behavior never reaches PyPI. This change wires the complete CLI validation layer into the existing CI pipeline with tiered gates (hard and advisory).

## What Changes

- **EXTEND**: `.github/workflows/pr-orchestrator.yml` with three new validation steps:
  1. Snapshot validation step in existing `tests` job (fast, fails on mismatch)
  2. Black-box acceptance test job (installs wheel, runs subprocess-path scenarios)
  3. Anti-pattern safety assertion step
- **NEW**: Snapshot update CI workflow (manual trigger) for developers to update snapshots after intentional output changes
- **EXTEND**: `contract-test` system to include CLI behavior contracts as a new tier
- **EXTEND**: `pyproject.toml` hatch scripts with combined CLI validation command

## Capabilities

### New Capabilities

- `cli-validation-ci-gates`: CI pipeline integration for the CLI validation layer — snapshot mismatch detection, black-box acceptance testing, anti-pattern safety verification — with tiered gating (hard gates block merge, advisory gates warn).

## Impact

- **Affected specs**: No existing specs modified
- **Affected code**: CI workflow YAML files and pyproject.toml hatch scripts only; no production CLI code changes
- **Integration points**: Consumes cli-val-02 (snapshots), cli-val-03 (anti-patterns), cli-val-04 (acceptance runner)
- **Documentation impact**: CI documentation update describing new gates and snapshot update workflow

## Dependencies

- **Hard blocker**: cli-val-02-output-snapshot-stability (snapshot tests to gate)
- **Hard blocker**: cli-val-04-acceptance-test-runner (acceptance tests to gate)
- Downstream dependents: cli-val-06-copilot-test-generation (enforcement convention)

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #283
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/283
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
