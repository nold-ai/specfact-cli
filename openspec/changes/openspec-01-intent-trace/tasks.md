# Tasks: OpenSpec Intent Trace — Bridge Adapter Integration

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests MUST precede production code for any behavior-changing task.

Order:
1. Spec deltas (already in `specs/`)
2. Tests derived from spec scenarios — run and expect failure
3. Production code — implement until tests pass

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/openspec-01-intent-trace -b feature/openspec-01-intent-trace origin/dev`
  - [ ] 1.1.3 `cd ../specfact-cli-worktrees/feature/openspec-01-intent-trace`
  - [ ] 1.1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.5 `git branch --show-current` (verify `feature/openspec-01-intent-trace`)

## 2. Define Intent Trace JSON Schema

- [ ] 2.1 Create `openspec/schemas/intent-trace.schema.json`:
  - [ ] 2.1.1 Root object with `schema_version` (required string), `intent_trace` object
  - [ ] 2.1.2 `business_outcomes` array: each item requires `id` (string), `description` (string), `persona` (string)
  - [ ] 2.1.3 `business_rules` array: each item requires `id`, `outcome_ref`, `given`, `when`, `then`
  - [ ] 2.1.4 `architectural_constraints` array: each item requires `id`, `outcome_ref`, `constraint`
  - [ ] 2.1.5 `requirement_refs` optional array of strings
  - [ ] 2.1.6 `additionalProperties: false` on all objects for strict validation
- [ ] 2.2 Write schema unit tests in `tests/unit/specfact_cli/test_intent_trace_schema.py`:
  - [ ] 2.2.1 Test valid complete intent trace block passes validation
  - [ ] 2.2.2 Test missing required `id` field on BusinessOutcome fails
  - [ ] 2.2.3 Test missing intent trace section (None) passes (optional)
  - [ ] 2.2.4 Test unknown `schema_version` raises descriptive error
- [ ] 2.3 Run schema tests — expect failure: `hatch test -- tests/unit/specfact_cli/test_intent_trace_schema.py -v`
- [ ] 2.4 Record failing test evidence in `TDD_EVIDENCE.md`

## 3. Write bridge adapter tests (TDD — expect failure)

- [ ] 3.1 Review existing OpenSpec bridge adapter tests in `tests/`
- [ ] 3.2 Add `tests/unit/specfact_cli/test_openspec_bridge_intent.py`:
  - [ ] 3.2.1 Test bridge import of proposal with `## Intent Trace` creates `.req.yaml` files (with `--import-intent`)
  - [ ] 3.2.2 Test bridge import without `## Intent Trace` section is unchanged (backwards compatible)
  - [ ] 3.2.3 Test `--import-intent` without `--overwrite` skips existing artifacts
  - [ ] 3.2.4 Test `--import-intent --overwrite` updates existing artifacts
  - [ ] 3.2.5 Test advisory warning on unresolved `requirement_refs`
  - [ ] 3.2.6 Test `requirement_refs` parsed into imported task metadata
- [ ] 3.3 Add `tests/integration/test_openspec_intent_trace_e2e.py`:
  - [ ] 3.3.1 End-to-end test: proposal with intent trace → bridge import → `.req.yaml` exists and validates
- [ ] 3.4 Run bridge tests — expect failure: `hatch test -- tests/unit/specfact_cli/test_openspec_bridge_intent.py -v`
- [ ] 3.5 Record failing test evidence in `TDD_EVIDENCE.md`

## 4. Implement Intent Trace schema validator

- [ ] 4.1 Add `src/specfact_cli/validators/intent_trace_validator.py`:
  - [ ] 4.1.1 `validate_intent_trace(yaml_block: dict | None) -> ValidationResult` with `@require` and `@beartype`
  - [ ] 4.1.2 Load `openspec/schemas/intent-trace.schema.json` (bundled resource)
  - [ ] 4.1.3 Use `jsonschema.validate()` for schema check
  - [ ] 4.1.4 Return structured errors with field path, message, and suggestion
- [ ] 4.2 Register schema file in `pyproject.toml` `[tool.hatch.build.targets.wheel]` force-include

## 5. Extend OpenSpec bridge adapter with intent import

> **Implementation constraint (from CHANGE_VALIDATION.md)**: `_parse_proposal_content()` in `openspec_parser.py` has return type `dict[str, str]`. Intent trace extraction MUST be done in `parse_change_proposal()` (returns `dict[str, Any]`) — NOT in `_parse_proposal_content()` — to avoid a `@beartype` type violation.

- [ ] 5.1 Locate OpenSpec bridge adapter in `src/specfact_cli/adapters/`
- [ ] 5.2 Add `## Intent Trace` section parser:
  - [ ] 5.2.1 Extract YAML fenced block under `## Intent Trace` heading from proposal Markdown
  - [ ] 5.2.2 Parse YAML with `yaml.safe_load()`
  - [ ] 5.2.3 Run `validate_intent_trace()` on the parsed block
- [ ] 5.3 Add `--import-intent` flag to `specfact sync bridge --adapter openspec` command:
  - [ ] 5.3.1 `@require`: intent import requires requirements-01 module is installed (advisory check)
  - [ ] 5.3.2 Write `.specfact/requirements/{id}.req.yaml` for each `BusinessOutcome`
  - [ ] 5.3.3 Embed `BusinessRule` entries in parent `.req.yaml` files
  - [ ] 5.3.4 Respect `--overwrite` flag; skip existing files otherwise
- [ ] 5.4 Add `requirement_refs` parsing from `tasks.md` task entries
  - [ ] 5.4.1 Parse optional `requirement_refs:` YAML field on task lines
  - [ ] 5.4.2 Include in imported task metadata in project bundle
  - [ ] 5.4.3 Advisory warning for unresolved IDs
- [ ] 5.5 Extend `openspec validate --strict` hook to call `validate_intent_trace()` when section present
- [ ] 5.6 Add `@require`, `@ensure`, `@beartype` decorators to all new public API functions

## 6. Passing tests and quality gates

- [ ] 6.1 Run all new tests — expect passing: `hatch test -- tests/unit/specfact_cli/test_intent_trace*.py tests/unit/specfact_cli/test_openspec_bridge*.py tests/integration/test_openspec_intent_trace*.py -v`
- [ ] 6.2 Record passing test evidence in `TDD_EVIDENCE.md`
- [ ] 6.3 `hatch run format`
- [ ] 6.4 `hatch run type-check`
- [ ] 6.5 `hatch run lint`
- [ ] 6.6 `hatch run yaml-lint`
- [ ] 6.7 `hatch run contract-test`
- [ ] 6.8 `hatch run smart-test`

## 7. Documentation

- [ ] 7.1 Update `docs/adapters/openspec.md` (or equivalent):
  - [ ] 7.1.1 Document `## Intent Trace` section format with full YAML example
  - [ ] 7.1.2 Document `--import-intent` and `--overwrite` flags
  - [ ] 7.1.3 Document `requirement_refs` field on tasks
- [ ] 7.2 Update `docs/guides/openspec-journey.md` — add Intent Trace section
- [ ] 7.3 Ensure front-matter on all updated/new doc pages is valid (layout, title, permalink, description)
- [ ] 7.4 Update `docs/_layouts/default.html` sidebar navigation if new pages are added

## 8. Version and changelog

- [ ] 8.1 Bump minor version in `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py`
- [ ] 8.2 Add CHANGELOG.md entry under new `[X.Y.Z] - 2026-XX-XX` with Added/Changed sections

## 9. GitHub issue creation

- [ ] 9.1 Create GitHub issue:
  ```bash
  gh issue create \
    --repo nold-ai/specfact-cli \
    --title "[Change] OpenSpec Intent Trace — Bridge Adapter Integration" \
    --body-file /tmp/github-issue-openspec-01.md \
    --label "enhancement" \
    --label "change-proposal"
  ```
- [ ] 9.2 Link issue to project: `gh project item-add 1 --owner nold-ai --url <ISSUE_URL>`
- [ ] 9.3 Update `proposal.md` Source Tracking section with issue number and URL
- [ ] 9.4 Link branch to issue: `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name feature/openspec-01-intent-trace`

## 10. Pull request

- [ ] 10.1 `git add` all changed files; commit with `feat: add OpenSpec Intent Trace section and bridge adapter import`
- [ ] 10.2 `git push -u origin feature/openspec-01-intent-trace`
- [ ] 10.3 Create PR:
  ```bash
  gh pr create \
    --repo nold-ai/specfact-cli \
    --base dev \
    --head feature/openspec-01-intent-trace \
    --title "feat: OpenSpec Intent Trace bridge adapter integration" \
    --body-file /tmp/pr-body-openspec-01.md
  ```
- [ ] 10.4 Link PR to project: `gh project item-add 1 --owner nold-ai --url <PR_URL>`
- [ ] 10.5 Set project status to "In Progress"

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd .../specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/openspec-01-intent-trace`
- [ ] `git branch -d feature/openspec-01-intent-trace`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/openspec-01-intent-trace`
