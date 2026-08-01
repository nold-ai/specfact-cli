# TDD Evidence: Requirements Runtime Proof Delivery

## Failing-before OpenSpec rule validation

- **Recorded:** 2026-08-01 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/openspec/test_openspec_config_rules.py -q`
- **Result:** failed as expected.
- **Failure:** `openspec/config.yaml` contained non-string nested rule entries;
  OpenSpec consequently ignored the affected proposal and task instructions.
- **Intent:** make the project-level SDD/TDD workflow enforceable before
  extending delivery orchestration.

## Passing OpenSpec rule validation

- **Recorded:** 2026-08-01 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/openspec/test_openspec_config_rules.py -q && openspec validate requirements-07-runtime-proof-delivery --strict`
- **Result:** 1 passed; strict OpenSpec validation passed.
- **Proof:** every configured artifact rule is now a string, so OpenSpec can
  inject the proposal and TDD instructions instead of silently ignoring them.

## Failing-before planned-maturity consumer wiring

- **Recorded:** 2026-08-02 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
- **Result:** failed as expected (4 failures).
- **Failure:** the core adapter did not request `--required-maturity planned`,
  and the pull-request workflow omitted that argument, so a complete proposal
  could still be evaluated by legacy evidence semantics.
- **Intent:** make the core consumer explicitly request proposal readiness
  while preserving the release pin as a separate immutable dependency step.

## Passing-after planned-maturity consumer wiring

- **Recorded:** 2026-08-02 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/openspec/test_openspec_config_rules.py -q`
  - `openspec validate requirements-07-runtime-proof-delivery --strict`
  - `SPECFACT_MODULES_REPO=<modules-v0.4.0-worktree> SPECFACT_MODULES_ROOTS=<modules-v0.4.0-worktree>/packages hatch run specfact requirements evidence --repo-root . --base-ref origin/dev --required-maturity planned ...`
- **Result:** 10 focused tests passed; strict OpenSpec validation passed; the
  v2 mapping report passed with `gate_decision: pass`, `observed_maturity:
  planned`, `delivery_status: proposal-only`, and `implementation_evidence:
  not-yet-available`.
- **Release boundary:** core's checked-in fixture remains pinned to the prior
  signed release until modules #368/#369 publishes a signed 0.4.0 main-branch
  SHA. This is intentional; the post-release pin update is required before
  PR #663 can be rerun against v2 in CI.

## Expected local pre-commit release-fixture block

- **Recorded:** 2026-08-02 (Europe/Berlin)
- **Command:** `pre-commit run`
- **Result:** Block 1 passed (format, YAML, Markdown, workflow lint, and
  changed Python lint). Block 2 stopped at Requirements evidence before review
  and contract tests.
- **Diagnostic:** the worktree does not contain the currently locked prior
  module fixture. CI will instead resolve that fixture, but it remains the
  pre-v2 release and therefore must be replaced only by the signed 0.4.0
  main-branch SHA described in task 1.3.1.
