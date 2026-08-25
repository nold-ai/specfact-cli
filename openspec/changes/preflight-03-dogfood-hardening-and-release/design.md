## Context

Core C14 adoption is a useful first dogfood subject because it is cross-repository, evidence-sensitive, and explicitly bounded by signed module handoff and native dependency metadata. The dogfood protocol tests whether the preflight loop detects planning drift before implementation without silently becoming a second source of truth.

## Goals / Non-Goals

**Goals:**

- Exercise the released core contract and unpublished modules runtime as one exact loop.
- Capture enough reproducible evidence to distinguish change defects from tool defects.
- Require a human decision for every material refinement and a complete rerun afterward.
- Produce a go/no-go handoff for modules hardening and stable publication.

**Non-Goals:**

- Implement, reimplement, or release C14.
- Tune validators to make a single fixture pass.
- Treat subjective reviewer disagreement as deterministic failure without a declared rule.

## Decisions

### 1. C14 is the first mandatory target

The protocol runs against the current accepted core C14 change and linked issue #680 using immutable repository and GitHub identities. It records the starting artifacts before any authorized refinement. Existing C14/C15 worktrees remain untouched by this planning setup; future dogfood occurs only in the C14 owner session or a read-only snapshot.

### 2. Evidence separates four defect owners

Every observed problem is classified as one of:

- core contract/canonicalization defect;
- modules runtime/validator/workflow defect;
- source change/GitHub metadata defect;
- generated instruction or operator-guidance defect.

Ambiguous classification is recorded as unknown and cannot authorize hardening scope.

### 3. Before/after evidence is identity-bound

Each run records source revisions, contract/result digests, validator identities, findings, user decisions, approved artifact edits, rerun identities, and seal verification. A narrative summary may explain results but cannot replace the machine-readable identities.

### 4. Readiness requires observed usefulness and safety

The handoff to module hardening requires:

- all required validators complete determinately on the final C14 snapshot;
- known scope/dependency/ownership/evidence risks are either detected or explicitly shown outside the MVP contract;
- no unapproved source edit occurs;
- stale inputs invalidate the seal;
- human and JSON views agree;
- every accepted hardening item maps to observed evidence and a specific owner.

### 5. One case does not prove generality

C14 authorizes the first hardening pass only. The modules release change must retain an explicit provisional-support statement and add a bounded regression corpus before stable publication.

## Risks / Trade-offs

- **Confirmation bias:** Preserve the initial snapshot and expected-risk inventory before running the tool.
- **Overfitting:** Require each hardening item to generalize to a declared rule and regression case.
- **Concurrent C14 work:** Stop if issue/worktree ownership is ambiguous; never edit another active worktree.
- **Narrative-only proof:** Bind summaries to exact result and source identities.

## Migration and Rollback

This change produces evidence and a decision only. A no-go result leaves the unpublished runtime in place for correction. Rollback is removal of dogfood artifacts and reversal of any separately approved C14 planning refinement; no product release occurs here.

## Open Questions Deferred to Execution

- Exact bounded secondary corpus after C14, selected from pending proposal-stage changes without changing their implementation status.
- Operator-time metrics worth retaining once the first run reveals the actual workflow shape.
