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

#### Scenario: Serialized ZIP changes reject without masking payload checks

- **GIVEN** a candidate with authenticated payload bytes and RECORD
- **WHEN** serialized headers, archive framing or ordering change independently
- **THEN** verification SHALL reject unauthorized archive changes
- **AND** isolated runtime, mode, entrypoint and metadata changes SHALL reject while an unchanged archive passes

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

#### Scenario: Installation retains the admitted artifact after transport mutation

- **GIVEN** an admitted artifact whose exact byte snapshot passed approval, archive and provenance verification
- **WHEN** the original transport file is overwritten in place without unlinking, replaced, deleted or redirected after admission
- **THEN** admission-owned materialization SHALL yield the same authenticated bytes under the original wheel basename
- **AND** the yielded path SHALL be separate from the caller transport path and scoped to a context that covers every installer read
- **AND** the private materialization SHALL be cleaned on success or failure
- **AND** the installer process, account and private storage SHALL be trusted; hostile same-account or privileged filesystem mutation is outside this boundary
- **AND** no production adoption or installer orchestration authority is granted

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

#### Scenario: Nonzero audit process rejects clean-looking output

- **GIVEN** an exact admitted graph and an audit process returning nonzero
- **WHEN** the process also emits a valid clean-looking advisory report
- **THEN** audit reconciliation SHALL reject the process failure

### Requirement: Complete Platform And MCP Behavioral Proof

One reviewed platform inventory SHALL define seven wheel targets and Python 3.11,
3.12 and 3.13. All 21 cells SHALL execute on their real architecture and OS/libc;
missing cells, skips and emulation reported as native SHALL NOT pass. Every cell
SHALL prove ordinary hash-enforced installation, package consistency, unchanged
SAST findings and errors, positive/negative detection controls, MCP command startup
and actual stateful session behavior. Tests SHALL exercise idle expiry, capacity,
DELETE cleanup and refused-opening cleanup with bounded test settings, and confirm
the fixed production defaults. Candidate evidence SHALL remain distinct from
protected producer admission. The recipe SHALL contain a runtime-policy object
bound to its declared SHA-256 using UTF-8 JSON with sorted keys and compact
separators. Missing or malformed policies and digest mismatches SHALL reject
before a matrix is returned. Command evidence SHALL decode stdout and stderr as
strict UTF-8 independently of the host locale, including Windows, and preserve
the decoded text as UTF-8. Invalid UTF-8 SHALL fail closed rather than produce
replacement characters or corrupted proof.

#### Scenario: Matrix aggregate rejects missing or conflicting cells

- **GIVEN** cell records from the reviewed matrix
- **WHEN** any required platform/Python result is absent, duplicated or unsuccessful
- **THEN** the aggregate SHALL reject and production adoption SHALL remain blocked

#### Scenario: Fixed MCP reclaims sessions and limits capacity

- **GIVEN** the real downstream Semgrep package and its fixed MCP dependency
- **WHEN** real local transport requests create, expire, delete or refuse sessions
- **THEN** lifecycle regressions SHALL observe reclamation and bounded capacity
- **AND** legitimate scanning and ordinary MCP requests SHALL remain functional

#### Scenario: Canonical runtime policy is bound before matrix enumeration

- **GIVEN** a recipe declaring a runtime-policy object and its SHA-256
- **WHEN** the policy is missing, malformed or differs from sorted compact UTF-8 JSON digest
- **THEN** matrix enumeration SHALL reject before returning any cell

#### Scenario: Command and timeout proof uses strict UTF-8

- **GIVEN** stdout and stderr command or timeout evidence under any host locale
- **WHEN** the runner records that evidence
- **THEN** valid UTF-8 SHALL retain its decoded text in UTF-8 proof files
- **AND** invalid UTF-8 in either stream SHALL reject without replacement text or partial proof files

#### Scenario: Native checkout preserves bound recipe bytes

- **GIVEN** a committed LF recipe and a Windows runner inheriting Git CRLF conversion
- **WHEN** the candidate workflow checks out its bound inputs
- **THEN** the checked-out recipe bytes SHALL match the committed blob before evidence hashes are recorded

#### Scenario: Bound input changes rerun candidate evidence

- **GIVEN** a pull request changing a source input consumed or bound by the candidate workflow
- **WHEN** workflow path filters select candidate validation
- **THEN** the changed input SHALL trigger fresh candidate evidence
- **AND** downstream regression test changes SHALL also trigger candidate validation
