## ADDED Requirements

### Requirement: Inactive caches do not invalidate an approved module tree

The CLI SHALL use the approved artifact inventory to authenticate installed module files and distinguish bytecode caches that cannot be selected by the running importer from caches it may use.

#### Scenario: An approved module is shared with a newer Python or pytest

- **GIVEN** an installed module whose released files match the approved artifact
- **AND** an authenticated source file has a standard CPython 3.14 cache for a different interpreter or a pytest assertion cache the current importer cannot select
- **WHEN** the CLI verifies the installed module
- **THEN** those inactive cache files do not prevent the module from loading.

#### Scenario: Cache handling preserves integrity checks

- **GIVEN** an installed module contains changed released files, an unrecognized cache, or an active cache that fails verification
- **WHEN** the CLI verifies the installed module
- **THEN** it rejects that module without executing its payload.
