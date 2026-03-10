# Implementation Tasks: backlog-02-migrate-core-commands

## 1. Branch and worktree setup

- [x] 1.1 Create worktree from origin/dev: `git worktree add ../specfact-cli-worktrees/feature/backlog-02-migrate-core-commands -b feature/backlog-02-migrate-core-commands origin/dev`
- [x] 1.2 Change to worktree: `cd ../specfact-cli-worktrees/feature/backlog-02-migrate-core-commands`
- [x] 1.3 Bootstrap Hatch environment: `hatch env create`
- [x] 1.4 Verify pre-flight checks: `hatch run smart-test-status` and `hatch run contract-test-status`
- [x] 1.5 Copy backlog-core source from `specfact-cli-worktrees/feature/agile-01-feature-hierarchy/modules/backlog-core/src/backlog_core/` to `specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/backlog_core/`
- [x] 1.6 Verify copied files: `add.py`, `analyze_deps.py`, `delta.py`, `diff.py`, `promote.py`, `sync.py`, `verify.py`, `release_notes.py`, `main.py`, `graph/`, `adapters/`, `analyzers/`

## 2. Integration and refactoring

- [x] 2.1 Update imports in all copied files: replace `backlog_core` with `specfact_backlog.backlog`
- [x] 2.2 Move command functions from `backlog_core/commands/` to `specfact_backlog/backlog/commands.py` or keep as submodules
- [x] 2.3 Register commands in main `commands.py` using `@app.command()` decorator
- [x] 2.4 Update `_ORDER_PRIORITY` in `_BacklogCommandGroup` to include new commands
- [ ] 2.5 Add ceremony aliases: `ceremony_add`, `ceremony_sync` in `commands.py`
- [ ] 2.6 Resolve any import conflicts with existing specfact-backlog utilities

## 3. Tests (TDD)

- [ ] 3.1 Copy tests from `modules/backlog-core/tests/` to `specfact-cli-modules/tests/unit/specfact_backlog/`
- [ ] 3.2 Update test imports to use specfact-backlog paths
- [ ] 3.3 Add failing test: `test_backlog_add_github_creates_issue` (run and capture failure)
- [ ] 3.4 Add failing test: `test_backlog_sync_bidirectional` (run and capture failure)
- [ ] 3.5 Add failing test: `test_backlog_delta_status_shows_changes` (run and capture failure)
- [ ] 3.6 Capture TDD_EVIDENCE.md with failing test timestamps

## 4. Implementation

- [ ] 4.1 Fix any import errors preventing test execution
- [ ] 4.2 Ensure `backlog add` command creates items via adapter
- [ ] 4.3 Ensure `backlog sync` performs bidirectional sync
- [ ] 4.4 Ensure `backlog delta` subcommands analyze changes
- [ ] 4.5 Ensure `backlog analyze-deps` builds dependency graph
- [ ] 4.6 Ensure `backlog verify-readiness` validates DoR
- [ ] 4.7 Re-run tests and capture passing evidence in TDD_EVIDENCE.md

## 5. Quality gates

- [ ] 5.1 Run `hatch run format` (specfact-cli and specfact-cli-modules)
- [ ] 5.2 Run `hatch run type-check`
- [ ] 5.3 Run `hatch run contract-test`
- [ ] 5.4 Run `hatch run smart-test` (or `hatch run smart-test-full`)
- [ ] 5.5 Verify no duplicate command warnings
- [ ] 5.6 Update module version in `module-package.yaml` (specfact-backlog)
- [ ] 5.7 Sign module: `hatch run python scripts/sign-modules.py --key-file <key> packages/specfact-backlog/module-package.yaml`
- [ ] 5.8 Verify signature: `hatch run ./scripts/verify-modules-signature.py --require-signature`

## 6. Documentation

- [ ] 6.1 Update `docs/guides/agile-scrum-workflows.md` to confirm command availability
- [ ] 6.2 Update `docs/guides/backlog-delta-commands.md` to confirm delta subcommands
- [ ] 6.3 Update `docs/guides/backlog-dependency-analysis.md` to confirm analyze-deps
- [ ] 6.4 Update CHANGELOG.md with restored commands

## 7. Validation and PR

- [ ] 7.1 Run `openspec validate backlog-02-migrate-core-commands --strict`
- [ ] 7.2 Run `/wf-validate-change backlog-02-migrate-core-commands` (if available)
- [ ] 7.3 Stage all changes: `git add -A`
- [ ] 7.4 Commit with GPG signing: `git commit -S -m "feat: migrate backlog-core commands to specfact-backlog bundle"`
- [ ] 7.5 Push branch: `git push -u origin feature/backlog-02-migrate-core-commands`
- [ ] 7.6 Create PR to `dev` with description referencing this change

## 8. Cleanup (post-merge)

- [ ] 8.1 Return to primary checkout: `cd /home/dom/git/nold-ai/specfact-cli`
- [ ] 8.2 Remove worktree: `git worktree remove ../specfact-cli-worktrees/feature/backlog-02-migrate-core-commands`
- [ ] 8.3 Delete local branch: `git branch -d feature/backlog-02-migrate-core-commands`
- [ ] 8.4 Prune worktree list: `git worktree prune`
