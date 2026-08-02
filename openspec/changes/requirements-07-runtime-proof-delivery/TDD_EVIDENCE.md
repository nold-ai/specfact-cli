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
- **Acceptance limit:** this digest differs from the existing acceptance
  record, so no higher maturity is claimed until product-owner acceptance is
  renewed for the new digest.
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
