# Tasks: upgrade-02-pipx-spaced-home-output

## 1. Readiness and spec validation

- [x] 1.1 Confirm issue `#570` is scoped to `specfact-cli` upgrade output handling.
- [x] 1.2 Create GitHub change issue `#572`, labels, parent `#375`, and dependency relationship blocking `#570`.
- [x] 1.3 Validate the OpenSpec change with `openspec validate upgrade-02-pipx-spaced-home-output --strict`.

## 2. Failing-first tests

- [x] 2.1 Add unit tests for successful pipx upgrade filtering and failed pipx diagnostic preservation.
- [x] 2.2 Add subprocess-backed validation for a fake pipx executable under a path containing spaces.
- [x] 2.3 Run targeted tests before production edits and record failing evidence in `TDD_EVIDENCE.md`.

## 3. Upgrade output hardening

- [x] 3.1 Capture upgrade subprocess stdout/stderr for replay.
- [x] 3.2 Suppress only the known benign pipx spaced-home warning block on successful pipx upgrades.
- [x] 3.3 Preserve all child-process output on failed upgrades.
- [x] 3.4 Replay partial child-process output on timed-out upgrades.
- [x] 3.5 Preserve existing pip, uv, uvx, and OS-error behavior.

## 4. Real-world validation and source tracking

- [x] 4.1 Run the subprocess-backed fake-pipx validation after implementation.
- [x] 4.2 Update sibling internal wiki source tracking and run `python3 scripts/wiki_rebuild_graph.py` from the internal repo root.
- [x] 4.3 Reconfirm GitHub issue metadata and project assignment.

## 5. Passing evidence and quality gates

- [x] 5.1 Re-run targeted tests and record passing evidence in `TDD_EVIDENCE.md`.
- [x] 5.2 Run required quality gates for touched scope.
- [x] 5.3 Run SpecFact code review JSON and fix findings unless an explicit exception is documented.
- [x] 5.4 Bump the patch release version and update `CHANGELOG.md` for the bugfix branch.
- [x] 5.5 Bump the touched bundled `upgrade` module version for PR-style module verification.
- [x] 5.6 Update task checkboxes and prepare the branch for PR to `dev`.
