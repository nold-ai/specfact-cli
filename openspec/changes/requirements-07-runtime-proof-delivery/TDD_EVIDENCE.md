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

## Failing-before final proof collection remediation

- **Recorded:** 2026-08-04 (Europe/Berlin)
- **Evidence:** PR #663 Requirements Evidence artifact from run `30951457551`.
- **Result:** final reconciliation failed with two uncollected selectors:
  `test_executor_accepts_module_valid_pytest_node_ids` and
  `test_executor_rejects_unsafe_selectors_before_spawning`.
- **Failure:** each mapped function was parametrized, so JUnit carried only
  its parameterized child node IDs while the released reconciler required the
  exact mapped parent node ID.
- **Intent:** retain full parameter coverage while exposing one stable,
  exact pytest node ID for each mapped proof case.

## Passing-after final proof collection remediation

- **Recorded:** 2026-08-04 (Europe/Berlin)
- **Commands:**
  - `hatch run test tests/unit/scripts/test_requirements_proof_executor.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
  - `hatch run refresh-frozen-delivery && hatch run python scripts/check_reproducible_delivery.py && hatch run security-audit`
  - `<pinned-fixture> specfact requirements evidence` → executor →
    `specfact requirements reconcile --run-stage final`
- **Result:** 25 focused tests passed; frozen delivery and security-audit
  gates passed. The 17-case plan executes and reconciles with exactly one
  remaining finding: `prior-red-proof-missing`.
- **Proof:** mapped tests now produce one JUnit property per exact parent
  node ID while retaining every former parameter assertion. `cryptography`
  is frozen at `50.0.0` and `GitPython` at `3.1.58`, removing the unwaived
  advisory findings from the committed CI export.

## Failing-and-passing pre-commit portability remediation

- **Recorded:** 2026-08-04 (Europe/Berlin)
- **Failure evidence:** `hatch run smart-test` completed with exit code `1`;
  its only failure was
  `test_pre_commit_quality_markdown_globs_include_mdc`, which rejected the
  Bash-4-only `mapfile` added to staged Requirements proof planning.
- **Fix and proof:** replaced `mapfile` with the existing portable
  `while read` array-collection pattern. The focused pre-commit and delivery
  tests passed (22 tests), and the subsequent full smart-test suite passed
  all 2,958 tests (one expected skip), exit code `0`.

## Failing-and-passing review-scope remediation

- **Recorded:** 2026-08-04 (Europe/Berlin)
- **Failure evidence:** two new PR #663 review findings were reproduced by
  focused tests: local pre-commit did not govern `openspec/specs/**`, and CI
  derived maturity only from rename destinations.
- **Fix and proof:** canonical specifications now enter local Requirements
  evidence scope. CI derives paths from `git diff --name-status --find-renames`
  and preserves both rename endpoints before classifying maturity. The focused
  pre-commit/workflow suite passed.

## Failing-and-passing staged artifact and rename remediation

- **Recorded:** 2026-08-05 (Europe/Berlin)
- **Failure evidence:** `hatch run pytest
  tests/unit/scripts/test_requirements_evidence_pre_commit.py -q` failed as
  expected with two failures: a stale plan report could satisfy a later
  invocation, and local scope/maturity evaluation read only rename
  destinations.
- **Fix and proof:** clear the JSON, Markdown, and owned plan reports before
  every Requirements evidence invocation. A single rename-aware staged-path
  helper now emits source and destination paths and drives both governed-scope
  and maturity classification. The focused pre-commit suite passed 14 tests;
  `bash -n scripts/pre-commit-quality-checks.sh` and the SpecFact code-review
  gate also passed with zero findings.

## Failing-and-passing selector and CI rename remediation

- **Recorded:** 2026-08-05 (Europe/Berlin)
- **Failure evidence:** `hatch run pytest
  tests/unit/scripts/test_requirements_evidence_pre_commit.py
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
  failed as expected. Two mapped pytest node IDs were not collectible, and CI
  retained rename endpoints on one tab-separated line so destination-only
  governed changes could be classified as `planned`.
- **Fix and proof:** map the lifecycle scenario to the current maturity test,
  restore the governed product-only planning regression, and require every
  mapping selector to collect. CI now splits source and destination paths from
  `git diff --name-status --find-renames` before classifying maturity. The
  focused suite passed 11 tests; YAML/workflow lint and the SpecFact code-review
  gate passed with zero findings.
- **Acceptance:** product-owner acceptance was renewed on 2026-08-05
  (Europe/Berlin) for mapping digest
  `sha256:eb7fdbe5ad8f0b434b72086420d8ada142dc4cf0914b925937443cae2844cd30`.

## Failing-and-passing archived-evidence selection remediation

- **Recorded:** 2026-08-05 (Europe/Berlin)
- **Failure evidence:** `hatch run test
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py
  tests/unit/scripts/test_requirements_evidence_pre_commit.py` failed as
  expected with three failures. CI and local pre-commit both discovered
  `review-evidence.json` records beneath `openspec/changes/archive/`, and CI
  could derive `archive` as a changed active-change identifier.
- **Fix and proof:** both record-discovery paths prune
  `openspec/changes/archive`; CI also filters archived changed paths before
  deriving a selected change. The focused suite passed all 12 tests, and
  workflow YAML lint passed.

## Failing-before runtime smoke dependency-closure remediation

- **Recorded:** 2026-08-05 (Europe/Berlin)
- **Command:** `hatch run pytest tests/integration/scripts/test_runtime_discovery_smoke.py::test_local_runtime_registry_includes_transitive_bundle_dependencies -q`
- **Result:** failed as expected.
- **Failure:** the isolated registry staged only the three fixed smoke roots,
  so a `specfact-code-review` manifest declaring
  `nold-ai/specfact-requirements` could not resolve its dependency during
  marketplace installation.

## Passing-after runtime smoke dependency-closure remediation

- **Recorded:** 2026-08-05 (Europe/Berlin)
- **Command:** `hatch run pytest tests/integration/scripts/test_runtime_discovery_smoke.py::test_local_runtime_registry_includes_transitive_bundle_dependencies -q`
- **Result:** passed (1 test).
- **Proof:** the temporary runtime-smoke registry now recursively stages every
  manifest-declared bundle dependency exactly once while retaining the bounded
  root-module smoke surface.
- **End-to-end check:** `hatch run python scripts/runtime_discovery_smoke.py
  --modules-repo /private/tmp/specfact-modules-pr379 --launcher direct` passed
  against the current read-only Modules #379 worktree. It installed
  `nold-ai/specfact-requirements` 0.5.1 transitively while installing Code
  Review, then completed the runtime discovery and IDE checks.
- **Review:** `specfact code review run` reported zero blocking findings. Its
  two informational LOC-versus-complexity suggestions require no change: the
  demo-builder note predates this remediation, and the registry-builder keeps
  ordered filesystem, integrity, archive, and index-writing steps explicit for
  auditability rather than collapsing them into less readable helpers.

## Failing-before legacy TDD-ledger reconciliation

- **Recorded:** 2026-08-05 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q -p no:cacheprovider`
  - `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_digest_bound_legacy_tdd_ledger_for_r07 -q -p no:cacheprovider`
- **Result:** failed as expected. The first run exposed the obsolete 0.4.3
  fixture pin and no retained legacy-ledger artifact. The second run exposed
  that the released evidence CLI writes a wrapper report, with the digest-bound
  executable plan under its `plan` field.
- **Intent:** consume the published 0.5.1 reconciliation contract without
  inventing a historical red-JUnit artifact. The one approved R07 migration
  must instead hash its existing TDD ledger and bind that record to the exact
  released plan and mapping digests.

## Passing-after legacy TDD-ledger reconciliation

- **Recorded:** 2026-08-05 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py -q -p no:cacheprovider`
  - `hatch run yaml-lint .github/workflows/requirements-evidence.yml && hatch run lint-workflows .github/workflows/requirements-evidence.yml`
  - `openspec validate requirements-07-runtime-proof-delivery --strict`
  - `<modules-0.5.1-fixture> specfact requirements evidence` →
    `scripts/requirements_proof_executor.py` →
    `specfact requirements reconcile --run-stage final --legacy-tdd-evidence <digest-bound-record>`
- **Result:** 15 focused tests, workflow lint, and strict OpenSpec validation
  passed. The end-to-end reconciliation passed with `observed_maturity:
  verified`, `implementation_evidence: passing-after-legacy-tdd-ledger`, and
  `execution_proof.proof_basis: legacy-tdd-ledger`.
- **Proof:** the workflow pins the immutable merged Modules #379 commit
  `69f075819be5e1ceca1446b026b0417f19e584ca` (Requirements 0.5.1), creates
  a record from the committed ledger bytes and the nested released plan,
  retains it as an artifact, and supplies it only when the selected R07 change
  has no normal `red.json`. Normal red-JUnit proof remains the preferred path
  for every other change.

## Failing-before Code Review requirements-context handoff

- **Recorded:** 2026-08-05 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_hands_final_proof_to_code_review -q -p no:cacheprovider`
- **Result:** failed as expected because the Requirements workflow had no Code
  Review handoff step, so the finalized JSON was only summarized and uploaded.
- **Intent:** pass the finalized, module-owned Requirements proof to the
  released Code Review interface as independent context without letting either
  gate replace the other’s verdict.

## Passing-after Code Review requirements-context handoff

- **Recorded:** 2026-08-05 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q -p no:cacheprovider`
  - `hatch run yaml-lint .github/workflows/requirements-evidence.yml && hatch run lint-workflows .github/workflows/requirements-evidence.yml`
  - `<modules-0.5.1-fixture> specfact requirements evidence` → executor →
    final reconciliation → `specfact code review run --requirements-evidence <final-json>`
- **Result:** workflow contract, lint, and strict OpenSpec validation passed.
  The review receives only a complete final Requirements JSON, writes a
  separate review report, and a failed review remains independently enforcing
  after the Requirements artifacts are retained.
- **Acceptance:** product-owner acceptance was renewed on 2026-08-05
  (Europe/Berlin) for mapping digest
  `sha256:4e5f8d53718955811aa66cd8d0f8a7446b739ef581a02eb443033791041b2361`.

## Failing-before Code Review deleted-path filtering

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_hands_final_proof_to_code_review -q -p no:cacheprovider`
- **Result:** failed as expected because the workflow did not filter deleted
  Python paths before passing its explicit review targets to Code Review.
- **Intent:** ensure a deletion-only or mixed Python pull request reaches the
  independent review gate with only files present in the Actions checkout.

## Passing-after Code Review deleted-path filtering

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q -p no:cacheprovider`
- **Result:** passed (6 tests).
- **Proof:** the workflow now builds its explicit review path array only from
  existing Python files, while retaining the separate review artifact and
  independent failure enforcement.

## Failing-before Code Review clean-worktree enforcement

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_hands_final_proof_to_code_review -q -p no:cacheprovider`
- **Result:** failed as expected because the workflow used `--enforcement
  changed`. The pinned Code Review module derives changed lines from `git diff
  HEAD`; GitHub Actions checks out a clean PR head, so blocking findings could
  remain advisory despite the explicit pull-request file list.
- **Intent:** enforce all blocking findings in the explicitly PR-diff-selected
  files without broadening the review to unchanged repository files.

## Passing-after Code Review clean-worktree enforcement

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q -p no:cacheprovider`
  - `hatch run yaml-lint .github/workflows/requirements-evidence.yml && hatch run lint-workflows .github/workflows/requirements-evidence.yml`
  - `openspec validate requirements-07-runtime-proof-delivery --strict`
- **Result:** passed: 6 workflow tests, workflow lint, and strict OpenSpec
  validation.
- **Proof:** Code Review now uses `--enforcement full` only after the workflow
  derives its current pull-request Python file list and filters deleted paths;
  every blocking finding in that bounded set independently fails the PR.

## Failing-before immutable legacy ledger and Git-bound red proof remediation

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q -p no:cacheprovider`
- **Result:** failed as expected with three failures: no core Git-bound red
  proof validator, no immutable historical-ledger source, and no retained
  approved-ledger artifact.
- **Intent:** prevent a mutable pull-request `TDD_EVIDENCE.md` from
  self-attesting the R07 migration exception, and prove that ordinary red proof
  is test-only, strictly ancestral, and has unchanged selected test files.

## Passing-after immutable legacy ledger and Git-bound red proof remediation

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q -p no:cacheprovider`
  - `hatch run yaml-lint .github/workflows/requirements-evidence.yml openspec/changes/requirements-07-runtime-proof-delivery/requirements-evidence.yaml && hatch run lint-workflows .github/workflows/requirements-evidence.yml`
  - `openspec validate requirements-07-runtime-proof-delivery --strict`
  - `<modules-0.5.1-fixture> specfact requirements evidence` → executor →
    final reconciliation with ledger read from
    `7dcf8b74fa8f904ec20ba9957bd9aa94f9110e5c`
- **Result:** 7 focused tests, YAML/workflow validation, strict OpenSpec, and
  the pinned-module end-to-end reconciliation passed. Final evidence reports
  `observed_maturity: verified` and
  `implementation_evidence: passing-after-legacy-tdd-ledger`.
- **Proof:** the workflow reads the approved ledger only with `git show` from
  the immutable commit and retains those exact bytes as an artifact. For normal
  red proof, core now rejects non-ancestor or same-commit source refs,
  production changes before the red source, and any selected test file changed
  after it. Product-owner acceptance was renewed for mapping digest
  `sha256:8e14cc71eb0023acd49939979b6831f91eb84aeb99a3007464106380393fa82c`
  while implementing the user-directed review corrections.

## Failing-before Git-bound red replay and no-impact proof remediation

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py -q -p no:cacheprovider`
- **Result:** failed as expected: a red commit already contained in the current
  base was accepted as valid current proof.
- **Intent:** prevent historical red evidence from being replayed after the
  base has advanced, preserve governed source paths when they are renamed away,
  and execute the released no-impact pull-request decision end to end.

## Passing-after Git-bound red replay and no-impact proof remediation

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py -q -p no:cacheprovider`
  - `hatch run format && hatch run lint-changed scripts/requirements_proof_provenance.py tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py`
  - `hatch run type-check`
- **Result:** 13 focused tests passed; formatter and changed-file lint passed;
  project type-check completed with its existing warning-only baseline; the
  clean-code review returned zero warnings.
- **Proof:** normal red reports now require the current PR base to be an
  ancestor of the red source and inspect both source and destination paths of
  renames before accepting a test-only pre-red diff. The mapped no-impact test
  creates a docs-only PR diff against the pinned Requirements 0.5.1 fixture and
  verifies its successful explicit `skipped`/`no-impact` report. Product-owner
  acceptance follows the current user-directed review remediation for mapping
  digest `sha256:53869b32919f5a086aa6e8a96d095c9be0baf5446e4e68dd7ffc04ca48715fb6`.

## Failing-before red-proof provenance diagnostic retention

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_retains_red_proof_provenance_stderr -q`
- **Result:** failed as expected.
- **Failure:** `requirements_proof_provenance.py` emits invalid-red-proof
  findings on stderr, but the workflow captured stdout only. The retained
  failure report therefore discarded concrete diagnostics such as
  `stale-red-proof` and fell back to `tdd-order-unproven`.
- **Intent:** retain the module-facing proof rejection reason in the workflow
  artifact and PR summary without changing the validator's command-line
  interface.

## Passing-after red-proof provenance diagnostic retention

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
  - `SPECFACT_MODULES_REPO=<modules-0.5.1-fixture> hatch run generate-command-overview`
- **Result:** 7 workflow tests passed and the generated command artifacts were
  refreshed against the same immutable module fixture used by the gate.
- **Proof:** the command substitution now captures stderr (`2>&1`) with the
  provenance result, so `write_failure_reports` records the validator's
  specific rejection finding instead of its generic fallback.

## Failing-before NUL-delimited pre-red path parsing

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_governed_path_with_tab -q`
- **Result:** failed as expected.
- **Failure:** text-mode `git diff --name-status` C-quoted a tab-containing
  `src/` filename. The parser treated the leading quote as part of the path,
  allowing a governed production change before red proof to bypass the
  failing-first-order guard.
- **Intent:** preserve Git path boundaries independently of tabs, newlines,
  or other valid filename characters.

## Passing-after NUL-delimited pre-red path parsing

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py -q`
  - `hatch run lint-changed scripts/requirements_proof_provenance.py tests/unit/scripts/test_requirements_proof_provenance.py`
- **Result:** 3 provenance tests and changed-file lint passed.
- **Proof:** the validator consumes `git diff --name-status -z` records and
  decodes each path separately with `surrogateescape`; a tab-containing
  `src/` path is now retained and correctly produces `tdd-order-unproven`.

## Failing-before NUL-delimited workflow path parsing and trigger proof mapping

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Command:** `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports tests/unit/scripts/test_requirements_evidence_pre_commit.py::test_governed_trigger_scenario_uses_the_workflow_trigger_contract -q`
- **Result:** failed as expected (2 failures).
- **Failure:** the pull-request workflow parsed text-mode Git name-status
  output, so quoted tab/newline paths could be misclassified as non-governed.
  `R07-CORE-007-S01` also selected an adapter failure-report test rather than
  the workflow trigger and terminal-enforcement contract.
- **Intent:** make CI maturity classification path-safe and bind the governed
  trigger scenario to the behavior it claims to prove.

## Passing-after NUL-delimited workflow path parsing and trigger proof mapping

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Commands:**
  - `hatch run pytest tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_pre_commit.py -q`
  - `hatch run yaml-lint .github/workflows/requirements-evidence.yml openspec/changes/requirements-07-runtime-proof-delivery/requirements-evidence.yaml`
  - `hatch run lint-workflows .github/workflows/requirements-evidence.yml`
  - `openspec validate requirements-07-runtime-proof-delivery --strict`
- **Result:** 15 workflow/mapping tests, YAML and workflow lint, and strict
  OpenSpec validation passed.
- **Proof:** the workflow retains raw NUL-delimited path records in Bash arrays
  for maturity and active-change selection. `R07-CORE-007-S01` now maps to the
  workflow contract that asserts pull-request scheduling, retained artifacts,
  and terminal enforcement.
- **Acceptance:** product-owner acceptance was renewed in this task for mapping
  digest `sha256:d5ace9663eeb811b339a7751ad042fbf5d7b981867e596cb6eba599ddbde30a0`.

## Failing-before legacy-binding, verdict-mapping, and staged-path remediation

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Command:** `hatch run test -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_pre_commit.py`
- **Result:** failed as expected (3 failures).
- **Failure:** the R07 fallback wrote the current plan digests beside an
  immutable historical ledger without proving that ledger covered them; two
  sidecar cases selected tests unrelated to competing terminal verdicts; and
  pre-commit decoded text-mode Git name-status records, allowing tabs/newlines
  to conceal governed staged paths.
- **Intent:** bind the one permitted historical exception to its approved plan,
  map each handoff claim to its terminal enforcement proof, and preserve every
  staged pathname byte through maturity and scope selection.

## Passing-after legacy-binding, verdict-mapping, and staged-path remediation

- **Recorded:** 2026-08-06 (Europe/Berlin)
- **Commands:**
  - `hatch run test -q -p no:cacheprovider tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_pre_commit.py`
  - `hatch run yaml-lint .github/workflows/requirements-evidence.yml openspec/changes/requirements-07-runtime-proof-delivery/requirements-evidence.yaml && hatch run lint-workflows .github/workflows/requirements-evidence.yml`
  - `openspec validate requirements-07-runtime-proof-delivery --strict`
  - `hatch run lint-changed scripts/pre-commit-quality-checks.sh tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`
  - `hatch run python scripts/pre_commit_code_review.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`
- **Result:** 19 focused tests, YAML/workflow validation, strict OpenSpec,
  changed-file lint, and the local SpecFact clean-code review passed (zero
  errors and warnings). A temporary staged Git repository proved that a tabbed
  `src/` pathname is preserved as a NUL-delimited record.
- **Proof:** CI rejects the legacy ledger whenever the current mapping or plan
  differs from the approved historical pair; the two R07 cases now select
  distinct parametrized workflow checks for Requirements and Code Review
  terminal failures; and local staged scope/maturity parsing consumes Git
  `--name-status -z` records, including both rename endpoints.
- **Acceptance:** product-owner acceptance was renewed in this task for mapping
  digest `sha256:9dbc87bfb035858400b6b746c51dc926107c1fe444bc8985a351f27bd01f796f`.

## Failing-before reachable-ledger and empirical-proof remediation

- **Recorded:** 2026-08-07 (Europe/Berlin)
- **Command:** `SPECFACT_MODULES_REPO=<immutable-fixture> hatch run test -q -p no:cacheprovider tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py`
- **Result:** failed as expected (2 failures).
- **Failure:** CI depended on a feature-only Git object for the legacy ledger,
  and three R07 verification cases selected forwarding or static-shell tests
  rather than exercising stale acceptance, staged no-impact, and incomplete
  JUnit reconciliation through the released Requirements module.
- **Intent:** make the historical ledger reachable after a squash merge while
  retaining an independently pinned digest, and bind each scenario to its
  actual released enforcement behavior.

## Passing-after reachable-ledger and empirical-proof remediation

- **Recorded:** 2026-08-07 (Europe/Berlin)
- **Commands:**
  - `SPECFACT_MODULES_REPO=<immutable-fixture> hatch run test -q -p no:cacheprovider tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py`
  - `hatch run yaml-lint .github/workflows/requirements-evidence.yml openspec/changes/requirements-07-runtime-proof-delivery/requirements-evidence.yaml && hatch run lint-workflows .github/workflows/requirements-evidence.yml`
  - `hatch run lint-changed tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py`
  - `hatch run python scripts/pre_commit_code_review.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py`
- **Result:** 34 focused tests, YAML/workflow validation, changed-file lint,
  and clean-code review passed with zero errors and warnings.
- **Proof:** final reconciliation now extracts the committed historical ledger
  prefix, verifies its pinned SHA-256 digest, and retains those exact bytes as
  an artifact without requiring an unreachable Git object. New fixture-backed
  tests prove stale acceptance fails, a staged docs-only diff emits an explicit
  no-impact report, and skipped JUnit output reconciles to an incomplete,
  failing red-proof decision.
- **Acceptance:** product-owner acceptance was renewed in this task for mapping
  digest `sha256:4e346ea42a4398a2336e10f5550e4a8e1107c9f9e1926a95b33e3748be92dccd`.

## Failing-before fixture-preserving executor and reachable-plan refresh

- **Recorded:** 2026-08-07 (Europe/Berlin)
- **Command:** `hatch run test -q -p no:cacheprovider tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`
- **Result:** failed as expected (3 failures).
- **Failure:** the executor stripped the workflow-verified module fixture from
  child pytest processes, causing fixture-backed mapped selectors to skip;
  the legacy R07 binding still used a superseded ledger-prefix and nested-plan
  identity; and Code Review parsed text-mode Git paths, allowing unusual valid
  Python names to evade its explicit review set.
- **Intent:** keep only the already-verified fixture variables in the bounded
  child environment, bind the retained ledger to the current accepted plan,
  and make Code Review consume raw path records.

## Passing-after fixture-preserving executor and reachable-plan refresh

- **Recorded:** 2026-08-07 (Europe/Berlin)
- **Commands:**
  - `hatch run test -q -p no:cacheprovider tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`
  - `SPECFACT_MODULES_REPO=<immutable-fixture> hatch run python scripts/requirements_evidence_delivery_gate.py --repo-root . --base-ref 9ac33e90 --required-maturity test-authored --review-evidence openspec/changes/requirements-07-runtime-proof-delivery/requirements-proof/review-evidence.json --plan-output /private/tmp/r07-test-authored-plan.json ... && hatch run python scripts/requirements_proof_executor.py --plan /private/tmp/r07-test-authored-plan.json --repo-root . --junit /private/tmp/r07-current-proof.xml`
  - `hatch run lint-changed scripts/requirements_proof_executor.py tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py && hatch run lint-workflows .github/workflows/requirements-evidence.yml`
  - `hatch run python scripts/pre_commit_code_review.py scripts/requirements_proof_executor.py tests/unit/scripts/test_requirements_proof_executor.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`
- **Result:** 17 focused tests passed; the current released 18-selector plan
  executed with 18 passed, 0 skipped, and 0 failed/errored; lint and clean-code
  review passed with zero errors and warnings.
- **Proof:** pytest receives only the verified `SPECFACT_MODULES_REPO` and
  `SPECFACT_MODULES_ROOTS` fixture variables in addition to the existing
  safe environment. The retained ledger prefix now ends at line 692 with its
  pinned digest and is bound to nested mapping
  `sha256:eccdf006792d8910c54a773e30967886063b4e30c99c180bc36d7372b1bbd9ef`
  and plan `sha256:27ea6e6bcea0d68d68688b89fc8f89315d213b96918f4f76979484756fd8335e`.
  Code Review now reads `git diff --name-only -z` records.

## Failing-before no-impact scheduling remediation

- **Recorded:** 2026-08-07 (Europe/Berlin)
- **Command:** `hatch run test -q -p no:cacheprovider tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_pre_commit.py`
- **Result:** failed as expected (3 failures, 18 passed).
- **Failure:** the pull-request workflow used a path filter that prevented
  docs-only pull requests from publishing the released adapter's no-impact
  result; local Block 2 similarly skipped docs-only staged paths instead of
  invoking the adapter.
- **Intent:** make CI and pre-commit both emit one explicit evidence decision
  for every nonempty change set, including no-impact changes.

## Passing-after no-impact scheduling remediation

- **Recorded:** 2026-08-07 (Europe/Berlin)
- **Commands:**
  - `bash -n scripts/pre-commit-quality-checks.sh`
  - `hatch run test -q -p no:cacheprovider tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_pre_commit.py`
  - `SPECFACT_MODULES_REPO=<immutable-fixture> SPECFACT_MODULES_ROOTS=<immutable-fixture-packages> scripts/pre-commit-quality-checks.sh all`
- **Result:** Bash syntax validation, 21 focused tests, and the full staged
  pre-commit pipeline passed with the locked modules fixture.
- **Proof:** Requirements Evidence now schedules for every pull request to
  `main` or `dev`, and the pre-commit scope decision accepts every nonempty
  staged diff. A temporary staged docs-only Git repository proves that local
  Block 2 reaches the adapter rather than silently skipping the decision.

## Failing-before delivery-input maturity remediation

- **Recorded:** 2026-08-09 (UTC)
- **Command:** `hatch run python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_treats_delivery_inputs_as_production tests/unit/scripts/test_requirements_evidence_delivery_gate.py::test_pre_commit_treats_delivery_inputs_as_production`
- **Result:** failed as expected (2 failures).
- **Failure:** root dependency and packaging inputs were not classified as
  production paths, so they could retain proposal-level Requirements maturity.
- **Intent:** require verified CI proof, and test-authored pre-commit planning,
  for the frozen delivery inputs governed by repository policy.

## Passing-after delivery-input maturity remediation

- **Recorded:** 2026-08-09 (UTC)
- **Command:** `hatch run python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py`
- **Result:** 20 passed, 4 fixture-dependent tests skipped.
- **Proof:** both CI and staged maturity assignment now classify
  `pyproject.toml`, `setup.py`, `uv.lock`, and
  `requirements/ci/locked.txt` as production delivery inputs.

## CI failing evidence for bounded adapter execution

- **Recorded:** 2026-08-09 (UTC)
- **Evidence:** GitHub Actions run `31303484792`, job `93219952313`.
- **Result:** failed (3 of 18 mapped selectors).
- **Failure:** fixture-backed selectors recursively started `hatch run` while
  already executing inside the bounded proof process. The nested environment
  returned status 1 before the released command could publish its report.
- **Intent:** invoke the already-installed CLI interpreter directly while
  retaining the same public `specfact requirements evidence` boundary.

## Passing-after bounded adapter execution remediation

- **Recorded:** 2026-08-09 (UTC)
- **Command:** `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 SPECFACT_MODULES_REPO=<immutable-fixture> SPECFACT_MODULES_ROOTS=<immutable-fixture-packages> hatch run python -m pytest -q tests/unit/scripts/test_requirements_evidence_delivery_gate.py -k 'bounded_no_impact or stale_acceptance' -vv -s`
- **Result:** 2 passed, 13 deselected.
- **Proof:** the adapter uses the active verified Python interpreter directly;
  fixture-backed evidence remains successful in the proof executor's bounded
  pytest environment without recursively entering Hatch.

## Failing-before review and expiring-audit remediation

- **Recorded:** 2026-08-09 (UTC)
- **Commands and evidence:**
  - `hatch run python -m pytest -q tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_delivery_input_before_red tests/unit/scripts/test_requirements_evidence_pre_commit.py::test_pre_commit_selects_review_evidence_from_the_staged_change`
  - GitHub Actions run `31303593942`, jobs `93220310934`, `93220310941`,
    and `93220310936`.
- **Result:** the focused review tests failed twice as expected; Python 3.11,
  Python 3.12, and security-audit CI failed after the reviewed MCP exception
  expired.
- **Failure:** red-proof provenance did not classify root delivery inputs as
  production, staged evidence selection treated parallel active changes as
  ambiguous, and the exact Semgrep/MCP exception reached its fail-closed date.
- **Intent:** align all production classifiers, bind local acceptance to a
  uniquely staged active change, and renew the still-unavoidable exact advisory
  exception only after rechecking the latest Semgrep release metadata.

## Passing-after review and expiring-audit remediation

- **Recorded:** 2026-08-09 (UTC)
- **Commands:**
  - `hatch run python -m pytest -q tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_security_audit_gate.py`
  - `hatch run security-audit`
  - `bash -n scripts/pre-commit-quality-checks.sh`
- **Result:** 31 focused tests passed; the frozen dependency audit passed with
  only the three exact reviewed MCP advisories waived; Bash syntax passed.
- **Proof:** provenance now rejects all delivery-input paths already governed by
  CI and pre-commit. Local evidence uses the uniquely staged active change when
  present and retains the prior fail-closed fallback when none is staged.
  Semgrep 1.172.0 metadata was rechecked on 2026-08-09 and still pins vulnerable
  `mcp==1.23.3`; the narrowly scoped exception now expires on 2026-09-08.

## Failing-before packaged-asset classification remediation

- **Recorded:** 2026-08-09 (UTC)
- **Command:** `hatch run python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_treats_delivery_inputs_as_production tests/unit/scripts/test_requirements_evidence_delivery_gate.py::test_pre_commit_treats_delivery_inputs_as_production tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_delivery_input_before_red`
- **Result:** 7 failed and 1 passed as expected.
- **Failure:** wheel force-included templates, schemas, mappings, keys, and the
  bundled mapper were not classified consistently as production inputs.
- **Intent:** require verified delivery proof for every force-included runtime
  payload and reject any red proof recorded after those payloads changed.

## Passing-after packaged-asset and Python 3.11 remediation

- **Recorded:** 2026-08-09 (UTC)
- **Command:** `uv run --python 3.11 --locked --extra dev python -m pytest -q tests/unit/scripts/test_pre_commit_smart_checks_docs.py::test_pre_commit_quality_markdown_globs_include_mdc tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports tests/unit/scripts/test_requirements_evidence_delivery_gate.py::test_pre_commit_treats_delivery_inputs_as_production tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_delivery_input_before_red`
- **Result:** 9 tests passed on Python 3.11.
- **Proof:** CI, staged maturity, and red-proof provenance classify every wheel
  force-included asset path as production. Staged change collection retains the
  Bash 3.2-compatible read loop required by the repository portability test and
  no longer uses `mapfile`.

## Tooling production-classification review remediation

- **Recorded:** 2026-08-09 (UTC)
- **Failing-before command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports tests/unit/scripts/test_requirements_evidence_delivery_gate.py::test_pre_commit_treats_delivery_inputs_as_production 'tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_delivery_input_before_red[tools/proof_runner.py]'`
- **Failing result:** 2 failed and 1 passed; CI and provenance omitted
  executable `tools/` behavior.
- **Passing-after command:** `uv run --python 3.11 --locked --extra dev python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports tests/unit/scripts/test_requirements_evidence_delivery_gate.py::test_pre_commit_treats_delivery_inputs_as_production 'tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_delivery_input_before_red[tools/proof_runner.py]'`
- **Passing result:** 3 tests passed on Python 3.11.
- **Proof:** workflow, staged maturity, and red-proof provenance now classify
  executable repository tooling consistently as production behavior.

## Promotion provenance-binding review remediation

- **Recorded:** 2026-08-09 (UTC)
- **Failing-before command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/scripts/test_requirements_proof_provenance.py -k 'requires_every_execution_binding or rejects_test_digest'`
- **Failing result:** 5 tests failed as expected because retained red proof did
  not require source-tree, merge-base, selected-test digest, or toolchain
  bindings and did not compare the test digest with committed source bytes.
- **Passing-after command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`
- **Passing result:** 50 tests passed and 4 fixture-dependent tests skipped.
- **Proof:** core now validates mapping and plan digests, the exact source tree
  and merge base, complete selected-test digests against Git blob bytes, the
  retained failing JUnit digest and selectors, and structured toolchain
  identity before forwarding red proof. Executor infrastructure failures also
  remain failures even when a partial JUnit file exists, staged change-ID
  writes and sorting fail closed, and fixture-tree mismatch coverage now uses a
  valid lock attestation with a distinct checked-out tree.

## Index-bound staged acceptance remediation

- **Recorded:** 2026-08-09 (UTC)
- **Failing-before command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/scripts/test_requirements_evidence_pre_commit.py::test_pre_commit_requires_review_evidence_from_the_index`
- **Failing result:** 1 failed as expected because pre-commit accepted the
  working-tree copy of review evidence without proving it matched the index.
- **Passing-after command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/scripts/test_requirements_evidence_pre_commit.py tests/unit/scripts/test_pre_commit_smart_checks_docs.py`
- **Passing result:** 23 tests passed.
- **Proof:** pre-commit now requires the selected review-evidence blob to exist
  in the Git index and rejects any unstaged content difference before invoking
  the staged Requirements evidence gate.

## 2026-08-09 PR promotion review remediation

### Failing-before

- `hatch run python -m pytest -q tests/unit/scripts/test_requirements_evidence_delivery_gate.py::test_failed_command_writes_missing_diagnostic_reports_and_exports_fixture_roots tests/unit/scripts/test_requirements_evidence_pre_commit.py::test_pre_commit_rejects_staged_path_enumeration_failures tests/unit/scripts/test_requirements_proof_pytest_plugin.py tests/integration/scripts/test_runtime_discovery_smoke.py::test_local_runtime_registry_rejects_traversal_in_manifest_version`
  failed 4 tests as expected: ambient secrets were forwarded, staged-path failures had no observable sentinel, the selector plugin imported private pytest internals, and an invalid manifest version reached the archive sink.

### Passing-after

- The same focused command passed `4 passed` after adding the explicit environment allowlist, observable staged-path error handling, public `user_properties` JUnit integration, and manifest-version validation.
- `bash -n scripts/pre-commit-quality-checks.sh` passed.
- The internal wiki sibling checkout was unavailable, so dependency-story mirror reconciliation remains the explicit task 1.4 follow-up.

### Follow-up promotion findings

- Failing-before: the focused fixture/pre-commit run failed three tests because
  the lock had no tree attestation and staged review evidence accepted symlink
  modes without repository-containment validation.
- Passing-after: the same focused cases plus provenance and workflow contracts
  passed `21 passed` after tree binding, Bash 3-compatible staged-change
  deduplication, regular-file/containment enforcement, and retained failing
  JUnit digest validation.

### Delegated import isolation and release-fixture enforcement

- Failing-before: the focused delegated-environment test failed because a
  caller-controlled `PYTHONPATH` remained in the released command environment.
- Passing-after: the focused adapter and R07 mapping tests passed after removing
  `PYTHONPATH` from the allowlist and making a missing active-or-archived R07
  fixture a blocking assertion rather than a suite skip.
- Workflow lint: grouped fixture outputs under one `$GITHUB_OUTPUT` redirect to
  satisfy ShellCheck SC2129.

### Final automated-review hardening

- Bounded committed test-blob reads to 10 MiB with a 30-second subprocess timeout before hashing.
- Rejected JUnit destinations that overlap the proof plan or any selected test before creating directories or unlinking output.

## Promotion review remediation: trusted red artifacts, complete history, and failing-result reconciliation

- **Failing-before command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/scripts/test_requirements_proof_provenance.py -k 'changed_and_restored'`
- **Failing result:** 2 tests failed because endpoint tree diffs hid a governed
  production edit restored before red and a selected-test edit restored after
  red.
- **Additional reviewed gaps:** pull-request-tracked red JSON and JUnit could
  authenticate one another without a trusted runner boundary, and the workflow
  replaced ordinary failing-test JUnit before module reconciliation.
- **Passing-after command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`
- **Passing result:** 26 passed. Provenance now rejects tracked red artifacts,
  inspects every commit in both ancestry ranges, and the workflow reconciles
  every non-empty JUnit report before enforcing its module-owned verdict.
- **Requirements assignment:** no mapping change was required. These fixes
  strengthen the existing Git-bound failing-first proof, safe execution, and
  reconciliation scenarios without adding a new requirement surface.
- Focused executor and provenance verification passed `25 passed`.

### Complete Semantic Versioning validation

- **Recorded:** 2026-08-09 (UTC)
- **Failing-before command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/integration/scripts/test_runtime_discovery_smoke.py::test_local_runtime_registry_rejects_malformed_semver`
- **Failing result:** all 3 cases failed because the smoke-registry validator
  accepted a leading-zero core version, a leading-zero numeric prerelease, and
  an empty prerelease identifier.
- **Passing-after command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/integration/scripts/test_runtime_discovery_smoke.py::test_local_runtime_registry_rejects_malformed_semver tests/integration/scripts/test_runtime_discovery_smoke.py::test_semver_prerelease_and_suffix_are_valid_for_runtime_registry tests/integration/scripts/test_runtime_discovery_smoke.py::test_local_runtime_registry_rejects_traversal_in_manifest_version`
- **Passing result:** 5 tests passed.
- **Proof:** isolated smoke-registry assembly now implements the complete
  Semantic Versioning 2.0.0 identifier grammar before writing module archives.

## Retained red-artifact and strict-base review remediation

- **Recorded:** 2026-08-09 (UTC)
- **Failing-before command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_base_commit_as_red_source`
- **Failing result:** 2 tests failed as expected because the workflow had no
  authenticated cross-run artifact download and the provenance chain accepted
  the pull-request base itself as the red source.
- **Passing-after command:** the same focused command passed `2 passed` after
  downloading the latest eligible failed run's same-repository artifact into
  runner temporary storage and requiring the red source to differ from the
  current base.
- **Requirements assignment:** no mapping delta was required. The remediation
  completes the existing Git-bound failing-first proof scenario's retained
  runner-artifact and strict post-base ancestry requirements.

## Pull-request red-stage bootstrap and checkout binding

- **Recorded:** 2026-08-09 (UTC)
- **Failing-before command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports`
- **Failing result:** 1 test failed because test-authored workflow runs skipped
  execution and reconciliation, reconciliation was fixed to the final stage,
  and checkout did not select the source ref recorded in proof provenance.
- **Passing-after command:** the same focused command passed after executing
  every non-planned proof, selecting `red` for test-authored runs and `final`
  for verified runs, and checking out the exact PR head or dispatch SHA.
- **Requirements assignment:** no mapping delta was required. The remediation
  makes the existing two-phase red/final proof and Git-bound source scenarios
  executable in GitHub Actions without changing their contract.

## Promotion clean-code gate remediation

- **Recorded:** 2026-08-09 (UTC)
- **Failing-before command:** `SPECFACT_MODULES_REPO=/tmp/modules665 SPECFACT_MODULES_ROOTS=/tmp/modules665/packages uv run --locked --no-sync specfact code review run <changed-python-paths> --include-tests --enforcement full --json --out /tmp/code-review.json --requirements-evidence /tmp/final.json`
- **Failing result:** the full review gate reported one blocking `CC16` finding
  for the retained-red workflow contract helper and one `CC13` warning for the
  fixture verifier.
- **Remediation:** separated Git diagnostic normalization from fixture policy
  checks and separated prior-run download assertions from proof/source binding
  assertions without changing either contract.
- **Requirements assignment:** no mapping delta was required because this is a
  behavior-preserving clean-code remediation of already mapped delivery gates.

## Retained-run selection and repository-output safety remediation

- **Recorded:** 2026-08-09 (UTC)
- **Failing-before command:** `uv run --locked --no-sync python -m pytest -q tests/unit/scripts/test_requirements_proof_executor.py::test_executor_rejects_existing_repository_file_as_junit_destination tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports`
- **Failing result:** 2 tests failed because an unrelated existing repository
  file could be unlinked as JUnit output and retained-run discovery compared
  candidates with the synthetic merge SHA without inspecting the artifact's
  execution stage.
- **Requirements assignment:** no mapping delta was required. These regressions
  strengthen the mapped safe-execution and Git-bound retained-red scenarios.
