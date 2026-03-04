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

### Requirement: Core Must Not Import From Bundle Packages

The `specfact-cli` core (`src/specfact_cli/`) SHALL NOT import from bundle packages (`backlog_core`, `bundle_mapper`, or other extracted bundle namespaces). Core modules (init, module_registry, upgrade) and shared infrastructure (models, utils, adapters, registry) must remain decoupled from bundle implementation details.

#### Scenario: Core import boundary is enforced by regression tests

- **GIVEN** core and bundle packages coexist in the repository
- **WHEN** boundary tests run
- **THEN** any file under `src/specfact_cli/` that imports from `backlog_core` or `bundle_mapper` causes the test to fail.

### Migration Acceptance Criteria

- [ ] Inventory of candidate core components (keep/move/interface) produced and documented
- [ ] No core file imports from `backlog_core` or `bundle_mapper`
- [ ] Boundary regression tests pass
- [ ] Quality gates (format, type-check, lint, contract-test, smart-test) pass
- [ ] docs/architecture updated with core vs modules-repo ownership boundary
