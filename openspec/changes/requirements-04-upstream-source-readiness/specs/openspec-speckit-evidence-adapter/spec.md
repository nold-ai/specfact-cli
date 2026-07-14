## ADDED Requirements

### Requirement: Native source readiness before requirement normalization

The OpenSpec and Spec Kit evidence adapter SHALL evaluate native source readiness
before emitting `RequirementInput` records. If readiness returns any error-level
diagnostic, the adapter SHALL return zero records and SHALL preserve the source
directory byte-for-byte. Readiness diagnostics SHALL use the existing structured
import-result contract and SHALL distinguish incomplete Spec Kit sources,
upstream-invalid OpenSpec sources, and required unavailable validators.

#### Scenario: Reject a pristine Spec Kit scaffold

- **GIVEN** a supported native Spec Kit feature created from the official
  scaffold that retains recognised draft placeholders or
  `NEEDS CLARIFICATION` markers
- **WHEN** the adapter imports the feature
- **THEN** it returns zero requirement records
- **AND** it returns an error diagnostic with code
  `incomplete-source-template` and the relevant source locator
- **AND** the feature directory remains byte-identical.

#### Scenario: Reject a structurally incomplete Spec Kit source

- **GIVEN** a native Spec Kit source with no substantive Functional Requirement
  or no meaningful acceptance scenario while user stories are present
- **WHEN** the adapter imports the feature
- **THEN** it returns zero requirement records
- **AND** it returns an error diagnostic with code `source-incomplete`.

#### Scenario: Import a completed native Spec Kit source

- **GIVEN** a native Spec Kit feature with substantive Functional Requirements
  and meaningful GIVEN/WHEN/THEN acceptance scenarios
- **WHEN** the adapter imports the feature
- **THEN** it returns normalized records with stable derived IDs and SHA-256
  source revisions
- **AND** re-importing the unchanged source returns the same result without
  changing the source directory.

#### Scenario: Reject invalid OpenSpec under required native validation

- **GIVEN** source-readiness policy requires native OpenSpec validation and
  `openspec validate --strict --json` reports the selected change invalid
- **WHEN** the adapter imports the OpenSpec change
- **THEN** it returns zero requirement records
- **AND** it returns an error diagnostic with code `source-invalid`
- **AND** it does not fall back to import that claims native validation passed.

#### Scenario: Report an unavailable required OpenSpec validator

- **GIVEN** source-readiness policy requires native OpenSpec validation and the
  OpenSpec CLI is unavailable
- **WHEN** the adapter imports an OpenSpec change
- **THEN** it returns zero requirement records
- **AND** it returns an error diagnostic with code
  `upstream-validator-unavailable`.

#### Scenario: Preserve portable OpenSpec import without required validation

- **GIVEN** source-readiness policy does not require native OpenSpec validation
  and the source satisfies the supported core schema profile
- **WHEN** the adapter imports the OpenSpec change on a host without the
  OpenSpec CLI
- **THEN** it preserves the existing normalized import behavior
- **AND** it does not claim native CLI validation occurred.
