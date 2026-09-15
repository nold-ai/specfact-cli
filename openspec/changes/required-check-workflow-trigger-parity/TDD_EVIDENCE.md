# Required workflow trigger evidence

## Scope and baseline

On 2026-09-15 (Europe/Berlin), PR #732 head `bffeea78cb6f9db8f41b5207aa15ba77cb278ba2` retained original dev tree `a696d32965bdc1f702684f8d981dc28ece3e9ffd`. GitHub documentation confirms manual dispatch checks cannot satisfy required PR rules. Only the two native pull-request path filters are targeted.

## Actual RED before implementation

After strict specification validation, the new two-case regression ran against unchanged workflows:

```sh
hatch run python -m pytest tests/unit/workflows/test_required_check_workflow_triggers.py -q
```

Result: **2 failed in 0.59 seconds**, exit 1. `TRIGGER_RED.txt` records actual assertion failures for Docs Review `paths` and SpecFact CLI Validation `paths-ignore`. Ruff lint and format checks on the regression passed. This local result does not confer protected CI RED authority.

## Prospective authority and remaining validation

The `.github/` implementation paths require verified maturity. Retain the independently reviewed immutable test/mapping commit through canonical CI before editing workflows. Actual GREEN, required native PR checks, and final protected validation remain outstanding. Existing docs proof files and fixture identities are unchanged.

## Rejected first CI binding and fresh cycle

Canonical Requirements run `35026816358`, attempt 2, at source `b94350c7f748afe6e89c7e6a92423ebb9239d017` executed exactly two assertion failures with zero errors/skips (Python 3.12.14, pytest 9.1.1). Artifact `10419259913`, digest `sha256:b15096adfa9856f68f91210412d3af652e68a984aef1688ff672d85896c4d341`, retains the JUnit but reports `Red proof binding rejected: prior-red-proof-invalid`. It is **not accepted RED evidence**.

The unchanged provenance validator examines merge commits against their second parent. The earlier ancestry-only merge therefore included governed production paths in history even though its tree matched dev. The new `codex/bugfix-required-workflow-trigger-parity` branch starts directly at public dev `a4a04786588d61fbc9105137dbaf0236fce009ee`. Only the signed tests/spec commit is cherry-picked; selected tests, mappings and independent review bytes remain unchanged. PR #732 and its commits remain intact. New canonical CI RED must succeed at binding before production edits.

Independent source-mapping acceptance: <https://github.com/nold-ai/specfact-cli/issues/733#issuecomment-5688443069>. Source mapping digest `sha256:0dc4fe32a24bbe080f82f6f6e6a3cde9f3d5d5a5bfa63b9c98a2a27dae01fc0f`.

## Authenticated RED accepted before production edits

Canonical native `pull_request` Requirements run `35027414640`, attempt 2, retained artifact `10419694628` (`sha256:5f9b709986428f25de29f772f7548347a7cc51a4b82ea9c52ebcf5e413cfbda2`). The downloaded report has `gate_decision: pass`, `observed_maturity: red`, and `implementation_evidence: failing-first-proven`. It binds source `cd763c12ab1a83c0a17d949babe6e8a722152761`, tree `2ad1da1b7f67e057b2bb0d03dff9dc12498350be`, base `a4a04786588d61fbc9105137dbaf0236fce009ee`, and test blob digest `sha256:6ea58fcb1d86e2450ba521db5f67d68022af45d4fc15096d43cd528485575799`.

JUnit records exactly **2 tests, 2 assertion failures, 0 errors, 0 skips in 0.102 seconds**, Python 3.12.14 / pytest 9.1.1. Both failures are the specified missing native-trigger behavior. Only after inspecting this accepted binding were the two production filter blocks removed. The overall RED workflow intentionally fails pending final implementation; the bound producer artifact, not a green workflow badge, is the proof.

## GREEN and scoped verification

The unchanged regression plus trustworthy-check, docs-fixture and docs-authentication suites passed **96 tests in 8.51 seconds**:

```sh
hatch run python -m pytest tests/unit/workflows/test_required_check_workflow_triggers.py tests/unit/workflows/test_trustworthy_green_checks.py tests/unit/workflows/test_docs_module_fixture.py tests/unit/workflows/test_docs_module_authentication.py -q
```

Canonical `workflows-lint` for both changed files, strict OpenSpec, and `docs-validate` passed. Documentation checks validated 117 command paths, 393 prefixes, 26 cross-site links and 24 enforced frontmatter documents. The only production changes are 38 removed lines in the two pull-request path filters; all push configuration and job definitions remain byte-identical. Tests, mapping and review receipt remain byte-identical to the retained RED source.

Fresh SpecFact review with `--bug-hunt --json` on the regression returned **PASS, score 120, zero findings**, timestamp `2026-09-15T21:50:02.862710Z`. The approved fixture module root was configured explicitly, matching the canonical hook environment. No runtime source changed, so runtime matrix execution is left to the applicable existing CI jobs rather than presented as a local test result. Final protected Requirements reconciliation and native PR status completion are still required.

## Supplemental PR review regressions (2026-09-16 Europe/Berlin)

Review comment `4020508005` correctly identified incomplete push-list coverage in the frozen representative regression. A separate supplemental file now compares every push pattern, including order, against the complete lists at base `a4a04786588d61fbc9105137dbaf0236fce009ee`. Four disposable mutations were rejected: remove the nonrepresentative Docs Review `pyproject.toml` pattern, remove a Contract Validation pattern, and add `**` to either list. `PUSH_FILTER_MUTATION_EVIDENCE.txt` records the results. Actual push configuration is unchanged.

Comment `4020546792` correctly identified optional comment publication failing on a read-only fork token. After adding explicit supported-PR scenarios, the supplemental regression ran before the guard edit: **1 failed, 2 passed in 0.08 seconds**, with the failure specifically identifying the absent same-repository guard (`REVIEW_FOLLOWUP_RED.txt`). Then only the `Post PR comment` condition gained `github.event.pull_request.head.repo.full_name == github.repository`. Validation, report upload and the existing failure step are unchanged. GitHub's pull-request event documentation confirms fork token permissions; these tests verify workflow configuration, not a live fork API call.

Supplemental plus original workflow/fixture/trust tests passed **99 tests in 9.92 seconds**. Four mutation checks passed separately. Source formatting/typing/lint reported zero errors, warnings or notes; workflow lint, strict OpenSpec and documentation checks passed. Fresh SpecFact `--bug-hunt` review returned **PASS, score 120, zero findings**, timestamp `2026-09-15T22:00:13.411931Z`. Independent supplemental diff review found no findings.

The protected retained proof still covers its original two trigger cases only. The new tests are explicitly supplemental local/CI regression evidence and are not represented as extra selectors in that proof. Canonical test-authored planning after the scenario additions passed: source mapping digest, aggregate mapping digest, plan identity digest and the entire two-case plan all equal the accepted RED plan. The frozen mapped test, mapping and review receipt remain unchanged. Current-head protected Requirements reconciliation is still required without any waiver.

The stale filter-removal comment `4020512367` was already resolved remotely; a reply records implementation `41786ddc`, the 96-test validation and the distinction between deliberate historical RED and current workflows. That head's native Docs Review, Contract Validation and protected Requirements execution subsequently passed before this supplemental patch.

## Read-only same-repository tokens (review 4020614527)

GitHub documents that Dependabot events receive read-only tokens by default even when the head repository matches the base repository: <https://docs.github.com/en/code-security/reference/supply-chain-security/troubleshoot-dependabot/dependabot-on-actions> (accessed 2026-09-16 Europe/Berlin). Same-repository identity alone therefore does not establish comment permission.

After specifying the scenario, three supplemental tests executed the actual workflow JavaScript with deterministic API responses 201, 403 and 500. Before implementation: **2 failed, 1 passed, 3 deselected in 0.16 seconds**, because the existing unawaited request rejected without handling either error (`READ_ONLY_TOKEN_RED.txt`). The implementation now awaits the request, warns only for HTTP 403, and rethrows every other error. It adds no actor list, token privilege, job-level suppression or weakening of contract validation.

The complete focused selection passed **102 tests in 9.42 seconds**. Review then identified a generic test name and an oversized inline harness; the supplemental test was renamed from `handles` to `tolerates` and the unchanged harness became a module constant. All **6 affected supplemental cases passed in 0.16 seconds** afterward. Formatting, typing/lint (zero errors/warnings/notes), workflow lint and docs checks passed. Fresh bug-hunt review at `2026-09-15T22:07:58.569384Z`: **PASS, score 120, zero findings**. Independent diff review found no findings.

## Typed supplemental harness and prose review

Review comments `4020675400` and `4020675405` prompted prose wrapping and strict Pydantic validation of the native
JavaScript harness result. The harness now exposes typed requests, warnings and HTTP status before assertions; existing
production behavior and all six assertions remain unchanged. The repository already depends on Pydantic and its canonical
code conventions require validated models. Markdown line-length enforcement is disabled locally, so the formatting
comment's claimed lint failure was not reproduced; the requested narrow readability improvement is applied anyway.

All **6 affected tests passed in 0.19 seconds**. Ruff lint/format, targeted authoritative BasedPyright (zero errors, warnings
or notes), Markdown lint and strict OpenSpec validation passed. Fresh SpecFact review with `--bug-hunt` at
`2026-09-15T22:20:54.489518Z` returned **PASS, score 120, zero findings**. Frozen Requirements tests, mapping and independent
review receipt remain byte-for-byte unchanged from accepted RED commit `cd763c12`.

The Node harness runs on the existing hosted Ubuntu test jobs, which do not use minimal containers. It stubs remote APIs and filesystem access; no GitHub comment is sent by these tests. The source mapping, aggregate mapping, plan identity and complete protected two-case plan remain unchanged. These three API cases are supplemental regression evidence, not added protected selectors. Current-head canonical verification remains required.
