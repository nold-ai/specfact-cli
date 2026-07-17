## ADDED Requirements

### Requirement: Native source readiness before requirement normalization

The OpenSpec and Spec Kit evidence adapter SHALL evaluate native source readiness
before emitting `RequirementInput` records. If readiness returns any error-level
diagnostic, the adapter SHALL return zero records and SHALL preserve the source
directory byte-for-byte. Readiness diagnostics SHALL use the existing structured
import-result contract and SHALL distinguish incomplete Spec Kit sources,
upstream-invalid OpenSpec sources, and required unavailable validators.

For the supported Spec Kit profile, a scaffold marker takes precedence over all
other content and returns `incomplete-source-template`. A marker is any pinned
official scaffold literal recognized by the adapter or the literal
`[NEEDS CLARIFICATION:`. Without a scaffold marker, a substantive Functional
Requirement is a supported `FR-` entry whose text after `System MUST` is
non-empty and contains no `[` or `]` placeholder delimiter. A meaningful
acceptance scenario is a parsed GIVEN/WHEN/THEN rule within the Markdown block
that starts with a `### User Story <number> - <title>` heading and ends at the
next heading of level one through three. A source lacking either required
element returns `source-incomplete`; a scenario outside such a story block does
not satisfy readiness. The pinned fixture mapping is: the byte-identical
`v0.12.18` scaffold is `incomplete-source-template`; a completed fixture is
accepted; and fixtures lacking a Functional Requirement or a story scenario are
`source-incomplete`. Core and module #346 SHALL use these same diagnostics.

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

- **GIVEN** a native Spec Kit source with no substantive Functional Requirement,
  no recognized user-story block, or no meaningful acceptance scenario within a
  recognized user-story block
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

#### Scenario: Reject failed or unusable native validation output

- **GIVEN** required native OpenSpec validation times out, exits non-zero, emits
  malformed or empty JSON, or exits zero without a passing result item for the
  selected change
- **WHEN** the adapter imports the OpenSpec change
- **THEN** it returns zero requirement records
- **AND** it returns an error diagnostic with code `source-invalid`
- **AND** the change directory remains byte-identical.

#### Scenario: Report an unavailable required OpenSpec validator

- **GIVEN** source-readiness policy requires native OpenSpec validation and the
  OpenSpec CLI is unavailable
- **WHEN** the adapter imports an OpenSpec change
- **THEN** it returns zero requirement records
- **AND** it returns an error diagnostic with code
  `upstream-validator-unavailable`.

#### Scenario: Require native OpenSpec validation for the enterprise tier

- **GIVEN** the effective requirements profile is `enterprise` and no layered
  configuration overrides its default
- **WHEN** the adapter imports an OpenSpec change
- **THEN** it requires native OpenSpec validation before emitting records.

#### Scenario: Resolve native validation policy through aliases and overrides

- **GIVEN** `strict` or `enterprise_full_stack` is the effective profile with
  no explicit policy value
- **WHEN** the adapter imports an OpenSpec change
- **THEN** it requires native OpenSpec validation
- **AND** an explicit layered boolean overrides that profile default.

#### Scenario: Preserve portable OpenSpec import without required validation

- **GIVEN** source-readiness policy does not require native OpenSpec validation
  and the source satisfies the supported core schema profile
- **WHEN** the adapter imports the OpenSpec change on a host without the
  OpenSpec CLI
- **THEN** it preserves the existing normalized import behavior
- **AND** it does not claim native CLI validation occurred.
