## ADDED Requirements

### Requirement: Compact preflight gate instructions

Generated instruction sections SHALL reference the installed canonical preflight workflow and SHALL state selection, approval, stale/unknown/blocking stop, owner-authorized refinement, and rerun requirements without embedding validator logic.

#### Scenario: AGENTS.md section is generated

- **GIVEN** a verified `specfact-preflight` skill installation and a supported AGENTS.md target
- **WHEN** instruction generation is approved
- **THEN** the managed section references the verified harness-native invocation
- **AND** the section does not copy the full skill or Python validation rules.

### Requirement: Idempotent managed sections

Instruction generation SHALL update only a bounded owned section identified by stable markers and inventory metadata.

#### Scenario: Generation runs twice unchanged

- **GIVEN** the workflow identity, target mapping, and generated gate content are unchanged
- **WHEN** generation runs again
- **THEN** no duplicate section or content churn is produced
- **AND** the inventory remains consistent.

#### Scenario: Managed markers are malformed

- **GIVEN** a target contains one missing or duplicated ownership marker
- **WHEN** regeneration is requested
- **THEN** generation stops with a recovery diagnostic
- **AND** user-authored content is not rewritten.

### Requirement: OpenSpec pre-apply ordering

For an OpenSpec project, generated instructions SHALL require proposal artifacts and strict validation followed by the installed preflight workflow before any apply/implementation command.

#### Scenario: Agent prepares to run OpenSpec apply

- **GIVEN** proposal, specs, design, and tasks are ready
- **WHEN** the agent reaches `/opsx:apply`, `/openspec:apply`, or the harness-equivalent implementation step
- **THEN** it first requires a current approved preflight seal
- **AND** blocked, unknown, stale, or unapproved results return to the owning planning artifact.

### Requirement: Spec Kit pre-implement ordering

For a Spec Kit project, generated instructions SHALL place the installed preflight workflow after the applicable specify/clarify/plan/checklist/tasks/analyze quality loop and before implementation.

#### Scenario: Agent prepares to run Spec Kit implement

- **GIVEN** the selected feature has completed its required planning and analysis commands
- **WHEN** the agent reaches `/speckit.implement` or the harness-equivalent form
- **THEN** it first requires current preflight approval
- **AND** findings route back to specify/clarify, plan, or tasks according to the owning artifact.

### Requirement: Respect upstream context ownership

Instruction generation SHALL use only supported owned sections and SHALL not assume the OpenSpec or Specify base CLI owns AGENTS.md or other context files.

#### Scenario: Spec Kit agent-context extension is absent

- **GIVEN** the selected integration requires the opt-in Spec Kit `agent-context` extension and it is not enabled
- **WHEN** generation is requested
- **THEN** the generator reports the missing owned context surface and supported setup path
- **AND** it does not silently take over the entire context file.

### Requirement: Installed metadata selects invocation syntax

The generator SHALL resolve the invocation form from verified installed workflow and target-adapter metadata rather than hard-coded harness-name guesses.

#### Scenario: Target uses skill-based invocation

- **GIVEN** the installed metadata declares a dollar-prefixed or skill-prefixed native form
- **WHEN** instructions are generated
- **THEN** that verified form is emitted
- **AND** an unsupported slash alias is not invented.

### Requirement: External packaging remains separate

Generated instructions SHALL expose a reusable managed-section contract without creating or publishing Codex, ECC, hatch3r, or other external adapter packages.

#### Scenario: Preflight adapter consumes the instruction contract

- **GIVEN** a later external adapter targets a supported harness
- **WHEN** it generates its native assets
- **THEN** it may reuse the same gate fields and workflow identity
- **AND** adapter packaging remains owned by its modules change.
