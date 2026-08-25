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
- Keep modules and harnesses able to consume the same contract without depending on one renderer or command syntax.

**Non-Goals:**

- Execute validators, prompt an LLM, render findings, persist project artifacts, or install skills.
- Define adapter-specific files for Codex, ECC, hatch3r, OpenSpec, Spec Kit, or any IDE.
- Claim that deterministic structure validation proves design quality or future implementation correctness.

## Decisions

### 1. One normalized design contract

The future `PreflightDesignContract` interface will include a schema version, change identity, repository identity, source records, in-scope and excluded boundaries, assumptions, unknowns, dependency edges, affected interfaces, acceptance criteria, test intent, risk/rollback records, and approval policy. Every source record carries a stable source kind, location, revision or content digest, and loader identity.

### 2. Deterministic validation result

The future `PreflightValidationResult` binds to exactly one contract digest and records the validator set, validator versions, ordered findings, and readiness state. Findings use stable identifiers and distinguish blocking, advisory, and unknown outcomes. `READY` is permitted only when the policy-required validators completed and no blocking or unknown outcome remains.

### 3. Seal is an approval-bound identity record

The future `PreflightSeal` binds the canonical contract digest, validation-result digest, source-snapshot digest, approval decision, approver identity, and approval time. Any bound-field change invalidates the seal. Cryptographic signing, if later required, is an additive implementation concern; the core semantic contract does not equate a digest with a signature or a proof of correctness.

### 4. Pure verifier boundary

The verifier interface accepts a contract, result, seal, and current source identities and returns a structured verification outcome. It performs no network access, file writes, rendering, approval, or automatic refinement. Modules own orchestration and persistence.

### 5. Canonicalization is versioned

Canonical bytes use a versioned, deterministic encoding with UTF-8, normalized strings, stable field ordering, and explicit handling of absent versus empty values. Unknown extensions fail closed unless their schema version is supported. Exact serialization details are finalized with tests before production implementation.

## Risks / Trade-offs

- **False authority from the word seal:** Mitigate with explicit non-proof semantics in models, docs, and rendering.
- **Schema churn before dogfood:** Mitigate with versioned canonicalization and no compatibility promise until the dogfood hardening change.
- **Ownership leakage into core:** Mitigate by excluding CLI, persistence, validation engines, skills, and adapters from this change.
- **Input drift after review:** Mitigate by binding exact source identities and requiring reseal after any bound change.

## Migration and Rollback

This is additive. Later implementations must remain opt-in until the modules runtime and dogfood evidence are accepted. Rollback is removal of the additive interfaces before external adoption; no stored project artifact is migrated by this planning change.

## Open Questions Deferred to Implementation

- Exact Python class/module names and canonical serialization library.
- Whether a later policy profile requires cryptographic signatures in addition to content digests.
- Retention policy for persisted contracts, which remains modules-owned.
