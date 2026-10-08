## ADDED Requirements

### Requirement: Caller-Owned JWT Verification Options

The frozen runtime SHALL preserve caller-owned JWT mappings across unverified inspection
and subsequent verified decoding, and SHALL retain supported signed-token behavior.

#### Scenario: Inspection cannot weaken expiry on reuse

- **GIVEN** an expired signed token and caller options disabling signature verification
- **WHEN** inspection is followed by verified decoding with that mapping
- **THEN** inspection leaves caller options unchanged and verified decoding rejects expiry.

#### Scenario: Ordinary signed tokens preserve padding compatibility

- **GIVEN** a valid signed token and an empty caller options mapping
- **WHEN** decoding normally and with trailing Base64URL padding in its signature
- **THEN** both decodes succeed and caller options remain unchanged.

### Requirement: Versioning Fixture Excludes Git Metadata

Versioning fixtures SHALL stage generated project files without Git metadata and retain
real patch, additive and breaking analyzer assertions.

#### Scenario: Retained analyzer classifications execute

- **GIVEN** a fresh repository and generated project bundle
- **WHEN** patch, additive and breaking tests initialize their repository
- **THEN** initialization excludes Git metadata and all classification assertions execute.

### Requirement: Coherent Reviewed Frozen Repair

The focused slice SHALL regenerate lock/export coherently, retain independent artifact,
security and compatibility evidence, and preserve existing governance.

#### Scenario: Only necessary reviewed updates enter the graph

- **GIVEN** the reported advisories and resolver constraints
- **WHEN** the focused graph is adopted
- **THEN** only reviewed required updates enter coherent inputs and both audits, trust,
  licenses, affected consumers, supported Python and applicable quality gates are verified.

#### Scenario: Broader planning and exact authority remain separate

- **GIVEN** broader #748 planning and the planning-only #755 workflow amendment
- **WHEN** the focused repair is published
- **THEN** broader tasks remain open, fixture proof cannot promote workflow runtime, and
  new exact-commit/tree authority is explicitly obtained before claiming green.
