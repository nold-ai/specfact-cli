## Context

## Scope rescope — 2026-09-20

Optional preflight, approval seals and development checkpoints are not prerequisites. Keep independent protected-range verification, complete scope, authenticated runtime and signed producer compatibility. Use focused regression reproduction and current-run results; do not require immutable RED history, frozen selector inventories or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

Modules C14 deliberately stops at a signed producer/report boundary. The
producer can emit `range_candidate`, but it cannot attest to the protected
workflow event or promote itself to `pr_range`. Core owns that separate trust
decision because core controls the protected checkout, event payload, workflow
identity, immutable modules fixture, and required check.

The accepted handoff is the canonical signed modules publication merged by
modules PR #419 at commit `6a0d0b31` (tree
`0531325d68ae21f75abda01ce8968f92ba1b6d06`), containing
`specfact-code-review` `0.49.46` with strict core compatibility `===0.55.1`.
The module was developed and smoked against core tag `v0.55.1`, commit
`b1e517e60e669eaba15a18ecfa83ef5a9df65276`, tree
`47984be5434d7ae65ed6908bf525a32053290337`.

## Goals / Non-Goals

### Goals

- Independently verify every finite identity and manifest named by the C14
  consumer handoff before claiming effective `pr_range`.
- Keep protected workflow context outside candidate-controlled paths and bind
  it to full immutable base/head identities.
- Fail closed as `UNKNOWN` for missing, ambiguous, incomplete, or mismatched
  required evidence.
- Preserve the local staged hook as truthful `explicit_files` assurance.
- Make rollout and rollback explicit and release-scoped.

### Non-Goals

- Producing or changing Code Review findings.
- Designing a reusable attestation framework or refactoring module trust
  primitives.
- Implementing C15/schema-1.7 severity, profile, policy, waiver, or broader
  enforcement behavior.
- Changing analyzer rules, runtime capsules, project-runtime semantics,
  Requirements, or test-selection policy.

## Decisions

### Decision 1: Isolate the verifier from the module producer

Core adds one verifier entry point that reads the immutable producer report,
the freshly written protected context, the signed module/profile identities,
and independently derived repository facts. It does not import producer
selection helpers or accept producer-derived expected values as authority.

The verifier emits a separate core-owned envelope. It never edits or replaces
the producer report.

### Decision 2: Verify a closed C14 manifest set

The verifier independently derives and compares:

1. exactly one best merge base and its commit/tree;
2. full base/head refs and the authenticated target-tip commit/tree;
3. complete governed path selection and changed-line manifest;
4. Git status, deletion, exact-rename, object-type, and mode manifests;
5. target-tip policy/config selection and declared project-runtime
   source-lock paths/blobs plus applicable dependency/build/artifact
   attestation;
6. approved suppression-catalog digest obtained from the signed module/profile
   policy, never from candidate input;
7. signed producer module/version/manifest/archive/signature, schema 1.6,
   profile, toolchain, checkpoint, package, and report identities; and
8. protected workflow, job, event, checkout, and artifact provenance.

An omitted governed input, multiple/no best merge bases, unapproved producer,
candidate-supplied trust identity, or any mismatch yields `UNKNOWN`.

### Decision 3: Promotion is envelope-only

The producer must report `assurance_kind=range_candidate`. Only the core
verifier envelope can state `effective_assurance_kind=pr_range`. The envelope
binds all compared identities, manifest digests, producer report digest,
context digest, decision, and reason codes.

`FAIL` producer evidence remains `FAIL`; infrastructure or reconciliation
uncertainty remains `UNKNOWN`. The verifier never upgrades
`range_preview`, `worktree`, `index`, `explicit_files`, or an unsigned report.

### Decision 4: Keep local and protected consumers separate

`scripts/pre_commit_code_review.py` continues to pass only staged positional
files. It may parse schema 1.6 `assurance_status` and authoritative exit
semantics for truthful summaries, but it cannot accept PR context, emit a
verifier envelope, or claim `pr_range`.

The workflow writes its canonical context under `${RUNNER_TEMP}` immediately
before producer invocation, passes full base/head refs and
`--pr-context-file`, retains producer report and verifier envelope as separate
artifacts, and ensures candidate code cannot pre-create the trusted context.

### Decision 5: Stage enforcement without weakening evidence

The verifier contract is identical in all phases:

- **shadow** records the authoritative result but is not a required gate;
- **warning** reports non-green results visibly while migration remains
  non-blocking; and
- **enforce** makes `FAIL` and `UNKNOWN` non-zero required-check outcomes.

Changing phase never changes manifest completeness or turns uncertainty into
PASS. Rollback changes only the enforcement phase and retains artifacts.

### Decision 6: File and review allowlist is normative

The proposal's named production, test, documentation, and release paths are the
default maximum implementation surface. Any additional path requires an
explicit proposal update, a named failing test, strict revalidation, and review
of whether the work belongs to C15 or another follow-up. Generic cleanup and
valid-but-unrelated review findings do not expand C14.

## Risks / Trade-offs

- **Identity drift**: a later modules publication or core release can invalidate
  the frozen matrix. Mitigation: pin commit/tree/checksums and rerun immutable
  smoke before release; update through a reviewed spec amendment.
- **Workflow context spoofing**: candidate-controlled files could impersonate
  event data. Mitigation: write canonical context in runner temp after checkout
  and bind protected provenance in the verifier envelope.
- **Verifier/producer correlated logic**: importing producer helpers could make
  equality checks circular. Mitigation: independently derive the closed
  manifests with core-owned code and compare only serialized evidence.
- **Scope creep**: general trust-framework refactors could make review
  unbounded. Mitigation: enforce the file/test allowlist and defer unmatched
  findings.

## Migration Plan

1. Pin and verify the signed modules C14 publication and exact compatibility
   matrix.
2. Add the named failing verifier and workflow tests and record the red
   checkpoint.
3. Implement the isolated verifier, protected context flow, staged-hook schema
   handling, and shadow envelope.
4. Record passing evidence, then promote shadow to warning and enforcement only
   through explicit reviewed checkpoints.
5. Publish a core release after final signed module/core immutable smoke.

## Open Questions

None for scope. Branch-protection selection of the final emitted check remains
an operational promotion step after warning evidence is accepted; it does not
change this software contract.
