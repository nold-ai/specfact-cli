TL;DR. ACCEPT the bounded packaging-test reconciliation. No actionable findings. The change preserves the approved `pycparser>=3.12,!=3.0.*` contract, adds rejection of the retired 2.22 floor, and leaves the mapped 33-case proof unchanged. This acceptance does not approve merge, signing, release, or claim a current passing full suite.

Reviewed on 2026-10-23 Europe/Berlin. Confidence is high for the exact diff, assertion strength, artifact bindings, and unchanged mapped test/import context. Runtime conclusions are limited to the retained evidence. I did not rerun suites, install, sync, change repository files, or perform Git/PR writes.

The inspected worktree is `/private/tmp/specfact-release-20261022/worktrees/hotfix/security-dependencies-0-55-11`, branch `hotfix/security-dependencies-0-55-11`, HEAD `2eef82529a8eb166b9a18898316ae92ce170f02a`. The sole reviewed modification is `tests/unit/packaging/test_core_package_includes.py`. Other existing worktree changes belong to root and are outside this acceptance.

The recomputed SHA-256 bindings are:

| Artifact | SHA-256 |
| --- | --- |
| Before test | `ecfaaa18afe1c49e4e93352280dfaae9447c38f3217c878cbebe9214a0e8462b` |
| After test | `1995bb7e3afa48c9073f80f676858958a8372b872a0ceec26dcda49ef397ea1a` |
| Fixture patch | `5000eff267fa85af90cbd621c070f0c0f37479a1e3923511b5ec13984f58ea9f` |
| `pyproject.toml` | `9c8c4da8a2e215f4b80c6e6cfd7db366b5559ba5e43028a6815d9577b8c23d72` |
| `setup.py` | `4089bd16460b65ee497555a6ec98d58d8d74cd88cf6e88b635791704d2eaceea` |
| Isolated scanner specification | `bc00f6593ec6a64bd47bd18933d1d222a34793a035be3f89542234960b056ef6` |
| Requirements mapping YAML | `cad89859300251d78206a5291077c127e43d2caef687c29c11842e2d36851dab` |

I compared the actual raw Git diff with `parser-packaging-fixture/fixture.patch`; the bytes match. Saved `before.py` matches the HEAD blob, and saved `after.py` matches the current test. Reversing only the two literal substitutions and one added assertion reconstructs the complete before file exactly. All 19 entries in `parser-packaging-fixture/artifact-sha256.json` recompute correctly, and every file in `handoff-binding.json` matches current source.

The specification at lines 106-108 requires both declarations to use `pycparser>=3.12,!=3.0.*`. Both manifests contain that exact requirement. The packaging test retains the exact expected dependency string, the equality of both dependency lists, the one-parser-declaration check for each manifest, and all unrelated dependency assertions. It now requires 3.12 to be accepted and 2.22 to be rejected. The existing 3.0, 3.0.1, and 3.0.post1 rejection assertions remain. The exact `!=3.0.*` literal continues to enforce the complete blocked family, including members beyond those examples. Nine test functions remain, with no decorators, skips, xfails, removed checks, relaxed comparisons, added comments, or suppressions. Existing helper code, imports, docstrings, and all other file content are unchanged. The naming, KISS, YAGNI, DRY, and SOLID review found no regression in this bounded change.

The original full-suite XML, `parser-green/smart-test-full.xml`, has SHA-256 `f428e7abecc7623a98d8a1c753c753f7d3866d7267b61897a4ff56b3d8a39772`. I parsed 3269 tests, two failures, zero errors, and ten skips. Both failures are precisely the stale packaging expectations. One reports the absent old literal `pycparser>=2.22,!=3.0.*`; the other reports `contains('2.22')` false for `SpecifierSet('!=3.0.*,>=3.12')`. This is substantive assertion disagreement, not setup or collection failure.

The retained focused before run records exit 1 and nine tests with two failures, zero errors, and zero skips. Its XML SHA-256 is `5d35f1b354da47459269675d88bca34d6c42a10db26878984e5bcbafd4830a87`. The after run records exit 0 and the same nine named tests with zero failures, errors, or skips. Its XML SHA-256 is `c6c0daf6e7088ff74e8e687e629dcce700708bd9a0535b19105d897189727568`. I read the actual logs, command records, and XML. Stored Ruff check, Ruff formatting check, and bounded diff check record exit 0. These observations support this fixture repair; they do not relabel the earlier full suite as passing.

The target file is absent from the eight selected mapped test files. Each current complete selected file matches both its preparation hash and the native proof's `test_file_digests`:

| Selected file | SHA-256 |
| --- | --- |
| `tests/integration/test_distribution_build.py` | `af24d9caa1259ecf9789440c516784ea01d4afb34acf8fe9ef377f5f2f46806b` |
| `tests/unit/scripts/test_dependency_trust_review.py` | `bb20822cb58c8f773f8ed7a54628feef2e1eadbf5cc5c53936422223986ee7ac` |
| `tests/unit/scripts/test_security_audit_gate.py` | `5a0c6669c793477bc8cabe518a7f7d20e8db98bb2201be255ed241654c4ed748` |
| `tests/unit/security/test_frozen_dependency_artifacts.py` | `146f45786ccb74b581c36a1a626130c540631e45fa869433d5663e56202b4215` |
| `tests/unit/security/test_frozen_gitpython_compatibility.py` | `284563d0d316d73910c7857afbc76f083d056f803765d79382c8a54ebfedc162` |
| `tests/unit/security/test_frozen_jwt_compatibility.py` | `35b8e0d571bf50a30599ad1634b068d2d3d37e9a46ffd45fe6dfea03771cab16` |
| `tests/unit/security/test_release_dependency_selection.py` | `24d9e8555a072c306fa332e429805d1b9ce16b2f18f245dff2a42ff1d957bd09` |
| `tests/unit/security/test_release_promotion_security_gates.py` | `9f0ede9d55afa5241b42b30660bec58099945a9b636b1a7c57cda69139a10487` |

The latest `trust-correction-tests/design-rebind/final-plan.json` is byte-identical to the extracted native plan, SHA-256 `7be1098f249b68f80d2a3916cbbea85e7b2b1ee303c80aaa79783e63744a2e52`. Both retain 33 canonical cases, mapping digest `sha256:7752d805c6911e719e9aa3dcb985526f8b10f3e587ebfb1d37c5e67c5703718f`, and plan identity `sha256:105b01868f04e3d382b9266bc38111825ca06ad0d00a42d477ac8f5e322e805b`. The older `plan-final.json` differs only in its planned/test-authored maturity fields. Its cases and identities agree. The fixture edit cannot alter those selectors or mapping bytes.

The native proof remains applicable as historical failing-first evidence for those exact mapped tests. Retained run metadata binds [run 39872159349](https://github.com/nold-ai/specfact-cli/actions/runs/39872159349), attempt 1, to HEAD `2eef82529a8eb166b9a18898316ae92ce170f02a`, tree `f82634e9b0f290cfce89a35199dfe5d6216fd54f`, and artifact 12466049727. Its zip SHA-256 recomputes as `3299a6b6dc8c25f4ce8b4e38abf9c05507972ffafc3a85abfc766e24f511a08a`, matching retained GitHub artifact metadata. Native JUnit recomputes as `2b249d0c3f273e9766fee45cc9d9323dcfdd574d12d5cc6c8c9c8acee5176536` and contains 33 unique test identities, all failing, zero errors, zero skips. Its run-stage remains RED. I did not refresh GitHub metadata or independently repeat that remote execution.

I inspected selected-module imports and the active root `tests/conftest.py`. Neither they nor repository searches under tests, scripts, src, and workflows reference the packaging test. Applicable test package initializers, root conftest, the `tests.helpers.doc_frontmatter_fixtures` plugin, and the native requirements workflow remain byte-identical to HEAD. The 2406-file frozen nonproduction manifest has only four current mismatches: this bounded test and root's live status-only CHANGE_VALIDATION, TDD_EVIDENCE, and tasks updates. Root confirmed ownership of those status edits. The target is a test module with unchanged top-level initialization; the changed literals and assertions execute only in its two test bodies. It therefore introduces no mapped-test import-context change. Current production inputs intentionally differ from native RED and are assessed by root's later GREEN gates.

Assumptions that could change this acceptance are further edits to the bound test, manifests, specification, mapping, selected files, or their import context. Artifact drift can invalidate the bindings, so root must recheck hashes after reconciliation. A focused pass can coexist with a full-suite regression, so root must retain and inspect the final full-suite result. This review incurs no install or paid-service cost. Root can roll back the bounded repair by restoring the saved before bytes; I performed no rollback or repository mutation.

The poteto-mode Investigation checklist is complete. How was handled as a direct bounded source inspection under the explicit no-subagent instruction. The throughput checkpoint is n/a, read-only investigation. The no-comments check found zero added or removed comments, zero MUST KILL flags, and no suppression changes. No comment deletion, restoration, architect work, encoding, or review rerun was needed. Unslop shaped the report. Prove It Works shaped the decision to recompute real artifact hashes and inspect actual XML disagreement rather than accept summary JSON alone. No extra todo or evidence file was created because this task authorizes only this report.

Next action is root's final canonical/source binding checks and required final quality/full-suite gates. No merge or signing is authorized by this report.
