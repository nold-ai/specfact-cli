## 1. Governance and release dependency

- [x] 1.1 Create isolated branch/worktree `feature/requirements-06-evidence-enforcement` from `origin/dev`.
- [x] 1.2 Verify core #657 parent, labels, project Todo state, and blocker relation to modules #361.
- [x] 1.3 Verify modules #352 is released and modules #361 remains the active fixture-release blocker.
- [x] 1.4 Record modules #361 release `specfact-requirements` 0.3.3,
  immutable commit `2438372f8e34c96d4e474afa4c66c92a9cee7979`, command/report
  contract, and fixture provenance; recheck #657 blocker state before
  production implementation.

## 2. Specification and failing evidence

- [x] 2.1 Add the `requirements-evidence-delivery-gate` specification, proposal, and design without inventing unpublished #361 interface details.
- [x] 2.2 Add failing script and workflow tests for fixture verification, staged red/green verdict behavior, report retention, gate ordering, CI summary, and always-upload artifacts using the released #361 fixture contract.
- [x] 2.3 Run the focused tests and record failing-before evidence in `TDD_EVIDENCE.md` before production edits.

## 3. Delivery-gate implementation

- [x] 3.1 Pin and verify the released modules #361 fixture in `ci/module-fixture.lock.json` and the local/CI materialization path.
- [x] 3.2 Add the pre-commit evidence hook after Block 1 and before code review/contract checks; retain and report JSON/Markdown artifact paths before a red exit.
- [x] 3.3 Add the pull-request CI evidence gate with base-reference mode, concise job summary, and always-run report upload.
- [x] 3.4 Keep module-owned verdict semantics, staged-index behavior, and remediation content unchanged; add no fallback to mutable module sources.

## 4. Verification, documentation, and delivery

- [x] 4.1 Run focused tests, then format, type-check, lint, YAML lint, contract tests, smart tests, and workflow lint; record passing-after evidence.
- [x] 4.2 Run fresh SpecFact code review JSON and independent Semgrep/Bandit checks; resolve all findings.
- [x] 4.3 Update affected core delivery and Requirements evidence documentation without duplicating modules command documentation.
- [x] 4.4 Bump the feature version and changelog after implementation, then verify synchronized version sources and released-fixture integrity.
- [ ] 4.5 Revalidate the OpenSpec change, update the internal wiki mirror and graph, open the PR to `dev`, and archive only after merge.
