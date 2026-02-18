## MODIFIED Requirements

### Requirement: Confidence-Based Routing

The system SHALL route bundle mappings based on confidence thresholds: auto-assign (>=0.8), prompt user (0.5-0.8), require explicit selection (<0.5).

#### Scenario: Refine/import `--auto-bundle` executes runtime mapping flow

- **GIVEN** `bundle-mapper` module is installed and a user runs backlog refine/import with `--auto-bundle`
- **WHEN** items are processed for OpenSpec bundle assignment
- **THEN** `BundleMapper` confidence scoring is executed for each item
- **AND** confidence routing behavior is enforced (auto/prompt/explicit selection) instead of placeholder or no-op import messaging
- **AND** resulting mapping decision is persisted via configured mapping history/rules storage.
