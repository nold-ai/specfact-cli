## MODIFIED Requirements

### Requirement: Live docs reflect lean-core and grouped bundle command topology

The live authored documentation set SHALL use command examples and migration guidance that match the currently shipped core and bundle command groups, and SHALL NOT present removed or transitional command families as current syntax.

#### Scenario: Reader copies a documented command after the split

- **WHEN** a reader copies a command from `README.md` or authored docs under `docs/`
- **THEN** the command path matches a currently shipped surface from the active CLI release
- **AND** removed or transitional syntax such as `specfact project plan ...`, `specfact project import from-bridge ...`, `specfact backlog policy ...`, or retired `specfact spec ...` subgroup trees is replaced, removed, or clearly labeled as historical context
- **AND** command examples route readers through the correct current group for that workflow area (`backlog`, `code`, `govern`, `project`, or `spec`)

### Requirement: Command reference reflects ownership and package boundaries

The command reference and migration guidance SHALL map old flat or pre-split syntax to currently shipped command groups and supported parameter forms, and SHALL NOT redirect readers from one removed surface to another removed surface.

#### Scenario: Reader checks migration mapping for removed syntax

- **WHEN** a reader opens command reference or migration guidance to translate older SpecFact examples
- **THEN** the docs identify whether a legacy surface still exists, moved to a current command group, or no longer has a direct supported equivalent
- **AND** the guidance uses currently executable commands and current option names for any documented replacement path
- **AND** the docs do not present `project plan` as the replacement for removed flat commands in the post-split CLI
