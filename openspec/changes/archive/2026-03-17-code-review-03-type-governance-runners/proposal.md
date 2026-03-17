# Change: basedpyright and pylint Runners for specfact code review run

## Why

Type safety violations and architecture smells (bare `except:`, `print()` in src, cross-layer calls) are the second most common failure class in the codebase after complexity issues. basedpyright strict mode catches type contract violations that ruff misses; pylint catches architectural patterns that neither ruff nor semgrep cover by default.

These runners complete the static analysis coverage for type safety and governance categories.

## What Changes

- **NEW**: `basedpyright_runner.py` — parses `basedpyright --outputjson`; maps all findings to `category=type_safety`; filters to changed files only
- **NEW**: `pylint_runner.py` — maps pylint message IDs to categories:
  - `W0702`, `W0703` → `category=architecture` (bare except)
  - `T201`, `W1505` → `category=architecture` (print in src)
  - custom cross-layer rules → `category=architecture`
- **CONSTRAINT**: Both runners filter to changed files only
- **NEW**: Unit tests with mocked subprocess calls (TDD-first)

## Capabilities

### New Capabilities

- `basedpyright-runner`: Type-safety finding extraction from basedpyright strict-mode output
- `pylint-runner`: Architecture smell extraction from pylint, mapped to `architecture` category

---

## Impact

- No breaking changes; additive to the `specfact-code-review` module
- Depends on `code-review-01-module-scaffold`
- **Documentation**: Update `docs/modules/code-review.md` with type-safety and architecture runner details

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: not created
- **Issue URL**: n/a
- **Repository**: nold-ai/specfact-cli
- **Modules PR (dev)**: [#66](https://github.com/nold-ai/specfact-cli-modules/pull/66)
- **Release PR (main)**: [#68](https://github.com/nold-ai/specfact-cli-modules/pull/68)
- **Last Synced Status**: implemented in `specfact-cli-modules` and merged to `main`; OpenSpec change ready for manual push/archive
