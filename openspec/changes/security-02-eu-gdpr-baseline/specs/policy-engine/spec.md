## MODIFIED Requirements

### Requirement: Policy Packs Define Declarative Enforcement Rules

The policy engine SHALL parse versioned policy packs that declare enforcement rules for review, security, privacy, and governance domains without hardcoding domain-specific logic in command handlers.

#### Scenario: Security GDPR namespace loads with deterministic keys

- **GIVEN** a policy pack contains a `security.gdpr` section
- **WHEN** the policy engine loads the pack
- **THEN** lawful basis, residency allowlist, retention, deletion, and breach-handling keys are validated against the core schema
- **AND** invalid keys or malformed values fail validation before command execution.

#### Scenario: Enforcement mode applies to GDPR findings

- **GIVEN** a loaded policy pack and incoming GDPR findings from the unified security model
- **WHEN** the policy engine evaluates those findings
- **THEN** advisory, mixed, and hard modes are applied consistently with other review/security domains
- **AND** category-specific metadata remains attached to the finding output.

### Requirement: `security.gdpr` namespace structure and validation

The policy engine SHALL treat `security.gdpr` as a structured subtree with the keys `lawful_basis`, `residency`,
`retention`, and `deletion` (each MAY be absent when not applicable to the active profile, but MUST be present and
well-typed when the baseline marks them required).

#### Scenario: Enterprise overlays merge with metadata precedence

- **GIVEN** enterprise pushed packs and local/project packs both define `security.gdpr` inputs
- **WHEN** resolution merges layers per `enterprise-01-policy-resolution-extension`
- **THEN** enterprise mandatory layers override conflicting non-enterprise values for the same key path
- **AND** enterprise layers that are **missing required pushed-rule metadata** (`mandatory`, `override_allowed`,
  `effective_from`, `pushed_by`, `signed_by`) or are **structurally invalid** for the declared schema are rejected
  before command execution (aligned with the metadata contract in `enterprise-01-policy-resolution-extension`, without
  claiming standalone cryptographic verification beyond what that change defines).

#### Scenario: Missing required GDPR metadata fails fast in hard mode

- **GIVEN** a profile marks a GDPR control as required and metadata is absent
- **WHEN** the policy engine validates the resolved configuration in `hard` mode
- **THEN** validation fails before scanners run with a deterministic validation finding.

#### Scenario: Missing required GDPR metadata is advisory-only in advisory mode

- **GIVEN** a profile marks a GDPR control as required and metadata is absent
- **WHEN** the policy engine validates the resolved configuration in `advisory` mode
- **THEN** the engine MAY emit advisory findings without blocking execution.
