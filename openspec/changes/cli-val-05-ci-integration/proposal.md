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
- **NEW**: Fail-closed documentation-accountability gate that derives official module ownership from the modules repository, validates core catalogues and handoffs against it, and runs locally before commit and in required PR CI.

## Capabilities

### New Capabilities

- `cli-validation-ci-gates`: PR-time CI gates for installed-package runtime validation, blocking coverage, independent SAST, cross-platform smoke, release-safety checks, property tests, and mutation baseline evidence.

### Modified Capabilities

- `acceptance-test-runner`: Black-box path installs from the built wheel instead of editable source.
- `trustworthy-green-checks`: Quality and release-fast-path checks are blocking and fail closed.
- `ci-integration`: Package-manager runtime checks run before merge for affected pull requests.
- `dependency-resolution`: Critical resolver and installer paths receive property-based regression coverage.
- `codebase-validation-depth`: Mutation testing is introduced as scheduled/advisory evidence for critical validation code.
- `documentation-accountability`: Core documentation catalogues, generated command artifacts, and module ownership handoffs stay synchronized with the official modules repository.

## Impact

- **Affected specs**: `cli-validation-ci-gates`, `documentation-accountability`, `trustworthy-green-checks`, `ci-integration`, `dependency-resolution`, `codebase-validation-depth`, `acceptance-test-runner`.
- **Affected code**: GitHub Actions workflow, pre-commit quality gate, documentation-accountability checker, command overview/contract inventory, workflow policy tests, resolver property tests, mutation baseline configuration.
- **Integration points**: GitHub Actions, Hatch scripts, OpenSpec validation, the checked-out modules repository, internal wiki mirror, module checkout/runtime smoke fixtures.
- **Documentation impact**: Canonical core catalogues, architecture/ownership pages, and contributor guidance must identify every official package and distinguish core-owned overview material from modules-owned deep documentation.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #643
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/643>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open; unblocked; parent #375 CLI Behavior Validation Suite
