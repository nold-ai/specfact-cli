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

#### Scenario: Smoke fallback does not inherit unchecked seed updates

- **GIVEN** the standard venv builder fails and an older shared virtualenv cache may exist
- **WHEN** the editable smoke launcher uses virtualenv as its fallback
- **THEN** it seeds with isolated workspace app data and disables background periodic updates,
  preserves the editable launcher, and never purges unrelated user cache contents.

#### Scenario: Broader planning and exact authority remain separate

- **GIVEN** broader #748 planning and the planning-only #755 workflow amendment
- **WHEN** the focused repair is published
- **THEN** broader tasks remain open, fixture proof cannot promote workflow runtime, and
  new exact-commit/tree authority is explicitly obtained before claiming green.

### Requirement: Compatible Python Security Layer

The selected Python layer SHALL use screened GitPython 3.2.0 and Hatchling 1.32.4,
preserve the merged #756 graph and generate coherent frozen lock/export inputs.

#### Scenario: Unsafe submodule checkout is rejected before cloning

- **GIVEN** a submodule checkout path outside its parent repository
- **WHEN** the hash-pinned delivery GitPython package updates that submodule
- **THEN** it rejects the path before cloning or writing outside the repository.

#### Scenario: Backend and release metadata remain coherent

- **GIVEN** both Hatchling declarations and the four canonical package versions
- **WHEN** the selected Python layer builds its wheel
- **THEN** the backend is 1.32.4, package metadata is 0.55.5, lock/export parity holds,
  both frozen audits pass and Python 3.11-3.13 installation preserves consumers.

#### Scenario: Source distribution rebuild retains bundled assets

- **WHEN** the reviewed backend builds a wheel from the release source distribution
- **THEN** the source distribution SHALL contain every forced wheel inclusion,
  including the unchanged signed bundle-mapper assets.

### Requirement: Compatible Documentation Security Stack

The documentation stack SHALL retain Jekyll 4.4.1 and JSON >=2.21.2,<3,
adopt the selected redirect and feed security fixes and preserve link behavior.

#### Scenario: JSON stays on the compatible patched major

- **WHEN** documentation dependency inputs are regenerated
- **THEN** JSON remains locked at 2.21.2, the declaration excludes JSON 3,
  and Jekyll remains at 4.4.1 without incidental resolver changes.

#### Scenario: Redirect output rejects script targets

- **WHEN** an unsafe scheme or an HTML/JavaScript delimiter enters a redirect target
- **THEN** the redirect plugin rejects unsafe schemes and encodes delimiters,
  while ordinary root and prefixed HTTP/HTTPS redirects remain usable.

#### Scenario: Feed metadata cannot escape XML or CDATA

- **WHEN** feed language or post content contains XML/CDATA delimiters
- **THEN** generated feed output remains parseable and preserves metadata as data.

#### Scenario: Relative links preserve configured deployment paths

- **WHEN** documentation builds at root or a configured base URL
- **THEN** Markdown, included HTML links and navigation resolve to current pages,
  preserving fragments and external targets across successive site builds.
