## Context

The preflight seal binds an approved plan and source snapshot. Implementation necessarily changes repository state, so the original seal becomes a reference contract rather than a claim about the resulting code. This change defines the core data boundary for a later explicit comparison.

## Goals / Non-Goals

**Goals:**

- Represent the implementation revision and evidence identities independently of the design contract.
- Map each approved scope/interface/acceptance/test obligation to observed implementation evidence.
- Detect both missing approved work and unexpected work outside the sealed boundary.
- Preserve unknowns when static evidence cannot prove conformance.

**Non-Goals:**

- Execute extractors, tests, or analyzers.
- Reopen or reseal the design automatically.
- Treat test success as proof of complete semantic conformance.

## Decisions

### 1. Separate implementation snapshot

The future `ImplementationSnapshot` records repository identity, base/head revisions, changed-path manifest, public-interface records, test/evidence references, and extractor identities. It does not mutate the original design contract.

### 2. Obligation mapping

The conformance input normalizes obligations from approved scope, interfaces, acceptance criteria, test intent, and explicit exclusions. Each obligation maps to zero or more evidence records with an explicit relationship and confidence class. Missing evidence remains missing or unknown; it is never guessed from filenames alone.

### 3. Closed drift classes

Initial finding classes are `missing`, `unexpected`, `modified`, `stale`, and `unverifiable`. Findings retain the sealed contract path, implementation evidence identity, extractor/verifier identity, and blocking/advisory policy outcome.

### 4. Side-effect-free verifier

Core comparison operates only on supplied normalized records. Modules owns repository extraction, test evidence import, rendering, policy, and persistence. A contract-changing drift requires a new preflight review and approval, not mutation of the existing seal.

### 5. Independent assurance statement

A conformance result states only what the declared extractors and evidence can compare. It does not prove runtime behavior outside captured evidence, absence of hidden behavior, or design quality.

## Risks / Trade-offs

- **False confidence from test exit codes:** Require exact test/evidence identities and preserve unverified obligations.
- **Noisy unexpected-path findings:** Use approved scope/exclusion mappings and declared generated/vendor path policy.
- **Contract changed during implementation:** Mark stale and require a new preflight seal.
- **Core ownership creep:** Keep extraction and command behavior modules-owned.

## Migration and Rollback

The conformance contract is additive and optional. Rollback removes the new interfaces before downstream adoption. Existing preflight contracts and seals remain valid for pre-implementation identity verification but do not gain conformance meaning.

## Open Questions Deferred to Implementation

- Exact confidence vocabulary for static versus runtime evidence.
- Minimum evidence profile for a blocking conformance policy.
- Whether architecture-01 records require a dedicated mapping subtype.
