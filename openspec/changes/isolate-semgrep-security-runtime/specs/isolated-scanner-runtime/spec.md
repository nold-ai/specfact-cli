## ADDED Requirements

### Requirement: Exclude compromised certificate authorities from delivered trust

The exact frozen certifi wheel SHALL exclude compromised
emSign ECC Root CA - G3 DER SHA256
`86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b`
while retaining a nonempty CA store. Canonical inputs SHALL require certifi
>=2026.10.19. Trusted Requirements proof SHALL inspect hash-bound inert CA data
without importing candidate dependencies into its verifier.

#### Scenario: Frozen certificate artifact rejects the compromised root

- **GIVEN** the certifi wheel selected by the frozen lock and hash export
- **WHEN** verified CA data is parsed by trusted SSL code
- **THEN** the store is nonempty and excludes the compromised DER fingerprint.

### Requirement: Bound the temporary official MCP advisory exception

The unchanged official Semgrep/MCP graph SHALL use only an exact reviewed
MCP 1.29.0 / CVE-2026-59951 exception, including its GHSA alias, from 2026-10-21
through 2026-11-04 inclusive. Every required audit SHALL remain strict and fail
closed on other versions, advisories, skipped dependencies, malformed records
or expiry. No Semgrep fork or conflicting dependency override SHALL be adopted.

#### Scenario: Only the approved official MCP finding is waived

- **GIVEN** the reviewed MCP register record and the official frozen graph
- **WHEN** the existing audit gate evaluates it on the review date
- **THEN** only the exact authorized finding passes with a visible WAIVED report.

#### Scenario: An unrelated or expired finding remains blocking

- **GIVEN** the reviewed record with a different version, advisory, skipped subject or date after expiry
- **WHEN** the existing audit gate evaluates that input
- **THEN** it returns a failure instead of suppressing the finding.

### Requirement: Admit only the explicitly approved late-cycle provenance gap

For only issue #780 and the owner-authorized direct follow-up to merged PR #782
on branch `codex/dependency-hotfix-admission`, CI MAY
admit missing historical failing-first proof through a separately approved
HumanApprovedLateCycle decision from immutable protected policy code. Every
producer, fresh and final boundary SHALL independently authenticate its inputs,
exact subject and policy, live human permission and unedited bounded approval.
The native report SHALL remain failed and byte-identical. Admission SHALL NOT
claim native RED, verified provenance, waive other findings, alter application
runtime, bypass Code Review, or authorize protected deployment or merge.

#### Scenario: Exact scoped admission retains the failed native report

- **GIVEN** authenticated exact-head evidence, all eleven dependency selectors and three admission controls passing, and a separate unexpired human grant
- **WHEN** the immutable protected evaluator runs independently at each CI boundary
- **THEN** it emits HumanApprovedLateCycle with the raw failed native report unchanged and keeps the independent Code Review gate enforced.

#### Scenario: Substitution or expired authority remains blocking

- **GIVEN** missing or changed policy, subject, evidence, selectors, permission, grant, expiry, or an additional failed obligation
- **WHEN** any CI boundary evaluates admission
- **THEN** it refuses and preserves the original report and every required check.

#### Scenario: Ordinary native proof retains its existing gate

- **GIVEN** valid complete native failing-first proof outside the scoped exception
- **WHEN** Requirements reconciles it
- **THEN** the existing native success path remains independent of late-cycle approval.

#### Scenario: Unrelated and fork pull requests do not start the attester

- **GIVEN** a fork, another repository, base or branch, or an absent native artifact
- **WHEN** CI evaluates the origin attester job
- **THEN** it skips that job and retains ordinary Requirements enforcement without requesting signing permissions for that subject.

#### Scenario: Exact artifact IDs survive same-name reruns

- **GIVEN** the bound producer or execution artifact ID and another artifact with the same name and a greater numeric ID
- **WHEN** any of the three current-run evidence transfers restores its artifact
- **THEN** it retrieves the requested immutable ID directly, authenticates repository numeric identity, run, head, name, expiry, SHA-256 and size, and requires the independent execution upload digest.

#### Scenario: Artifact bytes enter only as bounded inert evidence

- **GIVEN** authenticated exact-ID metadata and ZIP bytes
- **WHEN** the shared isolated workflow-owned program restores evidence
- **THEN** credentialed transport remains on the fixed GitHub API, HTTPS redirects never forward the token, digest verification precedes bounded flat regular-file extraction, all files validate in staging before exclusive publication, and unsafe paths, links, collisions or uncertain inputs fail closed while preserving unrelated context.

#### Scenario: Authenticated equivalent synthetic merge revisions

- **GIVEN** an attested workflow revision and current GitHub PR merge revision have different IDs but the same exact reviewed full tree and ordered two-parent ancestry
- **WHEN** the scoped policy verifies historical native origin for the unchanged head
- **THEN** it may accept that equivalent signed merge only after authenticated commit identity, valid signatures, exact head/tree/parents, unchanged workflow bytes and the existing exact source-digest attestation verification pass; mismatched ancestry, content, signatures or source still refuse.
