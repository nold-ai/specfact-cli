# GitHub Copilot Instructions — specfact-cli

## Clean-Code Charter

This repository enforces the **7-principle clean-code charter** defined in:
- `skills/specfact-code-review/SKILL.md` (`nold-ai/specfact-cli-modules`)
- Policy-pack: `specfact/clean-code-principles`

Review categories checked on every PR: **naming · kiss · yagni · dry · solid**

Phase A KISS thresholds: LOC > 80 warning / > 120 error per function.
Nesting-depth and parameter-count checks are active. Phase B (>40/80) is deferred.

Run `hatch run specfact code review run --json --out .specfact/code-review.json` before submitting.

## Key conventions

- Python 3.11+, Typer CLI, Pydantic models, `@icontract` + `@beartype` on all public APIs
- No `print()` in `src/` — use `get_bridge_logger()`
- Branch protection: work on `feature/*`, `bugfix/*`, `hotfix/*` branches; PRs to `dev`
- Pre-commit checklist: `hatch run format` → `type-check` → `lint` → `yaml-lint` → `contract-test` → `smart-test`

See `AGENTS.md` and `.cursor/rules/` for the full contributor guide.
