# Tasks: docs-15-clean-code-bazooka-onboarding

## 1. GitHub readiness and OpenSpec setup

- [x] 1.1 Create OpenSpec change `docs-15-clean-code-bazooka-onboarding`.
- [x] 1.2 Create GitHub issue [#584](https://github.com/nold-ai/specfact-cli/issues/584), link it under Feature [#356](https://github.com/nold-ai/specfact-cli/issues/356), and label it with `documentation`, `enhancement`, `openspec`, `change-proposal`, and `code-review`.
- [x] 1.3 Confirm issue project assignment, open/Todo state, parent linkage, blocked-by relationship, source tracking, and paired modules issue reference.
- [x] 1.4 Add `openspec/CHANGE_ORDER.md` row under active work.
- [x] 1.5 Validate the OpenSpec change with `openspec validate docs-15-clean-code-bazooka-onboarding --strict`.
- [x] 1.6 Create the implementation worktree from `origin/dev` instead of working directly on `dev`.
- [x] 1.7 Run `hatch env create` in the implementation worktree before verification.
- [x] 1.8 Run `hatch run smart-test-status` as a pre-flight scope check.
- [x] 1.9 Run `hatch run contract-test-status` as a pre-flight contract scope check.
- [x] 1.10 Perform the AGENTS.md policy self-check, including worktree, OpenSpec, and quality-gate requirements.

## 2. Spec-first docs tests

- [x] 2.1 Add or update docs assertions for README clean-code cleanup wording.
- [x] 2.2 Add or update docs assertions for quickstart cleanup forecast and AI IDE handoff wording.
- [x] 2.3 Add or update docs assertions for the Code Review module handoff page.
- [x] 2.4 Add or update docs/package metadata assertions for the AI-bloat defense hook and removal of Swiss-knife positioning.
- [x] 2.5 Record failing-before evidence in `TDD_EVIDENCE.md`.

## 3. Documentation updates

- [x] 3.1 Update `README.md` with the cleanup forecast / AI IDE handoff value path.
- [x] 3.2 Update `docs/getting-started/quickstart.md` with the JSON-first cleanup loop.
- [x] 3.3 Update `docs/modules/code-review.md` to reference cleanup forecasts, AI-bloat index, remediation packets, and modules docs as canonical command/schema reference.
- [x] 3.4 Update `docs/index.md`, `docs/README.md`, `docs/getting-started/README.md`, and `docs/_config.yml` so docs entry points share the AI-bloat defense first-contact story.
- [x] 3.5 Update package metadata in `pyproject.toml`, `setup.py`, and `src/specfact_cli/__init__.py`.
- [x] 3.6 Keep all cross-site links aligned with the modules docs permalink contract.
- [x] 3.7 Apply and verify GitHub repository description/topics metadata.

## 4. Verification

- [x] 4.1 Run targeted docs tests and record passing evidence.
- [x] 4.2 Run required docs quality gates for the touched scope.
- [x] 4.3 Run SpecFact code review for changed docs/test scope if the repository gate applies.
- [x] 4.4 Update `TDD_EVIDENCE.md` with passing evidence and before/after docs summary.
- [x] 4.5 Record post-merge cleanup requirements: remove the implementation worktree after the merged branch is no longer needed and archive this OpenSpec change with `openspec archive docs-15-clean-code-bazooka-onboarding`.
- [x] 4.6 Verify the release branch no longer treats this shipped docs contract as active pending work.
