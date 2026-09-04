# Tasks: Fix CI test environment isolation

## 1. Readiness and specification

- [x] 1.1 Create `bugfix/708-ci-test-env-isolation` in an isolated worktree from
  freshly fetched `origin/dev` before implementation edits.
- [x] 1.2 Verify issue #708 is open, assigned, labeled, in the SpecFact CLI
  project, and linked under #692; check for duplicate issues and changes.
- [x] 1.3 Define the step-scoped isolation behavior and rejected alternatives.
- [x] 1.4 Validate this OpenSpec change strictly before authoring tests.

## 2. Tests and failing evidence

- [x] 2.1 Add exact workflow tests for the Python 3.12 and Python 3.11 pytest
  steps plus a negative control proving non-test routing remains unchanged.
- [x] 2.2 Map the scenarios to exact pytest selectors in
  `requirements-evidence.yaml` and obtain the required mapping acceptance.
- [x] 2.3 Run the focused selectors before workflow edits and record the exact
  failing result, timestamp, environment, and expected assertions in
  `TDD_EVIDENCE.md`.

## 3. Minimal implementation

- [ ] 3.1 Isolate `GITHUB_BASE_REF` only on the two test-execution steps in
  `.github/workflows/pr-orchestrator.yml`.
- [ ] 3.2 Preserve the variable for all non-test workflow steps and avoid any
  production-script or test-helper change.

## 4. Passing evidence and quality gates

- [ ] 4.1 Re-run the focused selectors and the original two version-source
  follow-up regressions with passing evidence.
- [ ] 4.2 Run workflow lint, YAML lint, format, lint, type-check, contract gates,
  smart tests, strict OpenSpec validation, module-signature verification,
  Requirements evidence, and SpecFact code review; resolve every finding or
  document an explicitly approved exception.
- [ ] 4.3 Confirm PR #691's Python 3.11 and Python 3.12 failures no longer
  reproduce after the fix reaches `dev`.

## 5. Documentation, release, and delivery

- [ ] 5.1 Review README and published `docs/`; record that no user-facing page
  changes because only internal CI test isolation changes.
- [ ] 5.2 Keep the existing unreleased `0.55.4` version and changelog transaction
  unchanged; do not create `0.55.5` for this release-blocking follow-up.
- [ ] 5.3 Update the internal wiki source and rebuild its graph without changing
  internal wiki PR #38 or its planning branch.
- [ ] 5.4 Open the issue-linked PR to `dev` only after the required local gates
  pass; resolve all review threads and merge only under normal policy.
- [ ] 5.5 After merge, archive this change with `openspec archive
  fix-ci-test-environment-isolation`, validate the resulting canonical spec,
  and remove the dedicated worktree and merged branch.
