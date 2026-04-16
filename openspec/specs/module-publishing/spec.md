# module-publishing Specification

## Purpose

TBD - created by archiving change marketplace-02-advanced-marketplace-features. Update Purpose after archive.

## Requirements

### Requirement: Publishing script validates module structure

The system SHALL provide scripts/publish-module.py that validates module before publishing.

#### Scenario: Validate module structure

- **WHEN** publish script runs on module directory
- **THEN** it SHALL verify module-package.yaml exists and is valid
- **AND** SHALL verify namespace format for marketplace modules
- **AND** SHALL verify all required files present

#### Scenario: Create module tarball

- **WHEN** validation passes
- **THEN** script SHALL create tarball with format: {module-name}-{version}.tar.gz
- **AND** SHALL include only necessary files (exclude tests, .git, etc.)

### Requirement: GitHub Actions automates publishing on release

The system SHALL provide .github/workflows/publish-modules.yml that automates publishing.

#### Scenario: Publish on release tag

- **WHEN** git tag matches pattern `{module}-v{version}` is pushed
- **THEN** workflow SHALL run publish-module.py for that module
- **AND** SHALL generate checksum
- **AND** SHALL sign tarball (if signing configured)
- **AND** SHALL update `resources/bundled-module-registry/index.json` in **specfact-cli**
- **AND** SHALL create a pull request in **specfact-cli** (not in `specfact-cli-modules`)
