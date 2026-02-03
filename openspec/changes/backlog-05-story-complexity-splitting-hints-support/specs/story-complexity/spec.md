# Story complexity and splitting hints

## ADDED Requirements

This change implements the Story Complexity Analysis requirements from `openspec/specs/backlog-refinement/spec.md`; scenarios below restate and scope them for this change.

### Requirement: Complexity score and needs-splitting flag

The system SHALL calculate a complexity score from story_points and business_value and SHALL flag stories above a configurable threshold (e.g. 13 points) as needing potential splitting.

**Rationale**: Teams need to identify oversized stories before commitment.

#### Scenario: Story points complexity calculation

**Given**: A backlog item with `story_points = 13` and `business_value = 8`

**When**: Complexity score is calculated

**Then**: The score considers both story points and business value

**And**: Stories > 13 points (or above configured threshold) are flagged for potential splitting

**Acceptance Criteria**:

- Threshold is configurable (e.g. via config or default 13); needs_splitting(item, threshold) is deterministic.

#### Scenario: Needs splitting predicate

**Given**: A backlog item with story_points = 21 and threshold = 13

**When**: needs_splitting(item, threshold) is evaluated

**Then**: The result is True (item is flagged for splitting)

**Acceptance Criteria**:

- Items at or below threshold return False; items above return True; missing story_points handled per documented behavior.

### Requirement: Splitting suggestion (rationale and split points)

The system SHALL suggest splitting into multiple stories under the same feature and provide rationale and recommended split points (e.g. by acceptance criteria or logical boundaries).

**Rationale**: Teams need actionable guidance on how to split complex stories.

#### Scenario: Splitting suggestion generation

**Given**: A backlog item flagged for splitting (e.g. story_points > 13) with acceptance_criteria or logical boundaries

**When**: Story splitting detection is performed

**Then**: The system suggests splitting into multiple stories under the same feature

**And**: The suggestion includes rationale and recommended split points (e.g. derived from acceptance criteria or optional AI hint)

**Acceptance Criteria**:

- Suggestion is deterministic or explicitly best-effort; rationale and split points are present in output when available.

### Requirement: Splitting suggestion in refinement output

The system SHALL include a story splitting suggestion in refinement output (CLI and export-to-tmp) when the refined item is complex (above threshold).

**Rationale**: Refinement sessions must surface size/scope risks in the same flow.

#### Scenario: Story splitting suggestion in refinement output

**Given**: A backlog item refinement session with a complex story (e.g. story_points > 13)

**When**: Refinement completes and output (or export-to-tmp) is emitted

**Then**: The output includes a "Story splitting suggestion" section for that item

**And**: The suggestion includes recommended split points and rationale

**Acceptance Criteria**:

- Section appears only for items above threshold; non-complex items do not show splitting suggestion; export-to-tmp format includes suggestion when applicable.

### Requirement: Integration under backlog refine only

The system SHALL integrate complexity and splitting into `specfact backlog refine` only; there SHALL be no top-level scrum/refine command.

**Rationale**: Align with backlog command group; no new top-level commands.

#### Scenario: Invoke via backlog refine

**Given**: SpecFact CLI is installed and backlog refine is used

**When**: The user runs `specfact backlog refine` (with item(s) that may be complex)

**Then**: Refinement output (and export-to-tmp when used) includes complexity/splitting suggestion for complex items

**Acceptance Criteria**:

- Behavior is discoverable as part of existing `specfact backlog refine`; no new top-level commands.

### Requirement: Dependency-aware splitting (E3 extension)

The system SHALL consider dependency edges (minimize cross-team coupling) and blast radius (modules touched, component tags when available) when generating splitting suggestions. When patch mode (patch-mode-preview-apply) is available, SHALL provide "split proposal" as suggested child stories with titles, AC, and links. Splitting recommendation output SHALL include a "dependency impact" section when dependency data exists.

**Rationale**: Plan E3—splitting should reduce cross-team coupling and surface blast radius.

#### Scenario: Splitting suggestion includes dependency impact

**Given**: Dependency graph (add-backlog-dependency-analysis-and-commands) and optional patch mode are available; item has dependencies or touched modules

**When**: Splitting suggestion is generated for a complex story

**Then**: The suggestion includes a "dependency impact" section (cross-team edges, blast radius when available)

**And**: When patch mode is used, split proposal is emitted as suggested child stories (titles, AC, links)

**Acceptance Criteria**:

- Splitting recommendation includes "dependency impact" section when dependency data exists; patch output for split proposal when patch mode available.
