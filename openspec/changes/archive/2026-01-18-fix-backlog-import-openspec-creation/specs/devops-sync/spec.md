# devops-sync Specification

## Purpose

TBD - created by archiving change add-devops-backlog-tracking. Update Purpose after archive.

## Requirements

## MODIFIED Requirements

### Requirement: Selective Backlog Import into Project Bundles

The system SHALL support importing selected backlog items into a project bundle AND create complete OpenSpec change artifacts (proposal.md, tasks.md, spec deltas) when importing.

#### Scenario: Import specific backlog items by ID

- **WHEN** the user provides explicit backlog item IDs or URLs for import
- **THEN** only those items are imported into the target project bundle
- **AND** OpenSpec change directory is created: `openspec/changes/<change-id>/`
- **AND** `proposal.md` file is created with proper OpenSpec format:
  - Title: `# Change: {title}` (removes `[Change]` prefix if present)
  - Section: `## Why` with rationale content
  - Section: `## What Changes` with description content (formatted as bullet list)
  - Section: `## Impact` (generated or placeholder)
  - Section: `## Source Tracking` with backlog item tracking information
- **AND** `tasks.md` file is created with hierarchical numbered format:
  - Extracted from proposal acceptance criteria if available
  - Placeholder structure if no tasks found
  - Format: `## 1. Implementation`, `- [ ] 1.1 [Description]`
- **AND** spec deltas are created in `specs/<capability>/spec.md`:
  - Affected specs determined from proposal content analysis
  - `## ADDED Requirements` sections with extracted or placeholder requirements
- **AND** OpenSpec validation can be run on the created change
- **AND** no other backlog items are imported

#### Scenario: Create OpenSpec files from imported proposal

- **GIVEN** a backlog item (GitHub issue #111) is imported via `specfact sync bridge --adapter github --bidirectional --backlog-ids 111`
- **WHEN** import completes successfully
- **THEN** `ChangeProposal` object is created and stored in project bundle
- **AND** OpenSpec change directory is created: `openspec/changes/implement-sso-device-code-auth/`
- **AND** `proposal.md` file is written with:
  - Proper title format (no `[Change]` prefix)
  - All required sections (Why, What Changes, Impact)
  - Source Tracking section with GitHub issue reference
- **AND** `tasks.md` file is written with implementation tasks
- **AND** spec deltas are created in `specs/` subdirectory
- **AND** created change can be validated with `openspec validate implement-sso-device-code-auth --strict`

#### Scenario: Handle missing proposal content gracefully

- **GIVEN** a backlog item is imported with minimal content (title only, no body)
- **WHEN** OpenSpec files are created
- **THEN** `proposal.md` is created with:
  - Title from backlog item
  - Placeholder "Why" section if rationale is missing
  - Placeholder "What Changes" section if description is missing
  - Generated "Impact" section with default affected specs
- **AND** `tasks.md` is created with placeholder structure
- **AND** spec deltas are created with placeholder requirements
- **AND** user can manually fill in missing content later

#### Scenario: Handle file creation errors

- **GIVEN** backlog import attempts to create OpenSpec files
- **WHEN** file creation fails (permissions, disk space, invalid path)
- **THEN** error is logged with clear message
- **AND** import continues (proposal still stored in bundle)
- **AND** error is reported in sync result
- **AND** user is informed that OpenSpec files were not created

#### Scenario: Support cross-repo OpenSpec

- **GIVEN** backlog import is executed with `external_base_path` in bridge config
- **WHEN** OpenSpec files are created
- **THEN** files are created in external OpenSpec repository (not code repository)
- **AND** `external_base_path/openspec/changes/<change-id>/` directory structure is used
- **AND** files are created in correct location
