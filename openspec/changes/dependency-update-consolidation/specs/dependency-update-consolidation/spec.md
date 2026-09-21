## ADDED Requirements

### Requirement: Complete dependency assessment

The maintenance change SHALL inventory runtime, build, optional, Hatch/test, isolated Code Review, and transitive dependencies, including marker-specific versions, and SHALL distinguish latest registry releases from compatible candidates and approved upgrades.

#### Scenario: Exact pins and isolated tools are not omitted

- **GIVEN** the primary resolver retains an exact build pin and excludes the isolated Code Review graph
- **WHEN** the dependency assessment is produced
- **THEN** both surfaces SHALL receive separate latest-version and compatible-candidate checks
- **AND** every package SHALL have declaration/path context, current and candidate versions, evidence status, and an explicit disposition.

#### Scenario: Intervening releases and graph changes are reviewed

- **GIVEN** a candidate advances beyond several upstream releases or removes/adds transitives
- **WHEN** it is considered for adoption
- **THEN** the assessment SHALL enumerate and review the intervening release notes, compatibility, Python requirements, license/security changes, and changed dependency paths
- **AND** enumeration without review SHALL remain pending evidence.

### Requirement: Compatible update boundaries

The change SHALL preserve supported dependency constraints and Python versions, defer major migrations and dependency downgrades, and raise minimums only for evidenced security or compatibility needs.

#### Scenario: A loosely bounded dependency crosses a major version

- **GIVEN** the latest resolver selects Isort 9 from an Isort 8 baseline
- **WHEN** the compatible consolidation candidate is selected
- **THEN** the existing major line SHALL be retained and the migration SHALL be recorded as a follow-up.

#### Scenario: A docs update downgrades the framework

- **GIVEN** JSON 3.x resolution downgrades Jekyll 4.4.1 to 4.3.4
- **WHEN** source PR #727 is assessed
- **THEN** that proposal SHALL be deferred and compatible JSON 2.x alternatives SHALL be assessed without adopting the downgrade.

### Requirement: Independent vulnerability and malicious-package screening

Every new candidate artifact SHALL receive separate current vulnerability and malicious-package/provenance screening before installation or execution; successful resolution and absent repository alerts SHALL NOT constitute approval.

#### Scenario: A candidate has no CVE but unresolved malware evidence

- **GIVEN** advisory queries report no known vulnerability for a candidate but its malware/provenance assessment is unavailable or unresolved
- **WHEN** candidate adoption is evaluated
- **THEN** adoption SHALL be deferred
- **AND** missing evidence SHALL be stated without describing the candidate as safe.

#### Scenario: A successful status skipped dependency inspection

- **GIVEN** a Socket status is successful but its output says skipped or no dependency changes
- **WHEN** reviewers assess the new candidate version
- **THEN** the status SHALL NOT satisfy exact-artifact malicious-package screening.

#### Scenario: Source-only metadata requires inspection

- **GIVEN** dependency resolution cannot obtain static metadata from the registry
- **WHEN** the assessment examines a source archive
- **THEN** its identity SHALL be recorded and source contents SHALL be inspected as data without executing unreviewed build hooks
- **AND** unresolved metadata SHALL prevent promotion rather than trigger unreviewed execution.

### Requirement: Exact and current security evidence

The change SHALL retain baseline and candidate advisory results for both Python graphs and every marker-specific package/version, with affected/fixed ranges, identifiers, dependency paths, source URLs, timestamps, coverage, and exact artifact identities. Artifact hashes SHALL establish identity, not malware clearance.

#### Scenario: A changed artifact invalidates an earlier review

- **GIVEN** the generated final graph changes a version, artifact, marker branch, or transitive from the screened graph
- **WHEN** final validation runs
- **THEN** affected security review SHALL be repeated and bound to the final artifacts before adoption.

#### Scenario: Advisory information changes before release

- **GIVEN** final-graph audits passed before merge and relevant identities or advisory information later change
- **WHEN** release is prepared
- **THEN** advisory evidence SHALL be refreshed and upstream conflicts resolved before publication.

### Requirement: Trust policy cannot be bypassed

Known malicious or explicitly blocked releases SHALL be rejected without exceptions. Security-tool floors and version-specific trust records SHALL remain enforced. Vulnerability exceptions SHALL satisfy the existing exact package/version/advisory, mitigation, and expiry policy and SHALL NOT replace an available compatible fix.

#### Scenario: Resolver selects an unreviewed parser release

- **GIVEN** the provenance exception identifies pycparser 2.22 and the resolver suggests 2.23
- **WHEN** candidate selection applies repository trust policy
- **THEN** 2.22 SHALL remain selected until fresh artifact-specific review passes
- **AND** the blocked 3.0 family SHALL remain prohibited.

#### Scenario: Security services are unavailable

- **GIVEN** required live advisory or malicious-package evidence cannot be obtained
- **WHEN** the workflow runs offline or encounters an outage
- **THEN** existing local frozen-policy checks MAY run but fresh adoption SHALL remain unverified and deferred
- **AND** no network-dependent behavior SHALL be added to the CLI runtime.

### Requirement: Coherent frozen delivery and compatibility

Approved updates SHALL keep declarations, exact pins, generated locks/exports, policy records, and affected regression expectations consistent. Supported-Python and installation tests SHALL validate the resulting graph; advisory resolver checks SHALL NOT replace frozen release evidence.

#### Scenario: Hatchling is consolidated

- **GIVEN** PR #744 changes the build and dev Hatchling pins only
- **WHEN** the consolidation is implemented
- **THEN** its regression expectation SHALL be updated with failing-before evidence before declaration changes
- **AND** the frozen primary graph/export SHALL be regenerated and wheel metadata/build validation SHALL pass.

#### Scenario: Supported profiles execute against their selected graph

- **GIVEN** screened latest, lower-bound, and final frozen graphs exist
- **WHEN** compatibility is verified
- **THEN** Python 3.11, 3.12, and 3.13 SHALL execute tests through their synchronized environments across minimal runtime, relevant extras, and supported package installation methods
- **AND** the isolated Code Review graph and any changed Ruby graph SHALL receive their own validation.

### Requirement: Planning evidence is not implementation completion

The proposal SHALL record unstarted implementation and explicit evidence gaps. Completed implementation SHALL ship through the normal patch-release workflow with coherent rollback and native archival.

#### Scenario: Proposal contains security-negative discovery results

- **GIVEN** a planning snapshot has successful advisory queries but incomplete artifact reviews or compatibility tests
- **WHEN** its issue and PR are published
- **THEN** candidates SHALL remain unapproved, implementation tasks SHALL remain unchecked, and no dependency or release version SHALL be changed by the proposal.

#### Scenario: Consolidated implementation replaces bot PRs

- **GIVEN** the final implementation passes required checks and merges
- **WHEN** tracking is finalized
- **THEN** only genuinely superseded bot PRs SHALL be closed
- **AND** completed specs SHALL be archived with the OpenSpec CLI and rollback SHALL preserve a reviewed safe baseline.
