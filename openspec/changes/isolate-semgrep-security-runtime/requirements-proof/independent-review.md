# Independent technical mapping review

TL;DR. ACCEPTED for technical scenario-to-selector mapping and readiness to record independent acceptance, author the native test-first commit, and obtain genuine native CI RED. There are no unresolved blocking mapping or test-correctness findings in the reviewed content. This verdict does not authorize production changes before native CI RED, waive any repository gates, or authorize signing, merge, or publication.

Reviewer identity is independent AI reviewer gpt-6.1-sol, agent /root/release_mapping_review. The owner is a separate Astra agent. This is an AI technical acceptance, not human approval. Review date is 2026-10-22 Europe/Berlin. Confidence is High for the inspected mapping, selectors, and recorded local results. Confidence in future CI or release success is not established by this review.

The review was read-only against /private/tmp/specfact-release-20261022/worktrees/hotfix/security-dependencies-0-55-11 at HEAD 5262efb0881e4fac7697d629b0530250342bc656. I inspected staged contents and confirmed the reviewed files matched their working copies. I ran no test suite or build, changed no worktree content, staged nothing, and made no commit. The coordinating agent supplied frozen staged tree 9e61234b9130a48d8c7fac8e603881ec199176a7. The independently read file SHA256 values below are the precise review boundary.

## Acceptance binding

The schema is version 2. The final specification declares eight requirement/scenario pairs. All eight native requirement identities have mapping entries. Each scenario_id matches its corresponding imported native requirement slug. The final native planner reports planned maturity with gate_decision pass and no source findings. That is structural planning evidence only. It does not already represent accepted, test-authored, RED, or verified maturity.

I independently recomputed the lifecycle canonical digests from the staged YAML and plan JSON using the canonical typed encoding implemented by the native lifecycle module. The source mapping digest is the value to bind in the source review-evidence.json acceptance record.

- Source acceptance mapping digest is sha256:8e3941ca05ccf9bceaea351df6cc1e642508debfc4ab87ecdc7b6b9cc45e6820.
- Aggregate mapping digest is sha256:32cf65041606a9c43af3cfd506405d74a871d4cc07c292e63de3238ae87cddcf.
- Aggregate plan digest is sha256:9ef1ef74652759ecb82f7af7c8fa2b19c1d36b0d0bf043e2ed9b1a764bae95b2.
- Native plan identity digest is sha256:678474bc2cf581c9bf424833312f572c8ce234a9b92f66e6b95612282707bc6a.

There are 34 verification cases, 34 unique pytest selectors, and 34 cases in the native plan. The YAML and native-plan selector sets match exactly. Every selected case appears exactly once in mapped-local-red.xml. There are no missing or extra local XML cases, collection errors, or skips.

## Actual case coverage

| Native scenario | Cases | What the selected checks establish |
| --- | ---: | --- |
| Exclude compromised certificate authorities from delivered trust | 12 | Downloads the lock-selected certifi wheel from the approved exact host, checks the pinned hash and export agreement, validates its inert wheel inventory and RECORD, parses a nonempty CA bundle, excludes the specified DER fingerprint, and exercises wrong hash, six malformed-wheel controls, and four unapproved URL forms. |
| Reject submodule checkouts outside the repository | 1 | Installs the hash-pinned GitPython delivery wheel into a temporary target, runs it under -I -S, observes rejection before the mocked clone boundary, and checks no outside directory was created. |
| Preserve JWT verification options and compatibility | 1 | Installs the hash-pinned PyJWT delivery wheel into a temporary target and runs the options, expiry reuse, signed-token, padded-signature, and caller-options checks in the same isolated process. |
| Select the reviewed compatible tooling graph | 4 | Checks the reviewed Hatchling, urllib3, virtualenv, and python-discovery versions, official registry identities, and matching exported requirement versions. |
| Bound the temporary official MCP advisory exception | 10 | One case binds official Semgrep 1.179.0, MCP 1.29.0, the exact advisory register record and dates. Nine cases exercise the existing strict gate using the committed register for both advisory IDs, expiry day, other version, unrelated advisory, mixed advisories, skipped dependency, expiry, and future review date. |
| Rebuild the source distribution with its bundled manifest | 1 | Invokes ordinary offline uv build with the installed backend and verifies the bundled wheel manifest bytes equal the repository manifest. Recorded build diagnostics confirm this path builds the wheel from the source distribution. |
| Select the reviewed documentation dependency versions | 4 | Checks the three reviewed plugin lock versions and the JSON >=2.21.2,<3 declaration. These are dependency-selection checks, not executed gem compatibility coverage. |
| Publish one coherent patch version | 1 | Parses pyproject project.version and the version assignments in setup.py and both source init files to require 0.55.11. |

The initially observed JWT compatibility test used verifier imports for signed/padded decoding. The owner corrected it before freeze by moving those checks into the isolated frozen-wheel probe and removing the standalone verifier-package test. I re-read the corrected staged probe and mapping. The owner also replaced version-substring checks with actual assignment extraction before freeze. These findings are resolved in the reviewed content.

## Genuine local RED and its limits

The exact selected local run is /private/tmp/specfact-release-20261022/red-owner/mapped-local-red.log and mapped-local-red.xml, timestamp 2026-10-22T17:51:18.921142+02:00. The XML records 34 tests, 19 failures, 15 passes, 0 errors, and 0 skips. I independently reconciled its case identities with the 34 native-plan selectors.

I read the failure diagnostics rather than treating any nonzero exit as sufficient evidence. The certificate probe found the specified root fingerprint in the delivered CA set. GitPython reached the deliberately observed clone boundary for ../outside. PyJWT changed the caller options after inspection. The source build failed because the bundle-mapper forced include was absent from the generated source distribution. The reviewed tooling and documentation versions, release version, Semgrep selection, and missing exception produced the expected old-state declaration disagreements.

The exception expiry/future-review cases currently fail on the missing expected invalid-register diagnostic because the committed register is empty. They do not prove that old gate code incorrectly waived an expired record. Four other negative exception controls and the malformed-artifact controls already pass. That is expected. This review does not require every selected case to fail and does not reclassify passing controls as new RED evidence.

The older local-red.log and local-red.xml contain a broader 48-case run from before final portable parameter IDs and combined JWT coverage. They are historical diagnostics only and are not the final selector-bound local evidence accepted here. The initial rejected planner artifacts were superseded by the current passing planned artifacts.

Local results are supplementary test-first evidence. They are not retained native CI RED and carry no GitHub run identity. The next required gate is genuine native CI execution of this accepted frozen plan before any production dependency, version, packaging, or release changes. No earlier dev admission, synthetic failure, alternate fork, or late RED mechanism substitutes for that gate.

## Production boundary and supplementary checks

The staged diff contains the selected OpenSpec artifacts, CHANGE_ORDER, and tests only. It contains no production implementation changes. The design and mapping enumerate the intended later production touchpoints. Their union covers pyproject.toml, uv.lock, requirements/ci/locked.txt, ci/vulnerability-audit-exceptions.json, setup.py, src/__init__.py, src/specfact_cli/__init__.py, CHANGELOG.md, docs/Gemfile, docs/Gemfile.lock, scripts/check_jekyll_dependencies.rb, and .github/workflows/docs-dependency-checks.yml. Existing main requirements-evidence and audit infrastructure is unchanged.

Actual Ruby feed escaping, redirects, relative links, and JSON behavior are supplementary final compatibility evidence. Published-v0.55.4 runtime byte equality, signed asset equality, exact certifi/GitPython/PyJWT reviewed version selection, full frozen export/hash closure, strict signatures, both audit lanes, changelog scope, local hooks, and final CI checks also remain required. They are not implied by the 34 mapped selectors. The final specification and design avoid claiming native Python coverage for the Ruby probes, published payload comparison, or changelog semantics.

The tests prove the selected behavior and declarations at their stated boundaries. They do not prove every vulnerability or every compatibility property in every upgraded dependency. GitPython uses installed verifier gitdb/smmap dependency roots while selecting the delivery GitPython code first. The build test uses the installed backend and therefore must execute later in the intended frozen build environment. These are explicit environment assumptions, not claims of fully self-contained dependency execution.

The exception is exact MCP 1.29.0 for CVE-2026-59951 and GHSA-84m7-p3x7-pcfv, reviewed 2026-10-21 through inclusive expiry 2026-11-04. The tests pin these values. This review evaluates that contract and does not independently validate the external advisory facts or extend the exception window.

## Remaining actions and failure controls

One nonblocking formatting finding remains in the inspected index. git diff --cached --check reports a new blank line at EOF at spec.md line 79. The coordinator has explicitly taken this whitespace-only cleanup before hooks. Any resulting spec byte hash must be recorded separately; substantive spec, mapping, selector, fixture, or transitive-import changes require renewed review and appropriate fresh test-first evidence. Updating the acceptance identity record to cite this review is expected and does not imply permission to change selected test behavior.

The acceptance record must identify this AI reviewer accurately and bind the source mapping digest above. Retain genuine native CI RED before production edits. Freeze mapped tests, selected mappings, ancestor conftest files, and transitive test imports through the RED-to-GREEN cycle. A selector drift or changed test helper can break proof continuity; mitigate it with exact recorded identity checks rather than a renamed test or regenerated narrative. An unreviewed dependency graph or changed runtime payload can violate the dependency-only boundary; mitigate it with the required final graph and byte comparisons. An invalid or widened advisory register can weaken auditing; keep both audit lanes strict and rerun the exact positive and negative controls.

No runtime cost or performance claim was measured. The selected local run XML reports 1.012 seconds of suite time on this machine; that is not a CI duration forecast. Rollback before merge is removal of the unmerged release diff. No release effect occurred during this review.

Test Behavior, Not Implementation shaped the decision to require signed/padding checks against the frozen delivery PyJWT rather than verifier imports. Prove It Works shaped the direct comparison of staged mapping digests and exact selected XML outcomes, including the concrete disagreement in each behavior failure.

## Precise reviewed file identities

The following SHA256 values were read directly from the Git index. They matched the working files at review time. Paths are relative to the reviewed worktree root.

- `b9d8f369ba91041aef3707aa02e199381e70dfbb75d5ab6d35015ed0b48a27f2`  `openspec/CHANGE_ORDER.md`
- `0ad492a63d87e00a8bc135b0a1a2b19270dbb9ffd997a69b89fd4ab72015a944`  `openspec/changes/isolate-semgrep-security-runtime/.openspec.yaml`
- `27b886b35c4f802d4796d8b75c3f2aef9b554f70c27bf6f616e9f8ff93f9f93d`  `openspec/changes/isolate-semgrep-security-runtime/CHANGE_VALIDATION.md`
- `6ef7cc7a32b03505fb62a0f2215e560ed03cc73a98f2e1a8e99e5ce92fba75c3`  `openspec/changes/isolate-semgrep-security-runtime/TDD_EVIDENCE.md`
- `0f19e601ced4855fc0ae8da78eb6605d1262a7fd05f5a39d0ffefd7001a8daac`  `openspec/changes/isolate-semgrep-security-runtime/design.md`
- `87d33cfa09d1ad7ee89a7c4b45ab6b6d828b2b077f9f825a089c4ede622ac35c`  `openspec/changes/isolate-semgrep-security-runtime/proposal.md`
- `815016cd54dee63ba1fc66836593004e4c917c942f10eb24462408aadd22a5d1`  `openspec/changes/isolate-semgrep-security-runtime/requirements-evidence.yaml`
- `2ec960286a47415ce3f6f4cd275f699a138d8abcc4d45d3eeb18639b92fbec53`  `openspec/changes/isolate-semgrep-security-runtime/specs/isolated-scanner-runtime/spec.md`
- `d0bec2f806fbd9fff48f5c40d7b54eeea1d7558868a09679988cf75084aca330`  `openspec/changes/isolate-semgrep-security-runtime/tasks.md`
- `af24d9caa1259ecf9789440c516784ea01d4afb34acf8fe9ef377f5f2f46806b`  `tests/integration/test_distribution_build.py`
- `d0b1fcb16185b1908b6abc53e0c68e7baf04ede2b395492fa4d4cbb37ed8c3b9`  `tests/unit/scripts/test_security_audit_gate.py`
- `146f45786ccb74b581c36a1a626130c540631e45fa869433d5663e56202b4215`  `tests/unit/security/test_frozen_dependency_artifacts.py`
- `527d78a6dd07e04e00fefa06632cfa320725f035c22d988e0a1741a455ece728`  `tests/unit/security/test_frozen_gitpython_compatibility.py`
- `35b8e0d571bf50a30599ad1634b068d2d3d37e9a46ffd45fe6dfea03771cab16`  `tests/unit/security/test_frozen_jwt_compatibility.py`
- `7e41674b9b6c2bfb210f50084125821e54c662b079d932be2ba2ebb787bf876f`  `tests/unit/security/test_release_dependency_selection.py`
- `dcf6de107fea93357421daae229bbdd144d0e592d56b28c58b0429aa4ddd9531`  `tests/unit/security/test_release_promotion_security_gates.py`
- `6ec0f7ee75694f3ba75a1c103713e92aaf162758c869c3d4db353c6f9725c6e6`  `tests/conftest.py`
- `762543a00a6519647357e1e72d296cf64e9512f0885fd2563c4df9aec8f8f4d0`  `scripts/security_audit_gate.py`

Evidence file SHA256 values follow. Paths are relative to /private/tmp/specfact-release-20261022/red-owner.

- `7999adc5cc6bd8d1f689c40e14f573268872babb64dcea5380e549355fc38dbc`  `requirements-plan.json`
- `3a62f93ab41b10242e080a969cca36399143b7360fb3b2a611c753b9e6538bfe`  `requirements-evidence.json`
- `5f7e4988c0b8a50b3601712b54c176e0d916c6e947fb34e903961f3ead64e684`  `mapped-local-red.log`
- `1de2aacfd11fc90c4bf422e2824adadaa9aeeacbeef5297eaff28081e79defec`  `mapped-local-red.xml`
