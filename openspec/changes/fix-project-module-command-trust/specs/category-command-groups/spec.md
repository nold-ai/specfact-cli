## ADDED Requirements

### Requirement: Official bundle category groups are identity-bound

The CLI SHALL mount a recognized official bundle category only when an enabled discovered package declares both the recognized bundle and its expected canonical `nold-ai/<bundle>` module identity.

#### Scenario: Project manifest impersonates requirements bundle

- **GIVEN** a discovered package is named `attacker/evil-requirements`
- **AND** its manifest declares bundle `specfact-requirements` and command `requirements`
- **WHEN** installed category groups are mounted
- **THEN** the package is not treated as the official requirements bundle
- **AND** no attacker loader is mounted as the root `requirements` command

#### Scenario: Canonical requirements module is eligible

- **GIVEN** an enabled verified package is named `nold-ai/specfact-requirements`
- **AND** it declares bundle `specfact-requirements`
- **WHEN** installed category groups are mounted
- **THEN** the requirements category remains eligible for root mounting
