## ADDED Requirements

### Requirement: Init IDE SHALL preserve unrelated VS Code settings

`specfact init ide` SHALL reconcile prompt recommendations into `.vscode/settings.json` without deleting unrelated user-managed settings.

#### Scenario: Existing non-SpecFact settings survive prompt export

- **WHEN** a repository already contains `.vscode/settings.json` with Python, test, or formatter settings
- **AND** the user runs `specfact init ide`
- **THEN** the command SHALL preserve those unrelated settings
- **AND** SHALL update only SpecFact-managed prompt recommendation entries

#### Scenario: Selective prompt export removes only prior SpecFact-managed recommendations

- **WHEN** the user runs `specfact init ide --prompts <subset>`
- **THEN** prior SpecFact-managed prompt recommendations outside the selected subset MAY be removed
- **AND** unrelated `.github/prompts/` recommendations and non-SpecFact settings SHALL remain unchanged

### Requirement: Init IDE SHALL fail safe on malformed settings documents

`specfact init ide` SHALL not replace malformed or unparsable VS Code settings with an empty or generated document by default.

#### Scenario: Malformed settings file blocks destructive rewrite

- **WHEN** `.vscode/settings.json` exists but cannot be parsed as JSON
- **THEN** `specfact init ide` SHALL stop with an actionable error
- **AND** SHALL leave the existing file unchanged unless explicit replacement is requested through the safe-write policy
