# Design: workflow-01-git-worktree-management

## Summary

Introduce a lightweight shell helper that wraps `git worktree` operations with repository guardrails and predictable paths.

## Goals

- Standardize worktree folder naming by branch type and slug.
- Prevent worktree usage for protected branches (`dev`, `main`).
- Keep the helper local-only and offline-first.

## Non-goals

- No remote branch or PR automation.
- No replacement of existing git commands outside worktree lifecycle actions.

## Flow

1. `create <branch>` validates allowed branch type and blocks protected branches.
2. `create` derives path `../specfact-cli-worktrees/<type>/<slug>` and runs `git fetch origin` then `git worktree add ...`.
3. `list` delegates to `git worktree list`.
4. `cleanup <branch>` validates path/branch mapping and removes worktree, local branch (if merged), and prunes stale records.

## Risks and mitigations

- **Risk**: deleting wrong path during cleanup.
  - **Mitigation**: compute canonical path from branch and require exact match.
- **Risk**: branch naming inconsistencies.
  - **Mitigation**: strict `<type>/<slug>` validation and actionable errors.
