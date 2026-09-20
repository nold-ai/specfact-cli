## Scope rescope — 2026-09-20

Consume current_execution independently from optional chronology. No global graph, full-chain completeness, or historical proof prerequisite for <https://github.com/nold-ai/specfact-cli/issues/740>. Missing mappings remain unassessed coverage, not fabricated completeness. Preserve graph validation for users who request that capability.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../../../requirements-09-minimal-evidence/proposal.md).

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
