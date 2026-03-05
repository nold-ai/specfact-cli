## ADDED Requirements

### Requirement: Module development docs reflect the dedicated modules repository model
The module development guide SHALL describe that official bundle implementation lives in `specfact-cli-modules`, while `specfact-cli` owns the lean runtime, registry, marketplace lifecycle, and shared contracts needed by installed bundles.

#### Scenario: Developer reads module development docs after modularization
- **WHEN** a contributor reads the module development guide
- **THEN** the guide explains the current two-repository model
- **AND** it identifies which code and documentation concerns belong in `specfact-cli` versus `specfact-cli-modules`

### Requirement: Directory and dependency docs reflect bundle boundaries
Module development, directory-structure, and dependency documentation SHALL describe the current bundle/package layout, canonical repository ownership, and bundle dependency relationships introduced by marketplace-installed official bundles.

#### Scenario: Contributor checks structure and dependency guidance
- **WHEN** a contributor reads directory or dependency documentation related to modules
- **THEN** the docs show the current bundle/package boundaries and repository ownership
- **AND** dependency explanations match the marketplace-installed bundle model rather than the former in-repo bundled module layout
