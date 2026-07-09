# TDD Evidence: traceability-01-index-and-orphans

- Failing-before: `hatch run pytest tests/unit/traceability/test_evidence_traceability.py -q` — 2026-07-09 Europe/Berlin; failed during collection because `specfact_cli.traceability` did not exist.
- Passing-after: `hatch run pytest tests/unit/traceability/test_evidence_traceability.py -q` — 2026-07-09 Europe/Berlin; 3 passed.
- Failing-before generic-index expansion: `hatch run pytest tests/unit/traceability/test_artifact_index.py -q` — 2026-07-09 Europe/Berlin; failed during collection because the generic index contracts did not exist.
- Passing-after generic-index expansion: `hatch run pytest tests/unit/traceability -q` — 2026-07-09 Europe/Berlin; 7 passed after aligning the compatibility assertion to the generic finding taxonomy.

## Quality Gate Evidence

Verified 2026-07-10T00:41:51+0200 Europe/Berlin after Codex and CodeRabbit
remediation:

- `hatch run pytest tests/unit/traceability tests/unit/requirements/test_context_adapter.py -q` — PASS, 18 passed.
- `hatch run type-check` — PASS, 0 errors; 1,627 pre-existing baseline warnings.
- `hatch run docs-validate` and `hatch run yaml-lint` — PASS.
- `hatch run contract-test` — PASS.
- `hatch run bandit-scan`, `hatch run semgrep-sast --json`, and
  `hatch run semgrep-sast-gate` — PASS, no blocking findings.
- `hatch run specfact code review run --json --out .specfact/code-review.json --scope changed` — PASS, no findings.
- `openspec validate traceability-01-index-and-orphans --strict`,
  `openspec validate governance-01-evidence-output --strict`, and
  `openspec validate profile-01-config-layering --strict` — PASS.
