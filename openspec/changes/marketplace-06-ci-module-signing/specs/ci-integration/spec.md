# ci-integration Delta Specification

## ADDED Requirements

### Requirement: Branch-aware module signature verification in pre-commit

The pre-commit hook SHALL apply a branch-aware signature policy: checksum-only verification on
non-`main` branches, full signature verification on `main`.

#### Scenario: Pre-commit on feature or dev branch without local key

- **WHEN** a developer or agent runs `git commit` on any branch other than `main`
- **AND** the commit includes changes to module files
- **THEN** the pre-commit hook SHALL run `verify-modules-signature.py --allow-unsigned`
- **AND** SHALL accept manifests with a valid checksum but no signature
- **AND** SHALL NOT fail due to a missing or invalid signature

#### Scenario: Pre-commit on main branch

- **WHEN** a commit is staged on the `main` branch
- **AND** the commit includes changes to module files
- **THEN** the pre-commit hook SHALL run `verify-modules-signature.py --require-signature`
- **AND** SHALL fail if any changed module manifest lacks a valid signature

#### Scenario: Pre-commit with no module changes

- **WHEN** a commit contains no changes to `module-package.yaml` or module payload files
- **THEN** module signature verification SHALL complete without error regardless of branch
- **AND** SHALL not block the commit

### Requirement: PR orchestrator skips signature requirement for dev-targeting PRs

The `verify-module-signatures` job in `pr-orchestrator.yml` SHALL NOT enforce `--require-signature`
for pull requests or pushes targeting `dev`; it SHALL enforce `--require-signature` only for
`main`-targeting events.

#### Scenario: Feature-to-dev PR with unsigned module changes

- **WHEN** a pull request targets `dev`
- **AND** the PR contains module changes with checksum-only manifests (no signature)
- **THEN** the `verify-module-signatures` CI job SHALL pass
- **AND** all downstream jobs (tests, lint, etc.) SHALL not be blocked

#### Scenario: Dev-to-main PR without signed manifests (before approval)

- **WHEN** a pull request targets `main`
- **AND** module manifests are unsigned or have stale signatures
- **THEN** the `verify-module-signatures` CI job SHALL fail with `--require-signature`
- **AND** block the PR from merging until signed manifests are committed

#### Scenario: Dev-to-main PR after CI signing commit

- **WHEN** a pull request targets `main`
- **AND** the CI signing workflow has committed signed manifests to the PR branch
- **THEN** the `verify-module-signatures` job SHALL pass
- **AND** the PR SHALL be mergeable (assuming all other checks pass)

#### Scenario: Push to main with signed manifests

- **WHEN** a commit is pushed directly to `main` (post-merge)
- **THEN** the `verify-module-signatures` job SHALL enforce `--require-signature`
- **AND** fail if any module manifest lacks a valid signature

### Requirement: sign-modules.yml scopes full verification to main only

The `sign-modules.yml` hardening workflow SHALL enforce `--require-signature` only on `main`
branch events; `dev` branch events SHALL use checksum-only verification.

#### Scenario: Push to dev triggers sign-modules workflow

- **WHEN** a push to `dev` triggers `sign-modules.yml`
- **AND** the push contains module changes
- **THEN** the `verify` job SHALL run without `--require-signature`
- **AND** SHALL pass for checksum-only signed manifests

#### Scenario: Push to main triggers sign-modules workflow

- **WHEN** a push to `main` triggers `sign-modules.yml`
- **THEN** the `verify` job SHALL run with `--require-signature`
- **AND** fail if signatures are absent or invalid
