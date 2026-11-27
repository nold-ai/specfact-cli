## ADDED Requirements

### Requirement: Isolate marketplace smoke installations

Direct and console smoke launchers SHALL use a workspace-owned interpreter,
leaving the invoking test environment unchanged. Their marketplace resolution
SHALL use committed version constraints and SHALL not download new packages.

#### Scenario: Direct launcher owns its installation prefix

- **GIVEN** smoke is called from the running pytest interpreter
- **WHEN** the direct launcher is prepared
- **THEN** its prefix is inside the smoke workspace and differs from pytest's prefix

#### Scenario: Frozen marketplace resolution preserves parent imports

- **GIVEN** reviewed runtime dependencies are installed in the invoking environment
- **WHEN** direct or console marketplace modules are installed
- **THEN** frozen package versions satisfy module requirements without upgrading parent files
- **AND** missing or incompatible dependencies fail visibly
