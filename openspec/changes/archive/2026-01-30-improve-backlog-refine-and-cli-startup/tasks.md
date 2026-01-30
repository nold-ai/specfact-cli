# Tasks: Improve Backlog Refine and CLI Startup

## TDD / SDD order (enforced)

Per `openspec/config.yaml`: **tests before code**. For any task that adds or changes behavior:

1. **Spec deltas** define behavior (Given/When/Then) — already in `changes/.../specs/backlog-refinement/spec.md`.
2. **Tests second** — write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet).
3. **Code last** — implement until tests pass and behavior satisfies the spec.

Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

---

## 1. Create git branch

- [x] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
- [x] 1.1.2 Create branch: `git checkout -b feature/improve-backlog-refine-and-cli-startup`
- [x] 1.1.3 Verify branch: `git branch --show-current`

## 2. Startup: first output before checks

- [x] 2.1 Verify in `cli.py` that version line (or welcome) is printed before `print_startup_checks()`; add comment if order is correct
- [x] 2.2 Optional: add timeout (e.g. 3s) to `check_pypi_version()` in `startup_checks.py`
- [x] 2.3 Document `--skip-checks` in AGENTS.md or docs for faster startup in CI/slow environments
- [x] 2.4 Run `hatch run format` and `hatch run type-check`; run contract and unit tests for touched files

## 3. Backlog refine: ignore-refined and --id (TDD: tests first, then code)

**TDD for this section:** Write tests from spec scenarios below first; run tests and expect failure; then implement until tests pass.

- [x] 3.1 **Tests first:** From `changes/.../specs/backlog-refinement/spec.md` scenarios (Limit applies when ignore-refined; No-ignore-refined preserves behavior; Refine single item by ID; ID not found), add unit/integration tests in `tests/unit/commands/test_backlog_commands.py` (e.g. for `_item_needs_refinement` and refine filtering). Run tests: `hatch run smart-test-unit` or target file — **expect failure** (no implementation yet).
- [x] 3.2 Add `ignore_refined: bool = typer.Option(True, "--ignore-refined/--no-ignore-refined", ...)` and `issue_id: str | None = typer.Option(None, "--id", ...)` to refine command in `backlog_commands.py`
- [x] 3.3 Extract "already refined" logic into helper (e.g. `_item_needs_refinement(...)`) returning True if item needs refinement
- [x] 3.4 After fetch: if `ignore_refined`, filter items to those needing refinement; if `limit` set, slice to `items[:limit]`; when both set, consider fetching with larger limit (e.g. limit * 5) or no limit then filter+slice
- [x] 3.5 After fetch (and ignore-refined filter): if `issue_id` set, filter to `[i for i in items if str(i.id) == str(issue_id)]`; if empty, print error and exit
- [x] 3.6 Run tests again; **expect pass**. Then run `hatch run format`, `hatch run type-check`, `hatch run contract-test`, `hatch run smart-test`

## 4. Prompt: interactive refinement section

- [x] 4.1 Edit `resources/prompts/specfact.backlog-refine.md`: add section "Interactive refinement (Copilot mode)" with loop: present story → list ambiguities → ask clarification → re-refine until user approves → then mark done and next story; add formatting guidance for readability
- [x] 4.2 Ensure prompt states backlog item is updated only after user approval for that story

## 5. Docs and release

Specs are updated only when the change is **archived** (not during apply). Do not add tasks to merge spec delta into main spec during implementation.

- [x] 5.1 Update backlog refine docs (if any) for `--ignore-refined`, `--no-ignore-refined`, `--id`
- [x] 5.2 Update patch version and sync across files (`pyproject.toml`, `setup.py`, `__init__.py`)
- [x] 5.3 Update `CHANGELOG.md` with the new version number and the changes made in this change

## 6. Validation and PR

- [x] 6.1 Run `openspec validate improve-backlog-refine-and-cli-startup --strict`
- [x] 6.2 Run `hatch run format`, `hatch run type-check`, `hatch run contract-test`, `hatch run smart-test`
- [x] 6.3 Create Pull Request from `feature/improve-backlog-refine-and-cli-startup` to `dev` with conventional message and description referencing this change (use `.github/pull_request_template.md` for the PR body)
