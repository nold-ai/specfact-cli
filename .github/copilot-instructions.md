# GitHub Copilot Instructions — specfact-cli

Use [AGENTS.md](../AGENTS.md) as the mandatory bootstrap surface and [docs/agent-rules/INDEX.md](../docs/agent-rules/INDEX.md) as the canonical governance dispatcher.

## Minimal reminders

- This repository enforces the clean-code review gate through `hatch run specfact code review run --json --out .specfact/code-review.json`.
- Public APIs require `@icontract` and `@beartype`.
- Work belongs on `feature/*`, `bugfix/*`, `hotfix/*`, or `chore/*` branches, normally in a worktree.
- The full governance rules live in `docs/agent-rules/`; do not treat this file as a complete standalone handbook.
