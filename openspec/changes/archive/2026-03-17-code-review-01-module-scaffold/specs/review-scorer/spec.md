## ADDED Requirements

### Requirement: Review Scoring Algorithm
The system SHALL compute `score` (0-120) and `reward_delta = score - 80` from findings and bonus conditions. Base score is 100; deductions: blocking error=-15, fixable error=-5, warning=-2, info=-1; bonuses: +5 each for five conditions.

#### Scenario: Single blocking error deducts 15
- **GIVEN** one finding with `severity=error`, `fixable=False`
- **WHEN** score is computed with no bonuses
- **THEN** `score` equals `85` and `reward_delta` equals `5`

#### Scenario: Auto-fixable error deducts 5
- **GIVEN** one finding with `severity=error`, `fixable=True`
- **WHEN** score is computed
- **THEN** `score` equals `95` and `reward_delta` equals `15`

#### Scenario: Warnings deduct 2 each
- **GIVEN** three findings with `severity=warning`
- **WHEN** score is computed
- **THEN** `score` equals `94`

#### Scenario: Verdict thresholds applied correctly
- **GIVEN** scores of 85, 60, and 45
- **WHEN** verdict is determined
- **THEN** score 85 → `"PASS"`, score 60 → `"PASS_WITH_ADVISORY"`, score 45 → `"FAIL"`

#### Scenario: Score capped at 120
- **GIVEN** conditions that would produce a score exceeding 120
- **WHEN** score is computed
- **THEN** `score` equals `120`
