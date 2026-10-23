# PR785 probe TDD evidence

## Prepared tree correction failing-before evidence

Recorded 23 October 2026, Europe/Berlin. This test-only unit starts from auxiliary HEAD `a8323345ff3dce8cfe456f84ede211d9cf3bf34d`. Runtime remains unchanged at SHA-256 `77c290d1a7326f89df49980ef217f66f99d84fd84cb1146331d55945b42f24f7`. The accepted root design records that actual run 39927910182, artifact 12489599286, verified its baseline and refused POST trees with HTTP 403. The exact permission predicate is unknown. All three earlier partial runs remain refused and unadopted, with no accepted anchors.

The revised contract gives preparation ownership to root. CI must validate the pinned root and linked `.github` and `workflows` trees before either commit. Each nonrecursive response must have the exact SHA, explicit boolean false truncation, unique correctly typed direct entries, linked child identities and the inert `100644` blob derived from the actual manifest bytes. CI may POST commits only. CLI inputs, receipt schema, distinct service roles, signature checks, safe diagnostics and ref/context guards remain unchanged.

All 93 original case IDs remain. Of their selectors, 92 remain exact. Case `PR785-PROBE-054` replaces the obsolete third-write selector with drift after prepared-tree reads before either commit. Exactly four original mapping case objects change. Cases 002, 051, 054 and 068 now describe commit-only writes, prepared-root mismatch, the replaced drift boundary and second-commit refusal. The existing second-write drift selector now applies to the second commit instead of a removed tree POST. Both existing late HTTP refusal controls inject at the second commit and preserve every original receipt, raw JSON, identity and sanitized stderr assertion. The fixture still serves the old valid tree POST so the old implementation reaches real behavioral assertions. All unrelated test functions and service identity fixtures remain unchanged. Private `conservation.json` records exact old/new case objects and the bounded fixture/assertion changes.

The suite now has 170 exact native-mapped selectors. Its 77 added controls include 57 prepared-data faults across three levels, pinned and forbidden transport routes, arbitrary CLI input refusal, unavailable-tree CLI receipts, a complete same-run pair, a read-only Git blob oracle and a typed-manifest content mutation. The mutation changes only `Manifest.probe_content` after loading the pinned manifest, leaves prepared responses original and requires refusal before either commit. It proves byte derivation behavior. The canonical oracle runs `git hash-object --stdin` without `-w`, under root's bounded read-only authorization. Private conservation separately recomputes the pure Git blob hash. No object, index or ref is written by that calculation.

The existing Python environment ran this exact command against the unchanged runtime:

```sh
python -B -m pytest tests/unit/scripts/test_pr785_signing_recovery.py -q --no-cov -o addopts= -p no:cacheprovider --junitxml=/private/tmp/specfact-release-20261022/signing-recovery/prepared-tree-correction/red-final.xml --basetemp=/private/tmp/specfact-release-20261022/signing-recovery/prepared-tree-correction/pytest-final
```

Exit 1. Actual JUnit reports 170 tests, 70 failures, 100 passes, zero errors and zero skips. Decisive failures include `'/git/trees' != '/git/commits'`, `DID NOT RAISE ProbeRefusalError` for prepared-data faults and manifest-content mismatch, `Pinned prepared tree GET was refused: Forbidden API route`, and `assert 0 == 1` when the CLI wrongly completes despite unavailable prepared data. The late-refusal controls report `assert 2 == 1` because the old runtime still performs the prohibited tree write. Every failure is a behavioral assertion or the actual policy refusal of a required route. There are no absent-module, import, setup or collection failures. Test SHA-256 is `b10822edbdcb007902937cb4754759165d9f843b72d99e02c7aaf4e12ab0a3a7`.

The real native importer and lifecycle evaluator return planned/pass with eight unchanged native requirement IDs, all selectors present, and no findings. Canonical mapping digest is `sha256:be6a74c5a802494546f51c96bd7605aa00f2506bc67825b49f44c38f6880f08a`. This direct source-bound check does not claim independent acceptance, a staged gate or a refreshed receipt. The old active receipt is preserved privately and removed from its active pointer. Root owns the fresh exact-mapping review receipt after independent test acceptance.

Scoped lint/types report zero errors, warnings and notes. Actual SpecFact CodeReview reports PASS with no findings. Independent SAST executes all six configured rules with no findings or errors. Bandit has no blocking medium/high findings. Scoped YAML and strict OpenSpec pass. Private snapshot diff checks reject added trailing whitespace and conflict markers without touching Git or the index. Initial helper complexity warnings were resolved. The redundant direct SHA-1 oracle triggered the generic weak-hash rule; the final test uses Git's canonical read-only object calculation, with the behavioral content-mutation control retained and no suppression or scanner change. Existing certifi trust remains enabled. No package installation occurred. Inherited full-project 1449 type warnings and 30 YAML errors were not rerun or declared clean.

Manifest, workflow, inert bytes, bootstrap lock, original dependency inputs, module fixture lock and runtime hashes are conserved. Root separately owns the preparation operation and its denial, uncertainty and postguard tests. This CI test unit does not claim that operation is implemented or proven. Runtime authorization remains closed until fresh independent test acceptance, the actual staged test-authored gate and a normal test-first commit. The absent auxiliary wiki source remains a follow-up; the approved release-page and graph update is complete and this unit does not create a new sibling page.

Raw commands, logs, exact native report, JUnit, conservation and frozen hashes remain in `/private/tmp/specfact-release-20261022/signing-recovery/prepared-tree-correction/`. No runtime edit, index operation, commit, ref mutation, API request, dispatch, signing or merge occurred. A fresh complete actual same-run pair, both immutable root anchors, signed-prefix native 33-case RED and every later recovery/CI/forge READY gate remain mandatory.

## Safe refusal diagnostics passing-after evidence

Recorded 23 October 2026, Europe/Berlin. Normal test-first commit `26764ce44b305d4edb1810769341fcd38c0b3c57` passed the actual staged test-authored gate and every normal hook before root opened runtime authority. The unchanged runtime produced three meaningful empty-stderr failures while all 90 original controls passed. That genuine RED and its independent reproduction remain retained below.

The catch-only runtime correction has SHA-256 `77c290d1a7326f89df49980ef217f66f99d84fd84cb1146331d55945b42f24f7`. Test SHA-256 remains `879533ee4ff8762f1575313d99bc3267ea20eea15b1a4cd82e676f68a5c1b4af`, and canonical mapping remains `sha256:8998713988ae1df90f45940f48527a12e6196a5b0ace58e8d3f55f8fbc9fc4e4`. Both the writer and fresh independent reviewer executed the exact 93-case suite with zero failures, errors or skips. The genuine runtime acceptance is `requirements-proof/diagnostic-runtime-review.md`. Separate comment review found no changed comments or required removals.

The main handler writes only the already sanitized program-authored policy reason to stderr, or the exact generic local I/O message. Its initial print-based version triggered two CodeReview warnings; direct stderr writes resolved both without a waiver. Actual final CodeReview has zero findings at every severity. Focused lint/types, configured six-rule independent SAST, Bandit, scoped YAML/OpenSpec and whitespace checks pass. The optional local Semgrep version notification was disabled with all analysis rules and TLS verification retained. Inherited broad type and YAML debt remains unresolved.

Restoring only the old main handlers makes the complete module AST equal to the pre-fix source. All other 2,444 indexed files and the index were unchanged during implementation. Accepted tests/spec/mapping, workflow, manifest, inert bytes, locks, receipt schema and every signature, identity, context, ref and transport guard are conserved. Root directly checked the actual RED/GREEN XML, final CodeReview and frozen source hashes.

The external tree-request refusal remains unknown. Both prior CI probes stay refused and partial, with no accepted anchors. This diagnostic fix establishes no complete live probe, signing recovery, native release RED, final authority or readiness. Root owns the normal fix commit, exact executor and remote byte review, and a fresh actual CI diagnostic probe. The approved release wiki patch and graph rebuild are complete. The auxiliary matching source is absent; its follow-up remains recorded without expanding that narrow grant.

## Safe refusal diagnostics failing-before evidence

Recorded 23 October 2026, Europe/Berlin. This test-only correction starts at HEAD `54e8ee9bc807fda92981667aab28ccbebeeb5d0d`. Runtime remains byte-identical with SHA-256 `416d507c43d34a0b8d6d793070f4849b676f3eeb961535ec8a5d9b7be8146358`. The authenticated corrected live probe retained one verified baseline object and then refused its tree request. Its actual refusal reason remains unknown because the current CLI discards the already sanitized policy exception text. The synthetic 403 fixture below does not establish the live HTTP status or permission cause.

The existing Signing refusal requirement now specifies safe stderr diagnostics and the fixed `Probe refused: Local I/O failure` message for caught local I/O errors. The eight Requirement and Scenario names stay unchanged. All 90 prior mapping case objects remain semantically identical. The entire prior test file remains an exact byte prefix of the extended file. Three new controls call the actual `main` entrypoint and retain the original transport fixture. They cover the sanitized HTTP status, early context policy refusal and a raw-response write `OSError` containing arbitrary body and credential markers. Receipt schema and runtime guards remain unchanged.

The configured Python 3.12 environment ran the complete focused suite with this exact command:

```sh
.venv/bin/python -B -m pytest tests/unit/scripts/test_pr785_signing_recovery.py -q --no-cov -o addopts= --junitxml=/private/tmp/specfact-release-20261022/signing-recovery/probe-refusal-diagnostics/red.xml --basetemp=/private/tmp/specfact-release-20261022/signing-recovery/probe-refusal-diagnostics/pytest-temp
```

The run exits 1 with 93 tests, 3 failures, 90 passes, zero errors and zero skips. Each new test reaches its final diagnostic assertion after checking refusal status, retained evidence and absence of sensitive output. The decisive failure text is:

```text
assert 'API refused HTTP 403' in ''
assert 'Execution context mismatch' in ''
assert '' == 'Probe refused: Local I/O failure\n'
```

The failures belong to `test_cli_reports_sanitized_http_refusal`, `test_cli_reports_context_policy_refusal` and `test_cli_reports_generic_local_io_failure`. No import, setup or collection failure is counted as RED. Collection independently returns all 93 exact mapped selectors. The final test SHA-256 is `879533ee4ff8762f1575313d99bc3267ea20eea15b1a4cd82e676f68a5c1b4af`.

The locked actual Requirements fixture is verified by `verify_fixture`; its native source importer and lifecycle evaluator return planned/pass with no findings. The canonical mapping digest is `sha256:8998713988ae1df90f45940f48527a12e6196a5b0ace58e8d3f55f8fbc9fc4e4`. This is a source-bound planned check, not independent acceptance or the staged test-authored gate. The previous active review receipt was preserved privately as `prior-active-receipt.json` and removed from the active location because it binds the previous mapping. No new acceptance is asserted.

Scoped lint and type checks report zero errors, warnings and notes. Actual SpecFact CodeReview reports PASS with no findings after simplifying the new local I/O assertion. The first review invocation lacked the existing fixture roots; the retry used the configured installed fixture without installation. Its intermediate complexity warning is retained privately and resolved in the final bytes. Scoped YAML, strict OpenSpec, Bandit and final whitespace checks pass. Independent SAST executes all six configured rules on the test file and exits zero with no findings or errors. Broad inherited type warnings and YAML failures remain outside this focused check and are not waived or claimed clean.

Raw commands, logs, JUnit, conservation checks, native mapping, quality outputs and hashes remain under `/private/tmp/specfact-release-20261022/signing-recovery/probe-refusal-diagnostics/`. No runtime, workflow, manifest, lock, Git index, ref, signing or dispatch change occurred. Root owns fresh independent acceptance, the review receipt, actual staged gate, normal test-first commit and internal wiki follow-up before any runtime handoff. The separate release signed-prefix native 33-case RED and complete live probe authentication remain mandatory.

## Exact service role correction passing-after evidence

Recorded 23 October 2026, Europe/Berlin. Root normally committed the independently accepted test/spec package at `958a23567fbec4ea06caa9474a8378afd6c057a5` before authorizing runtime edits. Both genuine former positive failures are retained below and were independently reproduced against unchanged runtime `38456f44`. The implementation changes only the exact role model in three existing verification functions. A frozen identity record binds the Actions bot author and GitHub web-flow committer separately. All 52 other existing top-level AST nodes and every nonidentity guard are conserved.

Runtime SHA-256 is `416d507c43d34a0b8d6d793070f4849b676f3eeb961535ec8a5d9b7be8146358`. Test SHA-256 remains `a71283b3ec1447777f8365bb1d560c441f48fa80312f0f8a4eaf2211ee241c93`. Canonical mapping remains `sha256:f686345a624d61150d5fd2901ea0b6e567795a21d8e7b7d4a6eb6379c89dca27`. The exact full focused command executed all 90 cases with zero failures, errors and skips. Fresh independent runtime review repeated all 90 cases and accepted the frozen correction with no findings. Its report is `requirements-proof/service-identity-runtime-review.md`. A separate comment review found no changes required.

Focused lint/type checks report zero errors, warnings and notes. Actual SpecFact CodeReview reports PASS with zero findings of any severity. The configured six-rule independent SAST, Bandit, scoped YAML, actionlint, strict OpenSpec and whitespace checks pass. Root checked every retained implementation evidence hash. Full inherited type/YAML debt remains unresolved and is not called clean. Existing bootstrap, dependency inputs, workflow and manifest bytes are unchanged.

The retained authentic create response and separate Git/attribution readbacks now pass the corrected verifier locally. This is a replay only. Actual first run39918437102 remains refused and partial, with zero accepted objects and both anchor flags false. This note does not claim a new complete live probe, root anchors, signed release history, native 33-case RED, final authority, merge readiness or publication. Root owns the normal production commit and a fresh CI probe at its independently reviewed executor.

## Exact service role correction failing-before evidence

Recorded 23 October 2026, Europe/Berlin. Root authenticated actual run 39918437102, attempt 1, at auxiliary executor `d30507854113fa42af86fd2db82a3a0554121cfb`. Artifact 12486046412 has ZIP SHA-256 `ecbe22efd7429db12d9a00dfdf0753a0200da42117d7170f293553f97e0bd55c`. Its raw response 0004 created GitHub-verified commit `192a8db76d7356e7ccae1788ed86604154174786`, with reason `valid`, a signature and the exact role-specific payload. The author is the Actions bot. The committer is GitHub, attributed to `web-flow`. Root retained independent Git and commit-attribution readbacks. The actual old runtime refused that valid baseline because it required the Actions bot in both roles. The receipt has zero accepted objects and both anchor flags false. No complete probe or release acceptance is inferred from this partial run.

The existing eight native Requirement and Scenario names remain unchanged. The spec now states both exact identities. The test fixture reflects the authenticated role values. All original 68 case IDs, selectors, case objects, test bodies, decorators and assertions are conserved. Twenty-two new negative controls substitute the opposite role value in each name or email field in create metadata, readback metadata and both signed payloads, and in each login, ID or type field in service attribution. The new controls are authored and collected. Their future passing run must accompany both positive cases after the runtime correction.

The unchanged runtime SHA-256 is `38456f4429f5e3b4a68f82307dcfce2c1b74cd94063b2da1af198058db93d7f3`. The following exact command ran against that module after the spec and test edits, before any runtime edit.

```sh
python -B -m pytest -q -o addopts='' -p no:cacheprovider tests/unit/scripts/test_pr785_signing_recovery.py::test_probe_api_contract tests/unit/scripts/test_pr785_signing_recovery.py::test_success_persists_bound_receipt_and_raw_responses --junitxml=/private/tmp/specfact-release-20261022/signing-recovery/service-committer-correction/positive-red.xml
```

Exit 1. Two failures, zero errors and zero skips. The API contract raises `ProbeRefusalError: Git attribution mismatch` from the real name check. The existing persisted-success assertion reports `assert 1 == 0`. Neither failure is an import or setup error. The raw log, JUnit and exit status are retained in the private correction directory.

Fresh collection returns 90 selectors. The pinned module fixture was verified against its clean commit and tree. Its real native importer and lifecycle evaluator return planned maturity, a pass decision and no source-binding findings for all eight requirements. The canonical mapping digest is `sha256:f686345a624d61150d5fd2901ea0b6e567795a21d8e7b7d4a6eb6379c89dca27`. This direct source-bound evaluation does not claim a staged delivery command or a test-authored receipt. Root owns those next gates because index changes are excluded from this phase.

Focused lint, format and type checks, scoped YAML, strict OpenSpec, six configured independent SAST rules, Bandit and whitespace checks pass. SpecFact CodeReview reports PASS with zero findings at all severities. The first direct review invocation lacked the configured module-root environment and produced no review report. The retry supplied the existing pinned module package root and retained a genuine clean report. No package installation, waiver or scanner change occurred. Exact commands, statuses and reports are retained in the private correction directory.

The runtime, manifest, inert bytes, executor workflow, five-package bootstrap subset, original lock inputs, module fixture lock and original release sources remain unchanged. Root removed the previous active receipt before this phase and retains its historical copy. Fresh independent test acceptance, a new root receipt and normal test-first commit remain required before runtime authority opens. Root owns the internal wiki update and graph rebuild follow-up. No runtime implementation, index operation, commit, ref update, signing, dispatch, API request or merge occurred in this phase.

## Local implementation evidence

Recorded 23 October 2026, Europe/Berlin. Root opened implementation after independently accepted test c8dd2081, canonical mapping3c5f10dd and the genuine structural RED retained below. The final actual green.xml contains68passing cases and zero failures, errors or skips against runtime SHA38456f4429f5e3b4a68f82307dcfce2c1b74cd94063b2da1af198058db93d7f3 and test SHA02497db0fe053be57fde1f79f89d28dfdaab507f61599f8bcfa58f5d43b0b79a.

Root approved the sole test data-path correction from an inert .yml copy to a .txt data asset after the actual YAML file-kind warning. Exact content, Git blob, signed path, tree,68selectors and mapping are conserved. Inverting that one literal restores acceptedc8dd exactly. Fresh independent review accepted the exact runtime and delta in requirements-proof/independent-runtime-review.md; the actual source receipt now refers to that review.

Actual scoped CodeReview/lint/types/SAST/Bandit, workflow/scoped YAML/OpenSpec, reproducible-delivery and fresh five-package frozen bootstrap checks pass. Full inherited type/YAML diagnostics remain in unchanged files and are not waived or declared clean. Root staged the combined candidate through the real source gate. The first normal combined commit attempt refused this note's duplicate top-level heading; root corrected that documentation error. Normal commit hooks and hosted signing remain pending. The release's separate signed-prefix native33RED and all final native CI remain mandatory. No CI signing, release replacement, merge or publication has occurred.

## Historical pre-implementation record

Recorded 23 October 2026, Europe/Berlin. Production implementation has not begun.

## Meaningful failing-before evidence

The structural test ran against the original tracked specfact.yml before any production edit. It failed on the extra push and pull_request triggers. The original raw output and JUnit are retained privately as red.log and red.xml.

After formatting the complete test file, the exact selector was run again with the same actual behavioral mismatch and no collection or test errors.

```sh
.venv/bin/python -m pytest -q -o addopts='' tests/unit/scripts/test_pr785_signing_recovery.py::test_executor_is_dispatch_only --junitxml=/private/tmp/specfact-release-20261022/signing-recovery/probe-implementation/red-final-tests.xml
```

Exit 1. One failed assertion. Zero errors. The failure reports extra trigger keys push and pull_request.

In the first package, the other 53 cases were authored controls and had only been collected. No absent-module/import failure is claimed as RED evidence. The immutable source digest in the tests was computed from the original audit JSON using sorted compact JSON serialization.

## Test package checks

Ruff check and format check pass for the authored test file. YAML lint passes for the mapping and OpenSpec metadata. `openspec validate pr785-ci-signing-recovery --strict` passes. The initial exact file hashes and 54 collected selectors remain retained in the private pre-implementation package. Independent acceptance remains pending.

## Passing-after and live acceptance

Pending implementation and independent test/spec acceptance. Local test success will not establish live CI signing or root anchoring. The root owns review evidence, executor SHA review, dispatch, actual object/artifact authentication, and subsequent acceptance.

## Amended test-only package

The independent review rejected seven canonical selector IDs and missing receipt persistence coverage. The amended package preserves malicious input values under safe parameter IDs. It maps successful persisted receipt verification, later refusal retention, and early unauthenticated context refusal to separate matching scenarios. It also pins the root-grounded exact baseline tree, probe tree and inert bytes, and adds base/repository/merged-state and live-run identity controls.

The amended file collects 68 exact selectors. Only `test_executor_is_dispatch_only` was executed. It again fails on the real existing push and pull_request triggers, with one failure, zero errors and zero skips. The remaining 67 controls have only been authored and collected. No absent implementation or import failure is claimed as RED. Raw argv, exit codes, stdout, stderr and JUnit are retained under the private `probe-implementation/round2/` directory.

Ruff check/format, YAML lint, OpenSpec strict validation, tracked diff checks and explicit untracked-file whitespace checks pass. The real pinned Requirements lifecycle evaluator returns planned maturity, a pass decision and no findings. Its canonical mapping digest is `sha256:1549843cb0dc6b383166f133b6be58e02deaf74038adc20719fef3045b80dfc3`. This planned grammar check is not independent acceptance, a test-authored receipt or execution evidence. Root owns fresh acceptance against the amended digest.

## Native source binding correction

The subsequent actual staged delivery command rejected the round2 representation with unknown-source-scenario findings. The standalone evaluator result above did not check native source binding. The failed delivery report and prior acceptance receipt remain historical private evidence. No active acceptance receipt applies to this correction.

The eight original scenarios now each have a same-title Requirement and Scenario pair. Every original SHALL paragraph remains verbatim under each corresponding requirement, and every original WHEN and THEN remains verbatim. The mapping repartitions the same 68 case objects under the eight requirement IDs returned by the actual native importer. Test bytes remain unchanged at SHA-256 `c4d103e648672d325e3ffbae5377fe89b933b56c83f37f741d00347a97ad02b4`.

The actual released delivery command ran against the staged package with the pinned fixture and no review receipt.

```sh
.venv/bin/python -B scripts/requirements_evidence_delivery_gate.py --staged --required-maturity planned --output /private/tmp/specfact-release-20261022/signing-recovery/probe-implementation/round3/source-gate-verified.json --summary /private/tmp/specfact-release-20261022/signing-recovery/probe-implementation/round3/source-gate-verified.md --plan-output /private/tmp/specfact-release-20261022/signing-recovery/probe-implementation/round3/source-gate-verified-plan.json
```

Exit 0. The actual report has verdict passed, gate decision pass, observed maturity planned, one selected source, and no findings. Canonical mapping digest is `sha256:7d98da7920efa7f4b0c53df122e6e640e182ce4032ab3b3450014410aeef76d7`. Plan digest is `sha256:100851390de754bcf6152b331f96ad02b6e76cb4d6aabd4ecefd707a6bca5548`. Fresh independent acceptance remains pending. This result establishes source-bound planned mapping only.

Round3 collection still yields the same 68 exact selectors. The structural selector again fails on the original workflow's extra push and pull_request triggers, with one failure, zero errors and zero skips. The other 67 controls remain authored and collected only. Ruff check and format check, YAML lint, strict OpenSpec validation and whitespace checks pass. Private round3 artifacts retain raw commands, stdout, stderr, JUnit, source conservation and package hashes. Preliminary sandbox-blocked Git snapshot attempts carry no semantic source-binding verdict.

## Normal-hook fixture type correction

The first normal test-only commit was refused by `hatch run lint-changed`. It reported three argument type errors in fake HTTP fixtures: two HTTPError header arguments used dictionaries instead of Message objects, and a Request data union was passed directly to json.loads. The actual failed hook log is retained privately as test-first-commit.log. No commit was created.

The fixtures now use standard-library Message headers and assert that constructed request bodies are bytes before parsing. This changes only test fixtures. The exact same repository lint command passes with zero errors and warnings. At final test SHA-256 `41e6154ccc3de985fc49b3ba90114425134f7e27cb76c47181d2b0e10fa89b78`, collection still succeeds with68 selectors and the single structural test still produces one genuine trigger assertion failure with zero errors. Evidence is retained under fixture-types/. Fresh independent acceptance of the changed test bytes is pending before another commit attempt.

## Intermediate CodeReview test and interface correction

The subsequent normal test-first commit was refused by CodeReview with seven errors and 43 warnings. Its retained raw report identifies fixture and assertion complexity, a fake credential variable name, and unknown members of the intentionally absent implementation. No commit or production edit followed that refusal.

The fake API now separates workflow, ref, PR, commit creation, readback and attribution responses. Fault maps preserve each injected malformed response. Receipt, persisted response, bounded write and workflow assertions share checks for their respective contracts. The explicit fake credential bytes remain unchanged. A private old/new fixture comparison records equal outputs, write counts, saved objects and call histories across 35 fault/drift scenarios and 770 requests, including caller mutation and exception paths. This is fixture equivalence evidence only, not execution of the future probe or its 67 authored API controls.

A non-executable `.pyi` declares the accepted API and receipt types while the runtime module remains absent. Root approved renaming the planned exception to `ProbeRefusalError` so its future implementation satisfies the actual naming gate without an alias or suppression. The mapping changes only that exception name in 44 observable strings. All 68 case IDs, selectors and parameters remain unchanged, and all eight Requirement/Scenario blocks are byte-identical to the prior accepted spec. Canonical mapping identity is now `sha256:3c5f10dd228ae37cca648489438ff1bdb01a7aa8bba28d2e3413546060c9b06a`. Prior acceptance receipts do not apply to these changed bytes.

At test SHA-256 `2204105c9ee9ccaf5e177c80741875e4c9702cfad358d0802ff1098f5a4f023c`, fresh collection returns the same 68 selectors. Only the structural workflow test executed. JUnit reports one assertion failure on the original push/pull_request triggers, zero errors and zero skips. The runtime module and manifest remain absent; no missing-module failure is RED evidence. Original ten source records and root probe-tree grounding remain unchanged.

Normal `hatch run lint-changed` passes for the test and interface with zero errors and warnings. YAML lint and strict OpenSpec validation pass. The actual pinned lifecycle evaluator returns planned/pass with no findings. The actual `scripts/pre_commit_code_review.py` returns exit zero with zero errors, six warnings and three informational findings. All remaining findings concern the interface-only declarations: six missing executable icontract decorators and three optional parameters with no executable None checks. No fake contracts, suppression, scanner modification or warning waiver has been applied. Root judgment and fresh independent acceptance remain pending, so this is not a clean all-severity acceptance claim.

The first review attempt also retained a Semgrep trust-anchor initialization error. The subsequent actual review used the existing dedicated environment's certifi CA bundle through `SSL_CERT_FILE`; it installed nothing and did not disable certificate validation. Raw before/after findings, naming failure, fixture trace, source conservation, selector collection, structural JUnit and verification commands are retained privately under `probe-implementation/code-review-fix/`. Root owns the genuine new review receipt, actual staged test-authored gate and normal commit. The implementation commit must remove the `.pyi` and type-check the real module directly.

## Final frozen test-only boundary before implementation

Root selected one normally gated test-and-implementation commit for this auxiliary CI probe after fresh independent acceptance. This follows the integration-heavy auxiliary boundary in the accepted recovery plan. The attempted separate auxiliary test-first commit could not satisfy type review without a temporary interface, and the interface then produced non-runtime scanner findings. The temporary `.pyi` has been removed entirely. No fake contract, scanner exception, suppression or warning waiver replaces it. The actual API is documented in design only; the implementation script, manifest and workflow edits remain absent.

The final test SHA-256 is `c8dd2081dff2e5d607afdf6e45502778eb80d522da121fa3e769971fd0a43eb8`. Fresh fixture equivalence still covers the same 35 scenarios and 770 requests with identical old/new traces. Fresh collection preserves all 68 exact selectors. The structural workflow test again yields one genuine failure with zero errors and skips. The other 67 controls remain authored and collected only. The mapping remains `sha256:3c5f10dd228ae37cca648489438ff1bdb01a7aa8bba28d2e3413546060c9b06a`, reflecting only the approved `ProbeRefusalError` observable-name correction.

Final normal lint-changed, YAML lint, strict OpenSpec and whitespace checks pass. Actual normal CodeReview returns zero errors and 44 warnings, all `basedpyright/reportUnknownMemberType` findings caused by the still-absent runtime module. Every substantive test complexity, credential naming and known-data inference finding is resolved. The 44 implementation-dependent findings remain pending, not waived or passed. The future fully typed runtime module must resolve them, and the combined auxiliary commit must pass every normal gate with zero errors and warnings.

This changes only the auxiliary Git commit boundary. The order remains spec, authored tests, genuine failing-before evidence, fresh independent acceptance, then runtime code and passing evidence. The separate mandatory release signed-prefix native 33-case RED and Git ancestry requirements remain unchanged. Root owns the new acceptance receipt against the final frozen bytes and the implementation handoff. No staging, commit, production edit, ref mutation, dispatch, signing or external operation occurred in this correction.
