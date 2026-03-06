## ADDED Requirements

### Requirement: Intent Capture Skill
The system SHALL provide a SQUER-based intent capture Agent Skill at `skills/specfact-intent-capture/SKILL.md` that guides AI agents through a 7-question business intent interview and persists the result to `.specfact/requirements/{id}.req.yaml`.

#### Scenario: Intent capture skill performs SQUER 7-question interview
- **GIVEN** an AI IDE agent with the `specfact-intent-capture` skill installed
- **WHEN** the agent activates the intent capture skill
- **THEN** the skill prompts the user with the 7 SQUER questions in sequence: What problem? Who has it? What happens today? What should change? How will we know? What must not break? What's the priority?
- **AND** answers are mapped to `BusinessOutcome` fields (description, persona, current_state, target_state, success_criteria, constraints, priority)

#### Scenario: Intent capture produces valid requirement artifact
- **GIVEN** the SQUER interview is complete with all 7 answers
- **WHEN** the skill invokes `specfact requirements capture`
- **THEN** a `.specfact/requirements/{id}.req.yaml` file is created
- **AND** the artifact validates against the `BusinessOutcome` schema without errors

#### Scenario: Intent capture skill verifies CLI prerequisites
- **GIVEN** a fresh IDE session before the skill is activated
- **WHEN** the skill checks prerequisites
- **THEN** it runs `specfact requirements --help` to verify the requirements module is installed
- **AND** if the module is missing it directs the agent to install it before proceeding

### Requirement: Requirements Decomposition Skill
The system SHALL provide a decomposition Agent Skill at `skills/specfact-intent-decompose/SKILL.md` that takes a captured `BusinessOutcome` and decomposes it into `BusinessRule` (Given/When/Then) and `ArchitecturalConstraint` artifacts via `specfact requirements validate`.

#### Scenario: Decomposition skill generates G/W/T business rules
- **GIVEN** a `.specfact/requirements/{id}.req.yaml` file containing a `BusinessOutcome`
- **WHEN** the agent activates the intent decompose skill
- **THEN** the skill prompts the agent to derive at least one `BusinessRule` per success criterion
- **AND** each rule is expressed in Given/When/Then format and assigned a stable rule ID (BR-NNN)

#### Scenario: Decomposition skill identifies architectural constraints
- **GIVEN** a decomposition session with at least one business rule defined
- **WHEN** the skill processes the rules
- **THEN** it prompts the agent to identify at least one `ArchitecturalConstraint` derived from the constraints field of the `BusinessOutcome`
- **AND** each constraint is assigned a stable ID (AC-NNN) and linked to the parent `BusinessOutcome`

### Requirement: Architecture Derivation Skill
The system SHALL provide an architecture derivation Agent Skill at `skills/specfact-intent-architecture/SKILL.md` that invokes `specfact architecture derive` to generate ADRs from captured requirements context.

#### Scenario: Architecture skill generates ADR from requirements
- **GIVEN** at least one `BusinessRule` and one `ArchitecturalConstraint` in `.specfact/requirements/`
- **WHEN** the agent activates the architecture derive skill
- **THEN** the skill invokes `specfact architecture derive --requirement {id}`
- **AND** an Architecture Decision Record is produced with Context, Decision, and Consequences sections
- **AND** the ADR includes an explicit link to the `BusinessOutcome` ID and at least one `ArchitecturalConstraint` ID

### Requirement: Trace Validation Skill
The system SHALL provide a trace validation Agent Skill at `skills/specfact-intent-trace-validate/SKILL.md` that validates the full traceability chain (outcome → rule → constraint → spec → code) and reports gaps with structured fix prompts.

#### Scenario: Trace validation reports complete chain
- **GIVEN** a project with requirements, specs, and code present
- **WHEN** the agent activates the trace-validate skill
- **THEN** the skill invokes `specfact validate --full-chain`
- **AND** a gap report is produced listing any orphaned artifacts (requirements with no spec link, specs with no test, etc.)

#### Scenario: Trace validation generates fix prompts for gaps
- **GIVEN** the trace validation finds at least one gap
- **WHEN** the skill processes the gap report
- **THEN** it generates a structured fix prompt for each gap type (missing spec, missing test binding, missing requirement link)
- **AND** the fix prompt references the specific artifact IDs involved

### Requirement: Evidence Check Skill
The system SHALL provide an evidence-check Agent Skill at `skills/specfact-intent-evidence-check/SKILL.md` that checks evidence completeness for all artifacts in the intent-to-code chain.

#### Scenario: Evidence check reports missing evidence envelopes
- **GIVEN** a project where some artifacts lack evidence JSON files
- **WHEN** the agent activates the evidence-check skill
- **THEN** the skill invokes `specfact validate --full-chain --evidence-dir .specfact/evidence/`
- **AND** a report lists all artifacts missing evidence envelopes with their IDs and types
- **AND** the exit code is non-zero if any required evidence is missing in strict mode

### Requirement: Intent Skills Installation
The system SHALL extend `specfact ide skill install` with a `--type` option so intent skills can be installed independently of spec-validation skills.

#### Scenario: Intent skills installed via CLI
- **GIVEN** the `specfact ide skill install` command is available (from ai-integration-01)
- **WHEN** the user runs `specfact ide skill install --type intent`
- **THEN** all 6 intent skill files are copied to the IDE-appropriate location
- **AND** the command confirms each skill file was installed successfully

#### Scenario: Existing spec skill install is backwards-compatible
- **GIVEN** a user running `specfact ide skill install` without the `--type` flag
- **WHEN** the command executes
- **THEN** it behaves identically to the pre-change behavior (installs spec skills only)
- **AND** no error or deprecation warning is emitted

#### Scenario: All skill types installed with --type all
- **GIVEN** the `--type all` option is used
- **WHEN** the command executes
- **THEN** both spec skills (from ai-integration-01) and intent skills are installed
- **AND** no file is overwritten without a confirmation prompt if conflicts exist
