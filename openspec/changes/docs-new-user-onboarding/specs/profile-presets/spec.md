## MODIFIED Requirements

### Requirement: Profile presets resolve to canonical bundle sets and install them

The four profile presets SHALL resolve to the exact canonical bundle set and install each bundle
via the marketplace installer. The `solo-developer` profile SHALL include
`nold-ai/specfact-code-review` so that `specfact code review run` is available immediately after
running `specfact init --profile solo-developer`.

#### Scenario: solo-developer profile installs codebase and code-review bundles

- **GIVEN** a fresh SpecFact install or an install where specfact-codebase and specfact-code-review
  are not yet installed
- **WHEN** the user runs `specfact init --profile solo-developer`
- **THEN** the CLI SHALL install `nold-ai/specfact-codebase` from the marketplace registry
- **AND** SHALL install `nold-ai/specfact-code-review` from the marketplace registry
- **AND** SHALL confirm: "Installed: specfact-codebase, specfact-code-review"
- **AND** after completion, `specfact code review run --path . --scope full` SHALL be available
  and produce a scored review result

#### Scenario: backlog-team profile installs three bundles in dependency order

- **GIVEN** a fresh SpecFact install
- **WHEN** the user runs `specfact init --profile backlog-team`
- **THEN** the CLI SHALL install: `specfact-project`, `specfact-backlog`, `specfact-codebase`
- **AND** SHALL install `specfact-project` before `specfact-backlog`

#### Scenario: api-first-team profile installs spec and codebase bundles

- **GIVEN** a fresh SpecFact install
- **WHEN** the user runs `specfact init --profile api-first-team`
- **THEN** the CLI SHALL install: `specfact-spec`, `specfact-codebase`
- **AND** `specfact-project` SHALL be auto-installed if required as a transitive dependency

#### Scenario: enterprise-full-stack profile installs all five bundles

- **GIVEN** a fresh SpecFact install
- **WHEN** the user runs `specfact init --profile enterprise-full-stack`
- **THEN** the CLI SHALL install all five bundles:
  `specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, `specfact-govern`

#### Scenario: Profile canonical bundle mapping is machine-verifiable

- **GIVEN** a request for any valid profile name
- **WHEN** `specfact init --profile <name>` is executed
- **THEN** the resolved bundle set SHALL be:
  - `solo-developer` → `[specfact-codebase, specfact-code-review]`
  - `backlog-team` → `[specfact-project, specfact-backlog, specfact-codebase]`
  - `api-first-team` → `[specfact-spec, specfact-codebase]`
  - `enterprise-full-stack` → `[specfact-project, specfact-backlog, specfact-codebase, specfact-spec, specfact-govern]`
- **AND** no profile SHALL install bundles outside its canonical set

#### Scenario: Invalid profile name produces actionable error

- **GIVEN** the user runs `specfact init --profile unknown-profile`
- **WHEN** the CLI processes the command
- **THEN** the CLI SHALL print an error listing valid profile names:
  solo-developer, backlog-team, api-first-team, enterprise-full-stack
