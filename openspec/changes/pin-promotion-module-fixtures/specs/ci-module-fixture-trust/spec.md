## ADDED Requirements

### Requirement: CI module fixture checkouts use reviewed literal identities

Core CI SHALL check out the reviewed module fixtures using a literal official repository and immutable commit matching the checked-in lock. The workflow SHALL authenticate the resulting fixture before module-backed validation.

#### Scenario: The selected fixture matches the protected checkout inputs

- **GIVEN** a core workflow validates the CLI using the reviewed module or documentation fixture
- **WHEN** its module checkout step is resolved
- **THEN** the repository and commit are literal identities matching the corresponding lock, checkout credentials are not persisted, and the existing tree and documentation package integrity checks remain in force
