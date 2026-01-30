# Definition of Done (DoD)

## ADDED Requirements

### Requirement: DoD configuration

The system SHALL support loading a DoD configuration (checklist or rule set) from project config (e.g. `.specfact/dod.yaml` or under templates), similar in spirit to DoR.

**Rationale**: Teams need to define completion criteria (e.g. tests pass, docs updated, code reviewed) per project.

#### Scenario: Load DoD config from project

**Given**: A project with a DoD config file (e.g. `.specfact/dod.yaml`) defining a checklist (e.g. tests_pass, docs_updated, code_reviewed)

**When**: The user runs a backlog command that uses DoD (e.g. `specfact backlog list` or `specfact backlog dod` with DoD enabled)

**Then**: The system loads the DoD config and uses it for validation

**And**: If no DoD config exists, DoD validation is skipped or a clear message is shown

**Acceptance Criteria**:

- DoD config schema is documented; loader does not crash on missing or invalid config (report clearly).

### Requirement: DoD validation for done items

The system SHALL run DoD validation against backlog items in "Done" (or equivalent) state when the user opts in and config is present.

**Rationale**: Only items in done state are checked against completion criteria.

#### Scenario: DoD validation for done item

**Given**: A backlog item in Done state and a loaded DoD config with criteria (e.g. tests_pass, docs_updated)

**When**: The user runs backlog list/export or `specfact backlog dod` with DoD enabled

**Then**: The system runs the DoD checklist against the item and produces a result (pass/fail + which criteria failed)

**Acceptance Criteria**:

- Result is deterministic; failed criteria are listed; no silent swallow of errors.

#### Scenario: DoD not run for non-done items

**Given**: A backlog item not in Done state (e.g. In Progress)

**When**: The user runs a command with DoD validation enabled

**Then**: DoD validation is not applied to that item (or item is skipped for DoD)

**Acceptance Criteria**:

- Only items in Done (or equivalent) state are validated against DoD.

### Requirement: DoD status in output and export

The system SHALL display or export DoD status (pass/fail, criteria) for done items when DoD validation is enabled.

**Rationale**: Teams need to see which done items meet DoD and which do not.

#### Scenario: DoD status in CLI output

**Given**: Backlog items in Done state and DoD validation has been run

**When**: The user runs `specfact backlog list` (or equivalent) with DoD enabled

**Then**: The output includes DoD status per done item (e.g. pass/fail, list of failed criteria)

**Acceptance Criteria**:

- Output is readable (e.g. column or section per item); export format includes DoD status when applicable.
