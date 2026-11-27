## Decision

Keep existing protected proof_base_commit and native chain authentication. Add planning_base_commit only
for closed planning layers above an authenticated successful exact root. The changed-path modes and both
source/destination paths are read from Git objects, not submitted labels. Root-covered active source
prefixes are derived from the original protected-base-to-root source diff; every child byte under those
prefixes remains protected. All post-root runtime/test/support bytes are excluded by the document allowlist.

Require the root Requirements workflow and local CI action bytes to match protected-base objects before
allowing inherited proof. Candidate CI cannot establish its own planning exemption. Unsupported changed
proof controls retain the existing complete proof path.

Authenticate the latest matching GitHub Actions consumer and authority checks, then their immutable run
metadata and the exact signed root commit. A failed or in-progress latest run blocks consumption. Store
check/run identities in deterministic context so producer, execution and verdict reject intervening changes.
The planning report covers all sources from root to child, including earlier planning layers, at planned
maturity. Existing exact child member authority remains independent. This adds no execution claim for future
proposals and does not copy root RED into a different aggregate plan.

Materialize both helpers from protected origin/dev. Candidate helper bytes cannot authorize their own
scope. The new prerequisite itself uses the existing full implementation/RED path. Do not broaden the
allowlist to fix a failed gate; unsupported layers retain the existing path and require actual proof.

## Rollback and limits

Revert the coherent workflow/helper prerequisite and restack; planning children return to the existing
blocking aggregate gate. No requirements fixture, grant semantics, review gate or protected rule changes.
The root-to-child allowlist is deliberately limited to current OpenSpec planning paths. Exact-root successful
CI is inherited proof, not child acceptance, and subsequent runtime edits still require full independent proof.
