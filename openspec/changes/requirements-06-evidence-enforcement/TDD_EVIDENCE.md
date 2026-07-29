# TDD Evidence: requirements-06-evidence-enforcement

## Failing-before

- **Timestamp**: 2026-07-29 (Europe/Berlin)
- **Command**:
  `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
- **Result**: 4 failed, 0 passed.
- **Evidence**:
  - `scripts/requirements_evidence_delivery_gate.py` did not exist, so the
    fixture-verification and red-report-retention tests failed with
    `FileNotFoundError`.
  - `scripts/pre-commit-quality-checks.sh` had no
    `run_requirements_evidence_gate` stage before review or contract tests.
  - `.github/workflows/requirements-evidence.yml` did not exist.

Production changes begin only after this failing evidence.

## Passing-after

- **Timestamp**: 2026-07-29 (Europe/Berlin)
- **Focused command**:
  `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
- **Result**: 4 passed, 0 failed.
- **Additional focused checks**:
  - `hatch run ruff check scripts/requirements_evidence_delivery_gate.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py` — passed.
  - `hatch run ruff format --check scripts/requirements_evidence_delivery_gate.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py` — passed.
  - `hatch run yaml-lint .github/workflows/requirements-evidence.yml` — passed.
  - With `SPECFACT_MODULES_REPO=/tmp/specfact-cli-modules-2438372`, the adapter
    verified commit `2438372f8e34c96d4e474afa4c66c92a9cee7979` and produced
    schema-v1 JSON and Markdown reports for `--base-ref HEAD` (skipped verdict,
    zero changed sources).

## Delivery and review evidence

- **Timestamp**: 2026-07-29 (Europe/Berlin)
- **Passed**:
  - `hatch run format`, `hatch run type-check`, `hatch run lint`, and
    `hatch run yaml-lint`.
  - `hatch run python scripts/check_reproducible_delivery.py`, `uv lock --check`,
    and the checked-in BasedPyright authority command (0 errors; repository
    warning baseline retained).
  - `hatch run specfact code review run --json --out .specfact/code-review.json --scope changed`
    with the immutable module roots — `PASS`, 0 findings after remediation.
  - `hatch run semgrep-sast --json --output /tmp/specfact-semgrep.json`,
    `hatch run semgrep-sast-gate --results /tmp/specfact-semgrep.json --baseline tools/semgrep/sast-baseline.json`,
    and `hatch run bandit-scan` — passed with no blocking findings.
  - Generated command overview, command-contract, docs-command,
    documentation-accountability, frontmatter, whitespace, and strict OpenSpec
    validation checks.
- **Incomplete**:
  - `hatch run contract-test` and `hatch run smart-test` each forced a fresh
    2,936-test baseline in this worktree and stopped before a final summary in
    the available execution window. Focused delivery-gate tests remain green;
    rerun these two full gates from a persistent terminal before PR creation.

## Release preparation

- **Version**: `0.54.0` on 2026-07-29.
- **Passed**: `hatch run check-version-sources` and `hatch run check-pypi-ahead`
  (local 0.54.0 is ahead of PyPI 0.53.5).

## Dogfooding evidence

- **Timestamp**: 2026-07-29 (Europe/Berlin)
- **Failing-before**: the first signed commit attempt ran the new Block 2 gate
  and failed closed because no `SPECFACT_MODULES_REPO` fixture was supplied.
- **Fix**: add this change's `requirements-evidence.yaml`, linking the delivery
  requirement to the focused script and workflow tests; rerun with the verified
  immutable fixture at `2438372f8e34c96d4e474afa4c66c92a9cee7979`.
- **Passing-after**: staged execution imported one requirement with two valid
  test links, returned `verdict: passed`, and wrote the JSON and Markdown
  reports before the signed commit retry.

## CI runtime correction

- **Timestamp**: 2026-07-29 (Europe/Berlin)
- **Failing-before**: PR #658's `Requirements evidence` workflow installed the
  frozen `.venv` successfully, then failed with `hatch: command not found`.
  The workflow contract was tightened to require the frozen `uv run` form;
  the focused contract test failed against the `hatch run` invocation.
- **Passing-after**:
  `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py -q`
  returned 4 passed; `hatch run yaml-lint .github/workflows/requirements-evidence.yml`
  passed; and the exact command
  `SPECFACT_MODULES_REPO=/private/tmp/specfact-cli-modules-2438372 uv run --locked --no-sync specfact requirements evidence --repo-root <worktree> --base-ref origin/dev ...`
  returned a passed verdict with both reports written.
