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

### Requirement: Protected workflow SHALL provide canonical trusted context

The protected PR workflow SHALL write canonical context under the runner
temporary directory immediately before producer invocation, pass full base and
head refs plus `--pr-context-file`, preserve producer report and verifier
envelope as separate immutable artifacts, and bind protected event/workflow/job
provenance.

#### Scenario: Candidate checkout contains a lookalike context file

- **GIVEN** candidate-controlled repository content contains a file resembling
  protected PR context
- **WHEN** the protected workflow invokes the producer and verifier
- **THEN** only the freshly written runner-temporary context is trusted
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
