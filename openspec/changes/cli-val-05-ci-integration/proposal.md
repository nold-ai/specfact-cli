# Change: CLI Validation CI Integration

## Why

Runtime validation only protects users when it runs before merge against the same installation shapes users run: wheel, pipx, uv run, uvx, and source/hatch. The current PR workflow validates many process and contract gates, but coverage remains advisory, independent static analysis is not a dedicated blocking check, and package validation is mostly post-merge. This change moves those proofs into PR-time gates while keeping expensive cross-platform coverage targeted.

## What Changes

- **NEW**: Blocking `Quality Gates` CI job that enforces the configured coverage threshold instead of warning below an advisory threshold.
- **NEW**: Blocking `Independent Static Analysis` CI job that runs Semgrep and Bandit independently from `specfact code review`.
- **NEW**: Blocking `Package Runtime Matrix` CI job for runtime, packaging, module discovery, command-doc, and workflow changes.
- **EXTEND**: CLI black-box acceptance design to install and execute a built wheel, not an editable source install.
- **EXTEND**: Release PR fast-path logic so `dev -> main` parity skips only duplicate expensive tests, while release-safety checks still run.
- **NEW**: Targeted cross-platform runtime smoke: macOS is PR-blocking for runtime/package paths; Windows starts on schedule/manual.
- **NEW**: Property and mutation probes for dependency resolver, module installer, package parsing, marketplace selection, and upgrade/version logic.

## Capabilities

### New Capabilities

- `cli-validation-ci-gates`: PR-time CI gates for installed-package runtime validation, blocking coverage, independent SAST, cross-platform smoke, release-safety checks, property tests, and mutation baseline evidence.

### Modified Capabilities

- `acceptance-test-runner`: Black-box path installs from the built wheel instead of editable source.
- `trustworthy-green-checks`: Quality and release-fast-path checks are blocking and fail closed.
- `ci-integration`: Package-manager runtime checks run before merge for affected pull requests.
- `dependency-resolution`: Critical resolver and installer paths receive property-based regression coverage.
- `codebase-validation-depth`: Mutation testing is introduced as scheduled/advisory evidence for critical validation code.

## Impact

- **Affected specs**: `trustworthy-green-checks`, `ci-integration`, `dependency-resolution`, `codebase-validation-depth`, `acceptance-test-runner`.
- **Affected code**: GitHub Actions workflow, smart test coverage threshold handling, workflow policy tests, resolver property tests, mutation baseline configuration.
- **Integration points**: GitHub Actions, Hatch scripts, OpenSpec validation, internal wiki mirror, module checkout/runtime smoke fixtures.
- **Documentation impact**: CI and contributor guidance must distinguish blocking gates from advisory scheduled mutation evidence.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
