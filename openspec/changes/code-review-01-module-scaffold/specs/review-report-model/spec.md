## ADDED Requirements

### Requirement: ReviewReport Governance-01 Compatible Envelope
The system SHALL provide a `ReviewReport` Pydantic model carrying standard governance-01 fields (`schema_version`, `run_id`, `timestamp`, `overall_verdict`, `ci_exit_code`) and review-specific extensions (`score`, `reward_delta`, `findings`, `summary`).

#### Scenario: PASS verdict maps to governance-01 PASS
- **GIVEN** a run with `score=85`
- **WHEN** `ReviewReport` is constructed
- **THEN** `overall_verdict` equals `"PASS"` and `ci_exit_code` equals `0`
- **AND** `reward_delta` equals `5` (85 - 80)

#### Scenario: WARN verdict maps to PASS_WITH_ADVISORY
- **GIVEN** a run with `score=60`
- **WHEN** `ReviewReport` is constructed
- **THEN** `overall_verdict` equals `"PASS_WITH_ADVISORY"` and `ci_exit_code` equals `0`

#### Scenario: BLOCK verdict maps to FAIL
- **GIVEN** a run with `score=45`
- **WHEN** `ReviewReport` is constructed
- **THEN** `overall_verdict` equals `"FAIL"` and `ci_exit_code` equals `1`

#### Scenario: Blocking error forces FAIL regardless of score
- **GIVEN** a run with `score=75` but a finding with `severity=error` and `fixable=False`
- **WHEN** `ReviewReport` is constructed
- **THEN** `overall_verdict` equals `"FAIL"` and `ci_exit_code` equals `1`

#### Scenario: Standard governance fields always present
- **GIVEN** any `ReviewReport` instance
- **WHEN** its fields are inspected
- **THEN** `schema_version`, `run_id`, `timestamp`, `overall_verdict`, `ci_exit_code` are all non-null
