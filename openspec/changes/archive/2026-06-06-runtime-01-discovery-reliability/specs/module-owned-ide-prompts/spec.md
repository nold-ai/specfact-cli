## MODIFIED Requirements

### Requirement: IDE prompt export SHALL use installed module resources

`specfact init ide` SHALL discover prompt templates from installed module packages and their packaged resource directories. The export flow SHALL not depend on workflow prompt files stored under the core CLI package for bundle-owned commands.

#### Scenario: IDE setup accepts explicit environment manager

- **GIVEN** prompt templates are available for export
- **WHEN** the user runs `specfact init ide --env-manager uv`
- **THEN** IDE prompt export uses the selected `uv` environment manager metadata for dependency setup decisions
- **AND** the command does not emit the "No Compatible Environment Manager Detected" warning for that explicit manager
