# Tasks: Add thorough in-depth codebase validation (sidecar, contract-decorated, dogfooding)

## 1. Create git worktree branch from dev

- [x] 1.1 Ensure primary checkout is on dev and up to date: `git checkout dev && git pull origin dev`
- [x] 1.2 Create worktree branch: `scripts/worktree.sh create feature/validation-01-deep-validation` (used branch name aligned with CHANGE_ORDER).
- [x] 1.3 Verify branch in worktree: `git worktree list` includes the branch path; then run `git branch --show-current` inside that worktree.

## 2. Verify spec deltas (SDD: specs first)

- [x] 2.1 Confirm `specs/codebase-validation-depth/spec.md` exists and is complete (ADDED requirements, Given/When/Then scenarios).
- [x] 2.2 Map scenarios to implementation: Sidecar unmodified, Sidecar optional when CrossHair missing, Full contract-stack, CrossHair deep, Dogfooding commands, Dogfooding optional sidecar, Documentation of validation modes.

## 3. Optional: Deep CrossHair / repro options

- [x] 3.1 In repro command (implementation in `src/specfact_cli/modules/repro/src/commands.py`): add optional `--crosshair-per-path-timeout N` (default: use existing budget behavior).
- [x] 3.2 In `src/specfact_cli/validators/repro_checker.py`: when building CrossHair command, append `--per_path_timeout N` when option is set; keep default unchanged.
- [x] 3.3 Add unit test that repro with `--crosshair-per-path-timeout` passes through to CrossHair command: `test_repro_checker_crosshair_per_path_timeout_passed_to_command`.
- [x] 3.4 Run format and type-check: `hatch run format`, `hatch run type-check`.

## 4. Documentation: Thorough codebase validation

- [x] 4.1 Add or extend a reference section "Thorough codebase validation" in `docs/reference/thorough-codebase-validation.md` covering: (1) quick check, (2) thorough contract-decorated, (3) sidecar, (4) dogfooding.
- [x] 4.2 Document optional deep CrossHair: repro flag `--crosshair-per-path-timeout N` and `crosshair check --per_path_timeout=60 <module>`.
- [x] 4.3 Add dogfooding checklist in same doc: exact commands and order (repro + contract-test-full; optional sidecar).
- [x] 4.4 Docs are copy-pasteable; required env/config stated (`[tool.crosshair]`, sidecar bundle).
- [x] 4.5 New doc page has front-matter; `docs/_layouts/default.html` and `docs/reference/README.md` updated.

## 5. Optional: CI job for thorough validation (dogfooding)

- [x] 5.1 Add or update a CI job (deferred to follow-up by design decision; documented commands accepted as completion criteria for this change).
- [x] 5.2 Document the commands in "Thorough codebase validation"; CI job marked optional/follow-up.

## 6. Quality gates

- [x] 6.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [x] 6.2 Run contract test: `hatch run contract-test`.
- [x] 6.3 Run full test suite: `hatch run smart-test-full` (or `hatch test --cover -v`); validator unit tests passed.
- [x] 6.4 New/modified public APIs: `ReproChecker.__init__` and repro CLI already use contracts/beartype; no new decorators required.

## 7. Documentation research and review (per openspec/config.yaml)

- [x] 7.1 Affected documentation: new `docs/reference/thorough-codebase-validation.md`; reference README and sidebar updated.
- [x] 7.2 Front-matter and sidebar updated; no broken links.

## 8. Create Pull Request to dev

- [x] 8.1 Ensure all changes are committed: `git add .` and `git commit -m "feat: add thorough codebase validation (sidecar, contract-decorated, dogfooding)"`
- [x] 8.2 Push to remote: `git push origin feature/add-thorough-codebase-validation`
- [x] 8.3 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/add-thorough-codebase-validation --title "feat: add thorough codebase validation (sidecar, contract-decorated, dogfooding)" --body-file <path>` (use repo PR template; add OpenSpec change ID `add-thorough-codebase-validation` and summary).
- [x] 8.4 Verify PR and branch are linked to issue (if issue was created) in Development section.
