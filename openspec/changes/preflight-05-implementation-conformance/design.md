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

The future `ImplementationSnapshot` records `snapshot_kind` as `worktree`, `index`, or `range`, repository identity, exact kind-specific Git identity, a complete changed-path manifest, public-interface records, test/evidence references, and producer/policy/toolchain identities. It does not mutate the original design contract.

The path-manifest matrix is normative:

| Snapshot kind | Required identity | Manifest boundary | Untracked paths | Add/delete/rename | Modes and symlinks |
|---|---|---|---|---|---|
| `worktree` | repository identity, full base commit ID, worktree-manifest digest | exact base to the captured working-tree state, including staged and unstaged tracked state | included with explicit `untracked` state | additions, deletions, and both rename endpoints retained | before/after modes and symlink target identity retained |
| `index` | repository identity, full base commit ID, exact index tree ID | exact base to the captured index tree | excluded unless present in the index as an addition | additions, deletions, and both rename endpoints retained | before/after modes and symlink target identity retained |
| `range` | repository identity, full base/head commit IDs, and base/head tree IDs | exact immutable base tree to exact immutable head tree | not representable and therefore absent | additions, deletions, and both rename endpoints retained | before/after modes and symlink target identity retained |

Every manifest record retains its change kind and byte-preserving path identity. Rename classification is deterministic under the bound producer, toolchain, and policy identities; consumers cannot reinterpret a delete/add pair under different rename settings.

### 2. Obligation mapping

The `ImplementationObligationMap` normalizes obligations from approved scope roles, component ownership, interfaces, acceptance criteria, risk rows, Requirements plan identities, test intent, verification stages, and explicit exclusions. A checkpoint map may contain the deterministic affected subset for its sealed stage/profile. A final range map must contain the exhaustive transitive closure for every changed governed path/interface and every applicable sealed component, acceptance criterion, risk row, Requirements case, component target, stage including `ci`, and exclusion. The map and its digest are result-bound. Omitted, duplicate, empty-for-an-affected-range, or ambiguously resolved closure members produce `unverifiable`/`UNKNOWN`; a caller cannot make final conformance pass by supplying a smaller map. Each obligation maps to zero or more evidence records with an explicit relationship, confidence class, producer authority class, and verifiable snapshot/range provenance. A `ci`-stage obligation can be satisfied only by a seal/policy-authorized protected-CI producer whose authenticated evidence is bound to the exact immutable range. Local, self-asserted, unauthenticated, wrong-range, or missing CI evidence remains `unverifiable`/`UNKNOWN`; it is never guessed from filenames or promoted from a local checkpoint.

### 3. Separate checkpoint and conformance results

`DevelopmentCheckpointResult` uses `PASS`, `FAIL`, `UNKNOWN`, or `NOT_APPLICABLE` and records authority as only `local_worktree` or `local_index`. `ImplementationConformanceResult` requires immutable range identity. No transformation can promote a local result into range or protected PR authority.

### 4. Closed finding classes

Finding classes are `missing`, `unexpected`, `modified`, `violated`, `stale`, and `unverifiable`. Each candidate is assigned the first matching class in this precedence order so classes are mutually exclusive:

1. `stale`: a seal-bound contract/result/policy/source or selected Requirements identity differs from the supplied current identity.
2. `unverifiable`: required identity or evidence is absent, ambiguous, unsupported, or cannot be reconciled deterministically.
3. `unexpected`: a governed implementation path or public interface has no sealed scope/obligation mapping or accepted exclusion.
4. `missing`: a sealed required path, interface, obligation, or evidence record has no implementation counterpart.
5. `modified`: the counterpart exists, but its captured path, mode, symlink, interface, selector, or other structural identity differs from the sealed expectation.
6. `violated`: identities reconcile and required evidence ran, but the observed semantic outcome differs from the sealed acceptance or risk-case observable.

Findings retain the sealed contract path, implementation evidence identity, extractor/verifier identity, and blocking/advisory policy outcome. `stale` and `unverifiable` are blocking `UNKNOWN`; `unexpected` is blocking `FAIL`; required `missing`, `modified`, and `violated` findings are blocking `FAIL`. Only an obligation already marked non-required by the sealed policy may make `missing`, `modified`, or `violated` advisory. Deterministic aggregation returns `FAIL` when any determinate blocking failure exists, otherwise `UNKNOWN` when any blocking uncertainty exists, otherwise `PASS`; `NOT_APPLICABLE` is constructed only by the caller-owned applicability boundary.

### 5. Side-effect-free verifier

Core comparison operates only on supplied normalized records. Its input preserves the upstream verifier boundary by supplying the design contract, validation result, seal, policy, and current source identities. Those inputs are verified before obligation comparison; a digest or identity mismatch produces `stale`, while an unavailable identity produces `unverifiable`. Modules owns repository extraction, test evidence import, rendering, applicability decisions, and persistence. A contract-changing drift requires a new preflight review and approval, not mutation of the existing seal.

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
