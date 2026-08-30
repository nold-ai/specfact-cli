# Tasks: Bounded Red-Green Replay

> **Historical plan only — do not execute.** Issue #675 and paired modules issue
> #414 are closed as Not Planned. This change is parked and superseded by
> #682/#684 plus modules #431/#434. In particular, do not run the archive task:
> no R08 behavior was implemented, so archiving would merge an unimplemented
> delta into canonical requirements.

Every unchecked item below is retained historical planning text and is non-executable while parked. Un-parking requires a new explicit roadmap decision, fresh dependency/readiness evidence, strict revalidation, and an accepted replacement task list before any implementation or archive action.

## 0. Planning

- [x] 0.1 Define the bounded B < R < H proof claim, delivered-head binding H <= D, and explicit non-goals.
- [x] 0.2 Define allowed future paths and prohibit extension of static dependency inference.
- [x] 0.3 Record that this planning branch contains no behavior changes.

## Implementation-session checklist — before any unchecked implementation task

- [ ] B.1 Create a dedicated implementation worktree and feature branch from current `origin/dev`; do not implement from the primary, `dev`, or `main` checkout.
- [ ] B.2 Run `hatch env create`, then `hatch run smart-test-status` and `hatch run contract-test-status` in the worktree; record and resolve unexpected baseline failures before edits.
- [ ] B.3 **HISTORICAL — NON-EXECUTABLE:** the former readiness step assumed issue #675 and modules #414 were open and is invalid after their `not planned` closure. A future accepted replacement plan must refresh governance and dependency facts rather than reuse those assumptions.
- [ ] B.4 Follow `spec -> tests -> failing evidence -> code -> passing evidence`; in `TDD_EVIDENCE.md`, record separate failing-before and passing-after sections with exact commands, timestamps, actual results, behavioral summaries, environment limitations, and artifact identities. Record passing evidence only after implementation.
- [ ] B.5 Before PR finalization, rerun exactly `openspec validate requirements-08-bounded-red-green-proof --strict` plus the required format, type, lint, YAML, contract, focused/full test, workflow, independent-analysis, signature, and explicit base/head Code Review gates. Update `CHANGE_VALIDATION.md` with validation scope/impact, affected files, exact commands, actual results and test counts, focused/full tests, skipped or unavailable tests/dependencies with reasons, artifact locations/identities, environment limitations, and release hygiene. Keep planning evidence, failing-before evidence, and H..D passing/implementation evidence separate; rerun affected validation after every artifact fix and resolve every finding or document an approved exception.
- [ ] B.6 After each merge, remove the implementation worktree, delete its local feature branch, run `git worktree prune`, and complete an explicit `AGENTS.md` worktree/policy self-check. Archive only from a dedicated follow-up worktree when the stated dependency, release, and rollout gates are complete.

## 1. Paired modules release

- [ ] 1.1 Implement independent current-execution and chronology states in the paired modules R07/R08 changes.
- [ ] 1.2 Implement the versioned B/R/H/D replay-capsule schema and validation contracts: core supplies Git/execution facts; modules validate schema/hash/transition/outcome facts without running Git or tests.
- [ ] 1.3 In modules PR #412, add `test_code_review_accepts_current_execution_without_red_green_chronology` in `tests/unit/specfact_code_review/run/test_commands.py` and a focused Requirements reconciliation regression proving a valid historical capsule cannot substitute for missing current execution. The adapter may retain both claims, but neither may calculate or rewrite the other claim's status.
- [ ] 1.4 Publish the paired Requirements payload through the modules repository release generators. Version `packages/specfact-requirements/module-package.yaml`, update `CHANGELOG.md` and `registry/index.json`, generate the versioned archive/checksum/signature under `registry/modules/` and `registry/signatures/`, and record immutable commit/tree, package/capsule-schema versions, manifest integrity, approved signing-key fingerprint or trust-root identity, signer/signature identities, and passing package/signature/registry verification evidence.

- [ ] 1.5 Before core implementation starts, require a repository administrator to establish and independently review the external checkpoint issuer/trust set, exact `refs/tags/specfact-checkpoint/**` non-rewritable ruleset, canonical signed-annotation schema, and checkpoint-policy epoch. The PR workflow receives read-only contents permission and no tag-create/update/delete authority. Record the repository/ruleset/issuer/trust/schema/epoch identities in the pre-R `CHANGE_VALIDATION.md` readiness section; strict R08 remains blocked when any fact is absent.

## 2. Failing tests first

- [ ] 2.1 In `tests/unit/scripts/test_requirements_proof_provenance.py`, replace obsolete static-closure cases with temporary-Git-repository tests for valid B < R < H <= D, exact D delivery binding, and protected signed annotated R/H checkpoint tags derived from change ID plus frozen mapping digest. Reject missing, lightweight, movable, deleted/recreated, wrong-role/digest, unapproved-signer/ruleset/epoch, moved/deleted/reused tag namespace or stale checkpoint attempt, direct-SHA, PR-metadata, mutable-branch, workflow-input, and retained-artifact substitutes.
- [ ] 2.2 In `tests/unit/scripts/test_requirements_proof_provenance.py`, add failing tests that reject every undeclared/disallowed B..R path or rename endpoint, every R..H non-implementation change, and every H..D path except exact mapped `TDD_EVIDENCE.md`/`CHANGE_VALIDATION.md` delivery evidence. Also reject a missing, duplicate, reordered, rewritten, or deleted `specfact:frozen-failing` or `specfact:frozen-readiness` section at D even when the changed path is allowed.
- [ ] 2.3 In exactly `tests/integration/scripts/test_requirements_red_green_replay.py`, add failing integration tests proving each selector emits exactly one canonical red marker matching its frozen `expected_failure_id` at R, passes at H, and remains passing at a distinct D. Include a negative case where the same assertion class fails with a different ID and must remain unproven.
- [ ] 2.4 In `tests/unit/scripts/test_requirements_proof_provenance.py`, add shallow-history, invalid-ref, checkout-failure, missing-artifact, and rename-endpoint cases; execution timeout, selector-mismatch, and missing/duplicate/wrong failure-marker cases may additionally use `tests/integration/scripts/test_requirements_red_green_replay.py`. If the existing executor seam cannot accept explicit worktree/stage/output inputs, add one named failing compatibility test in `tests/unit/scripts/test_requirements_proof_executor.py` before R; without that frozen pre-R test, the executor source path is not authorized.
- [ ] 2.5 In `tests/unit/scripts/test_requirements_proof_provenance.py`, add a failing bootstrap test proving verifier/policy self-changes cannot self-attest.
- [ ] 2.6 In `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`, add `test_replay_capsule_requires_trusted_module_and_epoch`, rejecting an unreleased/mismatched signed-module identity, capsule schema, verifier epoch, missing/unknown approved public-key fingerprint, or missing/unknown trust-root reference before module import or chronology enforcement. Also add `test_replay_workflow_binds_trusted_checkpoints_delivery_and_network_isolation`, proving the YAML derives the exact protected R/H refs, validates tag/signature/issuer/trust/ruleset/epoch/attempt facts with read-only permissions, forwards resolved R/H plus B/D, binds D to the delivery SHA, retains artifacts before enforcement, and makes unavailable isolation explicitly unproven.
- [ ] 2.7 In `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`, add `test_current_run_pass_remains_valid_without_red_green_chronology` and `test_historical_capsule_cannot_substitute_for_missing_current_execution`. The first must pass with no chronology claim; the second must remain unresolved/non-pass when the current-run JUnit observation is absent even if chronology is valid.
- [ ] 2.8 In exactly `tests/integration/scripts/test_requirements_red_green_replay.py`, add `test_historical_replay_does_not_synthesize_current_execution`, proving successful B/R/H/D replay emits chronology facts only and cannot manufacture the independent delivered-head current-execution observation.
- [ ] 2.9 In `tests/unit/scripts/test_requirements_proof_provenance.py`, before accepting R add table-driven `test_replay_capsule_missing_or_altered_mandatory_field_is_unproven`. Delete or alter every mandatory capsule field named in task 3.4—including checkpoint authority/attempt, frozen-section, transition, mapping/plan/selector/failure, JUnit, environment/network/policy/verifier, module-trust, timestamp, and resource identities—and require explicit unproven chronology.
- [ ] 2.10 Before accepting R, update `requirements-evidence.yaml` under the paired released mapping schema: replace applicable planning-only inspection cases with exact executable test selectors, including tasks 2.6–2.9, one stable opaque `expected_failure_id` per replayed selector, and a positive accepted `checkpoint_attempt` incremented for every new R; declare complete `red_setup_touchpoints`, implementation touchpoints (including every required adoption-documentation path from task 4.1), and exact delivery-evidence touchpoints; include this mapping, the governed `TDD_EVIDENCE.md` failing-before record, and the governed `CHANGE_VALIDATION.md` pre-R readiness section in red setup; add exactly one `specfact:frozen-failing` and one `specfact:frozen-readiness` section boundary; verify every exact selector collects once; then freeze mapping, plan, selector, path-set, and both section-byte digests at R.
- [ ] 2.11 Before production edits and before accepting R, add the actual failing-before section to `TDD_EVIDENCE.md` with timestamps, exact commands/results, behavioral summary, environment limitations, and artifact identities. Wrap the failing-before bytes in exactly one `specfact:frozen-failing` section. This file is an explicitly mapped B..R `failing_tdd_evidence` touchpoint; the marked bytes and digest are frozen from R through D.
- [ ] 2.12 After R exists and before any production edit, have the approved external issuer verify R plus the frozen mapping/plan/selector/path-role/failing/readiness digests, create the exact protected signed annotated red tag, and push it under the established non-rewritable ruleset. Record the tag name, tag-object ID, target commit/tree, issuer/signature/trust identity, ruleset ID, and checkpoint-policy epoch outside the candidate transition and in retained diagnostics. Stop if issuance or independent verification fails; the read-only PR workflow must not create the tag.

## 3. Minimal implementation

- [ ] 3.1 In `scripts/requirements_proof_provenance.py`, resolve B from the PR merge base and D from the current delivery identity. Derive exact refs `refs/tags/specfact-checkpoint/<change-id>/<mapping-digest>/red` and `/green`; resolve R/H only from their protected signed annotated tag objects and validate canonical repository/change/role/commit/tree/mapping/plan/selector/path-role/epoch/issuer/signature bindings. Require complete declared `red_setup_touchpoints`, implementation touchpoints, and exact `delivery_evidence_touchpoints`; reject direct R/H SHA inputs or PR/body/label/comment/mutable-branch/workflow-input/artifact substitutes; do not auto-discover alternate checkpoints.
- [ ] 3.2 In `scripts/requirements_proof_provenance.py`, implement ancestry and all three closed B..R, R..H, and H..D changed-path/rename-endpoint validators. Do not parse Python AST.
- [ ] 3.3 In `scripts/requirements_proof_provenance.py`, implement isolated worktree replay for R, H, and distinct D with identical bounded subprocess arguments and enforced network-isolation evidence; reuse H as D only when the SHAs are equal. Change `scripts/requirements_proof_executor.py` only when the frozen conditional regression from task 2.4 proves the existing seam cannot support explicit worktree/output inputs; do not edit its tests after R.
- [ ] 3.4 In `scripts/requirements_proof_provenance.py`, produce and schema-validate the versioned capsule before handing it to the signed Requirements module. Mandatory fields: B/R/H/D commit and tree identities; both checkpoint tag names, tag-object identities, canonical annotations, signatures, approved issuer/trust identities, repository-ruleset identity, and checkpoint-policy epoch and accepted checkpoint-attempt identity; frozen failing/readiness section bytes and R/D digests plus equality results; B..R, R..H, and H..D path/rename manifests and digests; mapping and plan digests; exact selector list; mapped expected-failure IDs; canonical observed red failure IDs and their digest; red, green-checkpoint, and delivery JUnit digests; runner, toolchain, dependency, environment, plugin, and network-policy identities/results; policy/verifier identities and epoch; timestamps and resource bounds; and signed module repository, commit, tree, package, manifest-integrity, approved signing-key fingerprint or trust-root, signer, and signature identities. Implement only the capsule construction exercised by the pre-R mandatory-field regression in task 2.9.
- [ ] 3.5 In `.github/workflows/requirements-evidence.yml`, implement the workflow behavior already exercised by the frozen pre-R workflow tests from tasks 2.6 and 2.7, including the checkpoint/delivery/isolation regression: validate the fixture's signing-key fingerprint or trust-root reference against the configured approved key set before module import and fail closed when missing/unknown; derive and validate the exact protected signed R/H checkpoint tags with a read-only token, pass their resolved full identities plus B/D, bind D to the current delivery SHA, wire shadow mode, make unavailable network isolation unproven, and retain all artifacts before enforcement.
- [ ] 3.6 In `scripts/requirements_proof_provenance.py`, remove or bypass obsolete static pytest-input closure from the authoritative path; prefer deletion over parallel complexity.

## 4. Pre-H verification, green checkpoint, delivery, and rollout

- [ ] 4.1 Before H, create or update `docs/guides/requirements-evidence.md` to distinguish `current_execution`, bounded `red_green_chronology`, `unproven`, bootstrap/shadow status, external R/H checkpoint issuance/recovery, frozen-section preservation, and remediation. Update `docs/index.md` and `docs/_layouts/default.html` only when needed to expose the guide, and regenerate `llms.txt` through the existing docs generator rather than hand-editing it. These exact paths must already be declared implementation touchpoints by task 2.10.
- [ ] 4.2 Before H, run the #665–#671 benchmark plus seeded invalid-history/path/frozen-section/checkpoint-authority cases. Resolve every required non-evidence change before continuing; a test/harness change requires a new R.
- [ ] 4.3 Before H, establish and document the initial independently reviewed verifier and checkpoint-policy epochs outside the candidate's self-attestation boundary.
- [ ] 4.4 Before H, run exactly `openspec validate requirements-08-bounded-red-green-proof --strict`, workflow lint, focused/full tests, contracts, static analysis, signature checks, and explicit base/head Code Review. Retain external logs, resolve every finding that can require a non-ledger edit, and rerun affected gates until the candidate is stable. Do not issue H while any code, configuration, test, documentation, workflow, policy, schema, or other non-delivery-evidence edit remains.
- [ ] 4.5 Only after tasks 4.1–4.4 pass without pending non-evidence edits, designate that exact commit as H. Have the approved external issuer verify H plus the frozen red inputs, create the exact protected signed annotated green tag, and push it under the established non-rewritable ruleset. Record the same immutable issuance facts as task 2.12 outside the candidate transition. The read-only PR workflow must not create or mutate the tag.
- [ ] 4.6 After H, create D by appending only the passing-after section outside the `specfact:frozen-failing` markers in `TDD_EVIDENCE.md` and the final validation section outside the `specfact:frozen-readiness` markers in `CHANGE_VALIDATION.md`. Preserve both frozen sections exactly once and byte-identically. Record the pre-H commands/results and B/R/H plus policy/schema identities, but keep the exact D, capsule, artifact, and final workflow/check identities in the PR/check-suite record to avoid self-reference.
- [ ] 4.7 At D, run the final replay and all task B.5 gates read-only. Verify the R and D frozen-section bytes/digests are identical and retain final artifacts before enforcement. If any non-ledger or frozen-section edit is required, invalidate the checkpoint, increment and re-accept `checkpoint_attempt`, and start again with a new mapping digest, R, and tag namespace; if an allowed append-only ledger correction changes D, rerun the entire final D gate set at the new head.
- [ ] 4.8 Run shadow, warning, then strict rollout through separately reviewed follow-up changes/epochs; record rollback instructions. A rollout change to workflow, policy, schema, fixture, or verifier is not part of H..D and cannot be authorized by this checkpoint.
- [ ] 4.9 Merge the completed implementation to `dev` only after the paired signed module release is pinned, the final D gates pass, and every review thread is resolved.
- [ ] 4.10 **SUPERSEDED — MUST NOT RUN:** the former R08 archive step is retained only as historical planning text; the change was never implemented.
- [ ] 4.11 Merge checklist follow-up: create or update `wiki/sources/requirements-08-bounded-red-green-proof.md` (`depends-on`, `blocks`, `external-deps`, `status`, and summary) and run `python3 scripts/wiki_rebuild_graph.py` from the `specfact-cli-internal` repository root.
- [ ] 4.12 After each implementation or archive PR merges, remove its worktree, delete its local feature branch, run `git worktree prune`, and record the worktree-policy self-check.

## Prohibited shortcuts

- Do not cherry-pick PR #671.
- Do not add import, plugin, configuration, data-read, alias, mutation, namespace, symlink, or dynamic-execution inference.
- Do not reuse retained red artifacts in the strongest replay profile.
- Do not accept R/H identities from direct SHA inputs, PR text/labels/comments, mutable branches, workflow inputs, or retained workflow artifacts; require the derived protected signed checkpoint tags.
- Do not move, delete, or reuse a checkpoint tag; a retry requires an incremented accepted `checkpoint_attempt`, new mapping digest, and new immutable tag namespace.
- Do not give the pull-request workflow checkpoint-tag write authority or let it self-issue R/H; issuance is an external approved-signer ceremony under the pre-established ruleset/epoch.
- Do not allow test/config/harness changes after R; require a new R.
- Do not emit pass/no-impact for missing or unresolved mandatory facts.
- Do not manually move directories into `openspec/changes/archive/`. No archive command is authorized while this change is parked. Only after explicit un-parking, completed implementation, verification, shipment, merge, and explicit approval for canonical-specification promotion may the then-current governed repository-root archive procedure be used.

## Closed implementation allowlist

Anything not listed here is prohibited unless this OpenSpec change is updated and accepted first.

Pre-red mapping and evidence records:

- `openspec/changes/requirements-08-bounded-red-green-proof/requirements-evidence.yaml`: before R only, add schema-accepted exact selectors, one stable opaque `expected_failure_id` per selector and a positive accepted `checkpoint_attempt` that is incremented for every new R, plus complete red-setup, implementation, and delivery-evidence declarations; freeze its digest at R.
- `openspec/changes/requirements-08-bounded-red-green-proof/TDD_EVIDENCE.md`: exactly one marked frozen failing-before section in B..R whose bytes/digest must remain identical through D; append passing-after only outside the markers in H..D.
- `openspec/changes/requirements-08-bounded-red-green-proof/CHANGE_VALIDATION.md`: exactly one marked frozen pre-R `readiness_validation_evidence` section in B..R whose bytes/digest must remain identical through D; append final validation only outside the markers in H..D under its separate delivery-evidence role.

External checkpoint prerequisite (repository settings, not candidate-tree production code):

- A repository administrator establishes the approved issuer/trust set, non-rewritable `refs/tags/specfact-checkpoint/**` ruleset, canonical annotation schema, and checkpoint-policy epoch before implementation. The approved issuer creates the red and green tags at tasks 2.12 and 4.5; the PR workflow remains read-only. These external settings and tag objects are capsule inputs, not files authorized for candidate-branch modification.

Production/configuration:

- `scripts/requirements_proof_provenance.py`: replace the existing static/AST closure with the small Git-only B/R/H/D validator, isolated replay orchestration, and attestation builder. Delete the old import/plugin/config/data-read rules; do not add a parallel provenance script.
- `.github/workflows/requirements-evidence.yml`: verify the fixture's approved signing-key/trust-root reference before module import; derive and validate the protected signed R/H checkpoint tags, pass their resolved identities plus B/D, bind D to the current delivery SHA, invoke shadow replay, retain red/green/delivery JUnit artifacts and attestation before enforcement, and enforce verifier-epoch bootstrap.
- `ci/module-fixture.lock.json`: signed R08-capable modules identity plus approved public-key fingerprint or trust-root reference only.
- `scripts/requirements_proof_executor.py`: conditional only when replay cannot use its current public seam; permit explicit worktree root/run-stage/output while preserving argv/environment safety.

Tests — every listed test edit occurs in B..R before task 2.10 freezes the mapping and remains byte-unchanged R..H:

- `tests/unit/scripts/test_requirements_proof_provenance.py`: replace obsolete static-closure cases with B/R/H/D ancestry/delivery identity, protected signed checkpoint authority, three path-set, frozen-ledger-section preservation, missing-history/artifact, rename, pre-R mandatory-capsule-field, attestation, and bootstrap cases.
- New exactly `tests/integration/scripts/test_requirements_red_green_replay.py`: temporary-repository exact expected-failure-ID-at-R/pass-at-H/remain-pass-at-distinct-D replay, wrong same-class failure identity, timeout, and selector mismatch.
- `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`: shadow wiring, artifacts-before-enforcement, and epoch bootstrap.
- `tests/unit/scripts/test_requirements_proof_executor.py`: conditional only when the executor changes.
- Temporary repositories live inside the named tests; no fixture directory.

Adoption documentation:

- `docs/guides/requirements-evidence.md`: canonical current-execution versus bounded-chronology guide; create if absent.
- `docs/index.md` and `docs/_layouts/default.html`: link/navigation only when the guide is otherwise undiscoverable.
- `llms.txt`: generated from accepted docs only through the existing generator; never hand-edit.

Paired modules dependency allowlist — separate repository `nold-ai/specfact-cli-modules`, implemented and reviewed in PR #412 rather than on this core branch:

- Requirements sources: new `packages/specfact-requirements/src/specfact_requirements/requirements/replay_proof.py`; `lifecycle.py`, `evidence.py`, and `commands.py`; `app.py`/`__init__.py` only for required command/export wiring.
- Focused tests: new `tests/unit/specfact_requirements/test_requirements_replay_proof.py`; `test_requirements_lifecycle.py`, `test_requirements_evidence.py`, and `tests/integration/specfact_requirements/test_command_apps.py`.
- Code Review provenance handoff, only if the capsule context changes: `packages/specfact-code-review/src/specfact_code_review/run/commands.py`, `findings.py`, and their focused `test_commands.py`/`test_findings.py` tests.
- Release/docs sources: `docs/bundles/requirements/overview.md`, `packages/specfact-requirements/module-package.yaml`, and `packages/specfact-code-review/module-package.yaml` only when its payload changes.
- Generated publication outputs, only through existing generators after behavior passes: `registry/index.json`, `registry/modules/specfact-requirements-<version>.tar.gz`, its `.sha256`, `registry/signatures/specfact-requirements-<version>.tar.sig`, `CHANGELOG.md`, and generated command/docs outputs required by module policy.
- The module validator must not run Git, pytest, subprocesses, or infer Python/pytest dependencies. No core file is authorized by this companion allowlist.

Explicitly forbidden:

- any new general pytest analyzer/provenance production file;
- `scripts/requirements_proof_pytest_plugin.py` unless its existing canonical-selector contract demonstrably fails;
- `scripts/requirements_evidence_delivery_gate.py`, `scripts/pre-commit-quality-checks.sh`, all `src/**`, and `tools/**`;
- security, dependency, safe-write, and smart-coverage paths, `pyproject.toml`, `uv.lock`, and unrelated tests.
