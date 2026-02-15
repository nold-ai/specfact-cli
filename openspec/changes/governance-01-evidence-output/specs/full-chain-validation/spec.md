## MODIFIED Requirements

### Requirement: Full Chain Validation
Full-chain validation SHALL emit governance-ready evidence artifacts.

#### Scenario: Evidence artifact is written with stable schema envelope
- **GIVEN** full-chain validation executes with evidence output enabled
- **WHEN** command completes
- **THEN** evidence includes schema version, timestamp, profile, policy mode, layer summaries, and overall status
- **AND** artifact path is printed for CI ingestion.
