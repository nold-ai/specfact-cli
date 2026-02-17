# Tasks: workflow-01-git-worktree-management

## TDD / SDD order (enforced)

Per `openspec/config.yaml`: specs first, tests second (failing), implementation third, then passing verification.

## 1. Create git worktree branch from dev

- [x] 1.1 Ensure local `dev` is up to date.
- [x] 1.2 Create dedicated worktree branch `feature/workflow-01-git-worktree-management` from `dev`: `scripts/worktree.sh create feature/workflow-01-git-worktree-management`.
- [x] 1.3 Verify branch is active before code edits.

## 2. Spec and design confirmation

- [x] 2.1 Confirm spec scenarios in `specs/git-worktree-lifecycle/spec.md` map to test cases.
- [x] 2.2 Confirm design constraints in `design.md` match repository workflow policy.

## 3. Tests first (expected failure)

- [x] 3.1 Add `tests/unit/tools/test_worktree_helper.py` covering: protected branch rejection, unsupported type rejection, deterministic path, and cleanup command behavior.
- [x] 3.2 Run targeted tests before implementation and capture failure evidence in `openspec/changes/workflow-01-git-worktree-management/TDD_EVIDENCE.md`.

## 4. Implement helper and docs

- [x] 4.1 Add `scripts/worktree.sh` with commands: `create`, `list`, `cleanup`, `help`.
- [x] 4.2 Implement branch policy guardrails and deterministic path mapping.
- [x] 4.3 Implement cleanup flow (`git worktree remove`, `git branch -d`, `git worktree prune`) with clear output.
- [x] 4.4 Update `AGENTS.md` worktree section to reference helper usage commands.
- [x] 4.5 Update workflow command docs (`.cursor/commands/wf-create-change-from-plan.md`, `.cursor/commands/wf-validate-change.md`) to enforce dedicated worktree execution.
- [x] 4.6 Add worktree Hatch bootstrap and pre-flight guidance (`hatch env create`, `hatch run smart-test-status`, `hatch run contract-test-status`, `HATCH_DATA_DIR`/`HATCH_CACHE_DIR` fallback) in `AGENTS.md` and workflow command docs.

## 5. Post-implementation verification

- [x] 5.1 Re-run targeted tests and capture passing evidence in `openspec/changes/workflow-01-git-worktree-management/TDD_EVIDENCE.md`.
- [x] 5.2 Run quality gates relevant to this scope: `hatch run format`, `hatch run type-check`, and targeted test command.

## 6. Documentation research and review

- [x] 6.1 Verify whether `README.md` or `docs/` need usage updates for worktree helper workflow.
- [x] 6.2 Apply minimal documentation updates if user-facing workflow guidance changed.

## 7. Version and changelog (required before PR)

- [x] 7.1 Determine if this change requires a version bump (feature/minor by branch policy).
- [x] 7.2 If required, sync version in `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py` and update `CHANGELOG.md`.

## 8. Create Pull Request to dev

- [ ] 8.1 Commit with conventional message and push branch.
- [ ] 8.2 Open PR to `dev` referencing change `workflow-01-git-worktree-management`.
