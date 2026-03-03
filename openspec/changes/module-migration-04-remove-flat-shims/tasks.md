# Tasks: module-migration-04-remove-flat-shims

TDD/SDD order enforced. Version series: **0.40.x**.

## 1. Branch and prep

- [ ] 1.1 Create feature branch from `dev`: `feature/module-migration-04-remove-flat-shims`
- [ ] 1.2 Ensure module-migration-01 is merged to dev (category groups and shims exist)

## 2. Spec and tests first

- [ ] 2.1 Add spec delta under `specs/category-command-groups/`: when `category_grouping_enabled` is true, root CLI SHALL list only core commands (init, auth, module, upgrade) and the five category groups (code, backlog, project, spec, govern). No flat shim commands.
- [ ] 2.2 Update or add tests that assert root help contains only core + groups when grouping enabled; remove or rewrite tests that assert flat shim deprecation or `specfact validate --help` success for shim.
- [ ] 2.3 Run tests and capture **failing** result (shims still present) in `TDD_EVIDENCE.md`.
- [ ] 2.4 Scope note: restrict to shim-removal-focused tests in `specfact-cli`; do **not** absorb broad suite migration/cleanup failures here.

## 3. Implementation

- [ ] 3.1 In `module_packages.py`: remove the loop that registers shims from `FLAT_TO_GROUP`; keep only category group registration. Rename `_register_category_groups_and_shims` → `_register_category_groups` (or equivalent).
- [ ] 3.2 Remove `FLAT_TO_GROUP` and `_make_shim_loader()` (and any code only used by shims).
- [ ] 3.4 Run tests; capture **passing** result in `TDD_EVIDENCE.md`.

## 4. Quality gates

- [ ] 4.1 `hatch run format` and fix
- [ ] 4.2 `hatch run type-check` and fix
- [ ] 4.3 `hatch run lint` and fix
- [ ] 4.4 `hatch run contract-test` and fix
- [ ] 4.5 `hatch run smart-test` for this change scope; if `smart-test-full` exposes unrelated migration debt, record and defer to follow-up change(s) per migration-03 phase 20.

## 5. Documentation and release

- [ ] 5.1 Update `docs/reference/commands.md`: command topology is category-only (no flat commands).
- [ ] 5.2 Update `docs/guides/getting-started.md` and `README.md`: command list shows only core + categories; add migration note for users of flat commands.
- [ ] 5.3 Bump version to **0.40.0** in `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py`.
- [ ] 5.4 Add CHANGELOG.md entry for 0.40.0: **BREAKING** — removed flat command shims; use `specfact <group> <sub>` (e.g. `specfact code validate`).

## 6. PR

- [ ] 6.1 Create GitHub issue for change (title: `[Change] Remove flat shims — category-only CLI (0.40.x)`); link in proposal Source Tracking.
- [ ] 6.2 Open PR to `dev`; reference this change and breaking-change migration path.
