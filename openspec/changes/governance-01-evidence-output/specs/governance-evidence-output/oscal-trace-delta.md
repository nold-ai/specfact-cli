## ADDED Requirements

### Requirement: OSCAL-Aligned Evidence Envelope with Trace Fields
The system SHALL extend the governance evidence JSON envelope to include a `trace` object with `upstream` and `downstream` arrays, aligned with OSCAL Assessment Results model patterns, enabling bidirectional artifact navigation from any evidence record.

#### Scenario: Evidence envelope contains trace links for requirement-level artifacts
- **GIVEN** a `BusinessRule` artifact that was validated by SpecFact
- **WHEN** the governance evidence envelope is generated for that artifact
- **THEN** the evidence JSON includes a `trace` object:
  - `trace.upstream` contains the parent `BusinessOutcome` ID(s)
  - `trace.downstream` contains at least one of: spec ID, contract ID, or test ID linked to the rule
- **AND** the envelope validates against the updated evidence schema

#### Scenario: Evidence envelope captures per-check results
- **GIVEN** a validation run that checks schema_conformance, gwt_parseable, example_bound, and outcome_linked
- **WHEN** the evidence envelope is emitted
- **THEN** the `validation.checks` array contains one entry per check with `name`, `result` (pass/fail/error), and optional metadata fields (e.g., `test_id`, `outcome_id`)
- **AND** the overall `verdict` field is derivable from the check results without re-running validation

#### Scenario: OSCAL-aligned structure for compliance consumers
- **GIVEN** a governance evidence JSON file produced by SpecFact
- **WHEN** it is consumed by an OSCAL Assessment Results reader
- **THEN** the `validation.verdict` field maps to OSCAL's `finding.target.status` (pass/fail/not-applicable)
- **AND** the `artifact.hash` field provides the `subject.resource-id` equivalent for audit traceability

### Requirement: Artifact Hash in Evidence Envelope
The system SHALL include a SHA-256 hash of the validated artifact in every evidence envelope, enabling immutable audit trail construction.

#### Scenario: Artifact hash computed and included in evidence
- **GIVEN** a requirement artifact file at `.specfact/requirements/BR-001.req.yaml`
- **WHEN** `specfact validate --full-chain --evidence-dir .specfact/evidence/` runs
- **THEN** the evidence envelope for BR-001 includes `artifact.hash: "sha256:<hex>"`
- **AND** the hash is computed from the file contents at the time of validation (not from a prior snapshot)
