## ADDED Requirements

### Requirement: Preflight Context Assembler

The system SHALL select a tag-matched rule subset fitting a token budget and render it as an injectable context block.

#### Scenario: Assembler selects rules matching author intent

- **GIVEN** rules tagged `applies-to: [security, pii]` and `applies-to: [boundaries]` exist
- **WHEN** the assembler runs for intent `"add pii redaction to evidence writer"`
- **THEN** the selected set includes the PII-tagged rule
- **AND** the set includes boundaries-tagged rules only if `evidence writer` matches a boundaries keyword.

#### Scenario: Assembler respects token budget without splitting rules

- **GIVEN** a budget of 1500 tokens and candidate rules totalling 2200 tokens
- **WHEN** the assembler packs the set
- **THEN** the selected set is ≤ 1500 tokens
- **AND** no rule body is truncated — each is included whole or excluded.

#### Scenario: Assembler ordering is deterministic

- **GIVEN** candidate rules with equal confidence
- **WHEN** the assembler runs twice with the same rule snapshot
- **THEN** both runs produce the identical selected set and rendering order.

### Requirement: OpenSpec Authoring Gate

The system SHALL persist injected rule ids and a snapshot sha into `.openspec.yaml` whenever preflight injection occurs.

#### Scenario: `openspec new change` records preflight rules

- **GIVEN** rules exist and preflight is enabled
- **WHEN** `openspec new change <name>` runs
- **THEN** the generated `.openspec.yaml` contains `preflight_rules` with rule-id + version entries
- **AND** `preflight_rules_snapshot_sha` is populated.

#### Scenario: Disabled preflight emits explicit audit marker

- **GIVEN** preflight is disabled for this session
- **WHEN** a change is created
- **THEN** `.openspec.yaml` contains `preflight_rules: []` and `preflight_disabled_reason: <reason>`
- **AND** the reason is required (non-empty string).

### Requirement: Spec Validation Gate

The system SHALL enforce `enforcement: blocker` rules against draft specs and emit findings.

#### Scenario: Blocker rule violation fails validation

- **GIVEN** a draft spec that duplicates a requirement already covered by an existing capability
- **WHEN** validation runs
- **THEN** a blocker finding references the violated rule id and the duplicated requirement
- **AND** exit code is non-zero.

#### Scenario: Advisory rule violation surfaces without failing

- **GIVEN** a draft spec violating an `enforcement: advisory` rule
- **WHEN** validation runs
- **THEN** a finding is emitted with severity `advisory`
- **AND** exit code is zero.

### Requirement: Preflight Inspection Command

The system SHALL provide `specfact memory preflight <intent>` returning the rule set without mutating any file.

#### Scenario: Inspection returns selected rule set as JSON

- **GIVEN** a user runs `specfact memory preflight "add budget gate" --json`
- **WHEN** the command completes
- **THEN** stdout contains a JSON array of objects, each including the keys `rule_id`, `version`, `score`, and `included`
- **AND** `rule_id` is a string, `version` is a semver string, `score` is a number in the inclusive range `0.0`–`1.0`, and `included` is boolean (`true` when the rule is selected inside the token/budget allocation for this intent)
- **AND** future versions MAY add extra fields but MUST NOT remove or rename these four keys (compatibility guarantee for `enterprise-03-aggregation-and-drift-analytics` consumers of `specfact memory preflight --json` output)
- **AND** `.openspec.yaml` and `rules/` are unchanged
- **AND** authors follow project context rules in `openspec/config.yaml` when extending this contract in spec deltas.
