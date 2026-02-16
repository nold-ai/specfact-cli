# Tasks: CI — Attach Test and Repro Log Artifacts to PR Orchestrator Runs

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior. Order: (1) Spec deltas define behavior (Given/When/Then). (2) **Tests second** — write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet). (3) **Code last** — implement until tests pass and behavior satisfies the spec. Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

For this change, the main deliverable is workflow YAML and docs; "tests" are satisfied by workflow lint (`hatch run lint-workflows`) and optional manual/e2e verification that artifacts appear. No new application code; TDD for this change is: validate workflow syntax and lint first, then implement workflow and upload steps, then verify artifacts in a run.

---

## 1. Create git branch

- [ ] 1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
- [ ] 1.2 Create branch: `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name feature/ci-01-pr-orchestrator-log-artifacts --checkout` if issue exists, else `git checkout -b feature/ci-01-pr-orchestrator-log-artifacts`
- [ ] 1.3 Verify branch: `git branch --show-current`

## 2. Verify spec deltas (SDD: specs first)

- [ ] 2.1 Confirm `specs/ci-log-artifacts/spec.md` exists and is complete (Given/When/Then for test logs upload, repro logs/reports upload, documentation).
- [ ] 2.2 Map scenarios to implementation: Tests job smart-test-full + artifact upload; contract-first-ci repro log capture + artifact upload; doc section on CI artifacts.

## 3. Tests job: Run smart-test-full and upload test logs (TDD: validate then implement)

- [ ] 3.1 **Validation**: Run `hatch run lint-workflows` (or equivalent) to ensure workflow syntax is valid; note current pr-orchestrator.yml structure.
- [ ] 3.2 In `.github/workflows/pr-orchestrator.yml`, add or replace the test execution step in the **Tests** job so that it runs `hatch run smart-test-full` (with env such as `CONTRACT_FIRST_TESTING`, `TEST_MODE`, `HATCH_TEST_ENV`, `SMART_TEST_TIMEOUT_SECONDS`, `PYTEST_ADDOPTS` as needed). Ensure the script writes logs under `logs/tests/` (existing behavior of smart_test_coverage.py when level is full).
- [ ] 3.3 Add a step to upload test log artifacts: use `actions/upload-artifact@v4` with name `test-logs` (or `test-logs-py312`), path `logs/tests/`, and `if-no-files-found: ignore` or `warn` so the job does not fail if no logs (e.g. when step was skipped). Use `if: always()` or `if: success() || failure()` so artifacts are uploaded on both success and failure when the step ran.
- [ ] 3.4 Keep or adjust the existing "Upload coverage artifacts" step so quality-gates still receives coverage (e.g. continue uploading `logs/tests/coverage/coverage.xml` as `coverage-reports` if that path is still produced by smart-test-full or a separate coverage step).
- [ ] 3.5 Re-run `hatch run lint-workflows` and fix any issues.

## 4. Contract-first-ci job: Capture repro output and upload repro logs/reports

- [ ] 4.1 In the **contract-first-ci** job, ensure `logs/repro/` exists before running repro (e.g. `mkdir -p logs/repro`).
- [ ] 4.2 Change the repro run step so that stdout and stderr are captured to a timestamped file under `logs/repro/` (e.g. `repro_$(date -u +%Y%m%d_%H%M%S).log`) using `tee` or redirection, while still displaying output in the step log. Run `hatch run specfact repro --verbose --crosshair-required --budget 120`; keep `|| echo "SpecFact repro found issues"` or similar so the job can continue to upload artifacts even when repro fails.
- [ ] 4.3 Add an upload-artifact step for repro logs: upload `logs/repro/` with name `repro-logs`, `if-no-files-found: ignore`, and `if: always()` so it runs after the repro step whether repro passed or failed.
- [ ] 4.4 Add an upload-artifact step for repro reports: upload `.specfact/reports/enforcement/` with name `repro-reports`, `if-no-files-found: ignore`, and `if: always()`.
- [ ] 4.5 Run `hatch run lint-workflows` again.

## 5. Documentation: CI log artifacts

- [ ] 5.1 Identify the best doc location (e.g. `docs/guides/troubleshooting.md`, `docs/contributing/`, or a new `docs/reference/ci-artifacts.md`). Add or update a subsection that explains: (1) test logs and repro logs/reports are uploaded as workflow artifacts; (2) where to find them (Actions run → Artifacts); (3) artifact names (`test-logs`, `repro-logs`, `repro-reports`) and what they contain; (4) how to use them to debug failed runs without re-running locally.
- [ ] 5.2 If adding a new page, set front-matter (layout, title, permalink, description) and update `docs/_layouts/default.html` sidebar if needed.

## 6. Quality gates

- [ ] 6.1 Run `hatch run format`, `hatch run type-check`.
- [ ] 6.2 Run `hatch run lint` and `hatch run yaml-lint`; run `hatch run lint-workflows` for workflow files.
- [ ] 6.3 Run `hatch run contract-test` and `hatch run smart-test` (or `smart-test-unit` / `smart-test-folder` for minimal validation). No new application code; ensure no regressions.

## 7. Documentation research and review (per openspec/config.yaml)

- [ ] 7.1 Confirm affected docs are listed in task 5; check for broken links and correct front-matter.

## 8. Version and changelog (required before PR)

- [ ] 8.1 Bump patch version (this is a fix/enhancement to CI): update `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py`.
- [ ] 8.2 Add CHANGELOG.md entry under new version: Added — CI log artifacts (test logs and repro logs/reports) attached to PR orchestrator runs for easier debugging.

## 9. Create Pull Request to dev

- [ ] 9.1 Commit and push: `git add .`, `git commit -m "feat(ci): attach test and repro log artifacts to PR orchestrator runs"`, `git push origin feature/ci-01-pr-orchestrator-log-artifacts`.
- [ ] 9.2 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/ci-01-pr-orchestrator-log-artifacts --title "feat(ci): attach test and repro log artifacts to PR orchestrator runs" --body-file <path>` (use PR template; reference OpenSpec change `ci-01-pr-orchestrator-log-artifacts` and link to GitHub issue if created).
- [ ] 9.3 Verify PR and branch are linked to the issue in the Development section.
