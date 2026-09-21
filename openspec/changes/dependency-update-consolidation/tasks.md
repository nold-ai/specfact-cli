# Tasks: Dependency update consolidation

These tasks describe future implementation, not the completed proposal-authoring work. All remain unchecked. Split execution into units of at most two hours; record partial investigations honestly.

## 1. Establish implementation ownership and baseline

- [ ] 1.1 Fetch current origin/dev and create a dedicated implementation worktree/branch; preserve the primary checkout. Confirm no concurrent ownership, refresh hierarchy, and verify issue parent, labels, project, blockers, and status.
- [ ] 1.2 Revalidate this proposal, source PRs #744/#727, dependency policy, source tracking, and candidate evidence against current repository reality; do not reuse this dated snapshot as current security approval.
- [ ] 1.3 Create an isolated environment from reviewed frozen inputs and capture baseline tests, audits, and existing failures separately.

## 2. Complete discovery and security review before candidate execution

- [ ] 2.1 Inventory all declared runtime/build/extras/Hatch/Code Review dependencies, setup.py parity, relevant module-manifest declarations, and every marker-specific transitive; give each record a disposition.
- [ ] 2.2 Reuse the latest resolver lane in disposable metadata-only analysis, check exact pins separately, retain supported major lines, and enumerate every intervening release. Review upstream release notes, Python/platform compatibility, licenses, and changed transitive paths.
- [ ] 2.3 Audit baseline and candidate graphs, including isolated Code Review tooling and all marker branches; retain package/version/CVE/GHSA/OSV evidence, affected/fixed ranges, sources, timestamp, errors, and coverage.
- [ ] 2.4 Complete exact-artifact Socket and upstream/registry malware/provenance review before installing candidates. Reject confirmed malicious/blocked releases; defer missing evidence and unresolved signals. Verify hashes and reject skipped/no-change checks as approval.
- [ ] 2.5 Retain pycparser 2.22 unless a fresh exact-artifact review passes; preserve blocked 3.0 releases and security-tool floors. Review necessary CVE exceptions under existing policy without substituting exceptions for available compatible fixes.
- [ ] 2.6 Record deferred major migrations, JSON 3.x/Jekyll downgrade, incompatible latest releases, and any separately required module release as explicit follow-ups. Select one complete screened candidate graph.

## 3. Specify and prove required behavior changes

- [ ] 3.1 Revalidate scenario specs and map changed behavior to existing regression tests; add only meaningful new tests where coverage is missing.
- [ ] 3.2 Update the Hatchling build-backend expectation before changing its declarations; capture the actual failing-before result. For other behavior fixes, capture failing tests before production changes in TDD_EVIDENCE.md.
- [ ] 3.3 For pure dependency/data changes without a behavior fix, retain baseline and candidate audit/resolution evidence; do not fabricate a failing test or test execution claim.

## 4. Apply the screened dependency refresh

- [ ] 4.1 Update Hatchling's build/dev pins and reviewed compatible requirements; synchronize duplicated setup.py, extras, and Hatch/test inputs only where implicated.
- [ ] 4.2 Regenerate the primary lock and hash-protected CI export with existing refresh tooling; refresh isolated Code Review input/lock and its digest separately. Compare the resulting graph with the screened graph and re-screen every deviation.
- [ ] 4.3 Update version-specific trust or license evidence only after substantive review. If docs dependencies change, refresh JSON within the supported Jekyll graph without the downgrade.
- [ ] 4.4 Apply minimal compatibility fixes justified by failing tests; retain decorators/contracts for any introduced public function, without speculative abstractions or new CLI APIs.

## 5. Validate the final candidate

- [ ] 5.1 Run reproducible-delivery verification, uv lock --check, install consistency, dependency trust, license-check, security-audit for both graphs, Bandit, and independent Semgrep checks. Require Socket project and PR evidence that actually covers the final graph.
- [ ] 5.2 Run latest and lowest-direct compatibility lanes in separate synchronized environments on Python 3.11–3.13, covering minimal runtime and optional profiles. Record exact environments and interpreters; do not treat advisory results as release evidence.
- [ ] 5.3 Run the frozen wheel/package matrix, pip/pipx/uv installation paths, CLI and module discovery smoke checks, contract and relevant integration tests, typing, lint, coverage, and SpecFact review. Resolve all applicable findings; retain passing evidence and baseline failures separately.
- [ ] 5.4 Verify strict module signatures. If signed assets actually require changes, obtain a reviewed module version bump and signature and revalidate core compatibility; never move immutable fixtures merely to pass.
- [ ] 5.5 If the Ruby graph changes, audit it and build Jekyll. Review affected contributor/security docs, README, landing page, and navigation, changing only what the implemented behavior requires.

## 6. Release preparation and final PR

- [ ] 6.1 Select the next valid patch release and update all four canonical version sources and CHANGELOG.md. Rerun version checks, wheel metadata validation, and affected core/module compatibility against the resulting release identity.
- [ ] 6.2 Repeat audits on the final committed graphs, update audit dispositions and source tracking, and obtain fresh required CI/review evidence. Confirm no unreviewed advisory, blocked artifact, unresolved malware signal, or unknown coverage was promoted.
- [ ] 6.3 Open the implementation PR to dev with issue linkage, precise source-PR disposition, before/after evidence, limitations, and coherent rollback instructions. Keep source bot PRs open until replacement implementation merges.

## 7. After merge and release

- [ ] 7.1 Refresh advisory evidence if identities or advisory information change before release; promote through the established release workflow. Close only bot PRs actually superseded by the merged implementation.
- [ ] 7.2 Finalize the completed change with openspec archive dependency-update-consolidation; synchronize the internal wiki/status graph from its repository root and remove the implementation worktree after merge.
