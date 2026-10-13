# Design: Keep planning receipts separate from execution proof

The current root/child helper authenticates regular closed planning scope, signed exact root,
current protected workflow objects and successful root Requirements/authority runs. Repeat that
validation before retrieving review context, matching the previously authenticated context exactly.
Use the resulting Requirements run id to select one non-expired requirements-evidence artifact.
Validate its workflow repository ids, root head/branch/run identity and service digest. Read only one
bounded regular requirements-evidence.json member without extracting archive files. Reject malformed,
ambiguous, foreign, expired or corrupted archives. The report must identify the exact root and retain
schema 2, final stage, verified maturity, the existing provider-supported RED or approved legacy TDD basis, complete plans/selectors and no findings;
the immutable provider still performs its full finalized-proof validation before Code Review.

Both independent and final consumers use that unchanged root report only for inherited Python review.
They retain their own independently computed planned receipt/plan and protected-dev review diff.
Ordinary consumers keep their existing final report. The immutable provider retains its existing approved legacy-ledger support; the transport helper must not add a RED-only field restriction. No synthetic JUnit, stamped final stage, reduced
review scope, weakened enforcement or candidate-owned helper is permitted. The helper is materialized
only from protected origin/dev beside the protected native context readers.

Tests execute the actual workflow review shells in real isolated Git histories, with exact root artifact
metadata/ZIP responses and the actual frozen provider final-context reader. Positive controls establish
ordinary and native acceptance and retained inherited review paths. Negative controls retain planning
bytes and reject artifact/proof forgery before successful review. Test bytes stay unchanged after RED.
Rollback restores coherent workflow/helper/version inputs and captured branch heads; changed ancestry
requires fresh proof. Scope excludes module runtime, unrelated refactors and archive maintenance.
