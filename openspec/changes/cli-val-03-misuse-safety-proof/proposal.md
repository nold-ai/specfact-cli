# Change: Misuse Safety Proof

## Why

When a user invokes SpecFact CLI with wrong flags, missing files, invalid YAML, or forbidden option combinations, the CLI should always: exit non-zero, print a human-readable error to stderr, and leave no partial artifacts on disk. Today, anti-pattern handling is tested ad-hoc in some test files but not systematically per command. Users have encountered stack traces in error cases. A systematic anti-pattern catalog per command group — combined with Hypothesis property-based fuzzing — proves that every misuse case fails safely and predictably.

## What Changes

- **NEW**: Anti-pattern catalog per command group in `tests/cli-contracts/` following the scenario schema from cli-val-01
- **NEW**: Anti-pattern test suite in `tests/unit/specfact_cli/test_cli_misuse_safety.py` asserting three properties for every anti-pattern: (1) non-zero exit, (2) human-readable error without tracebacks, (3) no unintended filesystem side effects
- **NEW**: Hypothesis property-based test strategies in `tests/unit/specfact_cli/test_cli_hypothesis_fuzz.py` generating invalid enum values, path edge cases, Unicode edge cases per major command group
- **EXTEND**: Existing CliRunner test patterns to include systematic traceback-absence assertions

## Capabilities

### New Capabilities

- `misuse-safety-proof`: Systematic anti-pattern testing for every command group — codifying wrong flags, missing values, invalid paths, malformed input files, illegal combinations — with three-property assertion (non-zero exit, clean error, no side effects) and Hypothesis fuzzing for undiscovered edge cases.

## Impact

- **Affected specs**: No existing specs modified; new spec delta defines anti-pattern testing requirements
- **Affected code**: No production CLI code changes; new test files only (may surface bugs that require production fixes)
- **Integration points**: Consumes cli-val-01 scenario schema for anti-pattern definitions; consumed by cli-val-04 (acceptance runner executes anti-patterns) and cli-val-05 (CI gate)
- **Documentation impact**: Contributor guide update describing anti-pattern authoring conventions

## Dependencies

- **Hard blocker**: cli-val-01-behavior-contract-standard (anti-patterns follow the scenario YAML schema)
- Downstream dependents: cli-val-04-acceptance-test-runner, cli-val-05-ci-integration

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #281
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/281
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
