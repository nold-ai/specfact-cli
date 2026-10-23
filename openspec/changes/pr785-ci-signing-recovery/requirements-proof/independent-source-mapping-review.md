# Independent final source, test and mapping acceptance

TL;DR. **ACCEPT this frozen test/spec/mapping package for the bounded CI signing probe implementation unit.** The actual native source-binding defect is corrected. All 68 complete case objects and the unchanged test bytes are preserved. No substantive acceptance blocker remains at this pre-implementation boundary. This verdict establishes neither implementation correctness nor live signing, dispatch authority, root anchoring or release readiness.

Reviewed independently on 23 October 2026, Europe/Berlin, by `/root/signing_probe_source_acceptance`. Count this review once. I did not author the package or prior reports. My only file write is this private report. I performed no staging, commit, API operation, merge, delegation, full suite or production edit. The writer was paused. I read the requested poteto-mode skill and Codex mapping, Prove It Works and unslop, repository AGENTS/bootstrap/index/checklist, OpenSpec/TDD and quality rules. Prove It Works changed my checks to the actual native importer, actual pinned evaluator, exact staged bytes, fresh selector collection and genuine structural mismatch.

I read the accepted architecture, original rejected review, round2 acceptance and subsequent actual `canonical-test-authored.md` failure, the complete operational change and test file, and round3 handoff, conservation, selector, command/raw-log, hash, final-boundary and actual source-gate artifacts. Private relative paths below resolve under `/private/tmp/specfact-release-20261022/signing-recovery/probe-implementation/round3/`.

## Frozen package

Worktree `/private/tmp/specfact-release-20261022/worktrees/ci-signing-recovery`, branch `codex/pr785-ci-signing-recovery`, HEAD `3ce8248e0cb4249413f738759d8e5d89cdaca794`. I independently hashed all eight files and compared each to its index bytes. Exactly these eight paths are staged. There is no unstaged diff. `.github/workflows/specfact.yml` has no HEAD diff. `scripts/pr785_signing_recovery.py`, `ci/recovery/pr785-signing-inputs.json` and any active change receipt remain absent.

| Repository-relative path | SHA-256 |
| --- | --- |
| `tests/unit/scripts/test_pr785_signing_recovery.py` | `c4d103e648672d325e3ffbae5377fe89b933b56c83f37f741d00347a97ad02b4` |
| `openspec/changes/pr785-ci-signing-recovery/.openspec.yaml` | `54c2a6955b514abf783374521da3b6364c1d6b221970ad9faa7124a7e1124528` |
| `openspec/changes/pr785-ci-signing-recovery/TDD_EVIDENCE.md` | `a11c62088ee105b98b30902dbcd0407969dd9442d30de79d9a6aafe15eb061da` |
| `openspec/changes/pr785-ci-signing-recovery/design.md` | `0694b40887a4d19d0028109ee873e4b153603c77d0482a86be8566bcf416a831` |
| `openspec/changes/pr785-ci-signing-recovery/proposal.md` | `58de922054361f9d70954e5289ccdae92922e6de9dde3b689f43fcf9fb96cbad` |
| `openspec/changes/pr785-ci-signing-recovery/requirements-evidence.yaml` | `22686ffa029be81163bdb8cc0c5c11b555f7e66074e1301cd9c1f0b5800ab4e3` |
| `openspec/changes/pr785-ci-signing-recovery/specs/pr785-signing-probe/spec.md` | `4c617242dfedbe647a407a1efc6c1f36a0ba0bef529d63873ed7cf24b670501d` |
| `openspec/changes/pr785-ci-signing-recovery/tasks.md` | `78e842b57aeea6d4fc6e7bc53580405357dd0831ccc53eff0f7659d2e9282c17` |

## Actual source binding and preserved semantics

Round2's standalone evaluator passed grammar but did not check native source binding. The subsequent actual delivery command correctly rejected its nested scenario IDs. I inspected the current native importer in `src/specfact_cli/requirements/importers.py` and the pinned adapter's `_source_mapping_findings`. The importer derives IDs from Requirement headings. The adapter requires every mapped `scenario_id` to equal the native requirement ID suffix.

I independently ran `import_openspec_change` against the actual change. It returns no diagnostics and exactly the eight IDs below, equal to the mapping keys. Every case has the required matching scenario suffix.

| Native requirement ID | Cases |
| --- | --- |
| `openspec:pr785-ci-signing-recovery:pr785-signing-probe:existing-normal-validation-triggers-are-removed` | 2 |
| `openspec:pr785-ci-signing-recovery:pr785-signing-probe:context-mismatch` | 19 |
| `openspec:pr785-ci-signing-recovery:pr785-signing-probe:ref-or-source-drift` | 25 |
| `openspec:pr785-ci-signing-recovery:pr785-signing-probe:signature-and-identity-verification` | 2 |
| `openspec:pr785-ci-signing-recovery:pr785-signing-probe:signing-refusal` | 17 |
| `openspec:pr785-ci-signing-recovery:pr785-signing-probe:root-acceptance-remains-pending` | 1 |
| `openspec:pr785-ci-signing-recovery:pr785-signing-probe:later-refusal-preserves-earlier-successful-responses` | 1 |
| `openspec:pr785-ci-signing-recovery:pr785-signing-probe:early-context-refusal-remains-unauthenticated` | 1 |

I independently parsed `mapping-before.yaml` and the actual final mapping. All 68 unique complete case objects compare equal by `case_id`. I independently reconstructed each old scenario's associated SHALL paragraph and WHEN/THEN clauses from `spec-before.md`. Each appears verbatim once in its corresponding new same-title Requirement/Scenario block. This is a representation correction without loss of behavioral constraints. Proposal/design scope remains coherent with the accepted auxiliary-only, probe-only architecture.

I checked conservation records against the original audit JSON and root grounding artifact. All ten source commit records remain equal, with normalized original-source SHA-256 `8b11607cf78ad8c065e54dd2f83b4c6103ec8da0e362028162f139e450681389`. The fixed baseline tree remains `4c9ba46b2ace65cd8df0fcd5a77c2b14a42f599c`, inert blob `c00d710f49c952dee0ef3886acf476c7e49e0a8e` and probe tree `4b2cf05809c1cf687e4eae17a770cd33c97eff72`. I checked the retained grounding record and unchanged explicit test assertions. Round2 independently reconstructed those Git hashes; I did not repeat that reconstruction.

## Canonical planned evidence

I independently verified the fixture is clean at commit `69f075819be5e1ceca1446b026b0417f19e584ca`, tree `5d0b8e66c6cd467e6b1ad9d582e24c66b907e205`, matching `ci/module-fixture.lock.json`. I imported its actual lifecycle evaluator. Its source SHA-256 is `9352b1acde9f520e577657b5812e9b129a8b018ddd76113684b829e7b395d654`.

Fresh `evaluate_mapping(mapping, required_maturity="planned")` returns pass, planned and no findings. Its complete source plan equals the retained actual delivery report's source plan. The retained final command is the real staged `scripts/requirements_evidence_delivery_gate.py --staged --required-maturity planned`, with recorded exit 0 and released CLI v0.55.11 stdout. `source-gate-final.json` reports one selected source, passed/pass/planned, 68 cases, no findings and implementation evidence `not-yet-available`. I did not rerun the snapshot-producing delivery command or create a receipt.

Exact identities have distinct roles:

- Source canonical mapping digest is `sha256:7d98da7920efa7f4b0c53df122e6e640e182ce4032ab3b3450014410aeef76d7`.
- Per-source nested plan digest is `sha256:100851390de754bcf6152b331f96ad02b6e76cb4d6aabd4ecefd707a6bca5548`.
- Normalized plan-file aggregate mapping digest is `sha256:9773111405321c7c7de84d98ea3dee0420ace62f59c41bbc0d6b1713760b8f49`.
- Normalized plan-file nested plan digest is `sha256:97a798b494661d3b7f8a5fc846d0c50341e34dc1676323753357868ecf06c530`.
- Normalized `plan_identity_digest` is `sha256:9a85b4882b5ef9fd9fe842c754a3d7c079c6405548ecbfa56ca1435a2f59d2e5`.

The raw YAML hash is not the source canonical mapping digest. Root's review receipt must bind the intended source identity. No accepted/test-authored plan exists yet. The two preliminary gate artifacts report `gate-exception:CalledProcessError` with zero imports. They supply no semantic source-binding verdict. The separate successful final artifacts are the retained actual delivery evidence.

## Prior corrections and meaningful RED

Prior P1 remains corrected. Malicious values are preserved with safe explicit parameter IDs, including `shell-stage`, `post-ref`, `patch-main-ref`, `delete-main-ref`, `external-url`, `parent-path` and `commit-query`. Fresh cache-free, bytecode-free pytest collection exits 0 with 68 unique selectors. Mapped and collected sets match exactly and match the retained selector proof.

Prior P2 remains corrected in the actual unchanged test bytes. The successful receipt test exercises `main()` through the real adapter with fake transport and asserts persisted exact manifest/run/attempt/executor/context identities, both verified objects, false CI/root anchor claims and every successful raw response in order. The later-refusal test refuses the tree request after the first verified object and checks that object, immutable identities, raw-response preservation and credential/error-body exclusion. Early unapproved-actor refusal has its own matching unauthenticated scenario. These are adequate authored assertions for this boundary, with execution pending implementation.

I freshly reran only `test_executor_is_dispatch_only`, using `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -o addopts= -p no:cacheprovider` and the exact selector. Exit 1 has one assertion failure and zero errors. Its diff reports extra `push` and `pull_request` trigger keys in the unchanged original workflow. Retained `red.xml` likewise reports tests=1, failures=1, errors=0, skipped=0 at `2026-10-23T08:11:51.554374+02:00`. The other 67 cases remain authored and collected only. No absent-module error is counted as RED, and no all-case RED or GREEN is claimed.

I inspected retained passing Ruff check/format, corrected YAML lint, strict OpenSpec validation and whitespace evidence. I did not rerun these tools. The earlier indentation failure remains recorded. The existing independent round2 comment verdict applies to identical test bytes; I also confirmed zero tokenizer comments and zero AST docstrings without editing.

## Evidence hashes and limits

| Private artifact | SHA-256 |
| --- | --- |
| `source-gate-final.json` | `4d8834d61824a4631273ccf4303ba9779c9c44233628f4b4f540e02cd39c26eb` |
| `source-gate-final.md` | `d08484628a0993c1d3ab8ebcff6d4eac745bdb35022d7b64498668163653cf98` |
| `source-gate-final-plan.json` | `2cdc329c483fd0d319743c35126bd75e4b575f0aa6789fb27958ae66c9eb773c` |
| `commands.json` | `f60d95f40718fd35259a384d8668f22e280af911877a9cb93a9c63baf9372f13` |
| `source-conservation.json` | `9ebafebdcc04c3612a256c623db80d0cbaeaaca2e0a8c76bda7fd8be77f0336c` |
| `selector-proof.json` | `8e95cff772ab584d6f5a6eb9a14329aa94cf3b07120ed466943ca2f057e8be3d` |
| `package-hashes.json` | `ee61b92389521cd0a2ec0ffd13eef963d2215ba9aa7879f04adba172a628d04a` |
| `final-boundary.json` | `25e76df5b4bd4eede0780b2ea2a4c73f87ec1bd56b2964d64f6638f7a559aab2` |
| `red.xml` | `d5a723fe28c0de990d61966470a5d6101df54bd300be0a230c0ca17f035463a8` |

Confidence is **High** for preserved semantics, native binding, planned evaluator identity, selector completeness and genuine structural RED because each was independently checked against actual bytes. Implementation behavior and live signing remain unestablished. Changed package bytes, fixture identity or expansion beyond the bounded probe would invalidate this verdict.

The earlier transport/workflow limits remain implementation review targets, including redirects, malformed successful JSON, lost responses/timeouts, guard ordering, malformed later-object/readback fields and complete shell/job/upload configuration. They are not new blockers against this authored package. Fake transport cannot establish live signature or run provenance; root must authenticate actual CI/API/artifact evidence. Main guards cannot atomically lock main; implementation must abort observed drift and retain the no-ref-write boundary. Byte drift requires rehash and renewed applicable review. No external cost or CI runtime was incurred. Rollback is abandonment of this auxiliary package/report, with no release ref touched.

Next action is root-owned real review receipt creation against these frozen source bytes, then the actual staged test-authored delivery gate. After that gate passes, proceed with the bounded probe implementation and its required quality, independent source/security and live acceptance gates. Later recovery stages, dispatch, anchoring, release readiness, merge and publication remain outside this verdict.
