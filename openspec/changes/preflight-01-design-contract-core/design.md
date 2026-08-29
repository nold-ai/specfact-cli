## Context

This change defines the durable core boundary for a pre-implementation assurance loop. The loop may ingest OpenSpec, Spec Kit, repository governance, GitHub hierarchy, architecture records, and repository state, but those sources remain authoritative in their own domains. Core normalizes and verifies identities; it does not execute the workflow.

Current upstream patterns support this split. OpenSpec exposes proposal and verification workflows under harness-specific command forms, Spec Kit treats clarification and cross-artifact analysis as pre-implementation quality gates, and both allow the invocation surface to vary by agent. The shared contract therefore must be independent of slash-command spelling and harness packaging.

Research reviewed on 2026-08-25:

- OpenSpec command workflow: <https://github.com/Fission-AI/OpenSpec/blob/main/docs/commands.md>
- Spec Kit agentic SDD workflow: <https://github.github.com/spec-kit/reference/agentic-sdd.html>
- Spec Kit opt-in agent-context ownership: <https://github.com/github/spec-kit/blob/main/AGENTS.md>

## Goals / Non-Goals

**Goals:**

- Define stable contract, validation-result, seal, digest, and verifier interfaces.
- Make every readiness decision traceable to exact input identities and validator versions.
- Preserve explicit unknowns and unresolved findings instead of allowing optimistic inference.
- Bind enough implementation intent to select bounded semantic evidence later from identities already approved by the seal.
- Keep modules and harnesses able to consume the same contract without depending on one renderer or command syntax.

**Non-Goals:**

- Execute validators, prompt an LLM, render findings, persist project artifacts, or install skills.
- Define adapter-specific files for Codex, ECC, hatch3r, OpenSpec, Spec Kit, or any IDE.
- Claim that deterministic structure validation proves design quality or future implementation correctness.

## Decisions

### 1. One normalized design contract

The future `PreflightDesignContract` interface will include a schema version, change identity, repository identity, implementation-lineage identity with immutable origin base commit/tree, optional predecessor-seal identity, source records, role-classified scope, component ownership, approved influence relationships or explicit no-impact dispositions, assumptions, unknowns, dependency edges, affected interfaces, acceptance criteria, risk dimensions, verification stages, test intent, risk/rollback records, and approval policy. Every source record carries a stable source kind, location, revision or content digest, and loader identity. A successor seal may update the reviewed source snapshot after authorized refinement, but it preserves the first seal's lineage origin so implementation evidence cannot disappear behind a reseal.

Scope entries use the closed roles `source`, `test`, `docs`, `generated`, `evidence`, and `excluded`. Each governed source entry identifies one component and bounded pytest targets. Every non-excluded scope entry and every seal-bound test, dependency, policy, toolchain, or relevant configuration input also maps through approved influence edges to the acceptance, risk, Requirements-case, component-target, review/evidence, and stage obligations it can affect, or carries an explicit no-impact disposition with a non-empty rationale. Excluded entries retain their exclusion rationale and policy boundary. Missing, ambiguous, or contradictory influence disposition blocks approval so downstream checkpoints never have to guess from filenames.

### 2. Seal-bound semantic risk and verification intent

Each affected behavior or interface records the closed risk dimensions `boundary`, `malformed_or_missing_input`, `state_transition`, `idempotency`, `cache`, `error`, `status`, `timeout`, `unknown_precedence`, `path`, `repository_lifecycle`, `platform`, and `compatibility`. Every dimension is either `covered`, with references to existing Requirements requirement/scenario/case identities, or `not_applicable`, with a non-empty rationale. Covered cases identify their earliest required execution stage: `slice`, `commit`, `prepush`, or `ci`.

At Requirements `planned` maturity, the contract binds the existing mapping/plan digest and exact requirement, scenario, and verification-case identities plus their method, intent, observable, and touchpoints; it does not invent or require a selector before a test exists. After failing-first test authoring, the Requirements-owned test-authored plan supplies the exact pytest selector. Preflight verifies that it refines the same planned case and requires explicit approval of a successor seal, preserving the implementation-lineage origin, before production implementation proceeds. A later checkpoint may then select a subset of the exact identities bound by that test-authored successor. Adding, removing, replacing, or changing a bound identity requires validation, approval, and a new seal. Existing Requirements contracts remain authoritative for maturity, pytest selector syntax, plan identity, and JUnit reconciliation.

### 3. Deterministic validation result

The future `PreflightValidationResult` binds to exactly one contract digest and records the validator set, validator versions, ordered findings, and readiness state. Findings use stable identifiers and distinguish blocking, advisory, and unknown outcomes. `READY` is permitted only when the policy-required validators completed and no blocking or unknown outcome remains.

### 4. Seal is an approval-bound identity record

The future `PreflightSeal` binds the canonical contract digest, validation-result digest, source-snapshot digest, implementation-lineage identity, immutable origin repository/base commit/base tree, monotonic lineage sequence, optional predecessor-seal digest, approval decision, approver identity, and approval time. Any bound-field change invalidates the seal. A successor advances the sequence exactly once and cannot reset the origin while retaining implementation work. Cryptographic signing, if later required, is an additive implementation concern; the core semantic contract does not equate a digest with a signature or a proof of correctness.

### 5. Pure verifier boundary

The verifier interface accepts a contract, result, seal, and current source identities and returns a structured verification outcome. It performs no network access, file writes, rendering, approval, or automatic refinement. Modules own orchestration and persistence.

### 6. Canonicalization is versioned

Canonical bytes use a versioned, deterministic encoding with UTF-8, normalized strings, stable field ordering, and explicit handling of absent versus empty values. Unknown extensions fail closed unless their schema version is supported. Exact serialization details are finalized with tests before production implementation.

## Risks / Trade-offs

- **False authority from the word seal:** Mitigate with explicit non-proof semantics in models, docs, and rendering.
- **Schema churn before dogfood:** Mitigate with versioned canonicalization and no compatibility promise until the dogfood hardening change.
- **Ownership leakage into core:** Mitigate by excluding CLI, persistence, validation engines, skills, and adapters from this change.
- **Input drift after review:** Mitigate by binding exact source identities and requiring reseal after any bound change.
- **Planning overhead:** Keep the risk vocabulary closed and reusable; require explicit non-applicability instead of speculative tests for irrelevant dimensions.
- **Duplicate test ownership:** Reference Requirements plans and selectors by identity rather than copying their schema into preflight.

## Migration and Rollback

This is additive. Later implementations must remain opt-in until the modules runtime and dogfood evidence are accepted. Rollback is removal of the additive interfaces before external adoption; no stored project artifact is migrated by this planning change.

## Open Questions Deferred to Implementation

- Exact Python class/module names and canonical serialization library.
- Whether a later policy profile requires cryptographic signatures in addition to content digests.
- Retention policy for persisted contracts, which remains modules-owned.
