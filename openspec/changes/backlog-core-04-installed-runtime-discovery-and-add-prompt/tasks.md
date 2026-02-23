# Tasks: backlog-core-04-installed-runtime-discovery-and-add-prompt

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for behavior changes.

1. Update spec deltas first.
2. Add tests mapped to scenarios.
3. Run tests and capture failing results in `TDD_EVIDENCE.md`.
4. Implement production code.
5. Re-run tests and quality checks; capture passing evidence in `TDD_EVIDENCE.md`.

## 1. Branch and scope

- [ ] 1.1 Work on `bugfix/backlog-core-04-installed-runtime-discovery-and-add-prompt` (or active equivalent) before implementation changes.
- [x] 1.2 Confirm scope is limited to runtime module discovery parity and backlog-add prompt installation parity.

## 2. Specs first

- [x] 2.1 Finalize `specs/installed-runtime-module-discovery/spec.md` scenarios for installed runtime discovery fallback.
- [x] 2.2 Finalize `specs/backlog-add-slash-prompt/spec.md` scenarios for prompt file + IDE setup installation behavior.

## 3. Tests first (must fail before implementation)

- [x] 3.1 Add/extend unit tests in `tests/unit/specfact_cli/registry/test_module_packages.py` for installed-runtime fallback discovery behavior.
- [x] 3.2 Add/extend unit tests in `tests/unit/utils/test_ide_setup.py` to require backlog-add prompt installation.
- [x] 3.3 Run targeted tests and record failing results in `TDD_EVIDENCE.md`.

## 4. Implementation

- [x] 4.1 Update `src/specfact_cli/registry/module_packages.py` to include repo-local module root fallback for installed runtime (without requiring `SPECFACT_MODULES_ROOTS`).
- [x] 4.2 Add `resources/prompts/specfact.backlog-add.md` with workflow guidance matching existing prompt style.
- [x] 4.3 Update `src/specfact_cli/utils/ide_setup.py` (`SPECFACT_COMMANDS`) to include `specfact.backlog-add`.

## 5. Validation and docs

- [x] 5.1 Re-run targeted tests and record passing results in `TDD_EVIDENCE.md`.
- [x] 5.2 Run quality gates for touched scope (`hatch run format`, targeted tests, and any required checks for modified files).
- [x] 5.3 Update affected docs if command prompt references changed. (No docs updates required after review; prompt is bundled and auto-installed via IDE setup list.)
- [x] 5.4 Run `openspec validate backlog-core-04-installed-runtime-discovery-and-add-prompt --strict` and update `CHANGE_VALIDATION.md`.

## 6. Delivery

- [x] 6.1 Update `openspec/CHANGE_ORDER.md` status and placement.
- [ ] 6.2 Prepare PR with clear runtime parity verification notes (installed vs hatch behavior).
