# ci-integration Specification

## Purpose

TBD - created by archiving change ci-docs-sync-check. Update Purpose after archive.

## Requirements

### Requirement: Branch Protection Configuration

The system SHALL configure branch protection to require docs sync check.

#### Scenario: Main branch protection

- **WHEN** branch protection is configured
- **THEN** main branch SHALL require docs sync check
- **AND** prevent merges with failing checks

#### Scenario: Develop branch protection

- **WHEN** branch protection is configured
- **THEN** develop branch SHALL require docs sync check
- **AND** prevent merges with failing checks

### Requirement: Status Check Integration

The system SHALL integrate docs sync check as a required status check.

#### Scenario: Required status check setup

- **WHEN** CI integration is complete
- **THEN** docs sync check SHALL be required status check
- **AND** appear in branch protection settings

#### Scenario: Status check enforcement

- **WHEN** PR has failing docs sync check
- **THEN** PR SHALL be blocked from merge
- **AND** clear error SHALL be shown

### Requirement: Exemption Label Support

The system SHALL support exemption labels for intentional documentation exemptions.

#### Scenario: Docs exempt label

- **WHEN** PR has `docs-exempt` label
- **THEN** docs sync check SHALL be skipped
- **AND** PR SHALL not be blocked

#### Scenario: No exemption label

- **WHEN** PR doesn't have exemption label
- **THEN** docs sync check SHALL run normally
- **AND** enforce documentation requirements

### Requirement: Error Reporting Integration

The system SHALL integrate error reporting with GitHub UI.

#### Scenario: Clear error messages

- **WHEN** docs sync check fails
- **THEN** error messages SHALL appear in GitHub UI
- **AND** be clearly formatted

#### Scenario: Actionable guidance

- **WHEN** docs sync check fails
- **THEN** output SHALL provide actionable guidance
- **AND** list specific documents to update

### Requirement: Configuration Management

The system SHALL manage CI configuration appropriately.

#### Scenario: Configuration file updates

- **WHEN** CI integration is implemented
- **THEN** configuration files SHALL be updated
- **AND** changes SHALL be version controlled

#### Scenario: Backward compatibility

- **WHEN** CI integration is implemented
- **THEN** existing workflows SHALL not be disrupted
- **AND** backward compatibility SHALL be maintained

### Requirement: Branch-aware module signature verification in pre-commit

The pre-commit hook SHALL apply a branch-aware policy using **`scripts/module-verify-policy.sh`**:
strict verification on `main`, relaxed PR-style verification elsewhere.

#### Scenario: Pre-commit on feature or dev branch without local key

- **WHEN** a developer or agent runs `git commit` on any branch other than `main` (or on detached `HEAD`)
- **AND** the commit includes staged changes under `modules/` or `src/specfact_cli/modules/`
- **THEN** the pre-commit hook SHALL source `scripts/module-verify-policy.sh` and run
  `verify-modules-signature.py` with **`VERIFY_MODULES_PR`**
  (`--enforce-version-bump --skip-checksum-verification`) **without** `--require-signature`
- **AND** SHALL NOT fail solely because the stored payload checksum is stale relative to working-tree files
  (CI / `sign-modules` refresh is expected before protected-branch strict verify)

#### Scenario: Pre-commit on main branch

- **WHEN** a commit is staged on the `main` branch
- **AND** the commit includes changes to module files
- **THEN** the pre-commit hook SHALL run `verify-modules-signature.py` with **`VERIFY_MODULES_STRICT`**
  (includes `--require-signature`)
- **AND** SHALL fail if any module manifest fails strict verification

#### Scenario: Pre-commit with no module changes

- **WHEN** a commit contains no changes to `module-package.yaml` or module payload files
- **THEN** module signature verification SHALL complete without error regardless of branch
- **AND** SHALL not block the commit

### Requirement: PR orchestrator verify job aligns with policy bundles

The `verify-module-signatures` job in `pr-orchestrator.yml` SHALL source **`scripts/module-verify-policy.sh`**
and SHALL NOT pass `--require-signature` in this job.

#### Scenario: Pull request verification

- **WHEN** the job runs for a `pull_request` event
- **THEN** it SHALL invoke `verify-modules-signature.py` with **`VERIFY_MODULES_PR`**
  and `--version-check-base origin/<base_branch>`

#### Scenario: Push verification (post-merge)

- **WHEN** the job runs for a `push` event to `dev` or `main`
- **THEN** it SHALL invoke `verify-modules-signature.py` with **`VERIFY_MODULES_PUSH_ORCHESTRATOR`**
  and an appropriate `--version-check-base` (for example `github.event.before` with `HEAD~1` fallback)

### Requirement: sign-modules.yml verify job uses the same policy bundles

The `sign-modules.yml` **`verify`** job SHALL source **`scripts/module-verify-policy.sh`**.

#### Scenario: Push to dev or main after auto-sign

- **WHEN** a push to `dev` or `main` runs the strict verify step (after auto-sign when applicable)
- **THEN** it SHALL invoke `verify-modules-signature.py` with **`VERIFY_MODULES_STRICT`**

#### Scenario: Pull request or workflow_dispatch

- **WHEN** the job runs for `pull_request` or `workflow_dispatch`
- **THEN** it SHALL invoke `verify-modules-signature.py` with **`VERIFY_MODULES_PR`**
  and `--version-check-base origin/<base_branch>`
