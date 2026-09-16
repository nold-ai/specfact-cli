# TDD evidence

## Evidence scope for prospective re-delivery

The sections below through the round17 receipt describe historical work delivered in PR #729 at commit4181e05aa4827f2957fcc21a41aed38d4077636d. They are retained without claiming protected RED ancestry for that PR. The new branch starts at unchanged public dev45776bf0ee64e0a9cef07ee5d3c324114d8ac44f with tests/OpenSpec only. Its independent prospective proof cycle is recorded after the historical sections.

## Historical TDD evidence

## Readiness and spec-first preparation

On 2026-09-14 Europe/Berlin, core issue #728 was created and verified with native parent #356, owner djm81, bug/documentation/openspec/change-proposal/code-review labels, SpecFact CLI project Todo, and empty blocking/blocked-by lists. Base: 45776bf0ee64e0a9cef07ee5d3c324114d8ac44f. No competing documentation scope was found in core #725/#726.

The dedicated worktree was bootstrapped with frozen `uv sync --locked --all-extras`; offline setup lacked hatchling1.32.0, so the locked online sync completed. Hatch environment setup and smart/contract status preflight completed. Core CLI version remained0.55.4.

OpenSpec requirements were written before tests. `openspec validate docs-16-code-review-runtime-parity --strict` passed.

## RED before production edits

`SPECFACT_MODULES_REPO=<reviewed-module-source> .venv/bin/python -m pytest tests/unit/docs/test_code_review_command_parity.py tests/unit/workflows/test_docs_module_fixture.py -q` reported **3 failed, 1 passed**. The source used for reproduction was the active modules PR474 worktree, not final fixture acceptance. Failures show missing runtime commands/project options and the Docs Review workflow still selecting the Requirements lock. Requirements approved identity regression passes unchanged.

See sanitized `COMMAND_PARITY_RED.txt`. Production/workflow/generated artifacts and candidate fixture identity remain unchanged at this checkpoint. Final signed modules commit/tree and GREEN evidence are pending.

## Internal mirror

A corresponding source page and graph rebuild were prepared in a separate internal worktree for owner review. The original sibling checkout is unchanged; no private wiki text is copied into this repository. Rebuild produced broader graph changes from its existing baseline; those require owner review before any internal publication.

Additional workflow-shell RED before production changes: 3 failed / 5 passed. Executing the existing read/verify steps against real local Git fixtures showed a mismatched tree and dirty source accepted; repository, mutable-ref, and commit mismatch checks already rejected correctly. See DOCS_FIXTURE_RED.txt. Clean immutable source is part of the recorded design; this strengthens the docs-only adoption boundary.

Root inspection found CLI Command Validation also runs generated documentation checks against the shared older execution fixture. Before extending that one job, a spec scenario and RED regression were added: 3 failed / 7 passed. See DOCS_CONTEXT_RED.txt. Scope is limited to the cli-validation job, explicit docs-context tests, and Docs Review; all other orchestrator jobs remain unchanged.

## Generator argument and local source separation

The first canonical regeneration exposed an additional real mismatch: core omitted the review `FILES` positional argument. Existing Click and Typer arguments have an `opts` attribute, so the old attribute-absence check discarded them. After adding the positional-metadata scenario, four Click/Typer required/optional/variadic regression cases failed with empty argument metadata before the generator change (`ARGUMENT_METADATA_RED.txt`). Explicit parameter classes now preserve display name, arity and required status; canonical regeneration also restores positional arguments for other existing commands.

Canonical commit hooks regenerate documentation and execute Requirements evidence within one shell. A separate documented generator context is therefore necessary: after the local-source scenario, precedence and invalid-context tests produced **4 failed, 1 passed, 1 context skip** (`DOCS_SOURCE_RED.txt`). The generator now uses `SPECFACT_DOCS_MODULES_REPO` exclusively when explicitly provided and rejects empty/unavailable sources. Ordinary callers retain prior discovery. Only the generator child process updates its module-source environment; the Requirements fixture and authority are unchanged.

Independent review reproduced the older Docs Review workflow test's shared-lock assertion (`EXISTING_WORKFLOW_RED.txt`). Its existing trust helper now accepts an explicit expected fixture for Docs Review while preserving the approved default for standalone contract execution and all other trust assertions.

## Reviewed immutable input and current GREEN

The docs-only fixture selects modules commit `1d6f035c42fbfadf0d853eabd7f90315b7b36278`, tree `ee18bcef1378575b6fec14536f957e2d8d25e82c`. The parent delivery task independently verified all seven signatures with the publisher public key. Code Review version is `0.50.0`, payload checksum `sha256:3bc137548254eaa4093b1be9427089142acc6fc1bcfd356b555ff01fd37c6500`. This is a signed candidate source identity, not a public registry acceptance claim. A private clean detached checkout preserves this input while subsequent module implementation continues.

On 2026-09-14 Europe/Berlin, Python 3.13.14 validation of `tests/unit/docs`, `tests/unit/workflows`, and `tests/unit/scripts/test_reproducible_delivery.py` reported **213 passed, 1 skipped in 12.78 seconds**. The skip is an existing opt-in live HTTP handoff URL check. All substantive parity and fixture checks executed. Independent review additionally passed all 58 existing trustworthy-green workflow tests and the 33 focused changed-scope tests, reporting no remaining actionable findings.

Canonical generator `--check`, command contract (**117 command paths**), docs command examples (**393 unique prefixes**), documentation accountability, enforced frontmatter, agent-rule signals, format and lint passed. The BasedPyright authority check analyzed 663 files with **0 errors**; its existing 1,532 advisory warnings remain visible in the full JSON. Frozen delivery verification passed with unchanged lock/export inputs, and workflow actionlint passed.

The repository YAML wrapper exited zero but printed pre-existing non-workflow YAML errors in unchanged `requirements-07-runtime-proof-delivery` and archived `requirements-08` files; this is not a claim that all existing YAML is clean. Contract auto selected no modified runtime source files and performed no new contract exploration. The initial smart run could not initialize the default host UV/Hatch cache; a retry uses isolated temporary caches and the supported Python 3.13 test environment. The supported private-cache retry passed; final results are recorded below.

The isolated internal mirror was updated for the generator and source-context scope and rebuilt through its canonical script. A clean module checkout with the canonical directory name corrected path-derived repository labels; its graph still reflects pre-existing baseline task-count changes. Internal publication remains separately reviewed. No wiki bodies are included here.

## Final scoped gates and review dispositions

`HATCH_TEST_ENV=py3.13 hatch run smart-test` completed its configured full-suite policy run with **3,153 passed, 10 skipped, 2 existing lark deprecation warnings in 207.25 seconds**, exit 0. This describes the repository's selected Hatch suite, not every optional matrix or external integration. Reported source/tool coverage was 64%. No application behavior was added and contract auto correctly selected no changed runtime source files. After advisory cleanup (type annotations and non-nested equivalent fixture setup), affected docs/workflow/reproducibility tests passed again: **213 passed, 1 opt-in HTTP skip in 17.07 seconds**. Final canonical format and lint passed.

The schema-2 Requirements sidecar maps three requirements to eight verification cases. The canonical staged gate against the unchanged approved execution fixture `69f075819be5e1ceca1446b026b0417f19e584ca` passed at **planned** maturity. That is plan completeness, not stakeholder acceptance or protected delivery proof. The documentation fixture is separate and the same shell can run generator freshness and Requirements validation without changing execution authority.

Fresh staged-file SpecFact review used `code review run --bug-hunt --json --out .specfact/code-review.json` and the approved execution fixture. At **2026-09-14T21:15:11.657550Z** it reported **PASS_WITH_ADVISORY, 0 errors, 5 warnings**. Semgrep's initial empty-trust-store tool errors were resolved by selecting the environment's certifi trust bundle; no analyzer was skipped. New nesting and type-inference advisories were fixed and the review repeated.

The following exact unchanged findings are explicitly dispositioned for this documentation scope; no rule suppression or broad waiver was added. Each named declaration is present unchanged in core base `45776bf0ee64e0a9cef07ee5d3c324114d8ac44f`:

- `MISSING_ICONTRACT` on generator `build_records` and `main`: unchanged CLI-script entry boundaries, with output contracts covered by generated parity/freshness and focused tests. Adding a new runtime contract dependency or altering unrelated CLI entry behavior is outside this change. The parent Codex review task accepted this narrow legacy boundary exception.
- `banned-generic-public-names` on `test_primary_test_process_does_not_inherit_github_base_ref`, `test_compatibility_test_process_does_not_inherit_github_base_ref`, and `test_only_test_processes_override_github_base_ref`: false positives on the substring `process` in precise pytest launcher-test names, not generic production APIs. The parent Codex review task accepted retaining these unchanged trust-test names.

Independent Semgrep OSS SAST completed six rules on 299 tracked targets with zero findings; its accepted-baseline gate passed. The independent Bandit `-r src/ -ll` gate passed with no medium/high findings. Changed YAML (both workflows and the new sidecar) passes direct yamllint; the unrelated pre-existing YAML defects noted above remain visible. Signature/public registry acceptance is owned by the modules release task, and the final documentation fixture identity will be refreshed if that task receives another signed candidate.

## Final signed source refresh and live validator boundary

The final documentation source was refreshed to signed modules commit `1ac16e237b5f155962d602b488e4a5e8fa2f3c94`, tree `123472110299f01947b659f6b441b6add774d793`, authored predecessor `17ba3078`, Code Review `0.50.0`, payload checksum `sha256:6a1f342d9da63a39761f44616fa1fd679cd46ad4443386be1f70d7c5ab544bab`. Canonical publisher-key verification independently passed all seven manifests; the bot added only the signature. Both private documentation clones are clean at the supplied identity. The Git source signature remains distinct from public registry installation acceptance.

Canonical regeneration produced no changes to the already-staged JSON/Markdown/llms artifacts after this worker-only module update. Initial final-pin focused checks passed **91 tests in 6.28 seconds**. Running the complete canonical documentation checks with separate source variables exposed a remaining boundary: the live `check-command-contract.py` validator still selected the older execution fixture and rejected the three runtime command paths. The local-context scenario was clarified to include live validation before extending tests. Its four explicit-source/invalid-source cases failed while the generic fallback case passed (`CONTRACT_DOCS_SOURCE_RED.txt`).

The live documentation validator now honors the same explicit documentation source and rejects empty/unavailable choices; ordinary caller discovery and Requirements execution authority stay unchanged. After implementation, **218 affected docs/workflow/reproducibility tests passed, 1 existing opt-in HTTP check skipped, in 9.53 seconds**. The separate-source shell passes generator freshness, all **117 command paths**, and **393 documented command prefixes**. Final canonical format and lint passed. This bounded documentation-loader change required affected validation; the earlier configured full-suite result is retained with its original scope and input.

The canonical modular pre-commit hook is installed in the private Git common directory. No commit or push has been made by the delegated documentation task. The private wiki mirror and its canonical graph were refreshed for the final signed source and live-validator scope.

Final live-validator advisory remediation extracted source selection from import-path setup and added a verified JSON dictionary type annotation. The repeated affected suite passed **218 tests with 1 opt-in HTTP skip in 10.00 seconds**; canonical format/lint and all 117 live command paths passed. Fresh review at **2026-09-14T21:31:59.493916Z** reports **PASS_WITH_ADVISORY, 0 errors, 6 warnings**. No introduced complexity/type/nesting findings remain.

The six remaining warnings are the five exact dispositions above plus `MISSING_ICONTRACT` on the unchanged `scripts/check-command-contract.py` `main` CLI-script boundary. The parent Codex review task accepted the same narrow legacy entry-boundary exception. AST comparison against core base `45776bf0ee64e0a9cef07ee5d3c324114d8ac44f` confirms all three CLI declarations/bodies and all three precisely named pytest functions are unchanged. Existing and focused live-command tests validate the entry boundary and source-selection behavior; no broad suppression was added.

## Canonical test-authored planning and execution receipt

The first canonical commit attempt stopped before creating a commit because scripts/CI changes require **test-authored** planning and the review record was absent. The earlier planned result above was insufficient. The evidence correction preserves the approved execution fixture and does not change hook, executor, or workflow authority.

The generated-parity specification now also requires self-contained comparator fault tests for the Requirements executor, which intentionally does not inherit `SPECFACT_DOCS_MODULES_REPO`. A controlled generated contract with the runtime option removed failed the existing parity comparison (`PARITY_PROOF_RED.txt`). Four new cases exercise the actual comparator with positive controls and independent path, option, argument and subgroup mutations. Live signed-source parity remains mandatory in the separate documentation jobs.

The sidecar's three requirements now enumerate **32 unique exact pytest selectors**, expanding the earlier eight semantic case groups into collected parameter instances. Workflow context cases use stable selector-safe IDs. All 32 executed independently without the documentation environment variable: **32 passed, zero skips in 1.75 seconds**. The updated parity/fixture suite passed **38 tests in 1.71 seconds**.

Independent AI reviewer `Codex:/root/review_core_docs` accepted only the mapping and test design, after independently recomputing source mapping digest `sha256:39345cbeb452dae3587ecba1d2d5c2d0bbd83dd0bd1606ec9ee28360777c9e87`. The factual [AI review ledger](https://github.com/nold-ai/specfact-cli/issues/728#issuecomment-5671231444), recorded at `2026-09-14T21:44:40Z`, is bound by `requirements-proof/review-evidence.json`. This is neither human/stakeholder acceptance nor protected RED, verified execution, or public release acceptance.

The canonical staged command passed with no findings:

```sh
hatch run python scripts/requirements_evidence_delivery_gate.py \
  --repo-root . --staged --required-maturity test-authored \
  --output /private/tmp/specfact-473-core-docs-test-authored.json \
  --summary /private/tmp/specfact-473-core-docs-test-authored.md \
  --review-evidence openspec/changes/docs-16-code-review-runtime-parity/requirements-proof/review-evidence.json \
  --plan-output /private/tmp/specfact-473-core-docs-executable-plan.json
hatch run python scripts/requirements_proof_executor.py \
  --plan /private/tmp/specfact-473-core-docs-executable-plan.json \
  --repo-root . --junit /private/tmp/specfact-473-core-docs-executor-junit.xml
```

The actual canonical executor passed **32 tests, zero skips in 1.56 seconds**, on macOS with Python **3.12.13** and pytest **9.1.1**. Its JUnit contains exactly one result for each declared selector and the recorded interpreter/tool properties. Its **32 existing `record_property`/`xunit2` compatibility warnings remain visible**; this is not a zero-warning run. The aggregate executable mapping digest is `sha256:cf5e54f5ac5b443f3434685fd6818eb8a51642638da73d17ebe7cfdb4c405e27`, and plan digest is `sha256:4ccbfe56599656a3ef8f914d3e1e0c08e32ba8da3918ecdfaad2eb8ab4396f09`. These differ from the source mapping digest because the delivery gate composes source-qualified cases.

Fresh staged SpecFact review at **2026-09-14T21:43:54.226605Z** reports **PASS_WITH_ADVISORY, zero errors, the same six explicitly approved unchanged warnings**. No new warning exception or suppression was introduced.

### Protected verification remains outstanding

The unchanged Requirements workflow selects `verified` maturity for changes under `.github`, `ci`, or `scripts`. After successful test-authored planning it executes this plan and reconciles final results. The pinned validator emits `prior-red-proof-missing` when final execution has neither a matching retained RED proof nor explicitly authorized legacy evidence. This is an anticipated policy result from inspecting the workflow and validator, not a claim that public CI has already run.

The ordinary retained-RED route searches failed earlier pull-request runs on the same branch, verifies source ancestry between the current base and head, and validates the retained report/JUnit provenance. The current change has no such protected RED artifact. Raw local failing-before transcripts and the AI test-design ledger do not substitute for it, and several preservation cases already passed before implementation; no all-32-failed claim is made. Existing late-RED and legacy bootstrap routes are bound to other named changes/PR identities and cannot be reused for this change. A separate authentic, policy-supported proof cycle or separately governed bounded authority change is still required before protected verified acceptance. This documentation patch does not change that authority.

## Round 17 signed documentation source refresh

The documentation fixture now selects signed modules commit `2e095f1350fecb7e7eda0bcfba6bad89a6d82c88`, tree `8846ce1b47538ea78d600b7c82bfd2ccd1761ee2`, authored predecessor `e703ea827887a384d847f16c98c950ada204962c`, Code Review `0.50.0`, payload checksum `sha256:8c9304e96f9c8a4c2a7b54988e2f6c67336a59af46d32be252c737e497d5ca97`. The parent Codex task independently verified all seven manifests with the public publisher key and verified that the bot added only the signature. Both isolated documentation clones are clean at this identity. Prior receipts above retain their original source identities. The approved Requirements execution fixture remains `69f075819be5e1ceca1446b026b0417f19e584ca`.

Canonical regeneration after this worker-only update produced no change to the staged generated JSON, Markdown or llms artifacts. Generator freshness, all 117 live command paths, and all 393 documented prefixes passed. The final source-specific parity/freshness/fixture/trust-workflow selection passed **100 tests in 5.29 seconds**. Strict OpenSpec and the unchanged source-mapping test-authored gate were rerun for this exact documentation identity. No protected verified or public registry acceptance is inferred.

## Prospective test-only cycle at unchanged public dev

On 2026-09-15 Europe/Berlin, branch `codex/docs-code-review-runtime-parity-tdd` was prepared at public dev `45776bf0ee64e0a9cef07ee5d3c324114d8ac44f`. Only OpenSpec and test files are included in its first phase. Original PR #729 and its combined implementation commit remain unchanged. No implementation, workflow, docs-lock, generated command artifact, package constraint or policy file is changed in this phase.

The new plan maps four requirements to **38 exact regression selectors**: 22 direct documentation/generator/source-context regressions and 16 source-authentication regressions. All positive, unchanged-invariant, existing-rejection and parity fault-injection tests remain mandatory CI controls outside the failing-first map. The specification explicitly distinguishes these controls; none is relabeled as failing evidence. A missing documentation gate now has a direct presence assertion, replacing an incidental StopIteration diagnostic before freezing the new cycle's tests.

The finalized authentication tests were copied after independent review and type cleanup, SHA256 `6570d5d06898dd5a15ca50e6e2625f6668a67799d062d03374481371e6aeeb64`. The prospective source mapping digest is `sha256:7413ce0bbfd53f62a4f5467cd6856751266327a596f322cec2ab4ec6f0b08699`, computed by the unchanged approved Requirements lifecycle. Historical mapping approval does not apply to this new digest.

Actual local execution on this test-only checkout selected all 38 node IDs using pytest plus the unchanged `scripts.requirements_proof_pytest_plugin` and emitted `/private/tmp/specfact-473-core-tdd-red-final.xml`. It produced **38 failed, zero errors, zero skips, 38 existing record_property/xunit2 warnings in 2.67 seconds**, Python **3.13.14**, pytest **9.1.1**, exit 1. XML validation confirmed exactly one failure for every declared selector, no duplicate or missing outcomes; local JUnit SHA256 is `62a50a39ef6fec7a15047f70e49151a5db43a327ea97be096f11f4c212b13217`. Full output is retained in `FORWARD_RED.txt`. This is authentic local failing-before execution against unchanged dev implementation, not a protected retained CI artifact or a claim about PR729 history.

Command shape (the exact 38 selectors are enumerated in requirements-evidence.yaml):

```sh
python -m pytest -q -o addopts= -p no:cacheprovider \
  -p scripts.requirements_proof_pytest_plugin \
  --junitxml=/private/tmp/specfact-473-core-tdd-red-final.xml <exact-mapped-node-ids>
```

All five copied/updated test files pass Ruff formatting and lint checks. Strict OpenSpec validates the prospective scope. Independent mapping review and normal test-authored planning are requested before the first commit; protected workflow must retain valid RED proof before the implementation phase begins.

Independent reviewer `Codex:/root/review_core_docs` accepted this prospective mapping/test design only, independently recomputed digest `sha256:7413ce0bbfd53f62a4f5467cd6856751266327a596f322cec2ab4ec6f0b08699`, and independently executed all 38 selectors against the test-only checkout with documentation context removed: 38 failures, zero errors/skips. The [new factual AI review ledger](https://github.com/nold-ai/specfact-cli/issues/728#issuecomment-5671650936), created at `2026-09-14T22:25:58Z`, is bound by the new review-evidence.json. This accepts local prospective test design; it does not certify retained CI RED or implementation acceptance.

Canonical staged `requirements_evidence_delivery_gate.py --staged --required-maturity test-authored --review-evidence ... --plan-output ...` passed for the unchanged reviewed digest. The new worktree's canonical Hatch environment required standard dependency initialization; its initial restricted-network attempt failed, then authorized normal acquisition succeeded without changing package constraints or locks. The actual canonical `requirements_proof_executor.py` then produced **38 failed, zero errors/skips, 38 existing JUnit compatibility warnings in 2.74 seconds**, Python **3.12.13**, pytest **9.1.1**. Its private `/private/tmp/specfact-473-core-tdd-executor-red.xml` contains exactly one failed outcome for each selected node. This remains local evidence pending the first committed source and normal protected CI artifact.

Fresh staged SpecFact review at `2026-09-14T22:26:18.022030Z` reports **PASS_WITH_ADVISORY, zero errors, three warnings**. These are the same three unchanged `banned-generic-public-names` findings on precise pytest launcher-test names, previously explicitly accepted by the parent Codex review task and justified above; no new exception is requested. All five changed test files pass Ruff formatting/lint. Strict OpenSpec, direct configured sidecar YAML validation and cached diff checks pass. No production changes are staged; selected test files and semantic mapping are frozen for the prospective cycle.

## Authenticated CI RED and prospective implementation

On 2026-09-15 Europe/Berlin, signed tests/OpenSpec-only commit `e2c21f3471d616b7867b881fff0865a2bcd8ba7e` was published in PR #730. Its direct parent remains unchanged public dev `45776bf0ee64e0a9cef07ee5d3c324114d8ac44f`. Canonical hooks passed after correcting one duplicate Markdown heading; tests and mapping were unchanged.

Requirements run `34904539320` retained artifact `10371697122` (`requirements-evidence`, provider digest `sha256:2f13a6458a2be41c48be4a83e7d4afa6cd5d161d30d1ccdea5e7c83c216b175c`). The report has `gate_decision: pass`, `observed_maturity: red`, `delivery_status: failing-first-proven`, and no findings. All 38 unique selected cases failed during test calls, with zero errors/skips. JUnit SHA256 is `31aff9fe8cd3dc6fc259dc3e5dcda82934c1db413e223c039036fe84e148fc5b`. Independent AI review checked exact selectors, committed test hashes, source/tree, direct base ancestry, and absence of governed implementation paths. The root task independently checked the report and all 38 JUnit failures. Workflow failure at this checkpoint is intentional pending final reconciliation.

Only after that retained receipt was verified and current public dev rechecked, the reviewed implementation donor was applied to this forward branch. The donor adds strict publisher signature and filesystem payload verification before documentation CI exports module imports, using the canonical verifier/key from a separate immutable core base checkout. The documentation source remains signed modules `2e095f1350fecb7e7eda0bcfba6bad89a6d82c88`; Requirements execution authority remains unchanged. Frozen regression files and the accepted 38-case mapping were not modified. Complete GREEN validation and protected final reconciliation remain pending.

Prospective GREEN: the combined focused suite passed 118 tests. The configured full smart-test policy passed 3,181 tests with 9 skips and two existing lark deprecations in 149.07 seconds. Initial isolated environment setup was blocked by sandbox DNS before tests ran; the ordinary network-enabled initialization and rerun succeeded. Formatting, canonical lint/type checks, docs freshness (117 command paths / 393 documentation prefixes), actionlint, strict OpenSpec and frozen delivery passed. Full type diagnostics show zero errors and no diagnostics on changed scripts/tests; 1,526 baseline advisories remain visible. Strict trusted-base publisher verification passed all seven signed documentation bundles. Explicit YAML checking outside configured ignores finds only two unchanged historical trailing-space lines; no new YAML diagnostic is hidden. Frozen test files and accepted mapping remain byte-identical to the retained RED commit. Fresh review and protected final CI reconciliation are still required.

Fresh branch-wide SpecFact review with `--bug-hunt` at `2026-09-14T22:43:14.652766Z` reports zero errors and the six exact previously documented advisories (three unchanged precise test names and three unchanged legacy generator/validator entry points). The new wrapper logging advisory was fixed using the standard logger; all 18 authentication tests passed again in 4.52 seconds, and Ruff/format checks passed. Independent Semgrep scanned 300 targets with zero findings and a passing baseline gate; Bandit found no medium/high issues. Targeted Semgrep/Bandit reruns after the logging change also returned zero findings/errors. No selected test or mapping changed. These local gates do not replace protected final CI reconciliation against the retained RED artifact.
