## Scope rescope — 2026-09-20

Optional preflight, approval seals and development checkpoints are not prerequisites. Keep independent protected-range verification, complete scope, authenticated runtime and signed producer compatibility. Use focused regression reproduction and current-run results; do not require immutable RED history, frozen selector inventories or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## ADDED Requirements

### Requirement: Protected consumer SHALL independently verify C14 range evidence

The protected core consumer SHALL accept only a signed schema 1.6 producer
report whose `assurance_kind` is `range_candidate`. It SHALL independently
derive the unique merge base, complete governed selection, changed-line, Git
status/deletion/rename/object-type/mode manifests, target-tip policy/config and
project-runtime identities, approved suppression-catalog digest, signed
producer/package/profile/toolchain/checkpoint identities, and protected
workflow/artifact provenance. It SHALL compare those values to the producer
report without treating producer-derived expected values as authority.

#### Scenario: Complete trusted candidate is promoted

- **GIVEN** the signed C14 producer report declares `range_candidate`
- **AND** every independently derived identity and manifest exactly matches
- **WHEN** the protected core verifier evaluates the report
- **THEN** it emits a separate verifier envelope with
  `effective_assurance_kind=pr_range`
- **AND** the envelope binds every compared identity, manifest digest, producer
  report digest, protected-context digest, decision, and reason code.

#### Scenario: Merge base is ambiguous or mismatched

- **GIVEN** the protected verifier derives zero or multiple best merge bases,
  or its unique merge base differs from the producer claim
- **WHEN** it evaluates the report
- **THEN** the effective assurance status is `UNKNOWN`
- **AND** it does not emit effective `pr_range`.

#### Scenario: Governed input evidence is incomplete or mismatched

- **GIVEN** governed selection, changed lines, diff, rename, deletion, Git
  object type, or Git mode evidence is omitted or differs
- **WHEN** the protected verifier compares the manifests
- **THEN** it records the specific mismatch as `UNKNOWN`
- **AND** the protected check cannot report success in enforce mode.

### Requirement: Protected consumer SHALL bind policy and producer trust

The protected consumer SHALL independently select authorized target-tip
policy/config, obtain the approved suppression-catalog digest from signed
module/profile policy, verify declared project-runtime source-lock paths/blobs
and applicable dependency/build/artifact attestation, and require approved
signed producer module, schema, profile, toolchain, checkpoint, package,
workflow, job, and artifact identities.

#### Scenario: Target-tip project runtime is fully attested

- **GIVEN** every declared target-tip source-lock path and blob and every
  applicable runtime dependency/build/artifact identity is authorized
- **WHEN** the protected verifier evaluates the project-runtime evidence
- **THEN** that evidence may contribute to an effective `pr_range` decision.

#### Scenario: Candidate or untrusted runtime attempts to authorize itself

- **GIVEN** a candidate-controlled policy, catalog, runtime, producer, or
  artifact identity differs from the independently approved identity
- **WHEN** the protected verifier evaluates the report
- **THEN** the effective assurance status is `UNKNOWN`
- **AND** candidate input cannot authorize or promote itself.

### Requirement: Verifier execution SHALL use independently selected trusted code

Protected workflow policy SHALL select the verifier, imports/dependencies,
configuration and trust roots from an authenticated immutable base revision or
approved release. It SHALL execute outside candidate-controlled paths in a
separate trusted job. Candidate code SHALL NOT run with signing or repository
write credentials. Candidate workflow and fixture-lock edits SHALL NOT select
or replace approval authority. A trusted verifier publication SHALL precede
enforcement; its absence SHALL produce `UNKNOWN`, not candidate fallback.

#### Scenario: Candidate replaces verifier or its authority inputs

- **GIVEN** a candidate edits the verifier, its imports, workflow or fixture lock
- **WHEN** protected verification runs
- **THEN** it uses the independently authorized code and trust roots
- **AND** candidate edits cannot turn rejected evidence into effective `pr_range`.

#### Scenario: Trusted revision does not yet contain the verifier

- **GIVEN** the independently selected trusted revision lacks the verifier
- **WHEN** protected verification is requested
- **THEN** it reports `UNKNOWN` and does not execute the candidate copy
- **AND** enforce mode cannot succeed.

### Requirement: Protected workflow SHALL provide canonical trusted context

The protected PR workflow SHALL write canonical context under the runner
temporary directory immediately before producer invocation, pass full base and
head refs plus `--pr-context-file`, preserve producer report and verifier
envelope as separate immutable artifacts, and bind protected event/workflow/job
provenance. The separate trusted verifier job SHALL independently regenerate
canonical context from authenticated protected event/run data and immutable
base/head identities, compare its digest with the producer report, and bind the
regenerated digest to verifier input and output envelope. It SHALL NOT trust
producer-local files or require a shared runner filesystem. Shared context
SHALL exclude runner paths and per-job identities; producer-job/artifact and
verifier-job provenance SHALL be authenticated and bound separately.

#### Scenario: Producer and verifier use separate runners

- **GIVEN** the producer runner's temporary context is unavailable to the verifier
- **WHEN** the trusted job independently regenerates context for the same event/run and revisions
- **THEN** matching canonical context digests permit the remaining verification
- **AND** missing protected data or a different event/run or revision yields `UNKNOWN`.

#### Scenario: Candidate checkout contains a lookalike context file

- **GIVEN** candidate-controlled repository content contains a file resembling
  protected PR context
- **WHEN** the protected workflow invokes the producer and verifier
- **THEN** the producer uses freshly generated runner-temporary context and the verifier uses its independently regenerated context
- **AND** the candidate file cannot affect effective assurance.

### Requirement: C14 enforcement SHALL be staged and reversible

The same verifier contract SHALL operate in shadow, warning, and enforce
phases. Phase changes SHALL NOT reduce manifest completeness or reinterpret
`UNKNOWN` as PASS. In enforce mode, `FAIL` and `UNKNOWN` SHALL exit non-zero.

#### Scenario: Enforcement is rolled back after an operational incident

- **GIVEN** maintainers return the protected check from enforce to warning
- **WHEN** a report is `FAIL` or `UNKNOWN`
- **THEN** the producer report and verifier envelope remain available with the
  same authoritative status and evidence
- **AND** only merge-blocking behavior changes.
