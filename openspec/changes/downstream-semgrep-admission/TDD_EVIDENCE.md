# Downstream Semgrep evidence

Current status is recorded in the final accepted test-authoring section. Earlier
preparation sections are historical snapshots; their pending-acceptance and
unchanged-test-bytes statements do not describe the current source.

## Specification and authored RED

Signed specification commit: `40dc5c93d2a25284550247ce04147ae4e8509df6`.
Normal hooks and strict OpenSpec validation passed before authored tests were
copied into the worktree. The pinned planned Requirements validator accepted
all four native requirement mappings without findings.

Actual worktree run before production code existed:

```text
python -m pytest tests/unit/scripts/test_downstream_semgrep.py -q --tb=short
40 failed in 0.47s
JUnit: 40 tests, 40 AssertionError failures, 0 errors, 0 skips
```

The failures assert that the real build/admission boundary is absent. They are
initial missing-behavior evidence, not a claim that every rejection input exposed
a separate existing vulnerability. Synthetic wheel, provenance and audit fixtures
exercise the contract; they are not authenticated production admission.

The owner accepted exact mapping
`sha256:83f12bcec0ff756681c2cc1188c431fce1327e6d3371fae6bc4df4bf1ddd8425`
on 2026-10-16 at 23:04 Europe/Berlin. The separate accepted record identifies the
actual human reply. The native matrix inspection obligation remains pending.

The mapped complete-audit case was strengthened with candidate-only audit
assertions under the same accepted mapping. Actual pre-extension run:
`1 failed in 0.09s`, AssertionError `Candidate audit proof is absent`.
The original frozen test proposal, both RED runs and hashes remain retained in
`/private/tmp/specfact-downstream-semgrep-20261016/` during local preparation.

## Local MCP candidate experiments

A separate non-listening control on MCP 1.29.0 fails eight lifecycle/default
controls, with zero errors. Actual DELETE and refused opening requests retain a
registered session. MCP 1.30.0 passes those eight checks and the actual Semgrep
stdio initialize/list/custom-scan probe. Additional local checks verify the real
Semgrep HTTP factory rejects missing/malformed credentials and the SDK binds a
session to the verified test principal. These are isolated candidate experiments,
not seven-platform proof or protected producer admission.

## Pending

- Signed authored-test commit and exact commit-bound RED retention.
- Final build/admission GREEN and independent review.
- All 21 real platform/Python cells, including full SAST and MCP evidence.
- Normal native/FULL, quality, dependency/provider trust and signature gates.
- Protected producer bootstrap and separately reviewed production adoption.

No production pin, existing audit/floor or trusted provider has been changed. The
existing frozen MCP audit remains a release blocker. No merge is authorized.

## Native proof branch

The first implementation PR #773 correctly failed the unchanged hosted
Requirements gate with `prior-red-proof-missing`. The earlier local signed test
snapshot is real failing evidence, but cannot substitute for the hosted receipt.
This branch retains the original specification and authored-test ancestors and
freezes the final forty-selector test file before implementation. It contains no
implementation changes. The first hosted run must produce actual RED evidence.
The old PR, commits and failed artifacts remain preserved. No history is rewritten
and no existing gate or provider is changed.

## Corrected test-only local RED addendum, 2026-10-17 Europe/Berlin

This addendum supersedes the earlier claim that the forty-selector test file was
final. Historical commits and evidence above remain preserved. Test-local
Protocols replace the static type-only production import so future implementation
bytes are not imported into the authored test dependency surface. The synthetic
recipe now contains a runtime-policy object and its canonical SHA-256. All 40
original selectors and their 48 assertion nodes are unchanged. The accepted
requirements mapping file is byte-for-byte unchanged; no new requirement,
scenario, mapping case or acceptance record was added.

Ten supplemental review cases cover protected attestation identity, rejection of
an approved but invalid matrix, and preserved ZIP member attributes. Eight further
supplemental cases cover five runtime-policy rejection inputs and three real
subprocess encoding checks. The encoding checks simulate the Windows cp1252 text
default, assert UTF-8 stdout/stderr text and retained evidence, and require invalid
UTF-8 on either stream to fail closed. They do not replace native Windows proof.

Before production code exists in this worktree, the final local run was:

```text
hatch run python -m pytest tests/unit/scripts/test_downstream_semgrep.py tests/unit/scripts/test_downstream_semgrep_review_guards.py tests/unit/scripts/test_downstream_semgrep_runtime_evidence.py -q --tb=short --junitxml=/private/tmp/core774-root-causes/corrected-tests-red.xml
58 failed
JUnit: 58 tests, 58 AssertionError failures, 0 errors, 0 skips
```

Failures explicitly report `Downstream admission boundary is absent` or
`Downstream matrix runner is absent`. This proves missing behavior in the
test-only ancestor, not separate exposed defects in an existing implementation.
The log and JUnit artifact are retained in `/private/tmp/core774-root-causes/` as
`corrected-tests-red.log` and `corrected-tests-red.xml`.

Scoped `hatch run ruff check`, `hatch run ruff format --check`, and
`hatch run type-check` on those three test files pass. BasedPyright reports
`0 errors, 0 warnings, 0 notes` using the canonical project configuration and the
locked checker installed by `npm ci --ignore-scripts --prefix tools/basedpyright`.
`openspec validate downstream-semgrep-admission --strict` passes.

No corrected hosted RED receipt, implementation GREEN, native matrix completion,
commit or publication is claimed here. Those gates and the unchecked internal
wiki synchronization task remain pending.

## Additional review corrections, 2026-10-17

Independent review exposed lossy timeout decoding. Supplemental timeout cases now
check legitimate UTF-8 and reject invalid bytes on either stream. CRLF and CR
cases preserve the existing universal-newline text behavior across completed and
timed-out commands. Two archive cases also reproduce unauthorized compression
and creator-version changes that the published verifier accepted with valid
RECORD contents. The comparison uses the reviewed ZIP_STORED transformation, not
the original compressed representation. Broader ZIP flag and volume semantics
remain unresolved because CPython rewrites those headers during serialization.

The final corrected test-only snapshot supersedes the 58-case snapshot above.
Its local JUnit records 67 tests, 67 AssertionError failures, zero errors and zero
skips because both production boundaries are absent. The original forty selectors
and forty-eight assertion AST nodes remain unchanged, as does the accepted mapping.
No new owner acceptance is asserted.

A disposable copy of published implementation `7a1abb75` first reproduces eight
failing cases for two causes and then two additional archive failures. The
minimal encoding, policy-binding and archive comparison patch passes all 67
corrected tests locally. This is prospective patch evidence in a disposable copy,
not implementation restoration to the test-only branch or hosted Requirements
GREEN. No protected artifact, native Windows result or complete new matrix is
claimed. The old published native matrix ended with 18 successful cells and three
Windows failures; its aggregate correctly fails.

Local artifacts are retained under `/private/tmp/core774-root-causes/`:
`test-only-67-red.xml`, `old-implementation-red.xml`, `zip-metadata-red.xml`,
`newline-red.xml`, and `candidate-final-green.xml`, with their matching logs.
Publication awaits a decision on a fresh test-first successor PR. The existing
Requirements workflow searches only the same head branch, and production already
occurs in #774 history. No history rewrite, merge, retarget, policy exclusion or
reuse of a stale hosted receipt is authorized.

The final normal unmodified pre-commit run passes. SpecFact reports `PASS` with
zero findings at all severities. Two supplemental test names were made specific.
The analyzer's initial missing pytest types were resolved by preparing `.venv`
from exact `requirements/ci/locked.txt`, without changing dependency inputs. The
released Requirements validator passes at `test-authored` maturity. Contract
execution was skipped by the native hook because its input status was unchanged;
no new contract execution is claimed. Scoped type checks and strict OpenSpec pass.

## Expanded proof preparation on 2026-10-18

This local test-only successor proposal expands the mapping to 83 pytest cases and retains the separate pending inspection for all 21 native platform cells. It preserves the original 40 case mappings and all 48 original assertion AST nodes. Supplemental parameter ids use explicit native-compatible slugs. Assertions are unchanged.

The exact pinned Requirements module at `69f075819be5e1ceca1446b026b0417f19e584ca` accepts this mapping at planned maturity. Its source mapping digest is `sha256:68bc4e87f756f1643cce76ed62fb354b8fcdeec6a279d966bb20282e50dcffc8`. The normalized aggregate mapping digest is `sha256:000b21187a9553bc2d2ec80cb03d7ed55bf1d8e27e28faeb2951bb07f25c6806` and plan digest is `sha256:07e1c2ec58614f0a314c5f959017e58302e278cb4408cbeb9db5e50d7d4f720b`.

Local execution against this worktree with no downstream implementation produces 83 AssertionErrors, zero errors and zero skips. The historical 83-case collection, command, JUnit and SHA-256 records are retained in `/Users/dom/git/nold-ai/specfact-cli-worktrees/codex/pr774-root-causes-artifacts/expanded-proof/history-83/`. This local run does not provide hosted RED provenance.

The existing review-evidence.json remains immutable historical acceptance for the original mapping. The native accepted-maturity gate rejects it with `acceptance-stale` for this revised mapping. Existing retained RED and hosted receipts apply only to their original accepted mapping and plan. They cannot authorize the expanded mapping. New owner acceptance, the successor topology decision and fresh hosted RED are pending. No implementation restoration, commit or publication is authorized by this preparation.

## Revised 85-case proof preparation on 2026-10-18

This local test-only successor proposal expands the mapping to 85 pytest cases and retains the separate pending inspection for all 21 native platform cells. It preserves the original 40 case mappings and all 48 original assertion AST nodes. The two new workflow regressions cover committed recipe byte preservation with inherited Git CRLF conversion and pull-request triggers for every bound source input. Existing assertions are unchanged.

The exact pinned Requirements module at `69f075819be5e1ceca1446b026b0417f19e584ca` accepts this mapping at planned maturity. Its source mapping digest is `sha256:8fad85983d493870a3cefcc08511966fb9eb7cf821a34f3dc8c9d97b14944d11`. The normalized aggregate mapping digest is `sha256:5ca313a14b492010da58bfa39e3b6ac59ebacd9ca8713a69a3d6ea273c212380` and plan digest is `sha256:76e1abbf563d0b1a9ddf528e5d36ca0a4990036e906a1660e528bdd45c8826ee`.

Local execution against this worktree with no downstream implementation produces 85 AssertionErrors, zero errors and zero skips. Raw collection, command, JUnit and SHA-256 records live in `/Users/dom/git/nold-ai/specfact-cli-worktrees/codex/pr774-root-causes-artifacts/expanded-proof/`. This local run does not provide hosted RED provenance. Scoped Ruff lint and format, canonical BasedPyright (0 errors, 0 warnings, 0 notes), and strict OpenSpec validation pass; exact commands and outputs are retained in quality-commands.json and quality-*.log.

The existing review-evidence.json remains immutable historical acceptance for the original mapping. The native accepted-maturity gate rejects it with `acceptance-stale` for this revised mapping. Existing retained RED and hosted receipts apply only to their original accepted mapping and plan. They cannot authorize the expanded mapping. New owner acceptance, the successor topology decision and fresh hosted RED are pending. The two workflow tests separately fail against retained workflow 14b9726564473118e7c9480d8757bb45cfe498f7 and pass against a disposable prospective patch. Logs, JUnit and patch are retained as workflow-14b-red, workflow-prospective-green and prospective-workflow.patch. This is local prospective evidence only. No implementation restoration, commit or publication is authorized by this preparation.

## Accepted 85-case test authoring before hosted RED, 2026-10-18 Europe/Berlin

The owner accepted the exact source mapping digest
`sha256:8fad85983d493870a3cefcc08511966fb9eb7cf821a34f3dc8c9d97b14944d11`
and the signed test-only successor sequence on 2026-10-18 at 23:26:30
Europe/Berlin (21:26:30 UTC). The current `requirements-proof/review-evidence.json`
records that actual owner reply. The original forty-case acceptance remains in
`requirements-proof/historical-original-40-acceptance.json`. This supersedes the
pending-acceptance statements in the historical preparation sections above.

Before the signed test-only commit and new hosted RED, the original contract's
synthetic report factory was authored to include typed runtime and command
records. Its shapes follow the inspected native reports, including macOS
universal2, empty macOS/Windows libc identities, and musl `Version 1.2`. Interpreter
and output digests are deterministic synthetic values. These fixtures establish
schema expectations; they do not establish native execution or authenticity.
This fulfills the already accepted actual-native obligation without adding a
requirement, selector, mapping case, or acceptance claim.

The current original contract file SHA-256 is
`f28afd00d4ac915216cdc130eb87a826b51514da94dde0b9fbb6997512daa106`.
The earlier `0b6f7ab9ac472f415bd8452f2201faa02dff996046b00e9ad695149f5a78a86d`
is the historical pre-fixture source hash, not the current file hash. All 48
original assertion AST nodes are unchanged. The original forty mappings and all
85 selected cases remain unchanged. The Requirements source mapping digest above
is distinct from the raw mapping file SHA-256
`5d0321664619ece6ed95d819b6a93e2df3152bfa13f50f8775d97ee16d364096`.

The pinned Requirements module at `69f075819be5e1ceca1446b026b0417f19e584ca`
passes accepted and test-authored maturity using the real owner record. The
separate local run of exactly the 85 mapped selectors produces 85 AssertionError
failures, zero errors and zero skips because production boundaries are absent.
No production implementation was added to this checkout.

The supplemental `tests/unit/scripts/test_native_report_schema.py` is outside the
mapped test glob. Against a disposable copy of retained implementation `8aaf9e3f`,
its 23 malformed or contradictory runtime/command cases fail with `DID NOT RAISE`.
All five positive controls pass, including architecture aliases, universal2,
expected return code 1, and an empty non-executable argument. This 28-case local
regression experiment is separate from the mapped 85-case proof. No prospective
validator implementation was created for this experiment.

Fresh raw commands, JUnit, native gate reports, source preservation and hashes
are retained under
`/Users/dom/git/nold-ai/specfact-cli-worktrees/codex/pr774-root-causes-artifacts/expanded-proof/accepted-test-authoring/`.
Earlier preparation artifacts remain intact. Hosted authenticated RED, production
implementation, native inspection completion, independent review, and release
adoption remain later gates. Local synthetic RED does not satisfy them.

Scoped Ruff lint and formatting, canonical BasedPyright (zero errors, warnings or
notes), and strict OpenSpec validation pass. Direct local AI-bloat and Radon
analyzers from the pinned module fixture report no findings. These direct checks
do not substitute for the full SpecFact review gate. Its wrapper exited zero,
but its retained JSON correctly reports FAIL/UNKNOWN because every required
capsule analyzer reports `unsupported_controller_platform`. Full review remains
unverified on this host and must be completed through the supported environment.

The review was then rerun unchanged with the explicitly designated fixture paths
`SPECFACT_MODULES_REPO=/Users/dom/.codex/worktrees/core-review-reset-fixture/specfact-cli-modules`
and `SPECFACT_DOCS_MODULES_REPO=/Users/dom/.codex/worktrees/core-docs-module-fixture/specfact-cli-modules`.
The correct pinned module selection produces actual SpecFact PASS with zero
errors, warnings, or advisory findings. The earlier unsupported-controller result
came from the default module selection and is preserved separately, not relabeled
as passing. Exact fixture commits/trees and command are retained in
`pinned-review-command.json`; `specfact-code-review-pinned.json` retains the passing
report. Full normal hooks and independent review remain root finalization steps.

The complete staged normal review then caught `CC17` in the workflow checkout
regression, outside the earlier three-file authoring review. Extracting the
checkout-control selection preserves the accepted selector and assertion behavior;
all three workflow helpers now have Radon complexity 9 or lower. Independent
review also required the prospective trigger and its regression to include
`test_native_report_schema.py` explicitly. That correction was made before the
new RED source freeze. The retained workflow still yields two assertion failures;
the disposable prospective patch yields two passes. Mapped 85-case local RED and
accepted/test-authored validation were refreshed after these edits. Full normal
hooks and final independent review remain publication gates.

## Accepted installation identity successor (2026-10-19)

The owner explicitly approved the reviewed installation-identity contract, exact
89-test source mapping `sha256:488ec1a749b4fd4da337cc75ee942f67122e29c0c76054e81aa7a1ae61873b42`, trusted installer, process,
account and private-storage boundary, and signed test-only successor sequence.
The authentic reply is `call_0ed72e91880c4eb2a23022fa9ce383d6`, answered
"Approve this exact contract, mapping and sequence". The native acceptance record
was recorded at `2026-10-19T11:10:23Z`. This is new exact mapping acceptance, not reuse of
old 85-case approval, protected authority or merge permission.

Before recording acceptance, root verified every frozen proposal input, all
55 artifact hashes, manifest
`sha256:fbf0bdfbd61c8415e6c8c575fb5832af8d570cde560a72a4eeda7ca32e0217e9`
and staged patch
`sha256:0b8c58dc53916df3552235d644f7832976bafba7fe66d7db2e95fff33d25c6d7` against the independently reviewed packet. All six
contract, mapping and test paths remain byte-identical to that packet. The
proposal's retained local run has 89 AssertionErrors, zero errors and skips;
its independent review verified the raw JUnit and preserved selectors. This is
local evidence only. The old 85-case hosted RED and GREEN remain historical and
cannot establish the new hosted proof.

The successor starts from test-only `6e05f92a05b051cddf311ff6a07dcdfa00d9eba6`. Production
implementation remains absent. Authentic same-branch hosted 89-case RED, with
service artifact, JUnit, source, tree, mapping, plan and baseline bindings, is
required before restoring production or closing PR776. Stop if the hosted
baseline contains the implementation. No workflow, policy, dependency, frozen
security audit or pin changes are included to obtain RED. Materialization
native lifecycle and protected adoption remain unchecked.

### Pre-RED test shape correction (2026-10-19)

The first full normal-hook review found actual Radon CC16 in the new transport
mutation test and CC13 in the attestation test, plus two length recommendations.
The failed report is retained; it was not bypassed or relabeled. Before any new
hosted RED, four small private test helpers separate mutation, normal
materialization, failed-installer cleanup and attestation options. This local
fixture correction leaves the approved public contract and canonical source
mapping unchanged. It is not a change to the installation API or acceptance
expectations. All 27 assertion ASTs in the two files, test signatures, decorators,
parameter identities and all 89 selected cases are preserved. All other frozen
contract, design, mapping and test files remain byte-identical. The original
reviewed packet and all 55 artifact hashes remain unchanged historical evidence.

The two corrected test SHA-256 values are
`3b0ffd9364311536ef25d0eee2ffcd9a6a4c6cf0845fcdc97f6d90e8b1bbbd7c`
and `ad1d667168e82aa3475f2df1b35e3f6cf02d894c7e27dde801e0207d72246ab7`.
These are new test bytes and must be used for the new hosted source freeze.
Actual native Radon, Pylint, AST clean-code and AI-bloat adapters now report no
findings. Ruff format/lint and canonical BasedPyright pass. Refreshed local RED
remains exactly 89 AssertionErrors, zero errors and skips. The external snapshot
oracle passes all four mutations; shared-inode retention still fails the new
in-place approved-byte assertion while passing its three older controls.
Wrong-byte, original-path and leaked-cleanup controls retain their expected
assertion failures. These are test discrimination controls, not production GREEN
or native lifecycle acceptance. Root independently checked the assertion ASTs
and raw JUnit. Updated native acceptance, full normal hooks, fresh review and
hosted proof remain separate gates.

Independent final review caught four new line-length errors in the YAML mapping
despite the existing repository wrapper reporting success. Wrapping only those
four observable strings preserves the parsed mapping object exactly. Direct
strict yamllint on the changed mapping now exits zero. This is formatting before
the new hosted source freeze, not a contract or canonical mapping change. The
historical reviewed YAML byte hash is retained with the initial packet; the
new byte hash is recorded in the local semantic-preservation receipt. Other
repository YAML errors printed by the wrapper are pre-existing and outside this
change. Its error-propagation bug is not repaired or weakened here.

### Final signed test-only publication gate (2026-10-19)

After the pre-RED fixture cleanup and semantic-only YAML wrapping, the pinned
native gate again passes accepted and test-authored maturity for the exact
owner-approved mapping `sha256:488ec1a749b4fd4da337cc75ee942f67122e29c0c76054e81aa7a1ae61873b42`.
Strict OpenSpec and all normal hooks pass. The actual SpecFact review is PASS
with zero findings. Contract execution is skipped by the unchanged native
contract-test-status decision, so no new contract run is claimed. Direct strict
yamllint on the changed mapping exits zero. The remaining 18 global YAML
diagnostics belong to four files byte-identical to the test-only baseline; the
existing wrapper error-propagation defect remains disclosed and unchanged.

Fresh independent final review approved the exact nine-file test-only snapshot.
It independently expands the four private helpers and recovers both entire
approved test module ASTs, preserving statement order. It also reverses exactly
four YAML line wraps to the historical reviewed bytes and verifies parsed-value
equality. The final comment audit reports no new findings or suppressions. All
writers and reviewers were explicitly stopped before signing. No production
source, workflow, dependency, policy, authority or protected producer state was
changed. The new hosted source must bind the corrected test bytes above.

Authentic same-branch hosted 89-case RED remains required before implementation
or PR776 closure. Native materialization lifecycle and protected adoption remain
unproved and unchecked. This publication supplies neither merge permission nor
protected Requirements authority.
