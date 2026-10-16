## ADDED Requirements

### Requirement: Deterministic Metadata Only Downstream Build

The builder SHALL accept only a reviewed upstream Semgrep wheel whose filename,
platform and SHA-256 match the recipe. It SHALL produce a distinct local version
with the exact MCP 1.30.0 requirement. Its complete archive comparison SHALL allow
only the version and MCP metadata changes, corresponding dist-info/data directory
renames and a regenerated bijective RECORD. Runtime contents, modes, entry points
and every other metadata field SHALL remain unchanged. Invalid, duplicate,
traversing, linked, signed or unexpected archive entries SHALL reject before output.

#### Scenario: Reproducible legitimate downstream wheel

- **GIVEN** an exact reviewed upstream wheel and recipe
- **WHEN** the builder runs twice
- **THEN** both output bytes SHALL be identical and runtime contents unchanged
- **AND** RECORD SHALL authenticate every resulting entry exactly once

#### Scenario: Changed upstream or unexpected payload rejects

- **GIVEN** a wrong hash, unsafe archive member or unauthorized metadata change
- **WHEN** a build or archive comparison is requested
- **THEN** it SHALL reject without installing or publishing an artifact

### Requirement: Exact Protected Admission

Production admission SHALL require an exact reviewed local version, candidate and
upstream hashes, recipe identity, platform, validity interval and complete platform
evidence. Provenance SHALL authenticate the configured repository, immutable source
and signer workflow on the protected branch through a trusted verifier. A JSON
claim, PR event, unrecognized local version, missing or failed verifier, wrong
identity, expired approval or incomplete evidence SHALL NOT grant admission.
Admission SHALL precede production installation or audit identity substitution.

#### Scenario: Untrusted candidate cannot authorize itself

- **GIVEN** a PR-built candidate with internally consistent claims
- **WHEN** production admission runs without authenticated protected provenance
- **THEN** it SHALL reject before installation or identity substitution

#### Scenario: Exact complete protected candidate is admitted

- **GIVEN** exact independently verified provenance and complete fresh matrix proof
- **WHEN** all recipe, artifact, platform and validity bindings match
- **THEN** admission SHALL return only that exact verified artifact identity

### Requirement: Complete Vulnerability Identity Coverage

The audit SHALL retain actual installed distribution identities and SHALL query
the exact admitted upstream Semgrep code identity in addition to every package in
the actual fixed graph. Only that exact artifact binding may map a local identity.
No generic suffix removal, dependency override, package omission or new advisory
exception SHALL be introduced. Every unreviewed advisory, skipped or malformed
entry, absent or duplicate package, unexpected version, service error and timeout
SHALL reject. The existing upstream Semgrep floor and blocked releases SHALL remain
effective; downstream operation SHALL require MCP 1.30.0 or later in the fixed 1.x
line covered by the recipe.

#### Scenario: Complete fixed graph retains downstream inventory identity

- **GIVEN** an admitted exact downstream wheel and actual fixed dependency graph
- **WHEN** strict advisory lookup succeeds for every expected identity
- **THEN** the audit SHALL retain the local Semgrep identity in its report
- **AND** lookup SHALL use only its exact authenticated upstream identity

#### Scenario: Incomplete or vulnerable graph fails closed

- **GIVEN** a vulnerable control graph, missing package or failed advisory response
- **WHEN** audit evidence is reconciled against the complete actual inventory
- **THEN** the audit SHALL fail without a skip, exception or resolver fallback

### Requirement: Complete Platform And MCP Behavioral Proof

One reviewed platform inventory SHALL define seven wheel targets and Python 3.11,
3.12 and 3.13. All 21 cells SHALL execute on their real architecture and OS/libc;
missing cells, skips and emulation reported as native SHALL NOT pass. Every cell
SHALL prove ordinary hash-enforced installation, package consistency, unchanged
SAST findings and errors, positive/negative detection controls, MCP command startup
and actual stateful session behavior. Tests SHALL exercise idle expiry, capacity,
DELETE cleanup and refused-opening cleanup with bounded test settings, and confirm
the fixed production defaults. Candidate evidence SHALL remain distinct from
protected producer admission.

#### Scenario: Matrix aggregate rejects missing or conflicting cells

- **GIVEN** cell records from the reviewed matrix
- **WHEN** any required platform/Python result is absent, duplicated or unsuccessful
- **THEN** the aggregate SHALL reject and production adoption SHALL remain blocked

#### Scenario: Fixed MCP reclaims sessions and limits capacity

- **GIVEN** the real downstream Semgrep package and its fixed MCP dependency
- **WHEN** real local transport requests create, expire, delete or refuse sessions
- **THEN** lifecycle regressions SHALL observe reclamation and bounded capacity
- **AND** legitimate scanning and ordinary MCP requests SHALL remain functional
