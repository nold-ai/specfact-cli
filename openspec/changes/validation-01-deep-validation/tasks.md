# Tasks: Add thorough in-depth codebase validation (sidecar, contract-decorated, dogfooding)

## 1. Create git worktree branch from dev

- [ ] 1.1 Ensure primary checkout is on dev and up to date: `git checkout dev && git pull origin dev`
- [ ] 1.2 Create worktree branch: `scripts/worktree.sh create feature/add-thorough-codebase-validation`; if issue exists, link it with `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name feature/add-thorough-codebase-validation`
- [ ] 1.3 Verify branch in worktree: `git worktree list` includes the branch path; then run `git branch --show-current` inside that worktree.

## 2. Verify spec deltas (SDD: specs first)

- [ ] 2.1 Confirm `specs/codebase-validation-depth/spec.md` exists and is complete (ADDED requirements, Given/When/Then scenarios).
- [ ] 2.2 Map scenarios to implementation: Sidecar unmodified, Sidecar optional when CrossHair missing, Full contract-stack, CrossHair deep, Dogfooding commands, Dogfooding optional sidecar, Documentation of validation modes.

## 3. Optional: Deep CrossHair / repro options

- [ ] 3.1 In `src/specfact_cli/commands/repro.py`: add optional `--crosshair-per-path-timeout N` (default: use existing budget behavior) so users can increase CrossHair depth for repro runs.
- [ ] 3.2 In `src/specfact_cli/validators/repro_checker.py`: when building CrossHair command, append `--per_path_timeout N` when repro option is set; keep default unchanged.
- [ ] 3.3 Add unit or integration test that repro with `--crosshair-per-path-timeout` passes through to CrossHair command (or skip if deferred to docs-only).
- [ ] 3.4 Run format and type-check: `hatch run format`, `hatch run type-check`.

## 4. Documentation: Thorough codebase validation

- [ ] 4.1 Add or extend a reference section "Thorough codebase validation" (e.g. in `docs/reference/` or under existing validation doc) covering: (1) quick check (`specfact repro`), (2) thorough contract-decorated (`hatch run contract-test-full`), (3) sidecar for unmodified code (`specfact repro --sidecar --sidecar-bundle <bundle>`), (4) dogfooding (repro + contract-test-full on specfact-cli; optional sidecar).
- [ ] 4.2 Document optional deep CrossHair: how to run CrossHair with higher per-path timeout (repro flag or `crosshair check --per_path_timeout=60 <module>`); optional module list for critical paths.
- [ ] 4.3 Add dogfooding checklist or CI note: exact commands and order for validating specfact-cli (repro + contract-test-full; optional sidecar); link from README or contributing guide if appropriate.
- [ ] 4.4 Ensure docs are copy-pasteable; state any required env or config (e.g. `[tool.crosshair]`, sidecar bundle).
- [ ] 4.5 If adding a new doc page: set front-matter (layout, title, permalink, description) and update `docs/_layouts/default.html` sidebar if needed.

## 5. Optional: CI job for thorough validation (dogfooding)

- [ ] 5.1 Add or update a CI job (e.g. in `.github/workflows/`) that runs `specfact repro --repo .` and `hatch run contract-test-full` (or equivalent) so specfact-cli validates itself on PR or nightly. Use reasonable timeouts to avoid flakiness.
- [ ] 5.2 Document the job in the "Thorough codebase validation" section; mark as optional if job is added in a follow-up.

## 6. Quality gates

- [ ] 6.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [ ] 6.2 Run contract test: `hatch run contract-test`.
- [ ] 6.3 Run full test suite: `hatch run smart-test-full` (or `hatch test --cover -v`).
- [ ] 6.4 Ensure any new or modified public APIs have `@icontract` and `@beartype` where applicable.

## 7. Documentation research and review (per openspec/config.yaml)

- [ ] 7.1 Identify affected documentation: new or extended "Thorough codebase validation" section; README or contributing link if added; no new top-level pages unless created in task 4.
- [ ] 7.2 Verify front-matter and sidebar if a new page was added; confirm no broken links.

## 8. Create Pull Request to dev

- [ ] 8.1 Ensure all changes are committed: `git add .` and `git commit -m "feat: add thorough codebase validation (sidecar, contract-decorated, dogfooding)"`
- [ ] 8.2 Push to remote: `git push origin feature/add-thorough-codebase-validation`
- [ ] 8.3 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/add-thorough-codebase-validation --title "feat: add thorough codebase validation (sidecar, contract-decorated, dogfooding)" --body-file <path>` (use repo PR template; add OpenSpec change ID `add-thorough-codebase-validation` and summary).
- [ ] 8.4 Verify PR and branch are linked to issue (if issue was created) in Development section.
