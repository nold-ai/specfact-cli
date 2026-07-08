# Tasks: requirements-02-module-commands

## 1. Branch and dependency guardrails

- [x] 1.1 Create dedicated worktree branch `feature/requirements-02-module-commands` from `dev` before implementation work: `scripts/worktree.sh create feature/requirements-02-module-commands`.
- [x] 1.2 Refresh GitHub hierarchy cache, verify issue #239 is not in progress, and confirm available label/structure metadata.
- [x] 1.3 Verify prerequisite changes are implemented or explicitly accepted as parallel work.
- [x] 1.4 Reconfirm scope against `openspec/CHANGE_ORDER.md`: keep this change as import, normalization, validation, and coverage helpers for validation evidence.
- [x] 1.5 Update the public GitHub issue body to match the narrowed validation-evidence format.
- [x] 1.6 Update the internal wiki mirror and run `wiki_rebuild_graph.py` from the internal repo root.

## 2. Spec-first and test-first preparation

- [x] 2.1 Finalize `specs/` deltas for all listed capabilities and cross-check scenario completeness.
- [x] 2.2 Add/update tests mapped to new and modified scenarios.
- [x] 2.3 Run targeted tests to capture failing-first behavior and record results in `TDD_EVIDENCE.md`.

## 3. Implementation

- [x] 3.1 Implement minimal production code required to satisfy the new scenarios.
- [x] 3.2 Add/update contract decorators and type enforcement on public APIs.
- [x] 3.3 Update adapter helpers and models required by this change scope only.
- [x] 3.4 Keep runtime `specfact requirements ...` command handlers in the paired modules-repo scope; core only exposes reusable helpers.
- [x] 3.5 Add core registry category compatibility for the paired `requirements` module group without adding root CLI handlers.

## 4. Validation and documentation

- [x] 4.1 Re-run tests and quality gates until all changed scenarios pass.
- [x] 4.2 Update user-facing docs and navigation for changed/added commands and workflows.
- [x] 4.3 Run module-signature verification; if signed module assets changed, bump module versions and re-sign before PR.
- [x] 4.4 Run `openspec validate requirements-02-module-commands --strict` and resolve all issues.
- [x] 4.5 Run SpecFact code review JSON, independent static analysis, and clean-code gates; resolve all findings or document rare explicit exceptions.

## 5. Delivery

- [x] 5.1 Update version files and `CHANGELOG.md` with a minor feature release entry.
- [x] 5.2 Review `openspec/CHANGE_ORDER.md` status/dependency notes; update only if implementation sequencing changed.
- [x] 5.3 Open a PR from `feature/requirements-02-module-commands` to `dev` with spec/test/code/docs evidence.
