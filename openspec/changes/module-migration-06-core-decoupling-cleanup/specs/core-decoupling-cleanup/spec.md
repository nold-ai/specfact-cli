## ADDED Requirements

### Requirement: Core Package Ownership Boundary

The `specfact-cli` core package SHALL include only components required for permanent core runtime responsibilities and SHALL not retain bundle-only implementation structures after module extraction/slimming.

#### Scenario: Residual bundle-only components are identified and removed from core

- **GIVEN** module extraction and core slimming are complete
- **WHEN** the decoupling cleanup runs
- **THEN** components in core that are only needed by extracted bundles are either moved out or replaced by stable interfaces.

#### Scenario: Boundary regression tests prevent re-coupling

- **GIVEN** the decoupling cleanup is complete
- **WHEN** tests validate core import boundaries
- **THEN** tests fail if new bundle-only couplings are introduced into core.

#### Scenario: User-facing command behavior remains stable

- **GIVEN** internal decoupling refactors are applied
- **WHEN** users run supported core and installed-bundle commands
- **THEN** observable command behavior remains compatible with current migration topology.
