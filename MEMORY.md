# MEMORY.md — Non-Negotiable Guardrails

This file survives context compression. Re-read on every interaction.

## 1. OpenSpec Gate (HARD BLOCK)

**Do NOT edit any codebase file** unless an active OpenSpec change in `openspec/changes/` explicitly covers the requested scope. If none exists, stop and ask:
- a) Create new change (`/opsx:new`)
- b) Continue an existing change
- c) Add a delta to an existing change

Skip ONLY when the user says `"skip openspec"` or `"implement without openspec change"`.

Read `openspec/CHANGE_ORDER.md` first — it is the single source of truth for sequencing, blockers, and archive status. Update it in the same commit as any change lifecycle event.

## 2. Branch Protection

`dev` and `main` are protected. Never commit directly. Always use:
- `feature/` → minor version bump
- `bugfix/` → patch version bump
- `hotfix/` → patch version bump

## 3. Pre-Commit Checklist (ordered, all must pass)

1. `hatch run format`
2. `hatch run type-check`
3. `hatch run lint`
4. `hatch run yaml-lint`
5. `hatch run contract-test`
6. `hatch run smart-test` (or `smart-test-full` for larger changes)

## 4. Contract-First Development

- All public APIs: `@icontract` (`@require`, `@ensure`, `@invariant`) + `@beartype`
- Contracts are the primary validation; unit tests are secondary
- Never write redundant tests that just re-check what contracts enforce

## 5. No print() — Ever

Use `from specfact_cli.common import get_bridge_logger`. Debug logs go to `~/.specfact/logs/specfact-debug.log`.

## 6. Version Sync

Bump in lockstep: `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`. Update `CHANGELOG.md` in the same commit as the version bump.

## 7. Commits & Style

- Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- Python 3.11+, line length 120, Google-style docstrings
- Pydantic `BaseModel` for all data structures
- `rich~=13.5.2` is pinned — do not upgrade without checking semgrep compat
