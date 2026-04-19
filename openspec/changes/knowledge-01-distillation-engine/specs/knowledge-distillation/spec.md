## ADDED Requirements

### Requirement: Evidence / Learning / Rule Schema

The system SHALL define three artefact tiers — evidence, learning, rule — each with frontmatter contracts enforced at write-time.

#### Scenario: Evidence entry is written with canonical fingerprint

- **GIVEN** a reviewer emits a finding
- **WHEN** the evidence writer persists the entry
- **THEN** the entry includes `type: evidence`, `schema_version`, `source`, `domain`, `applies-to`, `fingerprint`, `observed-at`, `outcome`
- **AND** fingerprint is the sha256 of the canonical body with PII redaction applied first.

#### Scenario: Rule body exceeding 500 tokens is rejected

- **GIVEN** a promotion attempt produces a rule body of 501 tokens
- **WHEN** the writer validates the body
- **THEN** validation fails with a clear rule-id and the token overrun
- **AND** no rule file is written.

### Requirement: Distillation CLI Contract

The system SHALL provide `specfact memory distill` that produces learnings and a git-diff preview against rules without auto-merge.

#### Scenario: Distill produces a learning when evidence count meets threshold

- **GIVEN** 3 evidence entries share a `(domain, applies-to)` tuple and `min-evidence-count` is 3
- **WHEN** `specfact memory distill` runs
- **THEN** a learning file is written under `.specfact/memory/learnings/` referencing all 3 evidence fingerprints
- **AND** a dry-run diff against `.specfact/memory/rules/` is printed to stdout
- **AND** no rule file is modified on disk.

#### Scenario: Distill below threshold is a no-op

- **GIVEN** only 2 evidence entries share a tuple and threshold is 3
- **WHEN** `specfact memory distill` runs
- **THEN** no learning is written
- **AND** the command reports the group as `pending (2/3)`.

### Requirement: Promotion Gate

The system SHALL require an explicit `specfact memory promote` invocation to move a learning into `rules/`.

#### Scenario: Promote writes versioned rule file

- **GIVEN** a learning with confidence ≥ profile threshold exists
- **WHEN** `specfact memory promote <learning-id>` runs
- **THEN** a rule file is written with `version: 1.0.0`, `promoted-at`, `evidence-count`, `confidence`
- **AND** the learning file is updated to reference the promoted rule id.

#### Scenario: Promote respects supersedes chain

- **GIVEN** a learning proposes a rule that supersedes an existing rule in the same domain
- **WHEN** promotion occurs
- **THEN** the new rule frontmatter carries `supersedes: <previous-rule-id>`
- **AND** the previous rule is marked `status: superseded` but retained for audit.

### Requirement: MemoryBackend Protocol

The system SHALL expose a `MemoryBackend` protocol with a markdown-graph default implementation.

#### Scenario: Markdown-graph backend is the default

- **GIVEN** a fresh installation without explicit backend configuration
- **WHEN** memory operations execute
- **THEN** entries are persisted as markdown files under `.specfact/memory/`
- **AND** no vector-store dependency is imported or required.

#### Scenario: Backend protocol exposes required operations

- **GIVEN** an alternative backend implementation
- **WHEN** it is loaded
- **THEN** it exposes `add_entry`, `query`, `link`, `list_by_tag` with contract decorators
- **AND** failure to implement any raises at import time.
