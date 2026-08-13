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

## Completed red-run discovery review remediation

- **Recorded:** 2026-08-09 (UTC)
- **Failing-before command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports`
- **Failing result:** 1 failed because retained-proof discovery filtered for
  failed workflow conclusions even though valid red-stage reconciliation can
  complete successfully.
- **Passing-after command:** `uv run --python 3.12 --locked --extra dev python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`
- **Proof:** discovery now considers every completed prior run and retains the
  existing authenticated artifact inspection as the authority for selecting a
  red-stage report.

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
- **Follow-up review:** provenance now resolves symbolic base refs before strict
  source ordering and evaluates merge commits relative to their updated-base
  parent so imported base changes are not misclassified as branch production.

## Retained-run candidate authentication review remediation

- **Recorded:** 2026-08-09 (UTC)
- **Local review baseline:** `origin/main...origin/dev` at `e670ba7`.
- **Finding:** retained-run discovery accepted the first artifact that merely
  declared `run_stage: red`; an invalid newer artifact prevented discovery from
  continuing to an older, fully authenticated red proof.
- **Failing-before command:** `hatch run python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports`
- **Failing result:** 1 test failed because candidate discovery did not invoke
  the Git-bound provenance validator before selecting a run.
- **Passing-after command:** `hatch run python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_proof_provenance.py`
- **Passing result:** 27 tests passed. Discovery now selects a run only after
  its retained JSON/JUnit pair passes the same source, ancestry, digest, and
  history validation enforced during final reconciliation.
- **Requirements assignment:** the existing stale-red rejection scenario now
  explicitly requires invalid candidates to be skipped while older eligible
  runs remain discoverable; no new requirement surface was added.
- **Internal wiki follow-up:** the sibling `specfact-cli-internal` checkout was
  unavailable. Update `wiki/sources/requirements-07-runtime-proof-delivery.md`
  and run `python3 scripts/wiki_rebuild_graph.py` from that repository root.
- **Review exceptions:** the focused SpecFact review reported two pre-existing
  BasedPyright warnings on `pytest.mark.parametrize` at line 338 and one
  informational length heuristic on the unchanged `_assert_command_contract`
  helper. They are outside this patch; the helper's explicit fragments preserve
  readable workflow-domain evidence, and repository-wide type-checking retains
  those pytest typing warnings without errors.

## Retained-run pagination review remediation

- **Recorded:** 2026-08-09 (UTC)
- **Review finding:** PR #665 discussion `r3745221024` identified that the
  newest-100 run cap could hide an older eligible red artifact on a long-lived
  pull request.
- **Failing-before command:** `hatch run python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports`
- **Failing result:** 1 test failed because discovery used bounded
  `gh run list --limit 100` output rather than paginated workflow-run history.
- **Passing-after command:** `hatch run python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_proof_provenance.py`
- **Passing result:** 27 tests passed after switching discovery to the paginated
  GitHub workflow-runs API while retaining branch, event, status, ancestry, and
  provenance filters.

## Codex review proof-input and missing-JUnit remediation

- **Recorded:** 2026-08-09T21:30:23Z
- **Failing-before command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
- **Failing result:** 3 tests failed because post-red changes to root and test-tree
  `conftest.py` files were accepted and a zero-status executor without JUnit left
  the workflow step successful.
- **Passing-after command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
- **Passing result:** all 30 tests passed after applicable pytest support paths
  became stale-proof inputs and missing JUnit forced a nonzero evidence result.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1; no environmental
  limitations affected the focused run.
- **Requirements assignment:** the incomplete-execution scenario now explicitly
  rejects stale pytest support inputs and successful execution without retained
  JUnit proof.

## Release-review environment, symlink, and branch-scope remediation

- **Recorded:** 2026-08-09T21:46:00Z
- **Failing-before command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_symlink_selector tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports tests/unit/scripts/test_requirements_evidence_pre_commit.py::test_pre_commit_selects_review_evidence_from_the_staged_change -q`
- **Failing result:** 3 tests failed because selector symlinks were accepted, CI
  module commands inherited ambient variables, and production-only staging had
  no branch-scoped change binding.
- **Passing-after command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/scripts/test_requirements_evidence_pre_commit.py -q`
- **Passing result:** 47 tests passed; 0 skipped.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Namespace-package initializer review remediation

- **Recorded:** 2026-08-09 (UTC)
- **Failing-before command:** `uv run --python 3.11 --locked --extra dev python -m pytest -q tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_added_parent_package_initializer`
- **Failing result:** 1 failed because adding a previously absent parent
  `__init__.py` after the red run did not invalidate the proof.
- **Passing-after command:** `uv run --python 3.11 --locked --extra dev python -m pytest -q tests/unit/scripts/test_requirements_proof_provenance.py`
- **Passing result:** all 31 provenance tests passed.
- **Proof:** import provenance now retains every possible parent package
  initializer path, including namespace-package initializers absent at red.

## Codex review imported pytest-support freshness remediation

- **Recorded:** 2026-08-09 (UTC)
- **Review finding:** PR #665 identified that a selected test could import a
  changed test-support module after the red commit while the retained red proof
  remained accepted.
- **Failing-before command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_changed_imported_test_support -q`
- **Failing result:** 1 test failed because changing `tests/support.py` after
  red returned no provenance finding.
- **Passing-after command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py -q`
- **Passing result:** all 24 tests passed after recursively resolving
  repository-local Python imports from the red source and including them in
  post-red freshness checks.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.
- **Internal wiki follow-up:** the sibling `specfact-cli-internal` checkout was
  unavailable. Update `wiki/sources/requirements-07-runtime-proof-delivery.md`
  and run `python3 scripts/wiki_rebuild_graph.py` from that repository root.

## Codex follow-up conftest-import freshness remediation

- **Recorded:** 2026-08-09 (UTC)
- **Review finding:** PR #667 identified that import traversal started only at
  selected tests, so a helper imported exclusively by an applicable
  `conftest.py` could change after red without invalidating retained proof.
- **Failing-before command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py::test_git_bound_red_proof_rejects_changed_support_imported_by_conftest -q`
- **Failing result:** 1 test failed because the changed helper produced no
  provenance finding.
- **Passing-after command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py -q`
- **Passing result:** all 25 tests passed after seeding recursive import
  traversal with the selected test and every applicable `conftest.py` path.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.
- **Internal wiki follow-up:** the sibling `specfact-cli-internal` checkout was
  unavailable. Update `wiki/sources/requirements-07-runtime-proof-delivery.md`
  and run `python3 scripts/wiki_rebuild_graph.py` from that repository root.

## Post-merge Requirements evidence and plugin-closure remediation

- **Recorded:** 2026-08-09 (UTC)
- **CI failure:** Requirements Evidence run `31338563041` passed all 18 mapped
  tests and evidence execution, then failed finalized Code Review after PR #668
  merged to `dev`.
- **Review findings:** PR #668 identified that static `pytest_plugins`
  declarations and repository-local import targets absent at the red source were
  not included in freshness inputs.
- **Failing-before command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py -k 'changed_pytest_plugin or import_target_added_after_red' -q`
- **Failing result:** both selected tests failed because post-red plugin changes
  and newly added local import targets produced no provenance finding.
- **Passing-after command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py -q`
- **Passing result:** all 27 tests passed after parsing static
  `pytest_plugins` declarations and retaining possible paths for absent
  repository-local import targets.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Codex import-package and executable-selector remediation

- **Recorded:** 2026-08-09 (UTC)
- **Review findings:** PR #665 identified that provenance omitted wholly absent
  import roots and parent package initializers, and rejected executable regular
  selector blobs.
- **Failing-before command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py -k 'wholly_absent or parent_package_initializer or executable_regular' -q`
- **Failing result:** all 3 selected regressions failed before production edits:
  missing-root additions and changed parent initializers returned no finding,
  while the executable selector was rejected.
- **Passing-after command:** `hatch run pytest tests/unit/scripts/test_requirements_proof_provenance.py -q`
- **Passing result:** all 30 provenance tests passed after retaining absent leaf
  candidates, binding existing parent initializers, and accepting Git's two
  regular blob modes while continuing to reject symlinks.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Codex selector-package and annotated-plugin remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review findings:** PR #665 identified that provenance omitted package
  initializers for the selected test and ignored annotated `pytest_plugins`
  assignments in applicable conftests.
- **Failing-before command:** `uv run --python 3.11 --locked --extra dev python -m pytest tests/unit/scripts/test_requirements_proof_provenance.py -k 'changed_pytest_plugin or selector_package_initializer' -q`
- **Failing result:** two of the three selected cases failed: adding
  `tests/__init__.py` and changing a plugin declared with `ast.AnnAssign`
  returned no provenance finding, while the ordinary assignment case passed.
- **Passing-after command:** `uv run --python 3.11 --locked --extra dev python -m pytest tests/unit/scripts/test_requirements_proof_provenance.py -q`
- **Passing result:** all 33 provenance tests passed after retaining possible
  parent initializers for every seeded pytest input and accepting static
  annotated plugin declarations.
- **OpenSpec validation:** `uv run --python 3.11 --locked --extra dev openspec validate requirements-07-runtime-proof-delivery --strict` passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.11.15, pytest 9.1.1.

## Codex dynamic conditional plugin remediation

- **Recorded:** 2026-08-11 (UTC)
- **Review finding:** PR #671 identified that a non-literal assignment under a
  runtime-dependent branch discarded a previously known plugin constant even
  when that branch did not execute.
- **Failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k changed_pytest_plugin -q
  ```

- **Failing result:** a dynamic assignment under a false runtime branch removed
  the preceding literal plugin binding, so its post-red change returned no
  finding.
- **Passing-after command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 48 provenance tests passed after dynamic conditional
  assignments preserved previously known possible values while unconditional
  dynamic assignments still cleared stale bindings.
- **Validation:** Ruff, basedpyright, strict OpenSpec validation, and changed-file
  SpecFact code review passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Codex compound-statement plugin remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review finding:** PR #671 identified that plugin assignments under loops,
  exception handling, context managers, and match cases were flattened as if
  they always executed.
- **Failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k changed_pytest_plugin -q
  ```

- **Failing result:** an assignment inside an empty loop replaced the plugin
  constant that actually reached `pytest_plugins`, omitting the active plugin.
- **Passing-after command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 47 provenance tests passed after assignments under
  runtime-dependent compound statements contributed possible values instead of
  unconditionally replacing prior bindings.
- **Validation:** Ruff, basedpyright, strict OpenSpec validation, and changed-file
  SpecFact code review passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Codex nested guard and conditional plugin remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review findings:** PR #671 identified that executable nested assignments
  did not invalidate typing-guard aliases and that runtime-dependent plugin
  branches retained only the last AST branch visited.
- **Failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k 'changed_pytest_plugin or rebound_type_checking' -q
  ```

- **Failing result:** a nested runtime-true `TYPE_CHECKING` rebinding omitted an
  executed import, while a conditional plugin binding omitted the true branch.
- **Passing-after command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 46 provenance tests passed after conservatively
  recognizing nested rebindings and retaining the union of possible literal
  values from runtime-dependent plugin branches.
- **Validation:** Ruff, basedpyright, strict OpenSpec validation, and changed-file
  SpecFact code review passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Codex verified type guards and ordered constants remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review findings:** PR #671 identified that unverified `TYPE_CHECKING` names
  were always treated as false and that reassigned plugin constants were
  resolved in reverse rather than execution order.
- **Failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k 'changed_pytest_plugin or rebound_type_checking' -q
  ```

- **Failing result:** a rebound runtime-true `TYPE_CHECKING` branch was omitted,
  and the first textual plugin constant value won after reassignment.
- **Passing-after command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 45 provenance tests passed after pruning only verified
  typing guards and resolving literal constants in module execution order.
- **Validation:** Ruff, basedpyright, and strict OpenSpec validation passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Codex static branches and plugin constants remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review findings:** PR #671 identified that imports under `if False` and
  `if TYPE_CHECKING` were treated as executed, while `pytest_plugins` assigned
  through a simple literal module constant was ignored.
- **Failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k 'changed_pytest_plugin or unreachable_initializer' -q
  ```

- **Failing result:** the new constant-backed plugin case returned no finding,
  and changing support imported only by statically false initializer branches
  incorrectly returned `stale-red-proof`.
- **Passing-after command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 43 provenance tests passed after pruning known-false
  branches and resolving simple literal module constants used by
  `pytest_plugins`.
- **Validation:** Ruff, basedpyright, and strict OpenSpec validation passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Codex lazy initializer import remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review finding:** PR #671 identified that imports in uncalled initializer
  function bodies were incorrectly retained as if package import executed them.
- **Failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k lazy_initializer_import -q
  ```

- **Failing result:** changing a module imported only inside an uncalled
  `__init__.py` function incorrectly returned `stale-red-proof`.
- **Passing-after command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 41 provenance tests passed after import discovery
  stopped descending into deferred function, async-function, and lambda scopes
  while continuing to inspect executable class bodies.
- **Validation:** Ruff, basedpyright, and strict OpenSpec validation passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Codex registered-plugin target remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review finding:** PR #671 identified that parent package initializers of a
  registered plugin were incorrectly allowed to declare additional plugins,
  even though pytest registers only the specifically requested module.
- **Failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k plugin_parent -q
  ```

- **Failing result:** changing the target of `pytest_plugins` in the registered
  plugin's parent `__init__.py` incorrectly returned `stale-red-proof`.
- **Passing-after command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 40 provenance tests passed after parent initializers
  remained ordinary import inputs while only the requested file or package
  target was inspected for recursive plugin declarations.
- **Validation:** Ruff, basedpyright, and strict OpenSpec validation passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Codex comma-separated pytest plugin remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review finding:** PR #671 identified that a supported comma-separated
  string declaration was resolved as one malformed module path instead of one
  proof input per declared plugin.
- **Failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k changed_pytest_plugin -q
  ```

- **Failing result:** the tuple and annotated tuple cases passed, but changing
  a plugin named in an annotated comma-separated string returned no finding.
- **Passing-after command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 39 provenance tests passed after splitting and
  trimming each comma-separated plugin name before resolving module paths.
- **Validation:** Ruff, basedpyright, and strict OpenSpec validation passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## Codex root-initializer and plugin-source remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review findings:** PR #671 identified that the repository-root
  `__init__.py` was absent from proof inputs and that `pytest_plugins`
  declarations in ordinarily imported helpers were incorrectly treated as
  active pytest registrations.
- **Failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k 'imported_helper or repository_root_initializer' -q
  ```

- **Failing result:** changing a helper's plugin-like target incorrectly
  returned `stale-red-proof`, while adding the repository-root initializer
  returned no finding.
- **Passing-after command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 38 provenance tests passed after retaining the root
  initializer candidate and limiting plugin discovery to pytest-considered
  inputs and recursively registered plugins.
- **Validation:** Ruff, basedpyright, and strict OpenSpec validation passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.

## CI lint and legacy-ledger digest remediation

- **Recorded:** 2026-08-10 (UTC)
- **CI findings:** PR #671 failed Ruff formatting for the nested-plugin
  regression signature and rejected the approved 1,143-line legacy TDD ledger
  because its pinned SHA-256 no longer matched the retained ledger prefix.
- **Failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev ruff format --check \
    scripts/requirements_proof_provenance.py \
    tests/unit/scripts/test_requirements_proof_provenance.py
  ```

- **Failing result:** Ruff reported that
  `tests/unit/scripts/test_requirements_proof_provenance.py` required formatting.
- **Digest failing-before command:**

  ```shell
  uv run --python 3.12 --locked --extra dev python -m pytest \
    tests/unit/workflows/test_requirements_evidence_delivery_workflow.py \
    -k digest_bound_legacy_tdd_ledger_for_r07 -q
  ```

- **Digest failing result:** the workflow contract still required the prior
  legacy-ledger digest after the workflow pin was updated.
- **Passing result:** the exact CI Ruff format and check commands passed, the
  safe-write validator passed, and the workflow contract plus all 36 provenance
  tests passed (37 tests total).
- **Approved ledger binding:** the SHA-256 of the first 1,143 ledger lines is
  `sha256:d6e35c934757c08fd1f3e3071fc02b92b080c009ba5e428f6ea2888e7cd5e8c3`.
- **OpenSpec validation:** strict validation passed.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.12.13, pytest 9.1.1.
- **Internal wiki follow-up:** the sibling `specfact-cli-internal` checkout was
  unavailable. Update `wiki/sources/requirements-07-runtime-proof-delivery.md`
  and run `python3 scripts/wiki_rebuild_graph.py` from that repository root.

## Codex package-initializer import traversal remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review finding:** PR #671 identified that retained parent package
  initializers were proof inputs but were not traversal roots, allowing a
  repository-local module imported only by an initializer to change after red.
- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k changed_initializer_import -q
  ```

- **Failing result:** the regression failed because changing
  `tests/support.py`, imported by `tests/__init__.py`, returned no provenance
  finding.
- **Passing-after command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 34 provenance tests passed after package initializer
  paths became transitive import traversal roots.
- **Validation gates:** the Ruff, basedpyright, and strict OpenSpec commands
  recorded for the follow-up below cover both remediations and pass.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.11.15, pytest 9.1.1.
- **Internal wiki follow-up:** the sibling `specfact-cli-internal` checkout was
  unavailable. Update `wiki/sources/requirements-07-runtime-proof-delivery.md`
  and run `python3 scripts/wiki_rebuild_graph.py` from that repository root.

## Codex module-scope pytest plugin remediation

- **Recorded:** 2026-08-10 (UTC)
- **Review finding:** PR #671 identified that annotated `pytest_plugins`
  assignments inside functions or classes were incorrectly treated as
  module-level pytest declarations.
- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -k nested_pytest_plugin -q
  ```

- **Failing result:** both function-local and class-local annotation cases
  incorrectly returned `stale-red-proof` after the unrelated target changed.
- **Passing-after command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 36 provenance tests passed after plugin discovery
  stopped descending into function and class scopes.
- **Ruff:**

  ```shell
  uv run --python 3.11 --locked --extra dev ruff check \
    scripts/requirements_proof_provenance.py \
    tests/unit/scripts/test_requirements_proof_provenance.py
  ```

  Result: all checks passed.
- **Basedpyright:**

  ```shell
  uv run --python 3.11 --locked --extra dev basedpyright \
    --project pyproject.toml scripts/requirements_proof_provenance.py \
    tests/unit/scripts/test_requirements_proof_provenance.py
  ```

  Result: 0 errors, 0 warnings, and 0 notes.
- **OpenSpec validation:**

  ```shell
  uv run --python 3.11 --locked --extra dev openspec validate \
    requirements-07-runtime-proof-delivery --strict
  ```

  Result: the change is valid.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.11.15, pytest 9.1.1.

## Independent review remediation: configuration, rebinding, and fail-closed inputs

- **Recorded:** 2026-08-11 (UTC)
- **Review findings:** an independent review of PR #671 raised seven findings
  beyond the Codex turns: the typing-guard rebinding scan covered nested
  assignments but only top-level imports; the pytest configuration source was
  never a proof input; `pytest_plugins` written by augmented assignment or a
  tuple target was ignored; an unresolvable `pytest_plugins` value produced no
  plugins instead of failing closed; a malformed `selectors` entry raised
  `TypeError` instead of a deterministic finding; a non-UTF-8 committed module
  aborted the gate with `UnicodeDecodeError`; and Git results were never
  memoised across candidate paths or selectors.
- **Converging Codex finding:** Codex independently raised the first of these
  against `2f893e95`, in the form where a nested import rebinds the `typing`
  module alias rather than the `TYPE_CHECKING` name. The rebinding scan here
  covers both channels, so the regression is parametrized over the aliased
  module form and the imported-name form, and a genuine unrebound guard is
  still pruned.
- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -p no:randomly -q
  ```

- **Failing result:** 16 failed, 47 passed. The failures were the three new
  augmented and tuple-target plugin parameters, the rebound typing-guard import,
  all four pytest configuration parameters, all five unresolvable plugin
  parameters, both malformed selector parameters, and the non-UTF-8 support
  module case.
- **Passing-after command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -q
  ```

- **Passing result:** all 128 provenance tests passed, under both the default
  random ordering and `-p no:randomly`.
- **Reconciliation with `2f893e95`:** that commit landed the last open Codex
  finding by retaining known constant values when a conditional assignment is
  non-literal. This section supersedes its `_pytest_plugin_names` body with the
  stricter of the two options that finding offered. Known values are still
  retained, because a conditional unresolvable assignment appends the
  unresolved marker rather than replacing the list, but an active declaration
  that reaches that marker now fails closed instead of binding only the value
  that happened to be resolvable. The regression added by `2f893e95` still
  passes, through the fail-closed path rather than its original binding path.
- **Behavior changes:** rebinding detection now scans imports across the whole
  module tree as it already did for assignments; `PYTEST_CONFIGURATION_FILES`
  binds `pyproject.toml`, `pytest.ini`, `setup.cfg`, and `tox.ini` as proof
  inputs; `_destructured_targets` unpacks literal tuple and list targets and
  `_augmented_assignments` extends rather than replaces a binding; an active
  `pytest_plugins` declaration that cannot be resolved raises
  `stale-red-proof` through the `UNRESOLVED_PLUGIN_VALUE` marker rather than
  yielding no plugins; `_validated_selectors` rejects non-string entries before
  the JUnit selector comparison; `_python_tree_at_ref` parses committed bytes so
  PEP 263 declarations are honoured and applies `MAX_TEST_BLOB_BYTES`; and
  `_git_bytes` centralises Git execution with a `GIT_TIMEOUT_SECONDS` bound that
  degrades to an ordinary command failure.
- **Efficiency:** `_proof_inputs` resolves every selector in one traversal and
  `_python_tree_at_ref` and `_test_path_exists_at_ref` are memoised on the
  immutable `(repo_root, source_ref, path)` key. Measured against this
  repository for `tests/unit/scripts/test_requirements_proof_provenance.py`,
  Git invocations fell from 129 to 73 for a single selector, and a second
  selector sharing the same graph now adds none.
- **Fail-closed regression guard:** both committed `conftest.py` files in this
  repository still resolve their plugin declarations statically, and
  `pyproject.toml` and `tests/helpers/doc_frontmatter_fixtures.py` are present
  in the resolved proof inputs.
- **Ledger binding:** the approved legacy ledger digest covers the first 1143
  lines only. This section appends beyond that boundary, so
  `legacy_tdd_ledger_digest` in `.github/workflows/requirements-evidence.yml`
  remains `sha256:d6e35c93...5e8c3` and was reverified unchanged.
- **`pythonpath` root resolution:** declared plugins now resolve against the
  repository root and every configured `pythonpath` root. `_pythonpath_roots`
  reads `pythonpath` from all four configuration candidates at the red source
  (`[tool.pytest.ini_options]` via `tomllib`, and `[pytest]` or `[tool:pytest]`
  via `configparser`), rejects absolute or escaping entries, and is cached per
  ref. Reading every candidate instead of replicating pytest's inifile
  precedence only widens the proof inputs, which is the safe direction.
- **Scope decision:** roots widen plugin resolution only. Ordinary imports stay
  anchored at the repository root. Measured against this repository before
  making the change, rooting ordinary imports would have bound
  `src/specfact_cli/models/module_package.py`,
  `src/specfact_cli/modules/module_registry/src/commands.py`, and
  `src/specfact_cli/registry/module_discovery.py` for a single selector — the
  governed production modules a red-to-green change is expected to edit — so
  every valid failing-first flow would have returned `stale-red-proof`.
  `test_git_bound_red_proof_allows_production_change_under_pythonpath_root`
  locks that invariant.
- **Failing-before (`pythonpath`):**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py \
    -p no:randomly -k pythonpath_root -q
  ```

  Result: 4 failed, 1 passed. The four plugin-under-root parameters failed and
  the production-import invariant guard already passed, as intended for a
  regression that locks unchanged behavior.
- **Verified on this repository:** `_pythonpath_roots` returns
  `('', 'src', 'tools')` from the real `pyproject.toml`, the declared plugin
  `tests/helpers/doc_frontmatter_fixtures.py` remains bound, and no
  `src/specfact_cli/**` module appears in the resolved proof inputs for either
  a script-level or a module-registry selector.
- **Follow-on Codex findings on this work:** two P1 findings were raised
  against `1d288c8f` and are fixed here.
  `_compound_binding_names` now records names bound by loop, context-manager,
  exception, match, and walrus targets, which `_name_bindings` did not see, so
  `for PLUGINS in [...]` no longer leaves a stale literal active; the binding is
  recorded as unresolved and the declaration fails closed.
  `_imported_python_paths` now distinguishes an absent candidate from an
  existing input it cannot parse: when `_python_tree_at_ref` returns `None` for
  a path that `_test_path_is_regular_at_ref` confirms is a regular blob, the
  proof is rejected instead of silently dropping that file's imports. Checking
  the blob mode rather than mere existence keeps tree and symlink candidates
  treated as absent.
- **Failing-before (follow-on):**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -p no:randomly \
    -k "compound_target or unparsable or oversized" -q
  ```

  Result: 7 failed, 70 deselected. All seven pass after the fix.
- **No spurious rejection:** resolving proof inputs for three real selectors in
  this repository, individually and together, raises no fail-closed finding, so
  every file in the live traversal graph parses within the bound.
- **Second follow-on Codex round:** three further findings were raised against
  `5bb6189c` and are fixed here.
  `addopts` is now parsed for `-p` plugin names at the red source and those
  modules are seeded as plugin sources, because `-p` early-loads a module
  regardless of autoload; `no:` entries disable a plugin and are skipped.
  `_pytest_plugin_names` now reports only the final possible `pytest_plugins`
  binding instead of accumulating every historical assignment, so a declaration
  that a later one overwrites no longer stales the proof; the resolver records
  `pytest_plugins` through the same constant table as any other name.
  `_verified_type_checking_bindings` now scans `_executable_scope_nodes` rather
  than `ast.walk`, so a function-, lambda-, or class-local name no longer counts
  as rebinding the module guard, while a nested but reachable rebinding still
  does.
- **Refactor:** `_toml_pythonpath` and `_ini_pythonpath` collapsed into
  `_pytest_ini_option` over a cached `_pytest_configuration_sources`, so
  `pythonpath` and `addopts` share one reader. `_assigned_value_nodes` was
  removed as unused once the resolver reads bindings directly.
- **Failing-before (second follow-on):**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -p no:randomly \
    -k "addopts or overwritten or function_local" -q
  ```

  Result: 7 failed, 1 passed. The disabled-`-p` guard passed before and after,
  as a lock on unchanged behavior should.
- **Verified on this repository:** configured `addopts` yields no `-p` entries,
  `pythonpath` roots stay `('', 'src', 'tools')`, proof inputs are unchanged at
  80 and 105 paths for two real selectors, no production module is bound, and
  the declared plugin remains bound.
- **Third follow-on Codex round:** two further P1 findings against `a66956ed`.
  The configuration candidate list omitted `pytest.toml`, which the locked
  pytest 9.1.1 discovers *first*. Reading that version's own
  `_pytest/config/findpaths.py` showed the authoritative order is
  `pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini`, `pyproject.toml`,
  `tox.ini`, `setup.cfg`, so three candidates were missing rather than one, and
  `pyproject.toml` also accepts a TOML-mode `[tool.pytest]` table beside
  `[tool.pytest.ini_options]`. `PYTEST_TOML_TABLES` now maps each TOML
  candidate to its tables and `_toml_option_value` reads the first table that
  declares the option, so `pythonpath` and `addopts` resolve from every
  supported spelling.
  `_verified_type_checking_bindings` also now unions `_compound_binding_names`,
  so a module-scope `for typing in [...]` rebinding is detected; those targets
  were collected for plugin constants but unused for the guard.
- **Failing-before (third follow-on):** 10 failed — three configuration
  candidates, four `addopts` spellings, two `pythonpath` spellings, and the
  compound-target guard rebinding. All pass after the fix.
- **Verified on this repository:** the candidate list matches pytest's own
  order, configured `addopts` still yields no `-p` entries, `pythonpath` roots
  stay `('', 'src', 'tools')`, and no production module is bound. Proof inputs
  grew from 80 to 83 and 105 to 108 paths for two real selectors, which is
  exactly the three added configuration filenames.
- **Fourth follow-on Codex round:** two further P1 findings against `56e2a56e`.
  `_executable_scope_nodes` skipped whole `FunctionDef`, `AsyncFunctionDef`,
  `Lambda`, and `ClassDef` nodes, but only their *bodies* are deferred:
  decorators, argument defaults, annotations, and base-class expressions
  execute where the statement appears, so a walrus in a default such as
  `def helper(x=(TYPE_CHECKING := True))` rebinds the module guard.
  `_scope_header_nodes` now traverses everything except the body.
  `_pytest_ini_option` also constructed `ConfigParser()` with default
  interpolation, so a literal percent in an option value — valid to pytest, for
  example `addopts = --junit-prefix=foo%bar` — raised `InterpolationSyntaxError`
  from `get()`, outside the `try` that wrapped only `read_string`. The parser is
  now built with `interpolation=None` and the option read moved inside the
  guard.
- **Failing-before (fourth follow-on):** 7 failed — three scope-header
  rebinding forms (function default, lambda default, class base) and four
  ini-style percent-literal configurations. All pass after the fix.
- **Verified on this repository:** proof inputs stay at 83 and 108 paths for
  two real selectors, roots stay `('', 'src', 'tools')`, `addopts` still yields
  no `-p` entries, and no production module is bound.
- **Fifth follow-on Codex round:** four findings against `f4ad7bd8`.
  `_guard_attribute_targets` now drops a module guard whose `TYPE_CHECKING`
  attribute is written directly, which `_name_bindings` ignored because the
  target is an `ast.Attribute` rather than a name.
  `_global_rebound_names` treats a name that a `global` declaration rebinds from
  a nested scope as module-scoped, since a class body executes during import.
  `_pytest_configuration_sources` now fails closed on a configuration candidate
  that exists but exceeds the read bound, matching the Python-input rule: an
  unread configuration could declare plugins or roots this gate must bind.
  `_static_condition` resolves any literal condition through `ast.literal_eval`,
  so `if 0:`, `if None:`, `if "":`, and `if ():` prune as `if False:` does.
- **Correction found by the new tests:** the first attempt at the literal-guard
  fix special-cased `ast.Constant`, which left `if ():` unresolved because an
  empty tuple is an `ast.Tuple` display. `ast.literal_eval` covers every literal
  form uniformly and still leaves dynamic expressions runtime-unknown.
- **Failing-before (fifth follow-on):** 8 failed — three guard-mutation forms
  (attribute assignment, attribute augmented assignment, class-body `global`),
  the oversized configuration source, and four falsy literal guards. All pass
  after the fix.
- **Verified on this repository:** proof inputs stay at 83 and 108 paths for two
  real selectors, and the committed `pyproject.toml` is 29 KB against the 10 MiB
  bound, so the new fail-closed path is unreachable here.
- **Sixth follow-on Codex round:** one P1 against `40142261`. A
  `from tests.names import pytest_plugins` binding was invisible, because the
  resolver recorded only assignment-like bindings. `_import_binding_names` now
  records every imported name as unresolved, and `_has_star_import` records
  `pytest_plugins` as unresolved when a star import could supply it, so both
  forms fail closed rather than reporting no plugins. Resolving the value would
  require cross-module analysis; failing closed is the option the finding
  offered and matches the rule already applied to unevaluable expressions.
  An import binding replaces rather than extends, so a literal declaration made
  after an import still resolves normally.
- **Failing-before (sixth follow-on):** 3 failed — the plain import, the
  aliased import, and the star import. The fourth case in this round,
  `test_git_bound_red_proof_binds_plugins_declared_after_an_import`, passed
  before and after as a lock on the behavior that must not regress.
- **Verified on this repository:** both committed `conftest.py` files still
  resolve their declarations statically — `tests/conftest.py` binds
  `tests.helpers.doc_frontmatter_fixtures` despite carrying imports above the
  declaration — and proof inputs stay at 83 and 108 paths for two real
  selectors.
- **Seventh follow-on Codex round:** two findings against `e45eb375`.
  Each traversal entry now carries the module root it was discovered under, so a
  plugin loaded from a configured `pythonpath` root resolves its own imports
  against that root as pytest does; `source/plugin.py` importing `helper` now
  binds `source/helper.py` rather than only `helper.py`. `_module_relative_path`
  strips the root before computing the package for relative imports, and
  `_import_roots` keeps repository-root resolution for anything discovered at
  the root, so the invariant that ordinary test imports never bind governed
  production modules is preserved.
  `_pythonpath_entries` also splits a string form with `shlex` rather than
  whitespace, because pytest parses `paths` ini values that way — confirmed at
  `_pytest/config/__init__.py:1792` in the locked 9.1.1, which reads
  `input_values = shlex.split(value) if isinstance(value, str) else value`. A
  quoted root such as `pythonpath = "test support"` is now one path instead of
  two invalid ones.
- **Failing-before (seventh follow-on):** 2 failed — the rooted plugin's own
  import and the quoted root. Both pass after the fix, and the remaining 114
  tests passed before and after the restructure.
- **Verified on this repository:** roots stay `('', 'src', 'tools')`, proof
  inputs stay at 83 and 108 paths for two real selectors, the declared plugin
  stays bound, and no `src/specfact_cli/**` module is bound.
- **Eighth follow-on Codex round:** three P1 findings against `13b38d39`.
  `_mutated_name_targets` marks a tracked constant unresolved when a statement
  calls a method on it, so `pytest_plugins = []` followed by
  `pytest_plugins.append(...)` fails closed instead of reporting no plugins;
  only names already tracked are affected, so an unrelated call is inert.
  `_executable_scope_nodes` gained an `include_class_bodies` option used for
  guard-mutation detection, because a class body executes during import and
  `class C: typing.TYPE_CHECKING = True` mutates the module even though the body
  binds no module name — name bindings still exclude class bodies, so the
  round-3 fix is intact.
  The unparseable-input branch now rejects on existence rather than on being a
  regular blob, so a symlinked `conftest.py` fails closed instead of being
  skipped; a symlink executes bytes the gate never inspected, and selectors were
  already rejected for the same reason.
- **Failing-before (eighth follow-on):** 4 failed — two in-place mutation forms,
  the class-body guard mutation, and the symlinked conftest. All pass after.
- **Verified on this repository:** proof inputs stay at 83 and 108 paths for two
  real selectors, the declared plugin stays bound, and no production module is
  bound. 574 passed / 4 skipped across `tests/unit/scripts`,
  `tests/unit/workflows`, and `tests/unit/tools`.
- **Ninth follow-on Codex round:** two findings against `fb66d5e9`.
  `_module_scope_nodes` now traverses scope headers for deferred and excluded
  class scopes, the same correction made to `_executable_scope_nodes` earlier,
  so a plugin bound in a function default such as
  `def helper(arg=(pytest_plugins := (...)))` is seen by the resolver.
  `_global_rebound_names` was also narrowed, but not as reported: the finding
  asked to limit detection to class bodies and scope headers, which would have
  reintroduced a fail-open case, since a function *invoked while the module
  loads* genuinely does rebind the guard. Detection now applies a deferred
  function's `global` bindings only when that function is called at module
  scope, which removes the reported false positive without opening that hole.
- **Failing-before (ninth follow-on):** 2 failed — the scope-header plugin
  binding and the uncalled-function false positive.
  `test_git_bound_red_proof_tracks_called_global_guard_rebinding` passed before
  and after, and is the lock proving the narrowing did not become fail-open.
- **Known limit:** call detection is one level deep and matches direct
  invocation by name, so a `global` rebinding reached only through an
  indirection — a decorator, an alias, or a nested call chain — is not tracked.
  This is recorded rather than resolved, since deeper reachability analysis
  would be disproportionate to a construct this rare.
- **Verified on this repository:** proof inputs stay at 83 and 108 paths for two
  real selectors, the declared plugin stays bound, and no production module is
  bound. 577 passed / 4 skipped across `tests/unit/scripts`,
  `tests/unit/workflows`, and `tests/unit/tools`.
- **Tenth follow-on Codex round:** four findings against `c87f9a6c`. Three of
  them — an invoked setter assigning `pytest_plugins` through `global`, an
  invoked function writing `typing.TYPE_CHECKING`, and a rebinding function
  reached through an alias — are the same underlying gap: the round-nine call
  gate resolved call targets by name, one level deep. Rather than add three
  more shapes, `_unverifiable_module_state` now fails closed structurally: when
  a module both defines a function that can rebind a global, write a
  `TYPE_CHECKING` attribute, or assign `pytest_plugins`, **and** calls anything
  while loading, the guard set is emptied and the plugin declaration raises
  `stale-red-proof`. This subsumes aliases, wrappers, decorators, and transitive
  calls without pretending to resolve them, and it removes the by-name call
  resolution that could only ever cover the shapes it recognised.
- **Fourth finding, opposite direction:** `_verified_type_checking_bindings`
  now takes `before_line`, so a rebinding invalidates only the branches that
  follow it. `if TYPE_CHECKING: import tests.type_support` followed later by
  `TYPE_CHECKING = True` no longer binds the type-only helper retroactively.
- **Failing-before (tenth follow-on):** 4 failed — the three invoked-mutation
  forms and the retroactive invalidation.
  `test_git_bound_red_proof_tracks_guard_rebound_before_its_branch` passed
  before and after, locking the case where the rebinding does precede the guard.
- **Regression net:** all 123 previously added tests continued to pass across
  both restructures, including the round-ten pair whose two directions the new
  structural rule had to preserve.
- **Cost:** per-branch evaluation recomputes bindings for each `if`, so guard
  analysis is quadratic in module size. Measured against this repository,
  resolving both real selectors takes 0.62s in total, so the bound is not
  material at realistic conftest sizes.
- **Verified on this repository:** both committed `conftest.py` files still
  resolve their declarations, proof inputs stay at 83 and 108 paths, and no
  production module is bound. 582 passed / 4 skipped.
- **Ruff:**

  ```shell
  uv run --python 3.11 --locked --extra dev ruff check \
    scripts/requirements_proof_provenance.py \
    tests/unit/scripts/test_requirements_proof_provenance.py
  ```

  Result: all checks passed, and `ruff format --check` reports both files clean.
- **Basedpyright:**

  ```shell
  uv run --python 3.11 --locked --extra dev bash tools/run_basedpyright.sh \
    --project pyproject.toml scripts/requirements_proof_provenance.py \
    tests/unit/scripts/test_requirements_proof_provenance.py
  ```

  Result: 0 errors, 0 warnings, and 0 notes.
- **OpenSpec validation:**

  ```shell
  npx --yes @fission-ai/openspec@latest validate \
    requirements-07-runtime-proof-delivery --strict
  ```

  Result: the change is valid.
- **Skipped:** 0 tests.
- **Environment:** Linux, Python 3.11.15, pytest 9.1.1.

## Related-code audit for the same defect classes

- **Recorded:** 2026-08-11 (UTC)
- **Request:** check whether the defect classes fixed in this change exist in
  related code, and fix what is found.
- **Method:** searched for each class rather than reasoning from memory —
  `configparser` users, `ast.parse`/`ast.walk` users, pytest configuration
  filename lists, `git show` callers with `text=True`, and JSON reads whose
  `except` clause omits `UnicodeDecodeError`. Every candidate was then executed
  against a crafted non-UTF-8 input rather than judged by reading.
- **Fixed — undecodable input aborts a fail-closed gate (3 sites):**
  `scripts/security_audit_gate.py` `_read_exception_items` and
  `scripts/check_dependency_trust_exceptions.py` `_read_exception_records` and
  `_read_security_tool_floors` caught `(OSError, json.JSONDecodeError)` but not
  `UnicodeDecodeError`, so a non-UTF-8 register crashed each gate instead of
  producing the fail-closed error their docstrings promise. Confirmed by
  execution before the fix, and their `main` functions do not catch it.
- **Fixed — incomplete pytest configuration candidates (1 site):**
  `tools/smart_test_coverage.py` listed only `pytest.ini` and `tox.ini`, so a
  change to `pytest.toml`, `.pytest.toml`, `.pytest.ini`, or `setup.cfg` did not
  count as configuration drift and could leave coverage scoped from a stale
  cache. Aligned with pytest's discovery order, the same correction made in this
  change's own candidate list.
- **Checked and found correct, no change made:**
  `scripts/requirements_proof_executor.py` already catches
  `(OSError, UnicodeDecodeError, json.JSONDecodeError)` and its `main` catches
  `subprocess.SubprocessError`, which covers `TimeoutExpired`.
  `scripts/requirements_evidence_delivery_gate.py` omits `UnicodeDecodeError`
  from one `except`, but its `main` catches `(OSError, ValueError)` and
  `UnicodeDecodeError` is a `ValueError`, so the error is absorbed and only the
  diagnostic wording differs — verified by execution, and left unchanged rather
  than churned. `scripts/verify_safe_project_writes.py` already guards
  `OSError`, `UnicodeDecodeError`, and `SyntaxError`.
  `scripts/check_local_version_ahead_of_pypi.py` reads bytes, so the decode
  class does not apply.
- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_security_audit_gate.py \
    tests/unit/scripts/test_dependency_trust_review.py -p no:randomly \
    -k undecodable -q
  ```

  Result: 3 failed, each with the `UnicodeDecodeError` the gate should have
  converted into an error.
- **Passing-after:** 28 passed in those two files, and 570 passed / 4 skipped
  across `tests/unit/scripts`, `tests/unit/tools`, and `tests/unit/workflows`.
- **Static gates:** Ruff check and format clean across `scripts/`,
  `tools/smart_test_coverage.py`, and the touched tests. Basedpyright reports
  0 errors and 0 warnings at the `--level error` threshold CI enforces; at the
  default threshold the touched files go from 44 to 45 warnings, the added one
  being the same untyped-fixture pattern as the 44 already present in
  `test_security_audit_gate.py`.
- **Deferred:** four product-code reads under `src/` share the undecodable-input
  class with cache-fallback semantics; recorded as a task rather than changed
  here, because product paths need their own contract and coverage treatment.

## Codex round-13 remediation: roots, symlinked configuration, aliases, and `setattr`

Four new P1 findings arrived against `130260d0`. Each was reproduced by
execution before any production edit.

- **Traversing `pythonpath` root.** `_safe_module_root` returned `None` for any
  entry containing `..`, so `pythonpath = tests/helpers/../plugins` silently
  contributed no root and `addopts = -p localplugin` was searched only at the
  repository root. Pytest resolves the entry, so `tests/plugins/localplugin.py`
  loads and a post-red change to it was accepted. The root is now normalized
  within the repository; an absolute or escaping entry still yields no root,
  because a tree outside the repository holds no file any Git ref can bind.
- **Symlinked pytest configuration.** `git show <ref>:pytest.ini` returns the
  link text, while pytest reads the target, so an `addopts` or `pythonpath`
  declaration in the target was invisible. `_pytest_configuration_sources` now
  applies the same rule the traversal already applied to inputs: a candidate
  that exists but is not a regular blob yields `stale-red-proof`. The scenario
  already required this ("a symlink whose executed bytes were never inspected");
  only the implementation was missing.
- **Mutation through an earlier alias.** `PLUGINS = []`, `pytest_plugins =
  PLUGINS`, `PLUGINS.append("tests.localplugin")` binds both names to one list,
  but the resolver marked only `PLUGINS` unresolved and kept the empty list it
  had already copied for `pytest_plugins`. Mutation now propagates by object
  identity to every name sharing that container. Identity comparison is limited
  to mutable containers, because equal immutable values can be interned and
  would otherwise link unrelated bindings.
- **`setattr` rewrites of the typing guard.** `setattr(typing, "TYPE_CHECKING",
  True)` rewrites the guard without an attribute-assignment target, and
  `_unverifiable_module_state` did not apply because no separate function was
  defined. Rather than adding a `setattr` special case that the next equivalent
  form (`vars(typing)["TYPE_CHECKING"] = True`) would defeat, the module guard
  is now dropped whenever the module name is handed to any call at module load:
  a callee that receives the module can rewrite any attribute, and deciding
  which callees do would need their bodies. The same rewrite performed inside a
  function now also marks that function state-mutating, so an invoked one makes
  module state unverifiable.

- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -p no:randomly \
    -k "traversing_pythonpath or symlinked_pytest_configuration or \
    earlier_alias or setattr" -q
  ```

  Recorded 2026-08-11T21:52:41Z. Result: 5 failed, each accepting evidence the
  gate must reject.
- **Passing-after:** 133 passed in that file.
- **Real-repository check:** against this worktree's `HEAD`, the configuration
  sources (`pyproject.toml`), the `pythonpath` roots (`''`, `src`, `tools`), and
  the resolved proof inputs are byte-identical to the pre-change script — 163
  inputs for the 31 `tests/unit/scripts` selectors and 2186 for all 333 tracked
  selectors — so the change alters only the shapes the findings describe.

## Related-code audit: scope-header and class-scope classes

The two defect classes introduced in the preceding rounds — scope headers
execute where the statement appears, and a class body does not bind names for
the scopes nested in it — were audited across the repository's other static
analysis. `scripts/verify_safe_project_writes.py` is the only comparable
fail-closed gate; the `src/specfact_cli/analyzers/**` modules are best-effort
extractors whose misses are extraction quality rather than a gate hole, and
remain out of scope. Six fail-open cases were confirmed by execution in that
gate, each of which lets real unsafe JSON I/O through:

- A class attribute such as `json = None` suppressed offenders inside the
  class's methods, because every enclosing frame was unioned. A class body is
  not visible to scopes nested in it, so frames are now tagged and class frames
  are skipped when resolving a name from a nested scope.
- `except OSError as json:` suppressed offenders after the handler, although
  Python deletes the target when the handler ends. The binding is now removed
  again unless the name was already shadowed.
- Decorators, argument defaults, and class bases were never visited at all,
  because both scope visitors descended only into the body. They execute in the
  enclosing scope and are now visited there.
- A bare decorator (`@json.loads`) invokes the name without producing a `Call`
  node, so it was invisible. Decorator references are now matched directly, and
  the matching logic is shared with `visit_Call` rather than duplicated.

Two accuracy fixes in the opposite direction accompany them: a lambda parameter
named after an alias no longer produces a spurious offender, and annotations are
visited only when the analyzed module lacks `from __future__ import
annotations`, since PEP 563 leaves them unevaluated.

- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_verify_safe_project_writes.py -p no:randomly -q
  ```

  Recorded 2026-08-11T21:47:23Z. Result: 9 failed, 10 passed.
- **Passing-after:** 23 passed across the unit and integration files, and
  `python scripts/verify_safe_project_writes.py` still exits 0 against the real
  `src/specfact_cli/utils/ide_setup.py`.

## Self-review against change intent and mechanics

A review of the accumulated remediation against `proposal.md`,
`requirements-evidence.yaml`, and `CHANGE_VALIDATION.md` found four issues that
no reviewer had raised. Three are governance mechanics; one is a defect in the
preceding round's own fix.

- **The gate script was not a declared touchpoint.** `requirements-evidence.yaml`
  mapped `git-bound-failing-first-proof` to `requirements-proof/red.json` and
  `TDD_EVIDENCE.md`, but never to
  `scripts/requirements_proof_provenance.py` — the file that implements the
  requirement and carries every line of this remediation. R07 exists to enforce
  "changed interface -> mapped scenario -> exact selector", so the change was
  failing its own contract on itself. The script is now a `cli_command`
  touchpoint, matching the kind already used for
  `scripts/pre-commit-quality-checks.sh`, which the workflow invokes the same way.
- **The mapping covered two of the gate's scenarios.** Both provenance
  verification cases predated this work; the retained-input invariant and the
  symlinked-selector scenario had none. Five cases (R07-CORE-003-S04 through
  S08) now bind the configuration source and configured roots, unreadable
  inputs, unresolvable plugin declarations, guard rewriting, and symlinked
  selectors. Every mapped selector was checked to collect exactly one test:
  23 cases collect 23 tests, so no case points at a parametrized family whose
  bare node ID is not an exact selector. One draft case did — it named the
  nine-way parametrized `..._rejects_changed_addopts_plugin` — and was replaced
  before commit.
- **The requirement restated a proof-input list that had drifted.**
  `Git-Bound Failing-First Proof` enumerated selectors, `conftest.py` files, and
  imported support modules, while the retained-proof scenario enumerated a set
  several rounds larger, including the configuration source, configured roots,
  `addopts` plugins, and package initializers. The implementation followed the
  larger one, so the requirement text was normative and wrong. It now names the
  term and points at the single enumeration.
- **The round-13 `setattr` rule was defeated by aliasing.** Matching
  `setattr` by callee name repeated the mistake removed in round 12: with
  `from builtins import setattr as _set`, or with any helper that receives the
  module, `_unverifiable_module_state` stayed false and the guarded import was
  pruned. A function is now state-mutating when it hands a module-level typing
  binding to any call, tracking the guard by the name it is passed under rather
  than by the callee's name. The `setattr` check is retained alongside it,
  because it also covers a rewrite aimed at `pytest_plugins` rather than the
  guard.

- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -p no:randomly \
    -k handed_to_a_call -q
  ```

  Recorded 2026-08-11T22:04:21Z. Result: 1 failed — the aliased rewrite was
  accepted as fresh proof.
- **Passing-after:** 134 passed in that file. Re-probing the three rewrite
  shapes (plain `setattr`, aliased `setattr`, helper receiving the module) now
  reports unverifiable module state for all three; before the fix only the plain
  form was caught.
- **Not changed, and why:** the retained-proof scenario still sits under
  `Safe Pull-Request Proof Execution` although it governs retained red-proof
  freshness rather than plan execution. Moving it under
  `Git-Bound Failing-First Proof` would be structurally cleaner, but the
  scenario also carries the executor's empty-JUnit condition, so the move means
  splitting it — recorded rather than churned this late in review.

## Codex round-14 remediation: parseable symlinks, subscript mutation, module aliases

Three P1 findings against `ae03d4dd`, each reproduced before any production edit.
All three are second references to something the gate believed it had already
bound, and each defeated a rule added in an earlier round.

- **A symlink whose link text parses.** The traversal rejected an unreadable
  input by testing `tree is None`, but `git show` on a symlink returns the link
  text, and `real_conftest.py` is itself a valid Python attribute expression. It
  parsed, produced no imports, and the target's own inputs were never bound, so a
  post-red change to the target passed as fresh proof. `_python_tree_at_ref` now
  checks the Git mode independently of parsing, so the existing exists-but-
  unreadable path yields `stale-red-proof`. Parse success can never again stand
  in for "these are the bytes pytest executes".
- **Subscript mutation of an aliased list.** `_mutated_name_targets` recognized
  only method calls, so `PLUGINS = ["tests.old"]; pytest_plugins = PLUGINS;
  PLUGINS[0] = "tests.active"` left the copied binding reading `tests.old` while
  pytest loaded `tests.active`. Subscript and attribute writes and deletions are
  now mutations too, and they propagate to aliases through the identity rule
  added in round 13.
- **A typing guard written through a module alias.** `import typing as t;
  alias = t; alias.TYPE_CHECKING = True` recorded `alias` as mutated while `t`
  stayed verified, so `if t.TYPE_CHECKING:` was pruned although it executes.
  Copying a name into another binding now drops the guard outright: once a
  second reference exists, a write through it is invisible, and tracking the
  alias graph would only move the boundary rather than close it.

- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -p no:randomly \
    -k "symlinked_support_input_that_parses or subscript_mutation or \
    module_alias" -q
  ```

  Recorded 2026-08-11T22:11:34Z. Result: 3 failed, each accepting evidence the
  gate must reject.
- **Passing-after:** 137 passed in that file, and 629 passed / 5 skipped across
  `tests/unit/{scripts,workflows,tools}` and `tests/integration/scripts`.
- **Real-repository check:** configuration sources, `pythonpath` roots, and the
  resolved proof inputs are unchanged at 163 inputs for the 31
  `tests/unit/scripts` selectors and 2186 for all 333 tracked selectors. The
  second-reference rule is deliberately blunt — any `alias = typing` drops the
  guard — so this measurement is what establishes it costs this repository
  nothing.

## Requirements Evidence CI status and the withdrawn mapping change

An external quality assessment claimed the Requirements Evidence check was red
because the historical TDD ledger digest did not match. Checking the workflow
runs rather than the summary shows a different picture, and one correction to
an earlier note in this ledger.

- **The check is red on every commit of this branch, and on the base.** Run
  history for `requirements-evidence.yml` shows `failure` for every head from
  `fb66d5e9` through `b38ea723`, and also for `6a81ad3290` — the `dev` commit
  that is this pull request's merge base. An earlier note here treated the
  broadly green check-run list as "CI green"; that list did not include this
  workflow, so the claim was wrong and is corrected.
- **The current cause is not the ledger digest.** The job log shows the
  SpecFact CLI exiting 1 during planning with "Bundled Modules Need Refresh —
  some bundled modules are missing or outdated", before the legacy-ledger block
  runs. Only three of the six declared artifacts are uploaded, so no plan,
  JUnit, or ledger artifact is ever produced. The ledger-digest failure the
  assessment cites was the earlier cause at `ea2e256d`; the committed ledger
  digest over the first 1143 lines still equals the pinned
  `sha256:d6e35c93...5e8c3`, reverified after every append in this branch.
- **Because of that, one drafted correction was withdrawn.** Declaring the gate
  script as a touchpoint requires editing `requirements-evidence.yaml`, which
  changes the mapping digest. That digest is pinned in three places this branch
  cannot regenerate: the product-owner acceptance record
  (`mapping_digest: sha256:4e346ea4...`), and `legacy_tdd_mapping_digest` plus
  `legacy_tdd_plan_digest` in the workflow. The change would therefore have
  added a second, self-inflicted failure once the module-bundling problem is
  fixed, and by this change's own "Accepted Mapping Before Automation"
  requirement a mapping digest without matching acceptance blocks automation.
  The mapping is restored to its 18-case pinned state and the correction is
  recorded as task 3.9 with the full draft, so it can land in a change where
  acceptance is renewed deliberately.

No test or gate behavior changed with this withdrawal: the provenance fixes,
the spec de-duplication, and the guard-aliasing fix are unaffected.

## Codex round-15 remediation: seven remaining fail-open shapes

Seven unresolved P1 findings had accumulated across three review rounds — two
raised against `ce05b1c6`, three against `b38ea723`, two against `aab1570f`.
Each was reproduced by execution before any production edit.

- **Chained assignment split one object into two.** `PLUGINS = pytest_plugins =
  []` evaluated the shared right-hand side once per target, so the identity
  propagation added in round 13 saw two unrelated lists and a later
  `PLUGINS.append(...)` never reached `pytest_plugins`. Literal evaluation is now
  memoized per right-hand-side node, so chained targets share one object exactly
  as the runtime does.
- **An absolute `pythonpath` inside the checkout was dropped.** Round 13
  normalized traversal but still rejected every absolute entry. An absolute path
  is now resolved against the repository root and kept when it lands inside it;
  only a genuinely external tree yields no root.
- **A called lambda was not a state mutator.** `activate = lambda:
  setattr(typing, "TYPE_CHECKING", True)` followed by `activate()` mutates the
  guard at load, but only `FunctionDef` and `AsyncFunctionDef` were scanned.
  Lambdas are included now: a lambda body runs when it is called.
- **A `globals()` write declared plugins with no binding.** Subscript mutation
  detection required a plain name base, so `globals()["pytest_plugins"] = [...]`
  produced no binding at all. A module that writes its own namespace mapping
  through `globals()` or `vars()` is now unverifiable, failing closed for both
  the guard and the declaration.
- **A class-body `global` declaration was outside the plugin traversal.** The
  guard path already covered class-body globals, but the plugin resolver still
  used the class-excluding traversal. A `pytest_plugins` name created by a
  `global` statement now fails closed, because the value is bound outside the
  traversal that resolves it.
- **A guard nested in a call argument was invisible.** `setattr([typing][0],
  ...)` hands the module over, but only direct `ast.Name` arguments were
  inspected. Argument expressions are walked now.
- **A bare decorator was not a module-load call.** `@activate` invokes the
  decorator during import while producing no `ast.Call` node, so
  `_calls_during_module_load` returned false and an invoked mutator went
  unnoticed. Decorator application counts as an invocation. This is the same
  defect class already fixed in `scripts/verify_safe_project_writes.py`, found
  there by the related-code audit and here by review — worth recording, because
  it is the one class that has now appeared in both static analysers.

- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -p no:randomly \
    -k "chained_assignment or absolute_pythonpath or called_lambda or \
    module_namespace_plugin or class_body_global_plugin or \
    nested_in_a_call_argument or bare_decorator" -q
  ```

  Recorded 2026-08-12T16:34:45Z. Result: 7 failed, each accepting evidence the
  gate must reject.
- **Passing-after:** 144 passed in that file.
- **Real-repository check:** three of these rules are much broader than what
  they replace — every bare decorator now counts as a module-load call, and this
  repository uses them everywhere — so the measurement matters more than usual.
  Configuration sources, `pythonpath` roots, and the resolved proof inputs are
  unchanged at 163 inputs for the 31 `tests/unit/scripts` selectors and 2186 for
  all 333 tracked selectors. The broadened rules cost nothing here because
  failing closed still requires a state-mutating definition or a typing-module
  guard, which the repository's committed conftests and initializers do not
  have. Wall time for the full selector set rose from 14.2s to 17.4s, from
  walking nested call arguments.

## Codex round-16 remediation: imports inside invoked function bodies

One finding, and the first in this series that directly contradicts an earlier
accepted one.

- **The finding:** a conftest, test, or initializer that calls a local function
  whose body performs `import tests.runtime_support` executes that import during
  module load, but `_import_module_names` stopped at the function definition, so
  the imported file never entered `proof_inputs`.
- **The contradiction:** the "Codex lazy initializer import remediation" round
  above fixed the opposite complaint — imports in *uncalled* initializer function
  bodies were bound as though package import executed them, which rejected valid
  evidence. That fix discarded function bodies wholesale, which is what this
  finding now exposes as too coarse in the other direction.
- **The resolution:** the distinguishing fact is whether anything invokes the
  body. `_module_scope_nodes` gained `include_deferred_scopes`, and
  `_import_module_names` enables it exactly when `_calls_during_module_load` is
  true. A module that invokes nothing cannot reach a function body, so its
  imports stay unbound and the earlier finding still holds; once the module does
  invoke something, which body that reaches cannot be decided, so every body
  counts. Neither the by-name call resolution removed earlier nor a blanket
  widening would satisfy both findings at once.
- Static branch pruning still applies inside those bodies, so a
  `TYPE_CHECKING`-guarded import in a function stays unbound. That direction is
  pinned by its own regression rather than left to inspection.

- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -p no:randomly \
    -k "invoked_function or type_only_import_inside" -q
  ```

  Recorded 2026-08-12T17:14:03Z. Result: 1 failed, 1 passed — the over-strictness
  lock already held, only the fail-open case was missing.
- **Passing-after:** 146 passed in that file, including the earlier
  `..._ignores_lazy_initializer_import` that a blanket widening broke.
- **Real-repository check:** this is the first change in the series that moves
  the numbers — 163 to 174 inputs for the 31 `tests/unit/scripts` selectors and
  2186 to 2274 for all 333. The 88 additions were inspected individually rather
  than accepted as a total:
  - **87 do not exist in the repository.** They are candidate paths for
    third-party imports found in function bodies — `rich/progress.py`,
    `requests/HTTPError.py`, `ruamel/yaml.py`, and repository-root candidates for
    `specfact_cli`, whose package lives under `src`. A path absent from the tree
    can never change in a pull request, so it cannot produce a false stale.
  - **1 exists: `scripts/runtime_discovery_smoke.py`**, imported inside a
    function by a test that calls it. Binding it is correct.
  - **No `src/specfact_cli/**` path is bound**, so the invariant that a
    red-to-green change may edit governed production code without invalidating
    its own proof still holds.
  - Wall time for all 333 selectors rose from 17.4s to 41.6s. The gate validates
    only the selected subset in CI, where the comparable figure is 2.3s for 31
    selectors, but the growth is worth recording: descending into function bodies
    roughly doubles the traversal.

## Drift guards for the pinned legacy-ledger and plan digests

The Requirements Evidence check has been red on `dev` since `8766b8fe`, and the
cause is a class of drift nothing tested for.

- **What broke.** The workflow pins a digest over the first 1143 lines of this
  ledger. Commit `8766b8fe` inserted evidence at line 1086 — *inside* that
  window, not appended past it — so the committed prefix began hashing to
  `d6e35c93…` while the workflow still pinned `1df90efd…`. Every run since has
  been rejected with "Approved legacy TDD ledger digest does not match".
- **Why no test caught it.** The existing contract test asserted the workflow
  *contains* the literal digest string. The workflow and its test therefore held
  the same constant and could never disagree, and neither was ever compared to
  the ledger they describe. The pair drifted away from the artifact together
  while staying green.
- **The guards.** `test_workflow_legacy_ledger_digest_matches_the_committed_ledger`
  parses the pinned line count and digest out of the workflow and recomputes the
  digest from the committed ledger using the same algorithm the workflow's inline
  Python uses. It restates no constant, so it cannot drift alongside the pin.
  `test_workflow_legacy_ledger_line_count_is_within_the_committed_ledger` catches
  the other rejection path, "ledger is incomplete".
  `test_legacy_ledger_digest_detects_an_edit_inside_the_pinned_window` pins the
  sensitivity in both directions, because the whole point of the window is that
  an append past it stays valid while an edit inside it does not.
  `test_workflow_pinned_plan_digests_match_a_regenerated_plan` covers the
  remaining two pins by regenerating the plan through the released module and
  comparing `mapping_digest` and `plan_digest`; it skips without the fixture,
  matching the existing convention.

- **Failing-before evidence.** Rather than a synthetic mutation, the guard was
  replayed against the real history:

  | commit | pinned | committed prefix | guard |
  |---|---|---|---|
  | `f398b194` last green | `1df90efd` | `1df90efd` | passes |
  | `8766b8fe` first red | `1df90efd` | `d6e35c93` | **fires** |
  | `origin/dev` today | `1df90efd` | `d6e35c93` | **fires** |

  The guard passes at the last green commit and fires at exactly the commit that
  turned the check red, which is the strongest available proof that it detects
  this class rather than merely restating today's values.
- **Passing-after:** 13 passed in the workflow contract file with the pinned
  fixture mounted; 12 passed and 1 skipped without it, so CI behaviour is
  unchanged where the fixture is absent.
- **Scope note:** this branch already carries the corrected ledger pin
  (`d6e35c93…`), so the guards pass here. They will fail on `dev` until its pin
  is corrected — which is the intended signal, not a regression.

## Codex round-17 remediation and structural hardening

Six P1 findings, all reproduced by execution first, plus the hardening that
stops this class from recurring one shape at a time.

- **Imports in a selected test or fixture body.** The round-16 gate keyed body
  traversal on `_calls_during_module_load`, but pytest invokes test and fixture
  bodies during the run regardless. The gate now keys on file role instead: only
  a package initializer needs an import-time call to reach its own functions,
  which is exactly the distinction the earlier lazy-initializer round required.
- **Configuration beneath a selector.** Pytest searches upward from the
  arguments' common ancestor, so `tests/pytest.ini` decides collection for a
  selector beneath it. Discovery now walks the root and every selector ancestor.
- **Augmented assignment through an alias.** `PLUGINS += [...]` mutates the
  shared list, so it now propagates to aliases like the other mutation forms.
- **Imports through a symlinked directory.** Python follows the link while Git
  records it, so a candidate under a symlinked ancestor fails closed. One cached
  `ls-tree` collects every symlink, so this costs no per-lookup Git call.
- **Guard written through a module mapping.** `typing.__dict__["TYPE_CHECKING"]`
  reaches the attribute the guard reads.
- **Unreadable configuration read as absent.** A failed or timed-out `git show`
  now distinguishes an absent candidate from an unreadable one and fails closed.

### Hardening

Two structural changes, then two batteries that assert the families rather than
the instances.

- `_root_name` resolves attribute, subscript, and call chains to their base
  name, and every "which name does this touch" rule goes through it. The
  recurring finding shape was a known idea inside a new wrapper; wrappers now
  resolve identically to their unwrapped form.
- The batteries enumerate 16 guard-rewrite shapes and 16 unresolvable plugin
  shapes and assert every one fails closed, alongside positive controls proving
  the rules are not satisfiable by rejecting everything.

The batteries earned their keep immediately, in both directions:

- Two shapes I had listed as fail-open were **not** defects. A star import
  followed by an explicit assignment is definitively resolvable, and a
  conditional declaration binds the union of its possible values, which is the
  fail-closed direction. Both moved to the positive controls rather than
  "fixing" correct behavior — the labels were wrong, not the code.
- Broadening guard-write detection to every subscript target made
  `mapping[key] = value` inside any helper mark a module state-mutating, so
  **every proof on this repository was rejected**. The whole-repository
  measurement caught it before it shipped; the rule now matches the guard key,
  and `test_ordinary_mapping_writes_do_not_make_a_module_unverifiable` pins the
  boundary that nothing previously guarded.

- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -p no:randomly \
    -k "selected_test_body or selector_ancestors or augmented_mutation or \
    symlinked_package_directory or module_dictionary or cannot_be_read" -q
  ```

  Recorded 2026-08-12T20:27:33Z. Result: 6 failed.
- **Passing-after:** 188 passed in that file.
- **Real-repository check:** 176 inputs for the 31 `tests/unit/scripts`
  selectors and 2286 for all 333, up from 174 and 2274, the increase coming from
  test-body imports now binding. No `src/specfact_cli/**` path is bound, so a
  red-to-green change may still edit governed production code without
  invalidating its own proof.

## Codex round-18 remediation: follow-ups to the round-17 fixes

Three P1 findings, each a gap in a fix from the previous round rather than a new
class. All reproduced by execution first.

- **Nested configuration was discovered but not bound.** Round 17 taught
  discovery to read `tests/pytest.ini`, but the returned proof set still expanded
  only the root-level basenames, so changing or adding a nested candidate after
  the red source did not intersect the changed paths.
  `_configuration_candidate_paths` now binds every directory-qualified candidate.
  Binding candidates that do not exist is deliberate: the finding is as much
  about *adding* a configuration after red as changing one.
- **`pythonpath` was resolved against the wrong directory.** Pytest joins a
  relative entry to the declaring file's directory, so `tests/pytest.ini` with
  `pythonpath = plugins` names `tests/plugins`. Entries are now joined to that
  directory before normalization, which also leaves root-level configuration
  unchanged because joining against `.` is the identity.
- **An unbound-method call mutates its argument, not its receiver.**
  `list.append(P, "tests.p")` was invisible to mutation detection, which looked
  only at the call receiver. A declaration handed to any call now becomes
  unresolved through the same alias propagation, mirroring the rule the typing
  guard already uses: an object given to a call is no longer statically known.

- **Failing-before command:**

  ```shell
  uv run --python 3.11 --locked --extra dev python -m pytest \
    tests/unit/scripts/test_requirements_proof_provenance.py -p no:randomly \
    -k "nested_configuration_path or pythonpath_against_its_configuration or \
    receives_an_aliased_plugin_list" -q
  ```

  Recorded 2026-08-12T20:56:34Z. Result: 3 failed.
- **Passing-after:** 191 passed in that file.
- **Real-repository check:** 204 inputs for the 31 `tests/unit/scripts`
  selectors and 2776 for all 333, up from 176 and 2286. Every one of the 490
  additions is a nested configuration candidate under `tests/`, and **none of
  them exists in the tree** — which is the intended semantics rather than an
  accident, since a configuration added after the red source must invalidate the
  proof. No `src/specfact_cli/**` path is bound.

## Plumbing invariant: anything read to decide collection must be bound

The AST batteries cover the rule family, but two rounds of findings landed in the
path plumbing instead, where they could not reach: a configuration source was
discovered and read to derive plugins and roots, then never added to the returned
proof set, so changing it after the red source did not intersect the changed
paths. The batteries test helpers against parsed trees; nothing asserted that the
set of files the gate *reads* and the set it *binds* agree.

`test_every_file_whose_content_is_read_is_bound_as_a_proof_input` states that
directly. It records every `git show <ref>:<path>` the gate performs while
resolving a proof, and asserts that every recorded path which exists in the tree
appears in the returned inputs. The property needs no list of shapes, so a source
added by a future change is covered the day it is read.

Two companions bound the edges it cannot see. Absent candidates are invisible to
a read-based property, so
`test_every_configuration_candidate_is_bound_including_absent_ones` asserts the
full candidate set for the root and each selector ancestor is bound — the
semantics that make an *added* configuration invalidate the proof. And
`test_a_plugin_reached_through_a_nested_root_is_bound_with_its_imports` asserts
the chain end to end: nested configuration, its relative root, the plugin loaded
from it, and that plugin's own import.

- **Failing-before evidence.** Replayed against `1c46aac5`, the commit that had
  nested discovery but not nested binding:

  | version | read but unbound | nested plugin bound |
  |---|---|---|
  | `1c46aac5` pre-fix | `['tests/pytest.ini']` | no |
  | current | none | yes |

  The invariant fires on exactly the defect that two review rounds reported, and
  passes once it is fixed, which is stronger evidence than a synthetic mutation.
- **Passing-after:** 194 passed in the provenance file.

## Round 20: a dynamic import names its target in the argument

Review found that a conftest loading repository support through
`importlib.import_module("tests.runtime_support")` bound only the ordinary
`import importlib` statement, never the module actually executed. Editing that
support module between the red source and the final commit therefore left the
proof standing.

- **Failing-first evidence (2026-08-12T21:35:30Z).** Five spellings of the same
  load — `importlib.import_module`, `__import__`, `importlib.__import__`, a
  `from importlib import import_module` call, and the same call aliased to
  `_load` — all returned `[]` where `['stale-red-proof']` was required. The
  aliased spelling failing alongside the others is the evidence that rejected a
  name-matching fix: a rule keyed on the callee cannot see `_load`.

The fix resolves the **argument** rather than the callee. A dynamic import names
its target in data, so the mechanism does not identify it; the literal does. Any
dotted, identifier-shaped string a reachable body hands to a call is a candidate,
which covers every mechanism, alias, and wrapper at once, including a name read
out of a literal list, tuple, set, or dict handed to a loader.

Two positions bound the rule, and both were set by measurement rather than by
taste. Widening it to *any* literal in a reachable body was tried first and
rejected: it broke the five existing locks that keep a `pytest_plugins` value in
a scope pytest ignores from binding anything, because a string merely written
down is loaded by no one. Accepting bare words was tried and rejected too — on
this repository `Path("src")` bound `src/__init__.py` and the `repro setup`
subcommand argument bound `setup.py`. Prose is unbounded, while the residual gap
(a single-part target resting directly on an import root) is not.

Existence is then checked per **name**, not per candidate path, because
`src.module_a` in an analyzer fixture would otherwise bind `src/__init__.py`
through the parent-package candidate while naming nothing that exists. An
ordinary `import` statement is proof of its own target and keeps its absent
candidates bound; a name guessed from a literal earns that only once its module
is committed.

- **Whole-repository measurement.** 333 selectors over the real checkout:
  204 inputs for the scripts group and 2776 overall, identical to the previous
  head — 0 added, 0 removed, and nothing under `src/specfact_cli/**` bound. Each
  rejected variant was measured the same way and discarded on what it added:
  the any-literal rule added 9 paths, bare words added `src/__init__.py` and
  `setup.py`, and per-path existence checking left `src/__init__.py` behind.
- **Hardening.** `DYNAMIC_LOADER_SHAPES` holds 16 spellings — keyword argument,
  `find_spec`, a local wrapper, `functools.partial`, literal groups, conditional,
  `try`, class body, fixture, and test bodies — and `INERT_LITERAL_SHAPES` holds
  6 counter-shapes that must stay unbound, so the two directions are locked
  against each other. `test_a_dynamic_import_in_an_uncalled_initializer_is_not_bound`
  keeps the reachability rule in step with ordinary imports, which now share one
  `_deferred_scopes_are_reachable` helper rather than two copies that can drift.
- **Passing-after:** 217 passed in the provenance file.

## Round 21: the inputs a proof run reads that are not imports

Two findings landed together, both of the same shape: a file the proof run reads
that the import graph cannot see.

### The plugin the executor always loads

Every run passes `-p scripts.requirements_proof_pytest_plugin` on the command
line. The gate bound plugins declared in configuration and none from the command,
so changing that plugin after the red source left the proof standing while the
new code could alter collection, reports, and the selector properties JUnit
validation depends on.

- **Failing-first.** `test_every_plugin_the_executor_early_loads_is_a_proof_input`
  returned `[]` where `['stale-red-proof']` was required.

The name is now seeded beside the configured `addopts` names, since both arrive
through the same option and pytest treats them identically. Naming it in the gate
would ordinarily duplicate a fact owned by the executor, so
`test_the_gate_seeds_every_plugin_the_executor_early_loads` parses the executor's
own command shape and asserts every `-p` value it emits is seeded. The two files
are held together by a test rather than by remembering to edit both.

### Repository data the harness reads

A selected test or fixture that reads `tests/data/case.json` bound nothing, so
editing that data could turn the same test green with the retained failure still
accepted.

- **Failing-first.** All six shapes in `DATA_READ_SHAPES` returned `[]` where
  `['stale-red-proof']` was required: `Path(...)`, `open(...)`, a component-wise
  join onto a path root, a joined relative path, a read inside a fixture body, and
  a name iterated out of a literal list.

The scope was set by measurement, not by the finding's wording. Binding every
committed path a reachable body names would have bound 134 files on this
repository, including ten under `src/specfact_cli/**` — the modules a red-to-green
change edits by definition, whose exclusion is the reason ordinary imports already
stop at the repository root. Excluding governed production paths still left 37,
almost all `README.md`, `CHANGELOG.md`, and `docs/**`: documentation is likewise
what a change is expected to edit, so binding it would reject proofs for
documentation-driven work.

The line that holds is the harness itself. A read binds when the file lies inside
a directory the selected tests live in and is not a governed production path.
Data under the test tree is harness the change may not edit; everything outside is
a fix target. Three counter-shapes lock that boundary — a read of `src/product.py`,
of `README.md`, and of `docs/index.md` must all leave the proof valid.

The second half of the finding asked to fail closed on reachable repository I/O
that cannot be resolved. That is declined with a reason, and the reason is locked
by `test_a_read_that_cannot_be_resolved_does_not_fail_the_proof`: a harness builds
paths under `tmp_path` constantly, so failing closed there rejects every proof in
every repository that uses temporary directories, which catches no drift and
blocks all valid work.

- **Whole-repository measurement.** 333 selectors: 217 inputs for the scripts
  group and 2785 overall, up from 204 and 2776. Exactly two existing files were
  added — `scripts/requirements_proof_pytest_plugin.py` and
  `tests/fixtures/keys/test_private_key.pem`, one per finding. The remaining seven
  additions are absent candidates under the configured `src` and `tools` roots,
  bound as absent so adding one invalidates the proof, exactly as ordinary import
  candidates already are. Nothing under `src/specfact_cli/**` is bound.
- **Structure.** Both features answer the same question — is this literal handed
  to something that consumes it, or only written down — so they share one
  `_handed_over_expressions` helper covering call arguments and iterated values.
  That is what carried the comprehension shape without a second rule, and it keeps
  the module-name and path rules from drifting apart.
- **Passing-after:** 229 passed in the provenance file.

## Round 22: the over-strictness axis, measured by the suite instead of by hand

Every test in the provenance suite states what the gate must bind. None stated what
it must not, and that is the axis where this work has failed hardest: a rule that
binds too much satisfies every positive expectation while rejecting valid proofs.
One round widened a guard rule and rejected every proof on this repository; it was
caught only because a whole-repository measurement was run by hand before pushing.
That manual step was the entire safety net, and it depended on remembering it.

`tests/integration/scripts/test_requirements_proof_provenance_repository.py` runs
the measurement as part of the suite. It resolves the proof inputs once for all 333
committed selectors and asserts four things:

- no file under `src/specfact_cli/` is ever an input, stated separately by name so
  it cannot be weakened by appending to an exception list;
- every bound file outside the test tree is one of four recorded exceptions, each
  something pytest genuinely loads — the executor's `-p` plugin and three modules
  imported directly by the tests that exercise them;
- the set stays proportional to the selectors, which catches a rule that pulls in
  whole directories while staying inside the test tree, where the check above
  cannot see it;
- the selectors are still bound themselves, because restraint is only evidence
  while the gate still resolves what it must.

Failures name the offending paths, since the fix is always to narrow the rule that
bound them.

- **Proof that the guard fires.** The gate was mutated to the variant this work had
  already rejected once — bind every committed path a reachable body names — and
  the measurement failed on the mutation, listing all eight bound
  `src/specfact_cli/**` modules and 105 files outside the test tree. Reverted, it
  passes. A guard that has never failed is not evidence, so this was run rather
  than assumed.

### A latent crash the mutation exposed

Running the mutation raised `ValueError: embedded null byte` out of the middle of
the gate rather than failing an assertion. Path literals were handed to Git
unvalidated, and this repository already contains a literal of that class —
`tests/test_proof.py::test_selected\tinjected` in the executor's own tests. A
literal beginning `tests/` and containing a null byte passed the harness check and
reached the subprocess, where it cannot be passed at all.

- **Failing-before evidence.** Against the pre-fix module,
  `_literal_path_candidates` produced `'tests/data/case.json\x00truncated'`, it
  passed `_is_harness_path`, and handing it to Git raised `ValueError`.

`_names_a_repository_path` now discards a literal carrying a control character or a
traversal segment before it becomes a Git argument. Four shapes are locked: a null
byte, a tab, a newline, and `tests/../src/product.py`, which would otherwise have
named product source through the harness prefix.

### Correction to the round 21 figures

Round 21 recorded 217 and 2785 inputs. Those were measured before the final
`_handed_over_expressions` refactor in that same round and were not re-measured
after it. At the committed head the figures are **219 and 2787**. The delta the
round claimed is unchanged and remains the substantive result: 9 candidates added,
0 removed, of which exactly 2 exist —
`scripts/requirements_proof_pytest_plugin.py` and
`tests/fixtures/keys/test_private_key.pem`, one per finding. Absolute totals also
move as the repository moves, because the gate reads the committed tree, which is
why the automated measurement asserts structure rather than a pinned count.

- **Passing-after:** 233 passed in the provenance file, 4 in the repository
  measurement.

## Round 23: four findings on what the run reads and what it never runs

### A lookup Git could not answer is not proof of absence

`_git_bytes` reports a timeout as an ordinary non-zero result, and `git cat-file -e`
exits non-zero for both a missing path and an unusable ref. Existence therefore
conflated "definitely absent" with "could not determine". A module whose lookup
timed out was skipped as absent, and everything it imports went untraversed, so a
later change to a transitive helper passed as fresh evidence.

- **Failing-first.** With Git failing for `tests/support.py` and only
  `tests/helper.py` — reached *through* it — changed after the red source, the gate
  returned `[]` where `['stale-red-proof']` was required.

`git ls-tree` separates the two answers: it succeeds with empty output for a path
the ref does not contain and fails only when it could not answer. One cached
`_tree_entry_mode_at_ref` now drives both existence and regularity, so the fix
lands at the single place every caller goes through instead of at the call site
the finding happened to name. The mode it returns is what made the link fix below
possible without a second Git call.

### A read through a link binds nothing

The data pass filtered candidates to regular files, so a committed
`tests/data/case.json -> real.json` was dropped and its target was never bound —
pytest follows the link and reads bytes the gate had excluded.

- **Failing-first.** Changing only `tests/data/real.json` after the red source
  returned `[]` where `['stale-red-proof']` was required.

Links are now followed, binding every hop, because editing any of them changes what
the read returns. A link that leaves the checkout, cycles, or points at nothing
binds no bytes and is stale rather than silently dropped; four such shapes are
locked, along with a two-hop chain.

### A join is resolved against the base it starts from

`(Path(__file__).parent / "data" / "case.json")` discarded the base and produced
`data/case.json`, which named nothing and bound nothing. A harness names its data
beside itself far more often than beside the repository root.

- **Failing-first.** Changing `tests/data/case.json` after the red source returned
  `[]` where `['stale-red-proof']` was required.

Eight base shapes now resolve — `__file__` turned into a path, `.parent`,
`.parents[n]`, `.resolve()`, `os.path.dirname`, and a module-level name bound to
any of them, including nested forms such as `Path(os.path.dirname(__file__))`.

The same change closes an over-binding hole in the opposite direction that the
finding did not mention. A join was previously read as root-relative *whatever* it
started from, so `tmp_path / "tests" / "data" / "case.json"` bound the committed
file that happened to share those components. A base that cannot be known now
discards the join, which is the rule the specification already states for runtime
paths. Three unknowable bases are locked as binding nothing.

### The body of a test the run never enters

Reported as P2: an exact selector runs one node, but every deferred scope in the
module was traversed, so a helper imported only inside an *unselected* test body
was bound and editing it rejected still-valid evidence.

- **Failing-first.** With `tests/test_proof.py::test_selected` selected and
  `tests/helper.py` imported only inside `test_other`, changing that helper
  returned `['stale-red-proof']` where `[]` was required.

The finding's proposed remedy — reachability from the selected node and its active
fixtures — is **declined**, and the narrower rule implemented instead. Fixture
activation depends on autouse declarations, indirect parametrization, conftest
chains, and plugins; none is decidable from a module's syntax, and a partial
implementation would silently stop binding fixtures that do run. That is the
under-binding class this change has spent twenty rounds closing, and trading it for
a narrow false positive is a bad exchange.

What is implemented is provable: a scope is dropped only when it is a test, is not
itself selected, and its name appears nowhere else in the module. Nothing is
dropped at all unless a selected identifier matches a function defined there, so a
selection this gate cannot resolve to names leaves every scope traversed. Node
identifiers are now carried through from the red report rather than discarded after
their paths are taken, with parametrized cases reduced to the function they run.
Three locks hold the boundary: an import in the selected body, an import in an
unselected body that the selected one calls, and an import in a fixture body all
stay bound.

- **Whole-repository measurement.** One file added against the previous head,
  `tests/fixtures/speckit/spec-template-v0.12.18.md` — a fixture reached by a
  `__file__`-relative join that previously resolved to nothing. Nothing under
  `src/specfact_cli/**` is bound, and the automated repository measurement passes
  unchanged.
- **Passing-after:** 256 passed in the provenance file, 640 across the scripts,
  workflows, and integration suites.

## Round 24: closing three families rather than three spellings

All three findings were second spellings of rules changed in round 23, and each was
reported as "fresh evidence beyond the resolved thread". That is the signature of a
rule stated as a shape rather than as a principle, so each was fixed by replacing
the rule, not by adding a case.

### Reaching the namespace mapping

`globals().update(pytest_plugins=[...])` creates the attribute pytest reads while
the predicate inspected only assignment targets, so the declaration was invisible
and the plugin never bound.

- **Failing-first.** Of eight shapes in `NAMESPACE_REWRITE_SHAPES`, five already
  failed closed and three did not: `exec(..., globals())`, handing the mapping to a
  local function, and `sys.modules[__name__].pytest_plugins = [...]`.

Enumerating mutating methods would have admitted whichever spelling the list
omitted — `setdefault` after `update`, `__setitem__` after that. The rule is
positional instead: reading one key out of the mapping is fine, and **every other
use of it** leaves the module unknowable, whether that is a subscript write, any
method call on it, or handing it to anything. A `pytest_plugins` attribute write is
unverifiable wherever it appears, because the module object is reachable by other
routes than the mapping.

### One join, several notations

`os.path.join(os.path.dirname(__file__), "data/case.json")` is an `ast.Call`, and
the resolver read only `ast.BinOp`, so the operator form worked and the functional
form bound nothing.

- **Failing-first.** All six shapes in `FUNCTIONAL_JOIN_SHAPES` returned `[]` where
  `['stale-red-proof']` was required, including `joinpath`, `abspath` wrapping, and
  a doubled `dirname`.

`base / "a"`, `os.path.join(base, "a")`, and `base.joinpath("a")` are now one
construction behind a single splitter, and a join is itself resolvable as a path,
so nesting them composes without further cases.

The over-binding direction needed its own rule. A join's components are consumed
whether or not its base turns out to be knowable, because a component is part of a
path rather than a path of its own — otherwise the tail of
`os.path.join(tmp_path, "tests/data/case.json")` would still be read as
repository-relative and bind a file the run never opened.
`test_a_functional_join_from_an_unknowable_base_binds_nothing` locks that.

### Links at any component, not only the last

`tests/data_link/case.json` where `tests/data_link -> real_data` has no Git entry at
the full path, so looking up only the whole candidate found nothing to follow and
bound neither the link nor the target.

- **Failing-first.** Both shapes returned `[]` where `['stale-red-proof']` was
  required, including a two-deep chain of directory links.

Resolution now walks the path component by component from the repository root and
follows the first link it crosses, which subsumes the file-link case that was fixed
last round: a link at the end is simply the last component. Every link crossed is
bound.

Rewriting the walk lost a behaviour the previous version had, and the existing lock
caught it: a link resolving to nothing returned the link alone instead of failing.
That is fail-open — creating the missing file later would start feeding the read
while binding nothing — so a chain that crosses a link and ends at an absent path is
stale, while a path that was simply never there stays unbound.

- **Whole-repository measurement.** Zero added, zero removed against the previous
  head; no module in this repository reaches its namespace mapping, so the stricter
  rule rejects nothing here. The automated repository measurement passes unchanged.
- **Passing-after:** 273 passed in the provenance file.

## Round 25: one namespace, every door

The third finding on the same rule: `setattr(sys.modules[__name__], "pytest_plugins", ...)`
and `sys.modules[__name__].__dict__` reach the namespace pytest reads without
going through `globals()`. Round 24 made the rule positional — reading one key is
fine, every other use is not — but left the *subject* of that rule narrow, naming
only the mapping returned by `globals()` and `vars()`. A positional rule over an
incomplete subject is still an incomplete rule.

- **Failing-first.** Six of the nine shapes in `MODULE_OBJECT_REWRITE_SHAPES`
  already failed closed, but by accident rather than by rule: they were caught by
  the unrelated `setattr` check or by the `pytest_plugins` attribute-write check.
  Three were not caught at all — a subscript write through the module's `__dict__`,
  handing the module object to a local function, and `exec` against that `__dict__`.

The subject is now the namespace itself, recognized by every door that reaches it:
`globals()`, `vars()`, this module's own entry in the module table by subscript, by
`get`, or through `import_module`, and the `__dict__` of any of them. They are one
object seen from different sides, so one predicate recognizes all of them and every
rule already written applies to each without restatement.

Verified as such rather than by suite outcome: all nine shapes now trip the
predicate directly, so each is rejected by the rule that is supposed to reject it
instead of by a neighbouring check that happened to fire.

The key matters. `sys.modules["tests.substitute"] = ...` is ordinary test practice
and reaches nothing this gate reads, so only an entry keyed by `__name__` denotes
this module. `INERT_MODULE_REFERENCE_SHAPES` locks four such cases —
`logging.getLogger(__name__)`, splitting `__name__`, substituting another module,
and `setattr` on that substitute — alongside a plain `globals()["key"]` read, which
must stay verifiable for the positional rule to mean anything.

- **Whole-repository measurement.** Zero added, zero removed against the previous
  head. No module here reaches its own namespace by any door, so the wider subject
  rejects nothing on this repository; its coverage is the thirteen-shape battery.
- **Passing-after:** 286 passed in the provenance file.

## Round 26: the missing oracle, and the import root it would have caught

### Why findings kept arriving

Every rule in this gate is a hand-derived model of pytest: which files it reads to
decide collection, which directories it puts on `sys.path`, which modules a
declaration pulls in. A model has no error bar. Twenty-odd rounds of findings were
not twenty unrelated bugs; they were one condition — **the only oracle for the
model was review**, and review does not run on every change. Each round fixed the
instance a reviewer happened to read, and the next divergence waited for the next
reader.

`tests/integration/scripts/test_requirements_proof_provenance_against_pytest.py`
supplies the oracle. For seven repository layouts it runs pytest for real, records
every repository-local module the run imports through a plugin loaded from outside
the repository under test, and asserts the gate binds all of them. The layouts
differ in mechanism, not outcome: a bare sibling import, a package-qualified
import, a root conftest chain, a declared plugin importing its own helper, a plugin
behind a configured `pythonpath` root, an import inside a fixture body, and a
package initializer importing at load time.

- **Proof that the oracle fires.** With the import-root fix below reverted, it
  failed on the reported layout **and on a second one the review had not
  mentioned** — the root conftest chain had the same gap — naming
  `tests/helper.py` in both. Restored, all seven pass. An oracle that has never
  failed is not an oracle, so this was run rather than assumed.

This is the under-binding direction. The repository measurement added in round 22
guards over-binding. Together they bound the rule family from both sides without
anyone having to read it.

### Imports through the directory pytest prepends

Review found that a non-package `tests/conftest.py` containing `import helper`
loads `tests/helper.py`, because pytest's default import mode prepends the file's
own base directory to `sys.path`. The gate resolved imports against the repository
root and configured `pythonpath` roots only, so the sibling was never bound.

- **Failing-first.** Four shapes returned `[]` where `['stale-red-proof']` was
  required: `import helper`, `from helper import VALUE`, `import helper.sub`, and
  the same bare import inside the selected test rather than a conftest.

The roots are not a property of the repository, which is what the previous
enumeration assumed. They are a property of each file's position in it: pytest
walks up from the file while each directory is a package and prepends the first one
that is not. That rule is now computed per traversed file.

It is also conditional. `--import-mode=importlib` inserts nothing on `sys.path`, so
a bare name cannot reach a sibling under it, and binding one would reject valid
proofs. The configured mode is read from `addopts` and the directory is used only
when the mode places it there. Two counter-shapes lock this: an `importlib`
repository binds nothing through the sibling route, and a package directory never
becomes a root because pytest walks up past it.

- **Whole-repository measurement.** Zero added, zero removed. This repository
  configures `--import-mode=importlib`, so the new root is correctly withheld here —
  confirmed by reading the mode the gate resolves (`importlib`) alongside the base
  directory it would otherwise use (`tests/unit/scripts`, a real non-package
  directory). The fix is inert here and live for any repository on the default mode.
- **Passing-after:** 292 passed in the provenance file, 7 in the new oracle, 683
  across the scripts, workflows, and integration suites.

## Round 27: closing the oracle's own blind spot

Round 26 added the oracle and recorded three limits of it. One was not a limit but
a hole: the oracle read `sys.modules`, so it saw imports and nothing else. Every
path-resolution rule — the join notations, `__file__`-relative bases, links at any
component — governs files consumed as *data*, which never appear there. The rule
family that had produced the most findings was the one family the new oracle could
not see, and stating that in a docstring does not close it.

The observer now also records reads, through an audit hook on the `open` event
installed before the session begins. Writes are ignored, and `.git`, `__pycache__`,
and `.pytest_cache` are excluded because a run populates those itself and no gate
can bind what is not committed. Six layouts were added, all of them reads rather
than imports: a repository-relative literal, a base relative to the reading module,
a functional join, a read inside a fixture body, a linked file, and a linked
directory.

- **Proof that the read channel is real.** A green suite here could equally mean
  the hook recorded nothing, which is the failure mode this round exists to fix, so
  it was tested rather than assumed. With `_referenced_data_paths` disabled, **all
  six read layouts fail and none of the seven import layouts do** — the two channels
  are independent, and the read channel carries what it claims to. The message for
  the hardest case names `tests/real_data/case.json`, the target resolved through a
  directory link, not the link the source spelled.

The oracle now covers both kinds of input the gate binds. What remains genuinely
outside it is unchanged and worth stating plainly: it observes the layouts it is
given, so a shape nobody has thought of is still unobserved. Adding a layout is now
the cheapest way to close a class, and a layout is four lines.

- **Passing-after:** 13 in the oracle, 689 across the scripts, workflows, and
  integration suites.

## Round 28: three findings, and the check that would have caught one of them

### A mutation receiver read the way an argument already was

`[PLUGINS][0].append("tests.localplugin")` mutates the aliased plugin list, but the rule
matched only a bare `ast.Name` receiver, so the declaration resolved to no plugins.

- **Failing-first, after a false start worth recording.** The first attempt asserted
  through a whole proof and **passed while the defect was present**. The dotted
  literal `"tests.localplugin"` is bound by the dynamic-import rule, so the proof
  came out stale for an unrelated reason. Driving `_pytest_plugin_names` directly
  showed the truth: five of six wrapper shapes resolved to `[]` where
  `stale-red-proof` was required. The lesson is the same one round 25 recorded —
  a green test is not evidence until you know which rule made it green.

The receiver is now read exactly as an argument already was: every name inside it
counts, at any nesting. `_call_argument_names` had carried that reasoning since the
guard work; the receiver simply never received it. A positive control keeps the
widening honest — a declaration no wrapper touches still resolves.

### Every command, not every call site

Round 23 separated "absent" from "could not answer" for path lookups. A **second**
cached command kept the conflation: a failed symlink inventory returned an empty
set, which reads as "this repository has no symlinks", and an import beneath a
linked directory was skipped rather than rejected.

Rather than fix the reported one, every Git result in the module was audited.
`_is_ancestor`, `_changed_paths_in_history` and `_blob_digest_at_ref` already fail
closed. Two did not: the symlink inventory, and `_artifact_is_tracked`, which used
`ls-files --error-unmatch` — an exit code that means both "untracked" and "could not
run", so a timeout read as an untracked artifact and a committed proof would have
been accepted. It now asks for the listing instead, where an answer, an empty
answer, and a failure are three distinct outcomes.

- **Failing-first.** Both sites returned `[]` and `[]` where `['stale-red-proof']`
  and `['prior-red-proof-invalid']` were required.

### An over-strictness this work introduced

Review found that `registry.entries[__name__].touch()` was classified as the module
table purely because the mapping was an attribute and the key was `__name__`, so
every proof in such a repository was rejected. That predicate was written two rounds
ago in this change; the finding is against work done here, not against pytest.

The table is now identified as the table — an attribute named `modules` — rather
than by the shape of the expression around it.

### Making the oracle catch that class

The oracle added in round 26 checks one direction: everything pytest touched must be
bound. This finding was the other direction, and nothing executable covered it for
synthetic shapes. Every layout now also asserts that a production file the run never
opened stays unbound, and three layouts were added whose only purpose is to look
like something the gate rejects while reaching nothing it reads.

- **Proof the new direction fires.** The first version of the inert layout used a
  `Name`-keyed mapping and passed against the restored over-strict predicate —
  the wrong shape, and it proved nothing. Corrected to the attribute-backed form the
  finding names, it fails against that predicate and passes against the fix. The
  check was calibrated against the defect rather than assumed to cover it.

- **Whole-repository measurement.** Zero added, zero removed.
- **Passing-after:** 302 in the provenance file, 16 in the oracle, 702 across the
  scripts, workflows, and integration suites.
