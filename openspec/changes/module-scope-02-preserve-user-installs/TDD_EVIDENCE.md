# TDD Evidence

## Failing Before

- `hatch run pytest tests/unit/registry/test_module_discovery.py::test_project_shadow_warning_is_actionable_and_emitted_once tests/unit/modules/module_registry/test_commands.py::test_doctor_reports_effective_and_shadowed_duplicate_modules -q`
  - Result: FAIL before production edits (`2 failed`).
  - Discovery still recommended `specfact module uninstall backlog-core --scope user`, and doctor still printed `Recovery: specfact module uninstall nold-ai/specfact-codebase --scope user` instead of preservation/no-action guidance.
- Retained CI red proof: Requirements Evidence run `33274750805` at signed source commit `b5ad2ea0d5e0ee062906e0c7b2f156330ea1a39f` executed the same two selectors and produced a bound `observed_maturity: red` artifact with no reconciliation findings. The workflow's overall failure is expected at this checkpoint and requires a later final implementation commit.

## Passing After

- `hatch run pytest tests/unit/registry/test_module_discovery.py::test_project_shadow_warning_is_actionable_and_emitted_once tests/unit/modules/module_registry/test_commands.py::test_doctor_reports_effective_and_shadowed_duplicate_modules -q`
  - Result: PASS (`2 passed`).
- `hatch run pytest tests/unit/registry/test_module_discovery.py tests/unit/modules/module_registry/test_commands.py -q`
  - Initial implementation result: PASS (`67 passed`).
  - Discovery precedence, duplicate reporting, doctor output, and explicit uninstall command coverage remain green.

## Review Follow-up

- Review-driven tests were added before the follow-up production edit for actual effective-source guidance, qualified availability, and user-only discovery outside the shadowing project.
- Initial focused run: FAIL (`3 failed, 1 passed`). The current doctor always named project scope and both diagnostics made an unconditional availability claim. The user-only preservation scenario already passed, so it remains supplementary regression coverage rather than a retained red-proof selector.
- Passing focused run after the production edit: PASS (`4 passed`).
- Related discovery/doctor files after the review fixes: PASS (`69 passed`).

## Quality Gates

- `hatch run format`: PASS (942 files unchanged).
- `hatch run type-check`: PASS (0 errors; 1,657 existing warnings).
- `hatch run lint`: PASS.
- `hatch run yaml-lint`: exit code 0; it reports only pre-existing line-length/blank-line findings in untouched Requirements R07/R08 evidence.
- `hatch run contract-test` and `hatch run contract-test-contracts`: PASS using cached results after the full smart-test had refreshed hashes; both report no further modified contract inputs. The focused contract-sensitive discovery/doctor files pass, and the independent full suite exercised them.
- Schema-v2 Requirements evidence maps all changed scenarios to exact pytest selectors; the staged repository hook is the delivery gate.
- Product-owner review evidence is bound to mapping digest `sha256:fc0ff2c618b508f00943c66a987a14edf5175c730e9b26ac146785aa2045fe68` and core issue #699 for the required test-authored maturity gate. The executable plan contains the two original behavior regressions plus the failing effective-source review scenario; the already-passing user-only preservation scenario remains supplementary regression coverage.
- The built-in module-registry payload change advances the module-registry package to `0.1.34` with refreshed integrity metadata, advances all four canonical core version sources to `0.55.3`, and adds the matching changelog entry, as required by the release-integrity gates.
- `uv lock` refreshes the frozen project record from core `0.55.2` to `0.55.3`; `uv sync --locked --all-extras` then passes locally, resolving the first PR CI setup failures caused by the stale lock.
- Core CI's immutable module fixture is authoritative for generated command inventory. A local run against the newer paired modules checkout exposed three later Code Review PR-range options, but those options are intentionally absent from this core patch's generated artifacts so the frozen-fixture docs check remains reproducible.
- `hatch run bandit-scan`: PASS (no medium/high findings).
- Semgrep and its baseline gate: PASS (0 current findings, 0 baseline findings).
- Earlier local `hatch run smart-test` / `hatch run test` runs recorded `3029 passed, 12 skipped, 17 failed` before restoring the immutable fixture and refreshing the changed module signature.
- Final signed-head PR Orchestrator run `33275273173` executed `smart-test-full`: PASS (`3050 passed, 8 skipped`) on Python 3.12. Its Python 3.11 compatibility job also passed.
- The exact immutable-fixture full-enforcement Code Review used by CI passes locally with score 115 and zero findings after resolving all clean-code and type-safety warnings in the touched legacy files. The newer protected schema 1.6 capsule still reports assurance `UNKNOWN` on this macOS host because its controller supports Linux; Linux PR CI remains authoritative for that capsule.
- `git diff --check`: PASS.
