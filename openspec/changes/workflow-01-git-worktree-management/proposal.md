# Change: Standardize Git Worktree Lifecycle for Parallel Branch Development

## Why


The repository needs a consistent, low-risk way to run multiple feature streams in parallel using `git worktree`. Without a standard lifecycle, teams can accidentally use protected branches (`dev`, `main`) in worktrees, collide on branch-to-folder mappings, or leave stale worktrees that cause confusion and merge friction.

## What Changes


- **NEW**: Add a repository helper script (`scripts/worktree.sh`) that standardizes worktree operations: create, list, and cleanup.
- **NEW**: Enforce branch-type policy in helper workflow: only `feature/*`, `bugfix/*`, `hotfix/*`, and `chore/*` are allowed for worktree creation; `dev` and `main` are blocked.
- **NEW**: Document deterministic path layout and cleanup rules in `AGENTS.md` and script usage output.
- **NEW**: Add unit tests that validate helper behavior and guardrails (including forbidden branch handling).

## Capabilities
- **git-worktree-lifecycle**: Developers can create, inspect, and remove branch-specific worktrees with a standardized command flow that reduces branch/path conflicts and protects `dev`/`main` usage.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #267
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/267>
- **Last Synced Status**: proposed
- **Sanitized**: false
