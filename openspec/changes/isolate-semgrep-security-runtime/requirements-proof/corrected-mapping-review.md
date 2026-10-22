# Corrected dependency release mapping review

TL;DR. Accepted for the corrected 19-case technical mapping. This is independent AI review, not human approval, accepted native RED, permission to merge, or release readiness. Production edits still require a fresh authentic native RED run for the corrected test-only commit. Confidence is high for the mapping correction because the staged diff, exact test bytes, native reconciliation rule, and original CI JUnit agree.

Reviewed on 2026-10-22, Europe/Berlin, by Codex agent `/root/release_corrected_mapping_review`. The checkout is `/private/tmp/specfact-release-20261022/worktrees/hotfix/security-dependencies-0-55-11`, branch `hotfix/security-dependencies-0-55-11`, HEAD `dd1b4121944f247c4d5dff0903902e2721d8c1a6`. The review is limited to the staged correction and its supplied evidence. No test suite, build, hook, signing action, commit, or production edit was performed. Only this report was written. Throughput checkpoint is not applicable to this read-only review. The poteto-mode investigation and unslop guidance informed the evidence-first report.

The reviewed staged files are `TDD_EVIDENCE.md`, `design.md`, `requirements-evidence.yaml`, and `requirements-proof/review-evidence.json` under `openspec/changes/isolate-semgrep-security-runtime`. The working bytes equal their staged blobs. The review record correctly remains pending with a placeholder digest during independent review. The earlier `requirements-proof/independent-review.md` is historical and does not provide acceptance for this correction.

## Verdict basis

The correction removes precisely the 15 already-passing controls from the native failing-first mapping. It preserves the other 19 case records semantically, every requirement, all scenario IDs, all rationale/stakeholder records, and every touchpoint. No specification, test assertion, fixture, helper, application code, audit policy, native lifecycle, hook, or workflow changes occur in this staged correction. `git diff dd1b412 -- tests scripts .github ci pyproject.toml uv.lock requirements/ci/locked.txt` is empty.

The pinned lifecycle at `/Users/dom/.codex/worktrees/core-review-reset-fixture/specfact-cli-modules/packages/specfact-requirements/src/specfact_requirements/requirements/lifecycle.py:511` requires each RED selector to have exactly one `failed` outcome. The initial assumption that a RED plan could also contain passing controls was incorrect. The correction follows that rule without changing it.

I independently matched every retained exact selector against the original artifact's JUnit. All 19 have one `<failure>` and no `<error>` or `<skipped>`. All 15 omitted selectors have passing outcomes. The original 34-case set equals the corrected 19 plus the 15 supplied supplementary records. There are no newly omitted failing cases.

| Requirement scenario ID | Retained cases | Original CI failure basis |
| --- | ---: | --- |
| exclude-compromised-certificate-authorities-from-delivered-trust | 1 | Frozen certifi CA data contains the named fingerprint. |
| reject-submodule-checkouts-outside-the-repository | 1 | Frozen GitPython reaches the patched clone boundary for `../outside`. |
| preserve-jwt-verification-options-and-compatibility | 1 | Frozen PyJWT mutates caller options during inspection. |
| select-the-reviewed-compatible-tooling-graph | 4 | Hatchling, urllib3, virtualenv, and python-discovery select old versions. |
| bound-the-temporary-official-mcp-advisory-exception | 6 | Old Semgrep selection, missing exact exception acceptance, and missing date-specific register diagnostics. |
| rebuild-the-source-distribution-with-its-bundled-manifest | 1 | Ordinary offline sdist-to-wheel build cannot find the forced bundle-mapper include. |
| select-the-reviewed-documentation-dependency-versions | 4 | Three plugin lock selections and the JSON declaration do not match the reviewed targets. |
| publish-one-coherent-patch-version | 1 | Version metadata remains 0.55.4. |

The eight IDs above match the actual eight `#### Scenario` headings after native-style slug normalization. The seven test files remain byte-identical to HEAD.

The 11 artifact controls cover one wrong SHA256, six malformed wheels, and four disallowed URL forms. These validate test support that already refuses hostile input. They do not require a production fix. The four other controls cover a different MCP version, unrelated advisory, mixed advisories, and skipped dependencies. The existing audit gate already fails these inputs. All 15 remain necessary after the exception is added. Their original passing results cannot establish that the future exception stays narrow, so their final rerun is mandatory.

For MCP-EXPIRED and MCP-FUTURE-REVIEW, the existing gate already returns failure. Their RED assertions fail because the empty committed register produces the generic vulnerability diagnostic instead of `not currently valid`. These cases therefore demonstrate incomplete register/date-specific behavior. They are not evidence that the old gate accepted expired or future exceptions. Keeping them in the plan is technically valid with that limitation stated. The exact record test and the exact-CVE, exact-GHSA, and expiry-day cases provide the substantive positive change coverage. All negative cases must pass after the exact register entry is added.

The normal Python 3.12 full-suite step remains in `.github/workflows/pr-orchestrator.yml`, invoking `python tools/smart_test_coverage.py run --level full`; the Python 3.11 compatibility step invokes `python -m pytest -r fEw tests/unit tests/integration`. The affected test files remain in those directories with no new skip or deselection. This establishes retained configuration, not a claim that final CI has already passed.

The 12 intended production touchpoints remain mapped. They are `pyproject.toml`, `uv.lock`, `requirements/ci/locked.txt`, `ci/vulnerability-audit-exceptions.json`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py`, `CHANGELOG.md`, `docs/Gemfile`, `docs/Gemfile.lock`, `scripts/check_jekyll_dependencies.rb`, and `.github/workflows/docs-dependency-checks.yml`. Native cases cover dependency/artifact behavior, declarations, version metadata, and source-build inclusion. Real Ruby behavior, published runtime equality, signed-manifest preservation, and changelog scope remain separate final checks as the design states. Mapping touchpoints does not itself prove those checks.

## Immutable evidence and identities

Original GitHub run [39809800598](https://github.com/nold-ai/specfact-cli/actions/runs/39809800598) is recorded at HEAD `dd1b4121944f247c4d5dff0903902e2721d8c1a6`, artifact ID `12440155998`. Local evidence is under `/private/tmp/specfact-release-20261022/native-red/run-39809800598-artifact-12440155998`. I checked the downloaded archive SHA256 against its saved GitHub artifact metadata and each extracted file byte-for-byte against its archive member. I did not independently refetch GitHub metadata in this read-only review.

- Archive SHA256 is `b7c7d2d8b41daf8441b1b7ec2461ce3916ccb64b5be0e51d5e9daf6e66310c43`.
- Original report SHA256 is `87122f8964ab3d8188e4ea9f9c8d74f3b5f3d65ccd69be3c23d7cd8a654aaa8c`.
- Original JUnit SHA256 is `5d0c4f72df0252e79ce1d49a948e9efe8e3a345e779390ec538cb74768768d24`.
- The unchanged report says `gate_decision=fail`, `observed_maturity=incomplete`, and `required_maturity=red`, with exactly 15 `red-proof-passed-not-failed` findings.

I independently recomputed the corrected digests using the pinned lifecycle's typed canonical JSON encoding and normalized plan construction. The supplied corrected planning report is only `planned`, despite its passing planning verdict.

| Identity | SHA256 |
| --- | --- |
| Staged mapping file bytes | `55da4dc879b2fca6a78b383ad10920630d279e1d1ff1beb1a79d335d26323e42` |
| Native source mapping digest for review binding | `1abe2b6dc3e8a294795a00236803b002b98ad02ec05b22b2b0deb2cbf13a2020` |
| Native combined mapping digest | `e787fd8484005fa90644edfb5060dbebc15632195957652dd1ef03b4c9adcc9f` |
| Native plan digest | `02f8055fb0ddf38115533549fdb0dd093f001f7a99786e450e05e49626b0acf2` |
| Native normalized plan identity digest | `7d0b5500870357f8c6d802e3e33e1d51dc274441157e679a3ea55417f7ec8acb` |

The source mapping digest, with the `sha256:` prefix, is the acceptance digest for this independent technical mapping review. The combined mapping digest is the normalized execution identity and must not be substituted for the source digest in the source review record.

| Unchanged test file | SHA256 |
| --- | --- |
| tests/integration/test_distribution_build.py | `af24d9caa1259ecf9789440c516784ea01d4afb34acf8fe9ef377f5f2f46806b` |
| tests/unit/scripts/test_security_audit_gate.py | `d0b1fcb16185b1908b6abc53e0c68e7baf04ede2b395492fa4d4cbb37ed8c3b9` |
| tests/unit/security/test_frozen_dependency_artifacts.py | `146f45786ccb74b581c36a1a626130c540631e45fa869433d5663e56202b4215` |
| tests/unit/security/test_frozen_gitpython_compatibility.py | `527d78a6dd07e04e00fefa06632cfa320725f035c22d988e0a1741a455ece728` |
| tests/unit/security/test_frozen_jwt_compatibility.py | `35b8e0d571bf50a30599ad1634b068d2d3d37e9a46ffd45fe6dfea03771cab16` |
| tests/unit/security/test_release_dependency_selection.py | `7e41674b9b6c2bfb210f50084125821e54c662b079d932be2ba2ebb787bf876f` |
| tests/unit/security/test_release_promotion_security_gates.py | `dcf6de107fea93357421daae229bbdd144d0e592d56b28c58b0429aa4ddd9531` |

The typed canonical digest of the mapping from those seven paths to their SHA256 values is `sha256:9126c9f4d25cb03d55890fa5dd2bc5a365593c6c13aded5b3cc6deb2f337a015`. This inventory is not a substitute for the required full test/import/conftest freeze.

## Limits and next actions

No blocking finding remains in this 19-case planning correction. Acceptance assumes the reviewed scope remains dependency-only 0.55.11 with published 0.55.4 runtime preservation except version, the exact MCP 1.29.0 advisory exception through 2026-11-04 inclusive, ordinary CI/hooks, and CI-only signing. Any changes to selected tests, helpers, ancestor conftest files, transitive imports, native policy, or exception scope require renewed validation and may invalidate this verdict.

The principal failure modes are treating the failed original artifact as RED, allowing a broad exception to pass because the 15 controls are no longer selected by the native plan, or reading Python metadata checks as proof of Ruby/runtime compatibility. Mitigations are a new accepted native RED artifact bound to the corrected commit, a required final full-suite run including every supplementary control, and retained real Ruby plus published-runtime and signature evidence. The design and task list already require these checks.

The coordinator should bind this real independent review to the source digest, commit only the reviewed test/planning correction with normal hooks, obtain authentic accepted native RED for that new commit, and freeze the test closure before production changes. Final verification must use the same native mapping/plan and rerun all 15 controls. Keep the original failed artifact and earlier review historical. Complete the documented internal wiki follow-up through the coordinating agent. No merge or publishing is authorized by this report. Rollback remains the unmerged PR diff. This review incurred only local read/hash work; CI runtime and final release costs were not measured.

## Proposal change after the earlier review

The coordinator reported PR 785 review comment `4350610610` concerning the prior proposal hash. I independently compared `proposal.md` from the earlier reviewed tree `9e61234b9130a48d8c7fac8e603881ec199176a7` to current committed HEAD `dd1b4121944f247c4d5dff0903902e2721d8c1a6`, read the current proposal in full, and verified that working bytes equal committed bytes. The only changes are Markdown angle-bracket autolink wrappers around the existing issue 780 and parent issue 747 URLs. Replacing precisely those two strings in the old bytes reproduces the current file exactly. There is no scope, acceptance-criterion, release-version, exception-date, dependency-target, runtime-preservation, or authorization change.

The original proposal SHA256 was `87d33cfa09d1ad7ee89a7c4b45ab6b6d828b2b077f9f825a089c4ede622ac35c`. The current committed proposal SHA256 is `83e860e44ebc7778c48fb0ef382ed26c4d8ebe80ccdcd18037f85c57f37d21df`. This independent review explicitly accepts the current committed proposal bytes with the corrected 19-case mapping. The earlier report must keep its original hash and remain historical. The coordinator must point current acceptance to this report and record the post-review formatting change honestly. I verified the actual byte delta; the attribution to the ordinary pre-commit formatter comes from the coordinator and was not independently replayed. No hook was run or bypassed during this review.
