# Tasks: Requirements Runtime Proof Delivery

## TDD / SDD order (enforced)

Specs first, then scenario-mapped tests and captured failing evidence, then
production code. Do not implement gate, workflow, execution, or review-handoff
behavior before its tests exist and have failed for the expected reason.

---

## 1. Worktree, governance, and release dependency

- [x] 1.1 Create issue-linked worktree
  `../specfact-cli-worktrees/feature/requirements-07-runtime-proof-delivery`
  from current `origin/dev`; verify branch and clean scope.
- [x] 1.2 Create core User Story #662; verify labels, project `Todo`, parent
  Feature #374, Epic #258, and native blocked-by relation to modules #368.
- [x] 1.3 Before implementation, recheck that #662 is not already `In Progress`
  elsewhere and that modules #368/#369 has published the immutable reviewed
  `nold-ai/specfact-requirements` 0.4.3 release.
- [x] 1.3.1 After that release is on modules `main`, record its exact signed SHA
  in `ci/module-fixture.lock.json` and every matching fixture allowlist, then
  manually rerun core PR #663. Do not pre-pin the current feature-branch SHA.
- [x] 1.3.2 Pin merged modules PR #379 commit `69f075819be5e1ceca1446b026b0417f19e584ca`
  and verify its Requirements 0.5.1 release from that reviewed commit before
  enabling the approved legacy-ledger reconciliation exception.
- [ ] 1.4 Update the internal wiki mirror/graph when the current dirty internal
  checkout is reconciled; do not overwrite its unrelated pending wiki changes.

## 2. Specification and failing evidence

- [x] 2.1 Revalidate this change against the released modules #368 public
  plan/reconciliation/review-context contract without duplicating semantics.
- [x] 2.2 Add failing staged-gate tests for index isolation, mapped touchpoints,
  exact selectors, no-impact decisions, gate ordering, and report retention.
- [x] 2.3 Add failing selector-execution tests for path escape, option/control
  injection, unsupported runners, duplicates, plan limits, argument-array
  invocation, timeouts, and frozen environment boundaries.
- [x] 2.4 Add failing workflow tests for always-running decisions, targeted
  JUnit generation with canonical node-ID properties, reconciliation,
  requirements-aware review handoff, always-uploaded artifacts, and
  independent verdict enforcement.
- [x] 2.4.1 Add failing runtime-discovery coverage proving its isolated local
  registry contains the recursive module bundle-dependency closure.
- [x] 2.5 Record commands, timestamps, and expected failures in
  `TDD_EVIDENCE.md` before production edits.
- [x] 2.5.1 Add a failing workflow contract test for the R07-only,
  digest-bound `legacy-tdd-ledger` reconciliation path.

## 3. Core delivery implementation

- [x] 3.1 Pin and verify the immutable reviewed modules #368 fixture; reject any
  different repository, commit, package release, dirty checkout, or lock mismatch.
- [x] 3.1.1 Build the runtime-discovery smoke registry from its root modules'
  declared bundle-dependency closure, while retaining the bounded root
  command-surface assertions.
- [x] 3.2 Extend the local adapter and pre-commit Block 2 to produce and validate
  an index-isolated static proof plan before Code Review and contract tests.
- [x] 3.3 Replace narrow pull-request path omission with an always-reporting
  Requirements proof decision for relevant PR events and explicit no-impact
  evidence for governed skips.
- [x] 3.4 Add a bounded executor for supported structured selectors using
  argument arrays, repository containment, option/control rejection, timeout
  and environment limits, and deterministic JUnit output paths.
- [x] 3.5 Reconcile plan and JUnit through the pinned public module command; do
  not parse proof semantics or rewrite its verdict in core.
- [x] 3.5.1 Generate and pass the R07-only legacy-ledger proof basis after
  verifying the committed evidence-ledger digest; never generate `red.json`.
- [x] 3.6 Pass only finalized proof into the released Code Review context input,
  retain both reports, then continue to existing contract/full quality gates.
- [x] 3.7 Publish plan, JUnit, finalized JSON/Markdown, review provenance, and
  concise summaries before enforcing any red verdict.
- [x] 3.8 Resolve the complete set of pytest-determining inputs for a retained
  red proof — selected tests, applicable `conftest.py` files, parent package
  initializers, the pytest configuration source in every implicit candidate,
  configured `pythonpath` roots, `addopts` `-p` plugins, declared
  `pytest_plugins`, and statically reachable repository-local imports — and
  fail closed on any input that cannot be read, parsed, or statically resolved.
- [ ] 3.9 Declare `scripts/requirements_proof_provenance.py` as a governed
  touchpoint of the failing-first requirement and map its scenarios to exact,
  unparametrized selectors so this change's own gate covers its implementation.
  Drafted and withdrawn from this pull request: editing
  `requirements-evidence.yaml` changes the mapping digest, which is pinned in
  three places that only a product-owner run can regenerate — the acceptance
  record `requirements-proof/review-evidence.json`, and
  `legacy_tdd_mapping_digest` plus `legacy_tdd_plan_digest` in
  `.github/workflows/requirements-evidence.yml`. Landing it here would add a
  second CI failure on top of the pre-existing one. The draft raised the plan
  from 18 to 23 cases: a `cli_command` touchpoint for the gate script, and
  cases R07-CORE-003-S04..S08 covering the configuration source and configured
  roots, unreadable inputs, unresolvable plugin declarations, guard rewriting,
  and symlinked selectors. Every drafted selector was verified to collect
  exactly one test.

## 4. Passing evidence and delivery verification

- [x] 4.1 Run focused script/workflow tests and record passing evidence in
  `TDD_EVIDENCE.md`.
- [x] 4.2 Run an integration proof for changed interface -> selected scenario ->
  exact test execution -> JUnit -> reconciled verdict -> review context.
- [x] 4.3 Prove missing/uncollected/failed/stale proof remains blocking only
  after diagnostic artifacts are retained.

## 5. Quality, documentation, and release

- [x] 5.1 Run format, type-check, lint, YAML/workflow lint, contract tests,
  smart/full tests, reproducible-delivery checks, and strict module verification.
- [x] 5.2 Run independent Semgrep/Bandit evidence and fresh changed/full
  SpecFact code review; resolve every finding at every severity.
- [x] 5.3 Update core delivery and Requirements evidence adoption docs without
  duplicating modules-owned command reference; document branch protection and
  explicit skipped semantics.
- [x] 5.4 Bump synchronized core version sources and changelog only when the
  behavior implementation is ready for release.
- [x] 5.5 Run `openspec validate requirements-07-runtime-proof-delivery --strict`
  and retain validation evidence.

## 6. Delivery

- [x] 6.1 Commit implementation, push the issue-linked feature branch, and open
  the implementation PR to `dev` using the repository template and
  `Fixes nold-ai/specfact-cli#662`.
- [x] 6.2 Add the PR to project 1, set implementation status to `In Progress`,
  and verify Development, parent, blocker, and required-check metadata.
- [ ] 6.3 After merge, update the internal wiki status/graph and archive only
  with `openspec archive requirements-07-runtime-proof-delivery` from repo root.

## Post-merge cleanup

- [ ] Update `wiki/sources/requirements-07-runtime-proof-delivery.md`
  (depends-on / blocks / external-deps / status / summary) and run
  `python3 scripts/wiki_rebuild_graph.py` from the `specfact-cli-internal`
  repository root. The retained-proof scenario now states pytest-determining
  inputs as an invariant that includes the pytest configuration source, so the
  mirrored scope text is stale. Recorded as a follow-up because the sibling
  internal checkout was unavailable in the session that made the change.
- [x] Resolve declared pytest plugins against configured `pythonpath` roots so
  a plugin reachable only through such a root is bound as a proof input.
  Deliberately scoped to plugin resolution: rooting ordinary imports would bind
  governed production modules under `src`, which a red-to-green change is
  expected to edit, and would reject every valid failing-first flow.
- [ ] Apply the same undecodable-input guard to product code that reads JSON
  with `except (OSError, json.JSONDecodeError)`:
  `src/specfact_cli/registry/module_state.py`,
  `src/specfact_cli/registry/help_cache.py`,
  `src/specfact_cli/utils/context_detection.py`, and
  `src/specfact_cli/importers/speckit_scanner.py`. These are cache and scanner
  reads whose intended behavior is to fall back, so an undecodable file crashes
  the CLI instead. Deferred from the provenance change because they are product
  paths needing their own contract and coverage treatment.
- [ ] Return to the primary core checkout, fetch `dev`, remove the worktree,
  delete the local feature branch after merge, prune worktrees, and optionally
  delete the merged remote branch.
