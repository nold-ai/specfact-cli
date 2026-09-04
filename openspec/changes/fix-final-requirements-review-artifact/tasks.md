# Tasks: Fix final Requirements review artifact handling

## 1. Readiness and specification

- [x] 1.1 Create `bugfix/710-requirements-no-python-review` in an isolated
  worktree from freshly fetched `origin/dev` before implementation edits.
- [x] 1.2 Verify issue #710 is open, assigned, labeled, In Progress, linked under
  #692, and a native blocker; check for duplicate issues and changes.
- [x] 1.3 Define the no-target and required-review artifact behavior plus
  fail-closed controls.
- [x] 1.4 Validate this OpenSpec change strictly before authoring tests.

## 2. Tests and failing evidence

- [ ] 2.1 Add exact workflow tests for the no-Python-target output, required
  Python review artifact, and unchanged verdict enforcement.
- [ ] 2.2 Map the scenarios to exact pytest selectors in
  `requirements-evidence.yaml` and obtain the required mapping acceptance.
- [ ] 2.3 Run the focused selectors before workflow edits and record the exact
  failing result, timestamp, environment, and assertions in `TDD_EVIDENCE.md`.

## 3. Minimal implementation

- [ ] 3.1 Emit only fixed `review-required=false|true` values from the final
  Code Review step at the exact target-selection boundary.
- [ ] 3.2 Make artifact upload conditional on exact `true` while retaining
  `always()`, the pinned action, and `if-no-files-found: error`.
- [ ] 3.3 Preserve final review failure enforcement and all trusted setup,
  checkout, path, artifact, and toolchain controls.

## 4. Passing evidence and quality gates

- [ ] 4.1 Re-run the focused selectors and legitimate no-target/failure controls
  with passing evidence.
- [ ] 4.2 Run workflow lint, YAML lint, format, lint, type-check, contract gates,
  smart tests, strict OpenSpec validation, module-signature verification,
  Requirements evidence, and SpecFact Code Review; resolve every finding or
  document an explicitly approved exception.
- [ ] 4.3 Confirm PR #706 no longer reproduces the final artifact failure after
  this fix reaches `dev`.

## 5. Documentation, release, and delivery

- [ ] 5.1 Record that README and published docs need no change because this is
  an internal CI control-flow correction.
- [ ] 5.2 Keep the existing unreleased `0.55.4` version and changelog transaction
  unchanged; do not create `0.55.5` for this blocker.
- [ ] 5.3 After merge, update the internal wiki source without altering internal
  wiki PR #38 or its planning branch, and rebuild the graph from the internal
  repository root.
- [ ] 5.4 Promote the issue-linked draft PR to ready for review only after
  required local gates pass; resolve all review threads and merge only under
  normal policy. A draft opened at the test-only commit may retain immutable
  GitHub RED evidence before that promotion.
- [ ] 5.5 After merge, archive this change with `openspec archive
  fix-final-requirements-review-artifact`, validate the resulting canonical
  spec, and remove the dedicated worktree and merged branch.
