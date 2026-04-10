## ADDED Requirements

### Requirement: Compact AGENTS bootstrap contract
The repository SHALL keep `AGENTS.md` as the mandatory bootstrap governance surface, but it SHALL remain compact and SHALL delegate long-form operational detail to canonical rule artifacts.

#### Scenario: Session bootstrap reads compact governance contract
- **WHEN** an agent starts work in the repository
- **THEN** it reads `AGENTS.md` first
- **AND** `AGENTS.md` defines a mandatory bootstrap sequence rather than embedding the full long-form governance corpus
- **AND** the bootstrap sequence requires loading `docs/agent-rules/INDEX.md`
- **AND** the bootstrap sequence requires loading the canonical non-negotiable checklist before code implementation work

#### Scenario: AGENTS stays compact while preserving enforcement
- **WHEN** repository governance is updated
- **THEN** `AGENTS.md` SHALL retain only the bootstrap contract, invariant governance rules, and canonical references needed for startup
- **AND** detailed workflow, validation, or finalization guidance SHALL live in dedicated rule artifacts rather than being duplicated inline

### Requirement: Deterministic rule index and loading semantics
The repository SHALL provide a canonical rule index that deterministically decides which governance rule files must be loaded for a given task.

#### Scenario: Always-load rule subset
- **WHEN** an agent loads the governance rule index
- **THEN** the index SHALL identify a mandatory always-load subset
- **AND** that subset SHALL include the non-negotiable checklist
- **AND** the index SHALL define the order in which always-load rules are processed

#### Scenario: Applicability-based rule loading
- **WHEN** a task involves worktree management, OpenSpec change selection, GitHub issue coordination, TDD gating, quality verification, or finalization
- **THEN** the index SHALL map those task signals to specific `docs/agent-rules/*.md` files
- **AND** the index SHALL define which rule files are required versus optional for that task class
- **AND** the loading decision SHALL not depend on heuristic file-name guessing alone

#### Scenario: Deterministic precedence
- **WHEN** governance instructions overlap across `AGENTS.md`, the rule index, rule files, and change-local artifacts
- **THEN** the repository SHALL define a single precedence order for which instruction wins
- **AND** the precedence order SHALL include explicit handling for direct user override where repository governance permits it

### Requirement: Governance rule files use machine-readable frontmatter
Every dedicated governance rule artifact SHALL include machine-readable frontmatter that defines how and when the rule applies.

#### Scenario: Required frontmatter fields are present
- **WHEN** a file under `docs/agent-rules/` is intended to govern agent behavior
- **THEN** it SHALL include frontmatter fields for rule identity, applicability, priority, blocking semantics, and stop conditions
- **AND** it SHALL declare whether the file is always loaded
- **AND** it SHALL declare whether user interaction is required when the rule blocks progress

#### Scenario: Frontmatter drives deterministic behavior
- **WHEN** an agent evaluates a rule file with frontmatter
- **THEN** it can determine from metadata whether the rule is mandatory for the current task
- **AND** it can determine whether the rule requires a hard stop, read-only continuation, or interactive clarification
- **AND** it does not need to infer those semantics solely from unstructured prose

### Requirement: Governance must define explicit stop and continue behavior
The governance system SHALL define explicit blocking behavior for stale changes, concurrency ambiguity, missing metadata, and TDD gate violations.

#### Scenario: Blocking ambiguity requires user clarification
- **WHEN** a selected change is stale, superseded, ambiguous, or linked to GitHub work already in progress
- **THEN** the applicable rule SHALL require the agent to stop implementation work
- **AND** the rule SHALL state that the ambiguity must be surfaced to the user for clarification
- **AND** the rule SHALL define whether read-only investigation may continue while implementation remains blocked

#### Scenario: TDD gate remains non-bypassable in compact governance
- **WHEN** a task changes behavior in code
- **THEN** the applicable rule SHALL still require spec updates, test creation, failing-test evidence, implementation, and passing evidence in that order
- **AND** compact governance SHALL not weaken or omit that sequence

### Requirement: Public GitHub work must pass metadata completeness checks
The governance system SHALL define explicit readiness checks for linked GitHub change issues before implementation proceeds for public repository work.

#### Scenario: Parent and dependency metadata must be complete
- **WHEN** an agent prepares to implement a publicly tracked change with a linked GitHub issue
- **THEN** the applicable governance rules SHALL require verifying the issue's parent relationship, blockers, and blocked-by relationships against current repository GitHub reality
- **AND** the parent lookup SHALL use the local hierarchy cache first and refresh the cache when repository-defined freshness rules require it
- **AND** implementation SHALL not proceed if the required parent or dependency metadata is missing or ambiguous

#### Scenario: Labels and project assignment must be complete
- **WHEN** an agent prepares to implement a publicly tracked change with a linked GitHub issue
- **THEN** the applicable governance rules SHALL require verifying that the issue has the required labels and project assignment for repository workflow completeness
- **AND** implementation SHALL not proceed until that metadata is complete or the user explicitly directs an allowed exception path

#### Scenario: Live GitHub issue state can block implementation
- **WHEN** an agent prepares to implement a publicly tracked change with a linked GitHub issue
- **AND** the issue is already marked `in progress`
- **THEN** the governance rules SHALL treat that state as a concurrency ambiguity
- **AND** the agent SHALL stop implementation work and ask the user to clarify whether the change is already being worked in another session
- **AND** the rules SHALL define whether only read-only investigation may continue while implementation remains blocked

### Requirement: Canonical aliases prevent instruction drift
Repository instruction surfaces other than `AGENTS.md` SHALL reference the canonical governance rule system instead of embedding duplicate long-form policy text.

#### Scenario: Alias instruction surfaces stay synchronized
- **WHEN** a contributor reads another repository instruction surface such as `CLAUDE.md` or generated IDE guidance
- **THEN** the surface SHALL reference the canonical rule system for governance semantics
- **AND** it SHALL avoid copying long-form governance content that could drift from the canonical source
