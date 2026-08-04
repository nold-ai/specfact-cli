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
  signed release until modules #368/#369 publishes a signed 0.4.3 main-branch
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
  pre-v2 release and therefore must be replaced only by the signed 0.4.3
  main-branch SHA described in task 1.3.1.

## Failing-before core proof-executor boundary

- **Recorded:** 2026-08-02 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_executor.py -q`
- **Result:** failed as expected (8 failures).
- **Failure:** the core had no `requirements_proof_executor.py`, so no code
  could validate a module plan, prevent selector injection, invoke pytest as
  an argument array, or produce JUnit canonical-selector provenance.
- **Intent:** establish core-owned execution safety without moving Requirements
  verdict semantics out of the published module.

## Passing-after fixture pin and proof-executor boundary

- **Recorded:** 2026-08-02 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
  - `openspec validate requirements-07-runtime-proof-delivery --strict`
- **Result:** 18 focused tests passed; strict OpenSpec validation passed.
- **Proof:** core pins modules main commit
  `97e0f917903b09803f48b7d73f56ec9753cf95c7` (published Requirements
  0.4.3), accepts only exact existing pytest selectors, rejects unsafe or
  duplicate input before execution, avoids shell invocation, and writes the
  JUnit `specfact.selector` property used by the module-owned reconciler.
- **Pending acceptance boundary:** execution remains unconnected to the delivery
  workflow until an acceptance record for the current mapping digest authorizes
  `test-authored` maturity. This prevents the core from fabricating stakeholder
  approval or silently weakening the published lifecycle contract.

## Published-module sidecar compatibility

- **Recorded:** 2026-08-02 (Europe/Berlin)
- **Failing command:** `SPECFACT_MODULES_REPO=/private/tmp/specfact-cli-modules-r07 hatch run python scripts/requirements_evidence_delivery_gate.py --repo-root . --base-ref origin/dev --output /private/tmp/r07-planned.json --summary /private/tmp/r07-planned.md`
- **Initial result:** failed with `missing-source-requirement-mapping` and
  `unknown-source-requirement` findings because the proposal sidecar used
  invented `R07-CORE-*` identifiers rather than native OpenSpec requirement
  IDs.
- **Passing command:** rerun the same command after mapping each native
  requirement and scenario ID exactly.
- **Result:** passed with `required_maturity: planned`,
  `observed_maturity: planned`, and
  `implementation_evidence: not-yet-available`.
- **Proof:** the published module validates the current sidecar and proposal
  readiness without treating it as an executed implementation.

## Product-owner acceptance

- **Recorded:** 2026-08-02T20:59:14Z
- **Decision:** product-owner acceptance was confirmed in this task for PR
  #663 and mapping digest
  `sha256:7e4b116af97bddc0638c1830fbce6051672362b52d2f3efb9ede27ca1c0f2d05`.
- **Record:** `requirements-proof/review-evidence.json` stores the normalized,
  provider-neutral acceptance payload. Any sidecar edit changes the digest and
  requires a new approval before test-authored planning may proceed.

## Review-fix regression evidence

- **Recorded:** 2026-08-02 (Europe/Berlin)
- **Failing command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
- **Initial result:** 6 failures. The executor rejected module-valid
  parametrized and class-method node IDs, inherited ambient pytest controls,
  and its CLI test did not exercise `main()`. The workflow still forced
  `planned` maturity for governed runtime changes.
- **Passing command:** `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
- **Result:** 24 focused tests passed.
- **Proof:** the executor now matches the published module selector contract,
  uses an explicit environment allowlist with plugin autoload disabled, and
  has CLI parsing/rejection coverage. CI derives `planned`, `test-authored`,
  or `verified` maturity from the diff; the fixture-pin invariant is recorded
  as an OpenSpec `MODIFIED` requirement.
- **Published-module check:** the pinned fixture accepted the updated sidecar
  at `planned` maturity with mapping digest
  `sha256:e0201e196d073e7dc7c6b6fc7c4bbae1d447ac42a51d508e6fd253d799affde8`.
- **Acceptance:** product-owner acceptance was renewed for this digest on
  2026-08-02 and recorded in `requirements-proof/review-evidence.json`.
- **Validation:** `SPECFACT_MODULES_REPO=/private/tmp/specfact-cli-modules-r07 hatch run specfact requirements evidence --repo-root . --base-ref origin/dev --required-maturity accepted --review-evidence openspec/changes/requirements-07-runtime-proof-delivery/requirements-proof/review-evidence.json --output /private/tmp/r07-accepted.json --summary /private/tmp/r07-accepted.md`
  passed with `required_maturity: accepted` and `observed_maturity: accepted`.

## Failing-before acceptance and plan forwarding

- **Recorded:** 2026-08-02 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py::test_delegated_command_forwards_accepted_maturity_and_proof_inputs -q`
- **Result:** failed as expected.
- **Failure:** `EvidenceRequest` rejected `review_evidence` and `plan_output`,
  so the core adapter could not carry a published lifecycle acceptance record
  or retain the module-produced plan.

## Passing-after acceptance and plan forwarding

- **Recorded:** 2026-08-02 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py -q`
  - `hatch run python scripts/requirements_evidence_delivery_gate.py --repo-root . --fixture-root /private/tmp/specfact-cli-modules-r07 --base-ref origin/dev --required-maturity accepted --review-evidence openspec/changes/requirements-07-runtime-proof-delivery/requirements-proof/review-evidence.json --plan-output /private/tmp/r07-accepted-plan.json --output /private/tmp/r07-accepted.json --summary /private/tmp/r07-accepted.md`
- **Result:** 9 adapter tests passed; the published module returned
  `accepted` maturity and a passing retained plan report.
- **Proof:** the adapter transports lifecycle inputs unchanged and continues to
  delegate all Requirements semantics to the verified module release.

## Review follow-up verification

- **Recorded:** 2026-08-02 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
- **Result:** focused runtime-proof, maturity-selection, plan-retention, and
  acceptance-forwarding coverage passed.
- **Proof:** changed-path discovery fails closed before evidence evaluation;
  CI retains the module-produced plan artifact and supplies the current
  acceptance record when present. Exact pytest parameter IDs with safe text,
  including spaces, remain valid no-shell argument values, while path and
  shell-metacharacter safeguards continue to reject unsafe selectors.

## Failing-before CodeRabbit runtime-delivery findings

- **Recorded:** 2026-08-03 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
- **Result:** failed as expected (2 failures).
- **Failure:** the executor accepted a tab-containing pytest selector, and the
  workflow neither covered every governed path nor invoked the plan executor
  and module reconciler with retained JUnit evidence.
- **Intent:** reject every control character before subprocess execution and
  complete the released plan → executor → JUnit → reconciler handoff without
  hard-coding a specific OpenSpec change's acceptance record.

## Passing-after CodeRabbit runtime-delivery findings

- **Recorded:** 2026-08-03 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
  - `hatch run lint-changed scripts/requirements_proof_executor.py tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`
  - `hatch run yaml-lint .github/workflows/requirements-evidence.yml && hatch run lint-workflows .github/workflows/requirements-evidence.yml`
  - `openspec validate requirements-07-runtime-proof-delivery --strict`
- **Result:** 27 focused tests passed; lint, YAML/workflow validation, and
  strict OpenSpec validation passed.
- **Proof:** pull requests that touch any governed delivery surface schedule
  this gate. Verified-maturity changes are configured to obtain a
  test-authored plan from the change-derived acceptance record, execute a
  valid plan without a shell, retain JUnit, and reconcile through the pinned
  module before enforcing its final report. Every ASCII control character is
  rejected before pytest starts.
- **Remaining evidence boundary:** a direct pinned-module plan check still
  reports `missing-selector` for R07-CORE-001 through R07-CORE-008, so this
  change cannot yet produce an executable plan. After exact selectors are
  mapped, a valid historical red proof must also exist at the selected
  change's `requirements-proof/red.json`; without it, final reconciliation
  remains correctly blocking rather than accepting fabricated evidence.

## Failing-before CodeRabbit staged and terminal-proof findings

- **Recorded:** 2026-08-03 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/scripts/test_requirements_proof_executor.py -q`
- **Result:** failed as expected (3 failures).
- **Failure:** the staged caller did not derive required maturity, the executor
  accepted stale/non-executable plan states, and setup-phase JUnit failures
  lacked their canonical selector property.
- **Intent:** apply the same maturity policy in local and CI gates, reject
  untrusted plan states before spawning pytest, and preserve selector identity
  for every terminal pytest phase.

## Passing-after CodeRabbit staged and terminal-proof findings

- **Recorded:** 2026-08-03 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
  - `hatch run lint-changed scripts/pre-commit-quality-checks.sh scripts/requirements_proof_executor.py scripts/requirements_proof_pytest_plugin.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_requirements_proof_executor.py tests/fixtures/requirements_proof_terminal_states.py`
  - `hatch run python scripts/pre_commit_code_review.py scripts/requirements_proof_executor.py scripts/requirements_proof_pytest_plugin.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_requirements_proof_executor.py tests/fixtures/requirements_proof_terminal_states.py`
- **Result:** 30 focused tests passed; lint and the SpecFact code-review gate
  passed with zero findings.
- **Proof:** staged source paths now derive the same `planned`,
  `test-authored`, or `verified` maturity policy as pull-request paths. The
  executor admits only a schema-v2, passing, test-authored plan, and the JUnit
  plugin records every selected node ID on its first report, including skips
  and setup errors.

## Failing-before unresolved review-thread remediation

- **Recorded:** 2026-08-04 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/scripts/test_requirements_evidence_pre_commit.py -q`
- **Result:** failed as expected (3 failures).
- **Failure:** the staged gate skipped governed product-only changes, requested
  `verified` maturity despite having no JUnit reconciliation path, and every
  executable mapping case lacked the exact pytest selector required by the
  published plan contract.

## Passing-after unresolved review-thread remediation

- **Recorded:** 2026-08-04 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
  - `SPECFACT_MODULES_REPO=<pinned-97e0f91-fixture> hatch run python scripts/requirements_evidence_delivery_gate.py --repo-root . --fixture-root <pinned-97e0f91-fixture> --base-ref origin/dev --required-maturity test-authored --review-evidence openspec/changes/requirements-07-runtime-proof-delivery/requirements-proof/review-evidence.json --plan-output /private/tmp/r07-pr663-plan.json --output /private/tmp/r07-pr663-evidence.json --summary /private/tmp/r07-pr663-evidence.md`
  - `openspec validate requirements-07-runtime-proof-delivery --strict`
- **Result:** 33 focused tests passed; the pinned public module accepted the
  renewed mapping digest `sha256:e5ee3649f2fff0fa93adc5ffc7e30f6722616961d15530c511722c2a9d626e73`
  and emitted a 17-case `test-authored` plan with no findings.
- **Proof:** local pre-commit checks every staged Requirements-governed path,
  normalizes execution-required changes to planning-only `test-authored`
  maturity, and retains no false final-execution claim. Each mapped test case
  now has a unique, executable pytest node ID.
