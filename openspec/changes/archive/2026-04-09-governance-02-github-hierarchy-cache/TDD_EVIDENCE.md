# TDD Evidence

## Failing-before implementation

- Timestamp: `2026-04-09T21:03:37+02:00`
- Command: `python3 -m pytest tests/unit/scripts/test_sync_github_hierarchy_cache.py -q`
- Result: FAIL
- Summary: All three tests failed with `FileNotFoundError` because `scripts/sync_github_hierarchy_cache.py` did not exist yet.

## Failing-before path relocation refinement

- Timestamp: `2026-04-09T21:17:04+02:00`
- Command: `python3 -m pytest tests/unit/scripts/test_sync_github_hierarchy_cache.py -q`
- Result: FAIL
- Summary: The new default-path test failed because the script still targeted `openspec/GITHUB_HIERARCHY_CACHE.md` instead of ignored `.specfact/backlog/` storage.

## Passing-after implementation

- Timestamp: `2026-04-09T21:17:35+02:00`
- Command: `python3 -m pytest tests/unit/scripts/test_sync_github_hierarchy_cache.py -q`
- Result: PASS
- Summary: All five script tests passed after moving the cache into ignored `.specfact/backlog/` storage and keeping the no-op fingerprint path intact.

## Additional verification

- `python3 -m py_compile scripts/sync_github_hierarchy_cache.py` → PASS
- `python3 scripts/sync_github_hierarchy_cache.py --force` → generated `.specfact/backlog/github_hierarchy_cache.md`
- Second `python3 scripts/sync_github_hierarchy_cache.py` run → `GitHub hierarchy cache unchanged (46 issues).`

## Final scoped quality gates

- Timestamp: `2026-04-09T22:04:18+02:00`
- Ruff: `PATH=/home/dom/git/nold-ai/specfact-cli/.venv/bin:$PATH PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/governance-02-github-hierarchy-cache/src /home/dom/git/nold-ai/specfact-cli/.venv/bin/ruff check scripts/sync_github_hierarchy_cache.py tests/unit/scripts/test_sync_github_hierarchy_cache.py` → PASS
- basedpyright: `PATH=/home/dom/git/nold-ai/specfact-cli/.venv/bin:$PATH PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/governance-02-github-hierarchy-cache/src /home/dom/git/nold-ai/specfact-cli/.venv/bin/basedpyright scripts/sync_github_hierarchy_cache.py tests/unit/scripts/test_sync_github_hierarchy_cache.py` → PASS (`0 errors, 0 warnings`)
- pytest: `hatch test -- tests/unit/scripts/test_sync_github_hierarchy_cache.py -q` → PASS (`15 passed`, after parity with modules-side script/tests)
- SpecFact code review: `hatch run specfact code review run --json --out .specfact/code-review.json scripts/sync_github_hierarchy_cache.py tests/unit/scripts/test_sync_github_hierarchy_cache.py` → PASS (`overall_verdict` PASS, `ci_exit_code` 0; low-severity DRY hints on icontract preconditions documented in `proposal.md`)
