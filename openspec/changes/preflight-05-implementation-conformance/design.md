## Context

The preflight seal binds an approved plan and source snapshot. Implementation necessarily changes repository state, so the original seal becomes a reference contract rather than a claim about the resulting code. This change defines the core data boundary for repeatable local checkpoints and a later immutable-range comparison.

## Goals / Non-Goals

**Goals:**

- Represent worktree, staged-index, and immutable-range evidence identities independently of the design contract.
- Map each approved scope/interface/acceptance/test obligation to observed implementation evidence.
- Detect both missing approved work and unexpected work outside the sealed boundary.
- Preserve unknowns when static evidence cannot prove conformance.
- Prevent local checkpoint evidence from being promoted to protected pull-request authority.

**Non-Goals:**

- Execute extractors, tests, or analyzers.
- Reopen or reseal the design automatically.
- Treat test success as proof of complete semantic conformance.

## Decisions

### 1. Snapshot kinds and exact identity

The future `ImplementationSnapshot` records `snapshot_kind` as `worktree`, `index`, or `range`, the exact base identity, the worktree-manifest digest, index-tree identity, or full base/head object IDs required by that kind, a complete changed-path manifest, public-interface records, test/evidence references, and producer/policy/toolchain identities. Path manifests preserve additions, deletions, both rename endpoints, modes, symlinks, and untracked paths where the snapshot kind permits them. It does not mutate the original design contract.

### 2. Obligation mapping

The `ImplementationObligationMap` normalizes obligations from approved scope roles, component ownership, interfaces, acceptance criteria, risk rows, Requirements plan identities, test intent, verification stages, and explicit exclusions. Each obligation maps to zero or more evidence records with an explicit relationship and confidence class. Missing evidence remains missing or unknown; it is never guessed from filenames alone.

### 3. Separate checkpoint and conformance results

`DevelopmentCheckpointResult` uses `PASS`, `FAIL`, `UNKNOWN`, or `NOT_APPLICABLE` and records authority as only `local_worktree` or `local_index`. `ImplementationConformanceResult` requires immutable range identity. No transformation can promote a local result into range or protected PR authority.

### 4. Closed finding classes

Initial finding classes are `missing`, `unexpected`, `modified`, `violated`, `stale`, and `unverifiable`. Findings retain the sealed contract path, implementation evidence identity, extractor/verifier identity, and blocking/advisory policy outcome.

### 5. Side-effect-free verifier

Core comparison operates only on supplied normalized records. Modules owns repository extraction, test evidence import, rendering, policy, and persistence. A contract-changing drift requires a new preflight review and approval, not mutation of the existing seal.

### 6. Independent assurance statement

A conformance result states only what the declared extractors and evidence can compare. It does not prove runtime behavior outside captured evidence, absence of hidden behavior, or design quality.

## Risks / Trade-offs

- **False confidence from test exit codes:** Require exact test/evidence identities and preserve unverified obligations.
- **Noisy unexpected-path findings:** Use approved scope/exclusion mappings and declared generated/vendor path policy.
- **Contract changed during implementation:** Mark stale and require a new preflight seal.
- **Core ownership creep:** Keep extraction and command behavior modules-owned.
- **Authority confusion:** Encode snapshot kind and authority in result validation; reject local-to-range promotion.

## Migration and Rollback

The implementation-assurance contract is additive and optional. Rollback removes the new interfaces before downstream adoption. Existing preflight contracts and seals remain valid for pre-implementation identity verification but do not gain checkpoint or conformance meaning.

## Open Questions Deferred to Implementation

- Exact confidence vocabulary for static versus runtime evidence.
- Minimum evidence profile for a blocking final conformance policy after checkpoint dogfood.
- Whether architecture-01 records require a dedicated mapping subtype.
