## ADDED Requirements

### Requirement: Marketplace module installation verifies before side effects

Marketplace installation SHALL validate publisher policy and artifact integrity before recursively installing bundle dependencies or invoking pip dependency resolution or installation.

#### Scenario: Unverified marketplace archive is rejected first

- **GIVEN** a marketplace archive with dependency declarations and invalid integrity metadata
- **WHEN** module installation runs
- **THEN** installation rejects the archive without dependency installation side effects
