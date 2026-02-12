# Tasks: Backlog Refine Writeback Field Splitting for ADO/GitHub

## 1. Git Workflow

- [x] 1.1 Create git branch `bugfix/backlog-refine-writeback-field-splitting` from `dev`

## 2. Spec Deltas

- [x] 2.1 Add/modify `backlog-refinement` spec scenarios for provider-aware writeback field splitting
- [x] 2.2 Run `openspec validate backlog-core-03-refine-writeback-field-splitting --strict`

## 3. Tests First (TDD)

- [x] 3.1 Add tests for label-style refined output parsing into canonical fields
- [x] 3.2 Add ADO writeback regression test: structured output does not get written verbatim to description
- [x] 3.3 Add GitHub writeback regression test for label-style output normalization
- [x] 3.4 Run targeted tests and capture failing evidence in `openspec/changes/backlog-core-03-refine-writeback-field-splitting/TDD_EVIDENCE.md`

## 4. Implementation

- [x] 4.1 Implement refinement output parser integration in `backlog refine --write` flow
- [x] 4.2 Ensure parsed canonical fields are applied before adapter update calls
- [x] 4.3 Add adapter-safe fallback handling for structured label output where needed
- [x] 4.4 Run targeted tests and capture passing evidence in `openspec/changes/backlog-core-03-refine-writeback-field-splitting/TDD_EVIDENCE.md`
- [x] 4.5 Refactor `refine` command into smaller helper methods with clear responsibilities
- [x] 4.6 Keep behavior parity for export/import/write/preview flows after refactor
- [x] 4.7 Preserve heading-style `## Notes` / `## Dependencies` sections in parsed `body_markdown` for writeback
- [x] 4.8 Match heading-style `## Notes` / `## Dependencies` sections case-insensitively during parser writeback normalization
- [x] 4.9 Prevent label-only refinement output (without `Description:`) from leaking raw prompt labels into fallback description/body fields

## 5. Quality Gates

- [x] 5.1 `hatch run format`
- [x] 5.2 `hatch run type-check`
- [x] 5.3 `hatch run contract-test`
- [x] 5.4 `hatch run smart-test`

## 6. Documentation and Release Hygiene

- [x] 6.1 Review and update docs for backlog refine writeback behavior (if needed)
- [x] 6.2 Bump patch version and sync: `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`
- [x] 6.3 Update `CHANGELOG.md` with bugfix entry

## 7. Pull Request

- [ ] 7.1 Push branch and open PR to `dev`
