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
