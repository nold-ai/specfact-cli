# Implementation tasks

TDD / SDD order is enforced. Spec deltas precede scenario-derived tests, genuine
failing-before evidence precedes production edits, and fresh passing evidence
precedes adoption. Each checkbox is a bounded unit of at most two hours; split a
unit before execution if it cannot fit that limit. This planning PR completes no
runtime or release task.

## 1. Create and verify the worktree

- [x] 1.1 Fetch current dev and create the dedicated
  `hotfix/isolate-semgrep-security-runtime` worktree; preserve the primary checkout.
- [x] 1.2 Load repository governance and refresh the GitHub hierarchy cache in a
  dedicated planning environment.
- [ ] 1.3 Before implementation, refresh issue ownership, parent, labels, project
  and dependency state; check for concurrent in-progress work. Bootstrap the
  dedicated complete Hatch environment and run smart/contract preflight status.

## 2. Establish scope and readiness

- [x] 2.1 Verify current Dependabot targets, current dev graph, maintainer advisory,
  upstream metadata and the actual normal-resolution blocker.
- [x] 2.2 Compare independent isolation, replacement and minimal-adoption designs;
  retain the cross-judge and superseding adoption-cycle review, with explicit limits.
- [x] 2.3 Write the new proposal, design and scenario deltas without modifying the
  older consolidation or downstream-producer change.
- [ ] 2.4 Establish the candidate upstream native release, exact source revision,
  publisher/signature identity and independently trusted verification procedure.
  Verify actual bytes before execution. #772/#779 remains a related blocked
  alternative, not a prerequisite or an authority source for replacement.
- [ ] 2.5 Specify packaged trusted-policy delivery, supported native targets and
  explicit preparation for installed users. Verify that scanning-extra compatibility
  permits a patch release; if it cannot, retain the release block and reconcile
  release scope before implementation.
- [ ] 2.6 Inventory all installation, execution and audit surfaces, including
  external Code Review, generated workflows, wheel/sdist and offline operation.
  Resolve external contracts before claiming completion. Obtain complete native
  component/source/license inventory and a reproducible advisory assessment.
  Missing identity, component coverage or publisher proof rejects the candidate.
- [x] 2.7 Track the external Code Review module migration separately in modules
  #523, covering command paths, packaged rule payloads, bundle resources, integrity,
  module version and CI/CD signatures. Its implementation remains pending; do not
  claim end-to-end replacement before its verified completion. Task 4.4 is blocked
  until that migration preserves required Code Review coverage using the admitted
  replacement; investigation and candidate proof can proceed before the cutover.

## 3. Derive tests and capture genuine RED

- [ ] 3.1 Derive aggregate-audit tests from both complete-coverage scenarios.
  Prove scanner-only advisory and omitted scanner inventory fail for the intended
  reason. Preserve existing CI, Code Review and runtime-smoke coverage assertions.
- [ ] 3.2 Derive publisher admission, installed-identity and
  interrupted/concurrent preparation tests. Include empty, tampered, expired and
  wrong-platform artifacts without granting synthetic fixtures production authority.
- [ ] 3.3 Derive actual consumer tests for ambient PATH, stale cache, wheel-installed
  external projects and offline unavailable-tool behavior. Preserve public results.
  Prove Semgrep removal is rejected while the installed Code Review module still
  requires it; then prove real clean-code, bug and AI-bloat review coverage after
  module migration with Python Semgrep absent from a fresh delivery environment.
- [ ] 3.4 Add real scan fixtures for every used rule family, captures, ignores,
  baseline identity, autofix and required error/partial-result behavior. Compare
  current engine and authenticated replacement on identical targets. Execute every
  advertised native target and Python 3.11-3.13 installed consumer; filenames,
  mocks and synthetic authority do not establish parity or platform support.
- [ ] 3.5 Run the authored tests before production edits. Record timestamped commands,
  actual intended failures and scenario/test mapping in `TDD_EVIDENCE.md`. Resolver
  conflict evidence alone does not satisfy this implementation RED requirement.
- [ ] 3.6 Bind authored and final evidence through the repository's current native
  Requirements lifecycle, including any required independent protected acceptance.

## 4. Implement the verified replacement unit

- [ ] 4.1 After feasibility passes, bind exact native artifacts, publisher identity,
  provenance and complete component/advisory/license evidence in one reviewed
  packaged inventory. Candidate code cannot approve its own entries. No guessed
  coordinate, wildcard identity, advisory exclusion or unverified cache reuse.
- [ ] 4.2 Implement one packaged preparation/selection owner with `@beartype` and
  meaningful `@icontract` contracts. Verify actual installed native components, atomic
  publication, retries and current artifact/component identity before selecting an absolute executable.
- [ ] 4.3 Extend existing frozen-delivery verification and required audits for the
  native scanner inventory. Keep one owner for completeness; avoid a generic registry unless
  a demonstrated existing limitation requires one.
- [ ] 4.4 Migrate every scanner consumer and CI/Hatch invocation, then remove shared
  Semgrep dependency declarations in the same verified unit. This removal is blocked
  on verified modules #523 migration, including installed bundle command paths,
  packaged rules, integrity and required review coverage with Python Semgrep absent.
  A tracking issue or withheld end-to-end claim does not satisfy this prerequisite.
  Regenerate all Python inputs normally and account for every package moved, removed
  or added; keep removal and its actual fresh-environment proof in one cutover unit.
- [ ] 4.5 Execute the scenario suite and real scanner comparisons. Record actual
  passing results, refusal behavior, audit evidence and native/platform identities
  in `TDD_EVIDENCE.md`; keep incomplete matrix cells and differences blocking.

## 5. Verify integration and research documentation

- [ ] 5.1 Run required gates in order: `hatch run format`, `hatch run type-check`,
  `hatch run lint`, `hatch run yaml-lint`, `hatch run contract-test`,
  `hatch run smart-test`.
- [ ] 5.2 Run reproducible-delivery verification, `uv lock --check`, the committed
  BasedPyright npm install and canonical project type check. Preserve installed
  package/SBOM evidence from the Python 3.11-3.13 built-wheel matrix.
- [ ] 5.3 Run license, complete frozen security and dependency-trust checks,
  Bandit, independent SAST and unchanged baseline gate. Require every native scanner
  component check and required hosted Socket status as well.
- [ ] 5.4 Verify strict module signatures. If signed assets change, obtain their
  required version bump and CI/CD signatures, then verify again. Do not sign locally.
- [ ] 5.5 Research affected README, docs/index.md, installation/scanning guides and
  generated workflow documentation. Document explicit preparation, offline behavior
  and migration; preserve frontmatter and update navigation if pages move.

## 6. Prepare the eventual core patch and final review

- [ ] 6.1 Recheck current dev and PyPI. Select the next patch after current core
  only when scanner/extra compatibility remains suitable for a patch. At the
  inspected snapshot this would be 0.55.11 after 0.55.10.
- [ ] 6.2 Synchronize `pyproject.toml`, `setup.py`, `src/__init__.py`,
  `src/specfact_cli/__init__.py`, generated project metadata and a same-commit
  Security/Fixed changelog entry with the actual Europe/Berlin date.
- [ ] 6.3 Run `hatch run check-version-sources`, strict `hatch run check-pypi-ahead`,
  frozen parity and affected package installation checks after the version update.
- [ ] 6.4 Run fresh SpecFact review after final source/config/version changes.
  Resolve all findings, including clean-code warnings; retain independent static
  analysis, current-head review and required native/authority evidence. Verify the
  migrated installed module executes all required scanner rule families in that
  fresh post-removal environment; missing Semgrep cannot become skipped coverage.

## 7. Publish the implementation PR and disposition older PRs

- [ ] 7.1 Prepare Conventional Commits and one narrowly scoped implementation PR
  targeting dev. Per the owner's 2026-10-20 direction, signing is handled through
  a CI/CD follow-up, not locally. Use the repository PR template and link this issue.
- [ ] 7.2 Attach complete current-head validation and required project/development
  links. Do not present this planning PR as the verified security replacement.
- [ ] 7.3 After verified implementation coverage exists, comment on each covered
  dependency PR with the implementation PR link, then close it and read back state.
  Record the distinct JSON migration and incidental transitive-update dispositions.
- [ ] 7.4 Reassess #771 and actual dev-to-main contents. Merge or publish only under
  the applicable authority and required current-head checks; describe the real
  release scope. A dependency-only PR does not make all of dev dependency-only.

## Post-merge cleanup

- [ ] Update the internal wiki from its own repository root; preserve unrelated work.
- [ ] After implementation is complete and merged, finalize this change only with
  `openspec archive isolate-semgrep-security-runtime` and validate resulting specs.
- [ ] After reviewed integration, remove the dedicated worktree and its branch;
  retain required immutable evidence. Never manually move the change into archive.
