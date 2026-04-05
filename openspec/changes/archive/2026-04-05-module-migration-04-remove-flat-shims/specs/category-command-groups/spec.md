## MODIFIED Requirements

### Requirement: Bootstrap mounts category groups when grouping is enabled

Bootstrap SHALL mount only category group apps (and core commands) when `category_grouping_enabled` is true. It SHALL NOT register any shim loaders for flat command names.

#### Scenario: No shim registration at bootstrap

- **GIVEN** `category_grouping_enabled` is `true`
- **WHEN** the CLI bootstrap runs
- **THEN** the registry SHALL contain entries only for core commands and the five category group names
- **AND** SHALL NOT contain entries for `analyze`, `drift`, `validate`, `repro`, `backlog`, `policy`, `project`, `plan`, `import`, `sync`, `migrate`, `contract`, `spec`, `sdd`, `generate`, `enforce`, `patch` as top-level commands
