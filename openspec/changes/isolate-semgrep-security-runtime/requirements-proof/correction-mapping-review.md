# Corrected release mapping independent technical review

TL;DR. **Accepted** for this corrected test-only mapping and the exact reviewed source bytes below. No blocking technical finding. This is fresh independent AI technical review by Codex agent `/root/release_correction_mapping_review`. It is not human approval, native RED acceptance, GREEN verification, signing authority, merge authority, or publication authority.

Reviewed on 2026-10-22 Europe/Berlin against worktree `/private/tmp/specfact-release-20261022/worktrees/hotfix/security-dependencies-0-55-11`, branch `hotfix/security-dependencies-0-55-11`, HEAD `a2ee2c9d96e1cce5ba1f13f733ccc49580262ffb`. I did not write this correction. I read the actual correction diff, current proposal/specification/mapping/tests, restored production files, local failure messages and JUnit, controls, pending receipt, historical report context, correction metadata, and fixture regression evidence. No repository edit, staging, commit, test suite, installation, build, signing, PR action, merge, or publication was performed. My only executed verification beyond read/hash/Git inspection was a fresh planned-maturity run of the unchanged released Requirements CLI, writing separate reviewer artifacts outside the repository.

The exact base is `5262efb0881e4fac7697d629b0530250342bc656`. My fresh `correction-review-plan.json` equals supplied `correction-tests/plan-final.json` as parsed data. Both pass at planned maturity. Source mapping digest is `sha256:9405ba32fc071ee2092077f516c4d7baf57ac0acde1575025d5545c0cbda04a8`. Combined mapping digest is `sha256:6d114e1c20cf149c24c310009d9a3f975ee1cf4626c6d67842d0033d029c147f`. Plan identity digest is `sha256:29af99fc48f7afd6a0dc641716e9ccb5c8bf230ef290848cf5331738a33e7880`. The embedded plan digest is `sha256:550fc6841c666d357054b55803472f65d3a67ed2fbb626df31f1e36e9853e604`.

The actual post-format proposal SHA256 is `4ee2f880701c1c91532aaa8d904e82dcaad206a2be6eb41d9badd3b6d4e9a9c4`. All checkpoint entries matched actual files at review. All ten tracked production files are byte-identical to HEAD. The two backed-up new Ruby production files are absent. The complete base diff contains only OpenSpec/proof records and tests. No runtime, audit implementation, workflow, hook, manifest, signature, transitive Python helper, or ancestor conftest change was hidden in the correction. Six mapped test files other than the selection table are byte-identical to HEAD. The selection table's only code change is its approved package/version data. The separate analyzer fixture has exactly the one-line `repo.git.add("--all")` replacement.

## Coverage and actual failing-first evidence

The mapping contains 23 distinct selectors across all eight requirement/scenario pairs. Its selector set equals `selectors.json` and the actual 23 JUnit case names. Each case failed with an assertion on the specified restored baseline behavior or selection. `mapped-local-red.xml` records 23 failures, zero passes, zero errors, and zero skips. Its SHA256 is `49653320cc55fdc741b5344850631c6e9e067a4fed40598b5296175326884bd4`. This is host-enabled local evidence, not a fresh native CI artifact. I inspected actual failure message attributes and diagnostic tails, rather than treating a nonzero process status as proof.

| Requirement/scenario | Selected cases and decisive observed failure |
| --- | --- |
| Exclude compromised certificate authorities | One real wheel/CA parse retains the exact emSign DER fingerprint. Hash/origin and RECORD/metadata validation run before that assertion. |
| Reject outside submodule checkout | One frozen GitPython/gitdb/smmap closure installs with hashes and no dependencies, enters the isolated target, and reaches `AssertionError: clone boundary reached`. Installation completed before this behavioral failure. |
| Preserve JWT options and compatibility | One frozen PyJWT probe returns seven unexpected caller-option mutations. The test retains expiry reuse, signed decode, padding, and signed-options assertions for GREEN. |
| Select reviewed compatible tooling graph | Eight exact official registry versions and lock/export parity checks. Restored versions differ for certifi, GitPython, PyJWT, Hatchling, urllib3, virtualenv, python-discovery, and packaging. |
| Bound official MCP advisory exception | Six cases bind official Semgrep/MCP and the exact register; exercise CVE and alias, inclusive expiry day, expired date, and future review date. Failures are old Semgrep selection, absent waiver, and missing date-invalid diagnostic. |
| Rebuild source distribution with manifest | One ordinary offline source-to-wheel build reaches the backend and fails because the sdist lacks `modules/bundle-mapper`. This is not an unavailable build tool or download failure. |
| Select documentation dependency versions | Three lock plugin versions and the JSON >=2.21.2,<3 declaration fail against old selections/floor. |
| Publish coherent patch version | One data-only test retains all four canonical version assertions. The restored first source reports 0.55.4 instead of 0.55.11. |

Initial sandbox DNS/download failures are explicitly rejected as behavioral proof. Their historical `sandbox-*` artifacts must remain historical. Local evidence cannot supply native provenance. Several first assertions intentionally prevent later assertions running on the old baseline. Final GREEN must exercise those later checks.

The fifteen supplementary controls remain unchanged. Actual `controls-green.xml` records fifteen passes, zero failures/errors/skips, SHA256 `c4715403faf3bcae521030eea59784ee09d645119d80a55b92a41d1e8b5a75be`. Eleven cover malformed/hash/origin artifact rejection. Four cover wrong MCP version, unrelated/mixed advisories, and skipped dependencies. Excluding already-passing controls from a reconciler requiring every RED selector to fail is reasonable because their assertions remain required during final verification. Run all seven complete mapped test files for GREEN, not merely the 23 selected cases. Those files are the artifact, GitPython, JWT, release-selection, promotion-security, audit-gate, and distribution-build test files named in the manifest below. The analyzer consumer fixture remains an additional affected regression surface.

The fixture correction stages ordinary Git worktree contents through Git and preserves every consumer assertion. Supplied original evidence has three failures and 26 passes. Corrected evidence has 29 passes. I read those logs without rerunning them. This test-only correction is outside the native mapped proof and does not mask the frozen artifact probe's failure.

## Scope and evidence boundary

The correction selects official virtualenv 21.14.12, python-discovery 1.6.1, and packaging 26.3. Retained wheel metadata requires the latter two minimums. Supplied scratch-resolution data changes exactly those three versions relative to the prior candidate, adds/removes no package, and records `adopted=false`. Current proposal/spec/table retain all other exact targets, including certifi 2026.10.19, GitPython 3.2.0, and PyJWT 2.15.1. This yields nine Python dependency version updates relative to main, with core 0.55.11 and MCP 1.29.0 preserved as specified. Exact selection assertions complement, and do not replace, the frozen artifact behavior tests.

The active receipt honestly remains pending with a repository-relative status reference. The saved pre-correction receipt equals the old HEAD receipt byte-for-byte. Historical reports keep their original scopes and hashes. Their old nineteen-case acceptance/native runs cannot accept these changed tests. The coordinator may now bind a fresh accepted receipt to this report using a repository-relative durable path and the source mapping digest. Do not infer human approval from the reviewer's identity or an accepted machine receipt.

The known stale candidate exception rationale needs its separate correction after fresh native RED. This report does not approve additional exceptions, alternate exact dependency targets, a fork/override, check bypass, local signing, merge, or publication. Real Ruby behavior, strict audits, signatures, published-runtime equality, final quality checks, native GREEN, and final independent production review remain outside this mapping acceptance and still required.

## Comment and semantic flags

Read-only comment review covered the correction hunks and nearby code. New code comments, scoped suppressions, deletion recommendations, actual deletions, restored comments, reruns, `MUST KILL` flags, workaround flags, and open constraint encodings are all **zero**. No application edit or architecture sketch was needed. Existing external dependency and public-contract context was not treated as a new correction defect. Prior candidate Ruby comment cleanup recommendations remain separate historical review work because those files are currently absent.

Confidence is High for static scope, exact identities, requirement coverage, local behavioral failures, and planned CLI digest agreement. This acceptance assumes these bytes and the full test/import/conftest closure remain frozen through native execution. Three material failure modes remain. Changing proof bytes invalidates old provenance, so re-review and obtain fresh native evidence. Passing the selected cases while missing control or later assertions can conceal regressions, so require full seven-file GREEN and affected consumers. Treating selection tests as audit/Ruby/runtime proof overstates readiness, so retain those separate actual results. Review cost was local read/hash/planning computation; no paid or deployment action occurred and no performance claim is made. Rollback is the preserved unmerged correction/production patches and file backups.

Next action is a durable accepted technical receipt, normal hooks and test-only commit, then fresh genuine native CI RED before production reapplication. Keep historical proofs unchanged.

## Exact reviewed input identities

`worktree/` paths below are repository-relative under the reviewed worktree. Other release paths are relative to `/private/tmp/specfact-release-20261022`. `pstack-0.9.96/` paths are relative to the installed skill directory. SHA256 values bind the actual reviewed input bytes, including proposal after formatting. Reviewer-generated planned artifacts are included explicitly. The report itself is a new output and is not an input.

```json
{
  "audit/virtualenv-correction/METADATA.txt": "a4902e1954e11c6c06a5e235de89ca273dd8fb6b7ad93d35f076194a8d09e1ee",
  "audit/virtualenv-correction/resolution-result.json": "62fed2895c346541d79b73faf1e63f01c095bd3e5780226007c717eaef688c0e",
  "candidate-precorrection-review.md": "53c85521be72a8ac11ccddfa0674a3992cdad6f6714a2e796bad32950f910824",
  "correction-review-plan.json": "a5a96590762270c706387d1ba99b1c9dc990c09ae6496ff9f96cce0de74fd7c9",
  "correction-review-planning.json": "3681852d17eae60e327b150a41b5c05eeb076b60428d10e900eb44ff3b822423",
  "correction-tests/checkpoint-sha256.json": "0b9145751b7f90267a3201d1a6e20ca3471e2bd5374d2a4ef46a38805104613c",
  "correction-tests/checkpoint.md": "d8050a0a9bcdfd6ac89dfe98ef8d994c0b2bdf062099aff48bb40a287e4cfc27",
  "correction-tests/control-selectors.json": "b9d5ab7f19da658719c64105c65ee02a5d7914c7480d27e404330d5752d7e757",
  "correction-tests/controls-command.json": "cdc0d2d0bbb91880041dfe638637dc138b01c5ec3e66e4992f849334a227f2b9",
  "correction-tests/controls-exit.json": "e89df0eae5ec7db81135aed16463968955c578bcc4f2ec43172eff351f080c17",
  "correction-tests/controls-green.xml": "c4715403faf3bcae521030eea59784ee09d645119d80a55b92a41d1e8b5a75be",
  "correction-tests/correction.patch": "ea92dfacae85af2cf8091ffd7e986fb9f1d1270530ee22e31ce45fb8c97a20d2",
  "correction-tests/failure-diagnostics.json": "81a28e2c73d00fc9a4bb742f631089e851b57f7bcfc8504fafc0ed2552d2ecaf",
  "correction-tests/mapped-command.json": "75cc4169e5bc8b19fa47134eb4ba6c20a92eb2b82cc425cc57277e5778593810",
  "correction-tests/mapped-exit.json": "5cc319f54b05a38799195a491c303aa686eab7caccfdbbf1e8b8c07405cb7392",
  "correction-tests/mapped-local-red.xml": "49653320cc55fdc741b5344850631c6e9e067a4fed40598b5296175326884bd4",
  "correction-tests/plan-base.json": "a5a96590762270c706387d1ba99b1c9dc990c09ae6496ff9f96cce0de74fd7c9",
  "correction-tests/plan-final.json": "a5a96590762270c706387d1ba99b1c9dc990c09ae6496ff9f96cce0de74fd7c9",
  "correction-tests/planning-final.json": "3681852d17eae60e327b150a41b5c05eeb076b60428d10e900eb44ff3b822423",
  "correction-tests/pre-correction-production.patch": "d0ca6e1c88cf62cc79e14132cc539ff7a3e1277709981ea4c8e641a1220b2fd6",
  "correction-tests/run-evidence.py": "db283d821e8633f8fa96219aa32c2021c3f671c418b886c4387a81b8b5414650",
  "correction-tests/selectors.json": "54e819d757e2b63aa877bc91f88d13ff6530ea37c0f3cb48bba1c28bb792f164",
  "implementation/git-consumer-regression-fixed.log": "226295020010569b7601e49a465e42c7c20b1b30a32c7646ae447ee679629fcc",
  "implementation/git-consumer-regression.log": "a6b9f9e58a0fe63f81759915c60cff4705b1ff968c1fbc0ff19ae050222290b8",
  "pstack-0.9.96/no-comments/SKILL.md": "550d10e87e4110a29bba5f966c784569dd1f070a0b715d03309c2eb652cc719e",
  "pstack-0.9.96/poteto-mode/SKILL.md": "c0dc3827dd20ff0acadc1ade8f2139a62f62f1e7692e5de1e4c88f5bc89e5f08",
  "pstack-0.9.96/poteto-mode/references/agents/comment-sicko.md": "3e239e40b7b4b9beb2cf7f3ccc57f2388eb8b69bd1ba8ae888ef87ef6e0e2116",
  "pstack-0.9.96/poteto-mode/references/codex-tools.md": "c2f1d9bebdb157ea2b4e6e8d2f66a3b70a3ca3744e9fef0ff10436e24971b92c",
  "red-owner/env.sh": "8a2b1fa4222a07b130aa269dd8443c14921c959484ebd67760337e3dfc9d79b7",
  "worktree/AGENTS.md": "95b70856d492435262e9a86dbc42388682c44b9841b0a56c580838b986c9b5f8",
  "worktree/CHANGELOG.md": "9ae1d0a51c81d99c0dfdf18bb1faae269d8a49ff6525866fc646d3f8d655db91",
  "worktree/ci/vulnerability-audit-exceptions.json": "584e697cce0eb005ea6f0037f5757f418c6cad912bcca8f486ed97c7cdfa7fe1",
  "worktree/docs/Gemfile": "66d9ce7302ab7d4335ea4e0345b72b0f330f29fbc210fdb25f46cf17792dcbe6",
  "worktree/docs/Gemfile.lock": "1f92f6ac98a73680f8945a96ec5dd6a1bafd3b7489ccecaade42a0cac4ba0ea3",
  "worktree/docs/agent-rules/05-non-negotiable-checklist.md": "44495f2ddb73b01174b8fb0eb9ffc894de4866c520372815b9c1732a2164a7ac",
  "worktree/docs/agent-rules/10-session-bootstrap.md": "a4cf51a60499ff1acc76143a02042ca7d64a84b5236790cc8dd74258d52f7fb0",
  "worktree/docs/agent-rules/INDEX.md": "6fd104400707fd8264ba3ae743b991fdc009cb2d4fa68232235142a242317a6c",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/.openspec.yaml": "0ad492a63d87e00a8bc135b0a1a2b19270dbb9ffd997a69b89fd4ab72015a944",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/CHANGE_VALIDATION.md": "0db5c7bf37bc263840f7140c08b724ffe480ddb8f8a5ac390174925edbde0337",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/TDD_EVIDENCE.md": "06711ca6fc5e44b64b37401a953ba2e0baa61474017fc22354fa8f1408a1be50",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/design.md": "f25525e37756a6caa47eb584e109199ec81c6398e60a9b4d8c9d168ee74b7f77",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/proposal.md": "4ee2f880701c1c91532aaa8d904e82dcaad206a2be6eb41d9badd3b6d4e9a9c4",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/requirements-evidence.yaml": "f26fccaddb64ad7bcaa0ad2444c757dbce3270ba7151fb722130fc691a062d4d",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/requirements-proof/corrected-mapping-review.md": "c3d245b669e5bb57fa060bcb564a1d01e7b4e5403be7ba96122661429235dedc",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/requirements-proof/correction-review-pending.md": "d8b1b927ec372065cf07c48358b546bbea6772b448ea9218ec4701fd07d56532",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/requirements-proof/frozen-closure-review.md": "4908cff4a200a4747f3a0786cfb7007777ed97a54f00fc363273328b17f4da21",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/requirements-proof/independent-review.md": "a981d9f787bd7dab64650254f50ebaa74cef55b79af64441c41525d7ced9692e",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/requirements-proof/pre-correction-review-evidence.json": "a79552f7d6ae2322e9fb1e6f2a2df86352a315608681a12cb9864548a0add912",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/requirements-proof/review-evidence.json": "5cdda2171b39aab9331703af3720432344d1c170ae2d2580dd652010910b9834",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/specs/isolated-scanner-runtime/spec.md": "a0554d99216d85781e3f2df7d5b68142f8d51ce2933bc6e1120c5f0bb173a924",
  "worktree/openspec/changes/isolate-semgrep-security-runtime/tasks.md": "0c198a3f9f166d0466332b2eb1ddeb0acc56f87809973ca02b74774d2cf4e1bb",
  "worktree/pyproject.toml": "790b494893066b89f0b74608fc461a3071c4eaaa92d06ddfbb5b2d4ad2da2375",
  "worktree/requirements/ci/locked.txt": "6f192da46038d0a5577d91048985f7bc351a7f8ac707cb027f19e50bc14aa4c4",
  "worktree/scripts/requirements_evidence_delivery_gate.py": "fe83e438150f16798972a9a89257f904914187516fcbc269b0e13a470a701132",
  "worktree/setup.py": "bb6dc23d7602e9d716c54fb6106c38f0d37769f7a51f4daf995df4bd3897760c",
  "worktree/src/__init__.py": "328fb05f50f87bfa26caf37ad06de8de4a133d338c3826905e600d3ad649689c",
  "worktree/src/specfact_cli/__init__.py": "1f48daba70ce569f75df5611d2884e4489cf095b88391d30d57ccf9f8eb16cce",
  "worktree/tests/integration/test_distribution_build.py": "af24d9caa1259ecf9789440c516784ea01d4afb34acf8fe9ef377f5f2f46806b",
  "worktree/tests/unit/scripts/test_security_audit_gate.py": "d0b1fcb16185b1908b6abc53e0c68e7baf04ede2b395492fa4d4cbb37ed8c3b9",
  "worktree/tests/unit/security/test_frozen_dependency_artifacts.py": "146f45786ccb74b581c36a1a626130c540631e45fa869433d5663e56202b4215",
  "worktree/tests/unit/security/test_frozen_gitpython_compatibility.py": "0d0adc56f725dd4878024c6058c341574fd80222709ff4e47ebda259b9dd5f68",
  "worktree/tests/unit/security/test_frozen_jwt_compatibility.py": "35b8e0d571bf50a30599ad1634b068d2d3d37e9a46ffd45fe6dfea03771cab16",
  "worktree/tests/unit/security/test_release_dependency_selection.py": "4381649df105b1bba4440dfa78deb4fd221ae78d6a013dd5db5ab3784d43c16d",
  "worktree/tests/unit/security/test_release_promotion_security_gates.py": "dcf6de107fea93357421daae229bbdd144d0e592d56b28c58b0429aa4ddd9531",
  "worktree/tests/unit/versioning/test_analyzer.py": "96895ff03536b953743d890d0170958c66640644867230e67ffd59b2733e97d4",
  "worktree/uv.lock": "cc2b166f1facb3794d3c2fdd96b4b727631246fcc7e7fb2b1858d029742ba94b"
}
```

## Exact accepted selectors

- `tests/unit/scripts/test_security_audit_gate.py::test_committed_mcp_exception_is_exact_and_time_bounded[exact-cve]`.
- `tests/unit/scripts/test_security_audit_gate.py::test_committed_mcp_exception_is_exact_and_time_bounded[exact-ghsa]`.
- `tests/unit/scripts/test_security_audit_gate.py::test_committed_mcp_exception_is_exact_and_time_bounded[expired]`.
- `tests/unit/scripts/test_security_audit_gate.py::test_committed_mcp_exception_is_exact_and_time_bounded[expiry-day]`.
- `tests/unit/scripts/test_security_audit_gate.py::test_committed_mcp_exception_is_exact_and_time_bounded[future-review]`.
- `tests/unit/security/test_release_promotion_security_gates.py::test_frozen_graph_uses_official_semgrep_with_bounded_mcp_exception`.
- `tests/unit/security/test_frozen_dependency_artifacts.py::test_frozen_certifi_bundle_excludes_compromised_root`.
- `tests/unit/security/test_frozen_jwt_compatibility.py::test_inspection_preserves_options_and_expiry_on_reuse`.
- `tests/unit/security/test_release_promotion_security_gates.py::test_patch_release_uses_next_version_in_all_sources`.
- `tests/integration/test_distribution_build.py::test_source_distribution_rebuild_preserves_bundle_mapper`.
- `tests/unit/security/test_frozen_gitpython_compatibility.py::test_submodule_update_rejects_outside_checkout_before_clone`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[certifi-2026.10.19]`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[gitpython-3.2.0]`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[hatchling-1.32.4]`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[packaging-26.3]`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[pyjwt-2.15.1]`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[python-discovery-1.6.1]`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[urllib3-2.8.0]`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[virtualenv-21.14.12]`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_documentation_plugins_are_locked[jekyll-feed-0.18.0]`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_documentation_plugins_are_locked[jekyll-redirect-from-0.17.0]`.
- `tests/unit/security/test_release_dependency_selection.py::test_reviewed_documentation_plugins_are_locked[jekyll-relative-links-0.9.1]`.
- `tests/unit/security/test_release_dependency_selection.py::test_documentation_json_has_reviewed_floor_and_major_bound`.
