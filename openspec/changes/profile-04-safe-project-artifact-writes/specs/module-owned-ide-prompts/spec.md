## ADDED Requirements

### Requirement: Core materialization of module-owned IDE assets SHALL use safe project writes

When core setup flows materialize module-owned IDE assets into a user repository, they SHALL route all local file mutations through the core safe-write policy.

#### Scenario: Module-owned prompt export uses safe-write helper for settings mutation

- **WHEN** `specfact init ide` exports bundle-owned prompt files and updates a related IDE config artifact
- **THEN** the config mutation SHALL use the safe-write helper with declared ownership metadata
- **AND** the command SHALL preserve unrelated user-managed content in the target artifact

#### Scenario: Module-owned template copy does not silently replace existing user customization

- **WHEN** a core setup flow copies a module-owned template asset into a target path that already exists in the user repository
- **THEN** the flow SHALL skip, merge, or require explicit replacement according to the declared safe-write mode
- **AND** SHALL NOT silently overwrite the existing file
