# Proposal: security-requirements-evidence-exclusive-discovery

## Why

The Requirements evidence delivery gate verifies a pinned external module fixture, but normal module discovery still examines repository-local and user-controlled roots before or alongside that fixture. A pull request can therefore shadow the trusted Requirements package with an unsigned project module and execute attacker-controlled Python while fabricating a passing report.

## What Changes

- Add an explicit module-discovery mode that limits dynamic package discovery to `SPECFACT_MODULES_ROOTS` (while retaining bundled core modules).
- Require both the local adapter and pull-request evidence workflow to enable that mode when invoking the pinned Requirements fixture.
- Add regressions proving project, user, marketplace, custom, and legacy roots cannot shadow an exclusive fixture invocation.

## Capabilities

### New Capabilities

- `trusted-module-fixture-discovery`

## Impact

- Affected code: module discovery and the Requirements evidence adapter.
- Affected workflow: `.github/workflows/requirements-evidence.yml`.
- Affected tests: focused discovery, adapter, and workflow contract tests.
- Compatibility: ordinary CLI discovery remains unchanged; exclusivity is opt-in for trusted fixture execution.
