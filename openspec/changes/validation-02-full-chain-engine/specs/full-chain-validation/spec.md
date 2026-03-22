## ADDED Requirements

### Requirement: Full Chain Validation
The system SHALL validate Requirement -> Architecture -> Spec -> Code -> Test transitions and emit layered evidence.

#### Scenario: Full-chain command emits transition-level results
- **GIVEN** `specfact validate --full-chain --output json --evidence-dir .specfact/evidence/`
- **WHEN** validation runs
- **THEN** report includes transition groups `req_to_arch`, `arch_to_spec`, `spec_to_code`, and `code_to_tests`
- **AND** each group reports pass/fail/advisory counts.

#### Scenario: Severity respects policy mode and profile
- **GIVEN** enterprise profile with hard mode
- **WHEN** a required Req -> Arch mapping is missing
- **THEN** overall validation exits non-zero
- **AND** evidence marks the violation as blocking.

#### Scenario: Orphan detection is included in evidence
- **GIVEN** specs without requirement links exist
- **WHEN** full-chain validation runs
- **THEN** orphan entries are listed in evidence
- **AND** orphan summary is included in overall status computation.

#### Scenario: Code quality can be included without becoming a chain layer
- **GIVEN** `specfact validate --full-chain --with-code-quality` is executed
- **WHEN** the validation run completes
- **THEN** the evidence output includes a `code_quality` summary sourced from `specfact review`
- **AND** the traceability layers remain limited to `req_to_arch`, `arch_to_spec`, `spec_to_code`, and `code_to_tests`
