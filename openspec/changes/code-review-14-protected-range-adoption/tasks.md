# Tasks: code-review-14-protected-range-adoption

## Scope rescope — 2026-09-20

Optional preflight, approval seals and development checkpoints are not prerequisites. Keep independent protected-range verification, complete scope, authenticated runtime and signed producer compatibility. Use focused regression reproduction and current-run results; do not require immutable RED history, frozen selector inventories or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## 1. Readiness and compatible signed identity

- [ ] 1.1 At implementation start, create or verify the dedicated issue-linked worktree against current `origin/dev`; recovery-era worktree creation does not establish current ownership.
- [ ] 1.2 Refresh and read back existing core #680 at implementation start: parent #375, User Story type, labels, assignee, project/status, actual prerequisites, downstream #679 relationship and current ownership. Resolve concurrent implementation before proceeding; retain signed producer/runtime prerequisites without restoring optional preflight #431.
- [ ] 1.3 Select a signed C14-capable publication compatible with current core; verify packaged commit/tree, archive/signature/checksums and schema matrix. Treat the original `0.49.46` / `===0.55.1` pair as historical. Obtain a fresh signed publication if no compatible one exists.
- [x] 1.4 Update the matching internal-wiki source, correct C14/C15 dependency links, and rebuild its graph.
- [ ] 1.5 Revalidate current scope and run `openspec validate code-review-14-protected-range-adoption --strict` before tests or production edits; the recovery validation is historical.

## 2. Named regression tests

- [ ] 2.1 Add exactly these verifier acceptance tests before implementation:
  - [ ] `test_trusted_consumer_envelope_upgrades_range_candidate_to_pr_range`
  - [ ] `test_trusted_consumer_rejects_merge_base_mismatch`
  - [ ] `test_trusted_consumer_rejects_multiple_best_merge_bases`
  - [ ] `test_trusted_consumer_rejects_incomplete_governed_selection`
  - [ ] `test_trusted_consumer_rejects_diff_or_rename_manifest_mismatch`
  - [ ] `test_trusted_consumer_rejects_governed_object_type_or_mode_mismatch`
  - [ ] `test_trusted_consumer_rejects_policy_config_identity_mismatch`
  - [ ] `test_trusted_consumer_rejects_suppression_catalog_identity_mismatch`
  - [ ] `test_trusted_consumer_rejects_unapproved_producer_or_artifact_identity`
  - [ ] `test_trusted_consumer_accepts_target_tip_project_runtime_attestation`
  - [ ] `test_trusted_consumer_rejects_candidate_or_untrusted_project_runtime`
  - [ ] `test_candidate_verifier_lock_and_workflow_cannot_replace_trusted_authority`
  - [ ] `test_missing_trusted_verifier_is_unknown_without_candidate_fallback`
- [ ] 2.2 Add focused workflow contract tests in `tests/unit/workflows/test_code_review_14_protected_range.py` for trusted verifier/import/config/root selection and job isolation, independent context regeneration across separate runners, missing/mismatched context rejection, context digest binding, full refs, separate artifacts, compatible signed fixture, and shadow/warning/enforce behavior.
- [ ] 2.3 Add focused staged-hook tests in `tests/unit/scripts/test_pre_commit_code_review.py` proving schema 1.6 status/exit consumption and continued `explicit_files` assurance.
- [ ] 2.4 Select the focused regression cases needed to demonstrate the affected behavior; no frozen selector inventory or development checkpoint.
- [ ] 2.5 Observe relevant failures before production edits and summarize the reproduction briefly; retain detailed output in ordinary CI artifacts when applicable.

## 3. Bounded implementation

- [ ] 3.1 Pin `ci/module-fixture.lock.json` to the verified compatible signed C14-capable publication selected in 1.3 and verify commit/tree/archive/signature/manifest/matrix identities.
- [ ] 3.2 Implement `scripts/verify_code_review_range_assurance.py` to independently derive the closed C14 manifest set and emit a separate verifier-bound envelope.
- [ ] 3.3 Update the PR orchestrator and bounded organization invocation policy to select authenticated verifier code/dependencies/roots independently of candidate files. Isolate trusted execution; regenerate canonical event/run/revision context independently in each job, compare and bind its digest, pass full refs plus `--pr-context-file`, and retain separate producer/envelope artifacts. Never rely on sharing producer runner-temp files. Missing trusted verifier is `UNKNOWN`, never candidate fallback.
- [ ] 3.4 Update `scripts/pre_commit_code_review.py` only for schema 1.6 authoritative status/exit parsing; keep staged positional files and no PR authority.
- [ ] 3.5 Stop and amend/revalidate the proposal before touching any other production path.

## 4. Candidate verification

- [ ] 4.1 Set the intended core release version and prepare changelog/operator guidance and reviewed rollout/rollback configuration before candidate verification. Confirm the selected signed module's declared compatibility includes that resulting core version; the unpublished candidate verifier cannot authorize its own integration.
- [ ] 4.2 Run the named regression tests against the candidate and reference the passing CI results.
- [ ] 4.3 Run workflow policy tests, contracts, type, lint, focused/full tests as required, registry integrity, signature verification, and strict OpenSpec validation.
- [ ] 4.4 Run SpecFact Code Review over the explicit base/head range and triage every finding: fix introduced/relevant defects, explain false positives, and obtain an individual documented exception with impact and linked follow-up for any real deferred finding.
- [ ] 4.5 Run the compatibility matrix against the exact signed module and resulting candidate core build on supported Python versions. If the core version or signed module changes before publication, repeat the affected compatibility checks against the new identities.

## 5. Reviewed integration, publication and rollout

- [ ] 5.1 Commit, push, and open the implementation PR to `dev` with issue and OpenSpec references.
- [ ] 5.2 Integrate into `dev`, then promote through a reviewed PR to protected `main`, satisfying the effective required gates. Do not require the new verifier gate before its trusted source exists or substitute a candidate verifier for that source.
- [ ] 5.3 Run final immutable module/core smoke and publish the core release through the existing protected-main release workflow. Select/authenticate the integrated verifier from the approved immutable base or release before enabling enforcement.
- [ ] 5.4 Run trusted shadow, warning, then enforcement using current results and reviewed rollout decisions; preserve `FAIL`/`UNKNOWN` semantics throughout.
- [ ] 5.5 Unblock downstream C15 adoption #679 only after the compatible C14 core release and required protected-consumer handoff are available.

## 6. Cleanup

- [ ] 6.1 Archive with `openspec archive code-review-14-protected-range-adoption` after completed integration and release handoff.
- [ ] 6.2 Remove the worktree and prune the feature branch only after merge.
