# Tasks: code-review-14-protected-range-adoption

## Scope rescope — 2026-09-20

Optional preflight, approval seals and development checkpoints are not prerequisites. Keep independent protected-range verification, complete scope, authenticated runtime and signed producer compatibility. Use focused regression reproduction and current-run results; do not require immutable RED history, frozen selector inventories or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## 1. Readiness and frozen identity

- [x] 1.1 Create `feature/code-review-14-protected-range-adoption` from current `origin/dev` in a dedicated worktree.
- [x] 1.2 Create and verify public core issue #680: User Story; parent #375; required labels; SpecFact CLI/Todo; assignee `djm81`; no unresolved upstream blocker; native blocker of #679; no concurrent implementation.
- [ ] 1.3 Verify modules PRs #418 and #419, signed module `0.49.46`, modules commit/tree, archive/signature/checksums, schema-matrix digest, and strict `===0.55.1` compatibility.
- [x] 1.4 Update the matching internal-wiki source, correct C14/C15 dependency links, and rebuild its graph.
- [x] 1.5 Run `openspec validate code-review-14-protected-range-adoption --strict` before tests or production edits.

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
- [ ] 2.2 Add focused workflow contract tests in `tests/unit/workflows/test_code_review_14_protected_range.py` for runner-temp context timing, full refs, separate artifacts, exact signed fixture, and shadow/warning/enforce behavior.
- [ ] 2.3 Add focused staged-hook tests in `tests/unit/scripts/test_pre_commit_code_review.py` proving schema 1.6 status/exit consumption and continued `explicit_files` assurance.
- [ ] 2.4 Select the focused regression cases needed to demonstrate the affected behavior; no frozen selector inventory or development checkpoint.
- [ ] 2.5 Observe relevant failures before production edits and summarize the reproduction briefly; retain detailed output in ordinary CI artifacts when applicable.

## 3. Bounded implementation

- [ ] 3.1 Pin `ci/module-fixture.lock.json` to the canonical signed C14 publication and verify commit/tree/archive/signature/manifest/matrix identities.
- [ ] 3.2 Implement `scripts/verify_code_review_range_assurance.py` to independently derive the closed C14 manifest set and emit a separate verifier-bound envelope.
- [ ] 3.3 Update `.github/workflows/pr-orchestrator.yml` to write protected context under runner temp immediately before invocation, pass full refs plus `--pr-context-file`, and retain producer/envelope artifacts separately.
- [ ] 3.4 Update `scripts/pre_commit_code_review.py` only for schema 1.6 authoritative status/exit parsing; keep staged positional files and no PR authority.
- [ ] 3.5 Stop and amend/revalidate the proposal before touching any other production path.

## 4. Passing evidence and rollout

- [ ] 4.1 Run the named regression tests against the candidate and reference the passing CI results.
- [ ] 4.2 Run workflow policy tests, contracts, type, lint, focused/full tests as required, registry integrity, signature verification, and strict OpenSpec validation.
- [ ] 4.3 Run SpecFact Code Review over the explicit base/head range and resolve only findings traceable to this C14 scope or mandatory regressions; defer unrelated findings.
- [ ] 4.4 Run the compatibility matrix against the exact signed module and core release identity on supported Python versions.
- [ ] 4.5 Roll out shadow, then warning, then enforce through explicit evidence checkpoints.
- [ ] 4.6 Update version/changelog/operator guidance and publish a new core release only after final immutable smoke.
- [ ] 4.7 Unblock the downstream C15 adoption issue #679 after the C14 core release is available.

## 5. Delivery and cleanup

- [ ] 5.1 Commit, push, and open a PR to `dev` with issue and OpenSpec references.
- [ ] 5.2 Merge only after required gates and branch-protection checks pass.
- [ ] 5.3 Archive with `openspec archive code-review-14-protected-range-adoption` after merge completion.
- [ ] 5.4 Remove the worktree and prune the feature branch only after merge.
