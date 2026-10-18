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

## Authenticated expanded hosted RED before implementation, 2026-10-18

Active successor PR #776 published signed test-only commit
`6e05f92a05b051cddf311ff6a07dcdfa00d9eba6`, tree
`1747c90d18590106faecdd70ad4d4635ba46cc16`. Full normal and signed commit hooks
passed. Actual SpecFact review reported PASS with zero findings. A fresh independent
review approved the exact staged bytes. Native contract execution was skipped for
unchanged inputs; no new contract execution is claimed.

[Requirements run 39168987596](https://github.com/nold-ai/specfact-cli/actions/runs/39168987596)
produced artifact `12151776758` on this same head branch. The GitHub service ZIP
SHA-256 is `69c5fcbcd14c1a6b7bc24d908bb4e6d2399e237325df6205b5733045addaeee5`.
All 85 accepted selectors produced AssertionError failures with zero errors and
zero skips. Native reconciliation reports `gate_decision=pass` and
`observed_maturity=red`, with aggregate mapping
`sha256:5ca313a14b492010da58bfa39e3b6ac59ebacd9ca8713a69a3d6ea273c212380`
and plan `sha256:76e1abbf563d0b1a9ddf528e5d36ca0a4990036e906a1660e528bdd45c8826ee`.
The source mapping remains the exact owner-accepted 85-case mapping above.

The archive digest, API run/head identity, JUnit digest and selector set, committed
test blob digests, source tree and merge base were checked directly. The unchanged
native producer binding verifier returned zero on a disposable copy and reproduced
the original bound JSON exactly. Production implementation was still absent at
this verification. Raw archive, API metadata, XML, JSON and local binding results
are retained in the durable `hosted-red-39168987596` artifact directory. The public
receipt is `requirements-proof/hosted-red-85-receipt.json`.

Only after those checks, PR #775 closed unmerged as superseded. Its historical
40-case proof and review history remain attached to that PR. The retained
implementation was then restored, followed by the reviewed Windows checkout and
bound-input trigger corrections. Runtime-report boundary implementation follows
this new hosted RED. The frozen selected tests, imported fixture bytes, mapping
and owner acceptance are preserved. Native matrix acceptance, protected producer
bootstrap, production adoption, current-head review and final authority remain
separate unfinished obligations. A red workflow alone never supplies them.

## Post-RED local implementation checks

All 85 mapped cases and the separate 28 native-schema regressions pass locally,
113 total, after implementation. Canonical scoped type checking reports zero
errors, warnings and notes; Ruff lint and formatting pass. Actual pinned-fixture
SpecFact review of the two boundary scripts reports PASS_WITH_ADVISORY with the
nine retained preinstallation MISSING_ICONTRACT warnings and no new findings.
The published predecessor dispositions remain limited to their original scope.
No rule, threshold or scorer was changed.

The shared validator also accepts the shapes of all 21 unchanged actual retained
native reports from run `39164616971`. Their aggregate still rejects the historical
Windows recipe-byte mismatch with `Cell input binding differs`. This replay is
schema compatibility evidence only. It neither reruns native cells nor supplies
a passing matrix for the new source. Raw reports were not edited.

The Windows-only pre-checkout Git setting and PR input paths now satisfy the two
frozen workflow regressions. The driver and aggregate use the same private pure
runtime and command validators. Expected nonzero control exits and valid producer
formats remain accepted. Full staged hooks, independent review, current-head
hosted native evidence and final authority remain separate publication gates.

## Supplemental binding coverage from current review

Current-head review identified untested paths in the protected-policy loader and
matrix hash bindings. Direct source inspection confirmed those guards already
exist. The new `test_downstream_semgrep_binding_guards.py` exercises them without
changing production code, the selected 85 tests, imported fixtures, mapping or
owner acceptance. Its 18 supplemental cases pass on the existing implementation;
the combined focused selection passes 131 cases.

Nine disposable guard-removal mutations cause the expected rejection tests to
fail with `DID NOT RAISE ValueError`. This establishes regression sensitivity.
It is not a claim that these new tests preceded the retained implementation or
that another hosted RED occurred. Tests mock only external API process responses
when exercising the real protected-policy loader. Local and mutable policy
substitutions, recipe/upstream/candidate hash damage, and disagreement between
Python cells are covered. Ruff, canonical types and actual SpecFact review of
this test file pass with zero findings. Commands, source integrity and mutation
patches/results are retained under `expanded-proof/binding-review-regressions`.
These supplemental cases do not expand or replace the authoritative 85-case plan.
