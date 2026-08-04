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
  elsewhere and that modules #368/#369 has published the signed immutable
  `nold-ai/specfact-requirements` 0.4.3 release.
- [x] 1.3.1 After that release is on modules `main`, record its exact signed SHA
  in `ci/module-fixture.lock.json` and every matching fixture allowlist, then
  manually rerun core PR #663. Do not pre-pin the current feature-branch SHA.
- [ ] 1.4 Update the internal wiki mirror/graph when the current dirty internal
  checkout is reconciled; do not overwrite its unrelated pending wiki changes.

## 2. Specification and failing evidence

- [x] 2.1 Revalidate this change against the released modules #368 public
  plan/reconciliation/review-context contract without duplicating semantics.
- [ ] 2.2 Add failing staged-gate tests for index isolation, mapped touchpoints,
  exact selectors, no-impact decisions, gate ordering, and report retention.
- [ ] 2.3 Add failing selector-execution tests for path escape, option/control
  injection, unsupported runners, duplicates, plan limits, argument-array
  invocation, timeouts, and frozen environment boundaries.
- [ ] 2.4 Add failing workflow tests for always-running decisions, targeted
  JUnit generation with canonical node-ID properties, reconciliation,
  requirements-aware review handoff, always-uploaded artifacts, and
  independent verdict enforcement.
- [ ] 2.4.1 Add failing runtime-discovery coverage proving its isolated local
  registry contains the recursive module bundle-dependency closure.
- [ ] 2.5 Record commands, timestamps, and expected failures in
  `TDD_EVIDENCE.md` before production edits.

## 3. Core delivery implementation

- [ ] 3.1 Pin and verify the signed immutable modules #368 fixture; reject any
  different repository, commit, package release, dirty checkout, or signature.
- [ ] 3.1.1 Build the runtime-discovery smoke registry from its root modules'
  declared bundle-dependency closure, while retaining the bounded root
  command-surface assertions.
- [ ] 3.2 Extend the local adapter and pre-commit Block 2 to produce and validate
  an index-isolated static proof plan before Code Review and contract tests.
- [ ] 3.3 Replace narrow pull-request path omission with an always-reporting
  Requirements proof decision for relevant PR events and explicit no-impact
  evidence for governed skips.
- [ ] 3.4 Add a bounded executor for supported structured selectors using
  argument arrays, repository containment, option/control rejection, timeout
  and environment limits, and deterministic JUnit output paths.
- [ ] 3.5 Reconcile plan and JUnit through the pinned public module command; do
  not parse proof semantics or rewrite its verdict in core.
- [ ] 3.6 Pass only finalized proof into the released Code Review context input,
  retain both reports, then continue to existing contract/full quality gates.
- [ ] 3.7 Publish plan, JUnit, finalized JSON/Markdown, review provenance, and
  concise summaries before enforcing any red verdict.

## 4. Passing evidence and delivery verification

- [ ] 4.1 Run focused script/workflow tests and record passing evidence in
  `TDD_EVIDENCE.md`.
- [ ] 4.2 Run an integration proof for changed interface -> selected scenario ->
  exact test execution -> JUnit -> reconciled verdict -> review context.
- [ ] 4.3 Prove missing/uncollected/failed/stale proof remains blocking only
  after diagnostic artifacts are retained.

## 5. Quality, documentation, and release

- [ ] 5.1 Run format, type-check, lint, YAML/workflow lint, contract tests,
  smart/full tests, reproducible-delivery checks, and strict module verification.
- [ ] 5.2 Run independent Semgrep/Bandit evidence and fresh changed/full
  SpecFact code review; resolve every finding at every severity.
- [ ] 5.3 Update core delivery and Requirements evidence adoption docs without
  duplicating modules-owned command reference; document branch protection and
  explicit skipped semantics.
- [ ] 5.4 Bump synchronized core version sources and changelog only when the
  behavior implementation is ready for release.
- [ ] 5.5 Run `openspec validate requirements-07-runtime-proof-delivery --strict`
  and retain validation evidence.

## 6. Delivery

- [ ] 6.1 Commit implementation, push the issue-linked feature branch, and open
  the implementation PR to `dev` using the repository template and
  `Fixes nold-ai/specfact-cli#662`.
- [ ] 6.2 Add the PR to project 1, set implementation status to `In Progress`,
  and verify Development, parent, blocker, and required-check metadata.
- [ ] 6.3 After merge, update the internal wiki status/graph and archive only
  with `openspec archive requirements-07-runtime-proof-delivery` from repo root.

## Post-merge cleanup

- [ ] Return to the primary core checkout, fetch `dev`, remove the worktree,
  delete the local feature branch after merge, prune worktrees, and optionally
  delete the merged remote branch.
