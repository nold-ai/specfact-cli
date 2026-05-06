# ci-module-signing-on-approval Specification

## Purpose

TBD - created by archiving change marketplace-06-ci-module-signing. Update Purpose after archive.

## Requirements

### Requirement: Sign changed modules on PR approval

The system SHALL automatically sign changed module manifests using CI secrets when a pull request
targeting `dev` or `main` is approved, and SHALL commit the signed manifests back to the PR branch.

#### Scenario: PR to dev approved with module changes

- **WHEN** a pull request targeting `dev` is approved by a reviewer
- **AND** the PR contains changes to one or more `module-package.yaml` files or their module payload
- **THEN** the CI signing workflow SHALL sign all changed module manifests using
  `SPECFACT_MODULE_PRIVATE_SIGN_KEY` and `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE`
- **AND** SHALL commit the updated manifests back to the PR branch with message
  `chore(modules): ci sign changed modules [skip ci]`

#### Scenario: PR to main approved with module changes

- **WHEN** a pull request targeting `main` is approved by a reviewer
- **AND** the PR contains changes to one or more `module-package.yaml` files or their module payload
- **THEN** the CI signing workflow SHALL sign all changed module manifests
- **AND** SHALL commit the updated manifests back to the PR branch before merge

#### Scenario: PR approved with no module changes

- **WHEN** a pull request is approved
- **AND** no `module-package.yaml` files or module payload files have changed relative to the base
- **THEN** the CI signing workflow SHALL exit cleanly with no commit

#### Scenario: Secrets unavailable during signing

- **WHEN** the signing workflow triggers
- **AND** `SPECFACT_MODULE_PRIVATE_SIGN_KEY` is not set or empty
- **THEN** the workflow SHALL fail with a clear error message identifying the missing secret
- **AND** SHALL NOT commit any partial changes

### Requirement: Signing workflow is idempotent

The CI signing workflow SHALL produce byte-for-byte identical signed manifests when run twice on
the same module payload, and SHALL skip the commit when no manifest content changes.

#### Scenario: Signing run twice on unchanged payload

- **WHEN** the signing workflow runs on a PR branch where manifests are already signed
- **AND** no module source files have changed since the last signing commit
- **THEN** `sign-modules.py --changed-only` SHALL detect no changes and exit without writing
- **AND** no new commit SHALL be created on the PR branch

#### Scenario: Signing after a subsequent code push

- **WHEN** additional commits are pushed to the PR branch after a signing commit
- **AND** module payload files are changed by those commits
- **THEN** re-approving the PR SHALL trigger a new signing run covering only the newly changed
  modules

### Requirement: CI signing does not require local private key

The signing workflow SHALL operate entirely via GitHub secrets without any local private key
material, enabling non-interactive development on feature and dev branches.

#### Scenario: Non-interactive agent commit on feature branch

- **WHEN** an AI agent or headless CI tool commits a module change on a `feature/*` or `bugfix/*`
  branch
- **AND** no private key environment variables are set locally
- **THEN** the pre-commit hook SHALL accept the unsigned manifest (relaxed verify: `VERIFY_MODULES_PR`)
- **AND** the commit SHALL succeed without prompting for a passphrase

#### Scenario: Developer commit on dev branch without local key

- **WHEN** a developer commits a module change on the `dev` branch
- **AND** `SPECFACT_MODULE_PRIVATE_SIGN_KEY` is not set in the local environment
- **THEN** the pre-commit hook SHALL accept the manifest under relaxed verify (`VERIFY_MODULES_PR`)
- **AND** SHALL NOT invoke `getpass.getpass()` or any interactive passphrase prompt
