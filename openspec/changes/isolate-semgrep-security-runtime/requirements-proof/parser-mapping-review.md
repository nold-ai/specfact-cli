# Independent parser mapping review

TL;DR. ACCEPTED for the test-authored mapping and genuine local failing-first evidence described here. The 33-case plan preserves all prior 31 cases and adds only exact pycparser selection and provenance. The final local run has 33 genuine failures, zero errors and zero skips. All 33 supplementary controls pass. Production adoption still requires fresh authenticated native RED for the final source bytes, followed by the required production and release checks.

I am Codex `/root/parser_mapping_acceptance`, an independent AI technical mapping reviewer. I did not author this change, alter repository files, edit the acceptance receipt, execute mapped pytest, install dependencies, synchronize the environment, sign, commit, push, or write to GitHub. I independently ran canonical planning and inspected actual repository and retained artifact bytes. This is AI technical acceptance, without human, merge, publication, or vulnerability-waiver authority.

Review recorded at 2026-10-23T01:25:54.973004+02:00, Europe/Berlin. Worktree is `/private/tmp/specfact-release-20261022/worktrees/hotfix/security-dependencies-0-55-11`. HEAD is `4936750186fcb339913a8710f3034cf1d2be901f`; canonical exact main base is `5262efb0881e4fac7697d629b0530250342bc656`.

The independent canonical command used the owner environment from `/private/tmp/specfact-release-20261022/red-owner/env.sh`, `GITHUB_BASE_REF=main`, and the existing environment Python. It ran `scripts/requirements_evidence_delivery_gate.py --base-ref 5262efb0881e4fac7697d629b0530250342bc656 --required-maturity planned` with outputs solely in `trust-correction-tests/reviewer/`. Initial, refrozen and final planned gates each exited 0. The final full plan is byte-identical to the author's `plan-final.json`; observed maturity remains planned, with implementation evidence not yet available. This gate result is planning acceptance, not a green implementation result.

The canonical identities are:

| Identity | Digest |
| --- | --- |
| Source mapping | `sha256:b192853e22bfc854a30366891d76942d5c2ba9cc47260197c3c4df7bd77c923c` |
| Combined mapping | `sha256:7752d805c6911e719e9aa3dcb985526f8b10f3e587ebfb1d37c5e67c5703718f` |
| Plan identity | `sha256:105b01868f04e3d382b9266bc38111825ca06ad0d00a42d477ac8f5e322e805b` |

The immutable scope and final selected test bytes at acceptance are:

| Source | SHA-256 |
| --- | --- |
| `openspec/changes/isolate-semgrep-security-runtime/proposal.md` | `f8eee7cdcc150eb1562388f0d2290d65901895511a8ab9c1944a2f426a094049` |
| `openspec/changes/isolate-semgrep-security-runtime/design.md` | `431419ae2195fb0f7ef70ef7ce3f5d011c00f4f0d44aa92fc6080ba3f0e9e739` |
| `openspec/changes/isolate-semgrep-security-runtime/specs/isolated-scanner-runtime/spec.md` | `bc00f6593ec6a64bd47bd18933d1d222a34793a035be3f89542234960b056ef6` |
| `openspec/changes/isolate-semgrep-security-runtime/requirements-evidence.yaml` | `cad89859300251d78206a5291077c127e43d2caef687c29c11842e2d36851dab` |
| `tests/integration/test_distribution_build.py` | `af24d9caa1259ecf9789440c516784ea01d4afb34acf8fe9ef377f5f2f46806b` |
| `tests/unit/scripts/test_dependency_trust_review.py` | `bb20822cb58c8f773f8ed7a54628feef2e1eadbf5cc5c53936422223986ee7ac` |
| `tests/unit/scripts/test_security_audit_gate.py` | `5a0c6669c793477bc8cabe518a7f7d20e8db98bb2201be255ed241654c4ed748` |
| `tests/unit/security/test_frozen_dependency_artifacts.py` | `146f45786ccb74b581c36a1a626130c540631e45fa869433d5663e56202b4215` |
| `tests/unit/security/test_frozen_gitpython_compatibility.py` | `284563d0d316d73910c7857afbc76f083d056f803765d79382c8a54ebfedc162` |
| `tests/unit/security/test_frozen_jwt_compatibility.py` | `35b8e0d571bf50a30599ad1634b068d2d3d37e9a46ffd45fe6dfea03771cab16` |
| `tests/unit/security/test_release_dependency_selection.py` | `24d9e8555a072c306fa332e429805d1b9ce16b2f18f245dff2a42ff1d957bd09` |
| `tests/unit/security/test_release_promotion_security_gates.py` | `9f0ede9d55afa5241b42b30660bec58099945a9b636b1a7c57cda69139a10487` |

All eight selected test hashes match the refreshed `prepared-source-hashes.json`. There are 33 unique case IDs, 33 unique pytest node IDs and exactly eight selected test files. Comparing the actual previous quality plan with this plan preserves every prior 31 node identity and adds exactly `test_pycparser_has_current_exact_version_review_record` and `test_reviewed_tooling_versions_match_frozen_export[pycparser-3.12]`. `mapping.tsv`, `selectors.json`, the canonical cases and execution command agree. The 33 supplementary selectors are unique and disjoint from mapped selectors. All previous 23 controls remain unchanged.

Initial acceptance permitted execution before any mapped pytest body ran. After the initial full PR review surfaced three DRY warnings in newly reviewed trust-test scope, root consolidated only five unmapped negative cases into two literal pytest parameter tables. I independently substituted each row into its new function and compared it with its old function. Every fixture input, controlled date, expected error and executable statement matched the original AST. All other function source segments were byte-identical. The five renamed controls map exactly through `dry-fix/old-new-control-mapping.json`; the controls still represent all 33 original scenarios. No helper, policy bypass or suppression was introduced.

The first revised trust-test hash was `79706595f296942cddab04e5eaae41cbe9908b66ed62582ae42ca7ca88bb5881`. A separate comment review then removed only the two redundant new table-function docstrings. I reconstructed that entire prior file exactly by adding those two lines back and verified its full SHA-256. Final source hash is `bb20822cb58c8f773f8ed7a54628feef2e1eadbf5cc5c53936422223986ee7ac`. I issued renewed execution acceptance before root reran the mapped cases. Earlier runs remain in `pre-comment-red/` and do not stand in for this final run.

The new record test asserts exact version, complete wheel URL, complete artifact SHA-256, classification, UTC review date 2026-10-22, expiry 2026-11-04, and cryptography/CFFI/parser transitive path. The selection case reads actual lock and hashed delivery export and asserts exact version plus official registry origin. These are release invariants with direct artifact observations. They do not construct passing expected production data inside the test.

The two wrong-artifact and wrong-package fixtures now derive only baseline version and controlled review-day input from the current record. Their mutations and exact rejection expectations remain explicit. The date injection is confined to those deterministic fixture calls. The real `-S` subprocess test still passes no date override, and the production checker still uses `today or date.today()`. The 3.0 block and equivalent spellings, explicit expiry, prohibited wheel names and lock records, scanner floor, and wrong source/hash/package controls remain present and pass locally. No CVE waiver was created. The exact MCP and OpenTelemetry contracts retain their separate IDs and 2026-11-04 inclusive expiries.

Root's final actual execution ran the exact reviewed commands. I independently parsed both JUnit files, compared every node identity and order with its command and plan, checked uniqueness and counts, and read all 33 failure messages. I also inspected the substantive build and Git traces.

| Evidence | Observed result | SHA-256 |
| --- | --- | --- |
| `trust-correction-tests/mapped.xml` | 33 failures, 0 errors, 0 skips; process exit 1 | `99b63cef7ee46814a86ca3e66f1c2bebffc280e72e113389a2990b0c659fd697` |
| `trust-correction-tests/controls.xml` | 33 passes, 0 failures, 0 errors, 0 skips; process exit 0 | `ac3479cf77e1dbcc6ff99744fbc58bb352d6115a55f036f3f3d3c0eec61f7686` |

The mapped execution began at 2026-10-22T23:23:01.316715+00:00 and finished at 23:23:03.178972+00:00. Controls followed from 23:23:03.179383+00:00 through 23:23:03.878956+00:00. These are 2026-10-23 Europe/Berlin. Actual argv and exit records match `mapped-command.json` and `controls-command.json` exactly. The failures remain failures. They are accepted failing-first observations, without changing the machine outcome to pass.

Each reviewed failure has a substantive expected cause:

| Case | Actual disagreement |
| --- | --- |
| `PYCPARSER-EXACT-PROVENANCE-REVIEW` | Committed record or frozen selection is 2.22; required exact version is 3.12. |
| `OTEL-EXACT-CVE` | Actual audit gate returns 1 instead of the required 0 for an allowed exact advisory/date. |
| `OTEL-EXACT-GHSA` | Actual audit gate returns 1 instead of the required 0 for an allowed exact advisory/date. |
| `OTEL-EXPIRED` | Gate rejects vulnerability generally, but lacks the required invalid-date record diagnostic. |
| `OTEL-EXPIRY-DAY` | Actual audit gate returns 1 instead of the required 0 for an allowed exact advisory/date. |
| `OTEL-FUTURE-REVIEW` | Gate rejects vulnerability generally, but lacks the required invalid-date record diagnostic. |
| `MCP-EXACT-CVE` | Actual audit gate returns 1 instead of the required 0 for an allowed exact advisory/date. |
| `MCP-EXACT-GHSA` | Actual audit gate returns 1 instead of the required 0 for an allowed exact advisory/date. |
| `MCP-EXPIRED` | Gate rejects vulnerability generally, but lacks the required invalid-date record diagnostic. |
| `MCP-EXPIRY-DAY` | Actual audit gate returns 1 instead of the required 0 for an allowed exact advisory/date. |
| `MCP-FUTURE-REVIEW` | Gate rejects vulnerability generally, but lacks the required invalid-date record diagnostic. |
| `MCP-OFFICIAL-EXCEPTION-EXACT` | Frozen export has semgrep==1.175.0 instead of semgrep==1.179.0. |
| `CERTIFI-COMPROMISED-ROOT-ABSENT` | Downloaded hash-verified frozen certifi contains prohibited root fingerprint 86a1ecba...a36bbe6b. |
| `PYJWT-OPTIONS-AND-EXPIRY` | Actual old wheel mutates caller options, adding seven verification fields. |
| `RELEASE-0-55-11-VERSION-SOURCES` | Current project version is 0.55.4 instead of 0.55.11. |
| `SOURCE-DISTRIBUTION-BUNDLED-MANIFEST` | Backend reaches wheel-from-sdist and cannot find forced include modules/bundle-mapper. |
| `GITPYTHON-CREATE-ABSOLUTE-METADATA` | Old wheel reaches mocked clone once and reports rejected=False, boundary_reached=True. |
| `GITPYTHON-CREATE-GIT-METADATA` | Old wheel reaches mocked clone once and reports rejected=False, boundary_reached=True. |
| `GITPYTHON-CREATE-GIT-SHORT-NAME` | Old wheel reaches mocked clone once and reports rejected=False, boundary_reached=True. |
| `GITPYTHON-SUBMODULE-CONTAINMENT` | Old wheel reaches the explicit clone boundary sentinel after outside-checkout lookup. |
| `CERTIFI-FROZEN-SELECTION` | Frozen version differs from the exact required reviewed version. |
| `GITPYTHON-FROZEN-SELECTION` | Frozen version differs from the exact required reviewed version. |
| `HATCHLING-FROZEN-SELECTION` | Frozen version differs from the exact required reviewed version. |
| `PACKAGING-FROZEN-SELECTION` | Frozen version differs from the exact required reviewed version. |
| `PYCPARSER-FROZEN-SELECTION` | Committed record or frozen selection is 2.22; required exact version is 3.12. |
| `PYJWT-FROZEN-SELECTION` | Frozen version differs from the exact required reviewed version. |
| `PYTHON-DISCOVERY-FROZEN-SELECTION` | Frozen version differs from the exact required reviewed version. |
| `URLLIB3-FROZEN-SELECTION` | Frozen version differs from the exact required reviewed version. |
| `VIRTUALENV-FROZEN-SELECTION` | Frozen version differs from the exact required reviewed version. |
| `JEKYLL-FEED-LOCKED` | Actual Gemfile.lock lacks the required exact plugin version. |
| `JEKYLL-REDIRECT-FROM-LOCKED` | Actual Gemfile.lock lacks the required exact plugin version. |
| `JEKYLL-RELATIVE-LINKS-LOCKED` | Actual Gemfile.lock lacks the required exact plugin version. |
| `JSON-REVIEWED-FLOOR` | Gemfile has >=2.19.9 and lacks required >=2.21.2 with <3 bound. |

For the source distribution, the trace explicitly reaches `hatchling.build.build_wheel`, forced-inclusion traversal, and `FileNotFoundError: Forced include not found .../specfact_cli-0.55.4/modules/bundle-mapper`. This is the packaging behavior under test, not a missing tool or collection failure. For submodule update, the trace traverses the old GitPython outside checkout lookup and reaches the deliberately mocked `_clone_repo` sentinel with `AssertionError: clone boundary reached`. For creation, all three prohibited paths report one clone call, `rejected=False`, and `boundary_reached=True`. The ordinary and `.github` positive controls pass, showing the mock boundary can be reached for valid paths. The certifi test reads the actual hash-pinned wheel trust store and observes the prohibited fingerprint. The JWT test installs the pinned old delivery package in an isolated target and observes actual options mutation. No setup exception is counted as behavioral proof.

The smoke fixture changes only two environment removals, `PYTHONPATH` and `PYTHONHOME`, before the existing bootstrap. All three real bootstrap commands, real CLI invocation, CLI success marker, and parent package inventory comparison remain. I inspected the actual child probe source and before/after JSON. Before the edit, the sentinel module imports through inherited PYTHONPATH and the owner-default src path is visible; both child cases inherit PYTHONHOME. After the edit, both variables are absent, neither sentinel nor parent src is visible, and both children exit 0. This verifies environment construction with real child Python. It does not claim that the complete bootstrap or CLI smoke ran successfully for the current correction.

I read the managed official-source investigation at `/Users/dom/.codex/state/plugins/codex-security/scans/security-dependencies-0-55-11/artifacts-911581b64ba03e8c6a2c66516d91e6dc5c452f0bbad92e640370aae36e201715/artifacts/pycparser-supported-replacement-investigation.md`, SHA-256 `3421322320d59bf16d339ecb6bc0f6ffdc5f02bd20ade001d2290be7cd1faacc`. It records fresh official PyPI, immutable GitHub and exact-wheel Socket observations accessed on 2026-10-23 Europe/Berlin. I independently recomputed the five retained download hashes, verified all eight wheel package files against both the official sdist and immutable upstream archive at `3ec766b7cd94724cba714296509604597ea4ce4e`, checked wheel RECORD digests and lengths, and verified the identical packaged/upstream/sdist BSD license SHA-256 `0a9e78156ae8b96caf1b4f11ac2df424b83de29736f9e757630548a6272fdf90`. The retained wheel SHA-256 equals the exact contract `a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e`.

That evidence supports factual source-provenance review. It discloses optional preprocessing, filesystem access, URL strings, and the license-heading classification. It does not support an alert-free claim, exhaustive parser safety claim, all-platform compatibility claim, or organization-specific Socket PR approval. I did not rerun the investigator's installs or compatibility probes and do not claim to have done so.

The proposal and TDD companion clarification correctly limit prior Semgrep 1.179.0 runtime probes and schema 1.2 review to pinned fixture 0.48.15 with ordinary PATH passes. They distinguish the published main 0.51.2 and dev 0.51.4 capsule path, which clears the environment, uses `-I -S`, dedicated PATH and capsule version maps, and returns UNKNOWN on failure without host fallback. I inspected the retained source trace. The text explicitly states that signature verification and capsule execution did not run. It makes no false signature or capsule-runtime assurance claim.

The actual initial whole PR Code Review had three DRY warnings and six infos. The warnings were real review findings and triggered the table repair. The initial report remains intact. The final post-comment actual report is schema 1.2 run `review-604c5557-2339-4f01-b564-0e3a6566beb7`, timestamp `2026-10-22T23:22:39.529594Z`, `PASS_WITH_ADVISORY`, exit 0, zero errors, zero warnings and six infos. Its SHA-256 is `ba003b07c462f10a2fefcffeaa1ed41c5e201275ee526bcee855747a2d9135b3`, byte-identical to actual `.specfact/code-review.json` at inspection. The actual argv covers all 13 PR Python paths. No machine report was normalized, and the six findings remain visible.

My fresh source-specific dispositions preserve those six informational design judgments:

| Report location | Disposition and source reason |
| --- | --- |
| `tests/integration/scripts/test_runtime_discovery_smoke.py:58` | Preserve. The 56-line test owns disposable environment construction, three bootstrap commands, actual CLI execution and unchanged parent inventory. Moving these into a helper would hide the tested isolation boundary. The two added removals have actual child-interpreter evidence. |
| `tests/unit/docs/test_docs_validation_scripts.py:189` | Preserve. The 45-line test's frontmatter and navigation YAML are literal fixture content for route resolution. Compressing or extracting those literals would separate the tested document from its assertion. |
| `tests/unit/security/test_frozen_jwt_compatibility.py:37` | Preserve. The 48-line test keeps exact export parsing, pinned isolated install, child JSON observation and separate options, expiry, signed and padded-token outcomes together. A comprehension would not replace these distinct steps. |
| `tests/unit/security/test_release_promotion_security_gates.py:244` | Preserve. The 44-line function checks trusted materialization, forbidden artifact reuse, trusted imports, consumer execution order and timeout. They are distinct integrity invariants with explicit literal workflow inputs. |
| `tests/unit/security/test_release_promotion_security_gates.py:393` | Preserve. The 53-line function asserts exact official graph and two separate exact expiring advisory records, including mitigation/rationale presence. The record literals are the reviewed domain contract. |
| `tests/unit/security/test_release_promotion_security_gates.py:545` | Preserve. The 43-line test supplies the full external authority CLI boundary and asserts fail-closed behavior for invalid UTF-8. Extracting that argv hides which inputs the malformed-byte invocation actually exercises. |

The final source hashes for all 13 reviewed Python paths are in `reviewer/final-code-review-source-binding.json`. The selected test and frozen boundary hashes are also in `reviewer/local-evidence-verification.json`. Earlier `reviewer/code-review-source-binding.json` remains historical, before removal of the two docstrings.

All twelve restored production paths still match `restoration.json`, including absent new Ruby probe and workflow paths. Trust register SHA-256 remains `aed15e900850691789baedbcd7ee6c82cef6a80e8e09bf95ab9ac8f23329a875`; checker SHA-256 remains `4433fabc6412476764da49548e44643def974ae482bf27e78ec2ed211d15970c`. Held docs-floor file SHA-256 remains `29aae452c99fa57f49df3758951f294a8cdfbfb22c5df1b77631a8ea003a9c98`. At initial inspection all 2404 nonowned tracked paths matched the preparation baseline. The bounded table amendment changed only the trust test. The Git index remains empty at final acceptance.

The unchanged real-clock refusal is actual retained evidence in `advisory-green/dependency-trust.log` and `smart-test-full.xml`. It reports pycparser 2.22 expired on 2026-10-22, including the actual `-S` child exiting 1. I verified the restored register/checker identities and the unchanged real-clock test function. I do not relabel that earlier full suite as current or passing. No clock was frozen to bypass expiry. The later changed production state must pass the real-date gate again.

At this acceptance, active status prose and receipt still truthfully say pending. Root may now reconcile those operational records with this verdict and actual local metrics. This report binds the listed proposal, design, spec, mapping and final tests, rather than requiring the pending-status files never to change. Root must rerun canonical planning after adding the repository-relative review and receipt, confirm identical canonical identities and immutable test/spec hashes, and retain the old receipts as history. The authentic 31-case native proof cannot approve the new test bytes.

Confidence is high for mapping identity, preserved control semantics, source correspondence, actual local failure causes and the bounded review dispositions. It is limited for platform/runtime behavior that has not run. Artifact-source mismatch would invalidate evidence, so root must keep these exact hashes through test-only commit and native proof. Date expiry can affect UTC CI independently of Berlin observations, so actual-date gates stay mandatory. Earlier proof can be misapplied after a byte change, so fresh native RED and then production GREEN must bind the new commit and complete test/import context.

This review used temporary artifact writes and existing local Python only. No release or paid-service side effect occurred. Rollback is restoring the saved bounded test/spec diff; root owns that operation. The internal wiki authorization/update remains a separate recorded follow-up. Full smoke, frozen graph/export refresh, parser dependency floors in both declarations, new exact provenance record, audits, signatures, all required local/native gates and final independent production review remain open.

Test Behavior, Not Implementation shaped the decision to require direct artifact and child-process outcomes. Prove It Works shaped independent canonical planning, hash recomputation, literal-row equivalence checks and inspection of actual XML failure traces. These principles were read in this review session.

Next action is root's status/receipt reconciliation, normal test-only hooks and commit, followed by authentication of a fresh native 33-case RED artifact. This acceptance does not open production adoption before that native gate.
