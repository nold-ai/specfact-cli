# Current phase: specification before authored RED

This head intentionally contains specification only and remains Draft. Production and newly authored tests
are absent until the normal TDD sequence adds them. All earlier passing-after claims below describe the
historical candidate a63156e1 or its explicitly identified local corrections, not this specification head.
Protected baseline is c4ee5be8457f69848bf9bc2150ebc3df56b52d4f after #761; fresh native proof is mandatory.
Owner djm81 already accepted mapping e550f23e with 20 exact selectors and authorized exact signed-head grants.
The mapping and genuine acceptance bytes are preserved; no repeated approval or stale proof is assumed.

## Historical TDD evidence: workspace registration isolation

Date: 2026-10-11 (Europe/Berlin). Protected baseline: dev
`4e7c38c2830f4bc53ffe78eeb0a2bfbabfc711e2`. Local environment: macOS, CPython 3.13.14,
dedicated frozen uv environment. The published PR remains unmerged.

## Retained first implementation history

Historical authored head `8a03cf5898335f22dc411d75e22ea74d700df0fa` and native RED
[run 38172950463](https://github.com/nold-ai/specfact-cli/actions/runs/38172950463) preceded the first
implementation `facb6904843ab38521e8129024fddfa25b38247e`. The original digest was explicitly accepted
by djm81. That implementation passed 78 focused tests and a fresh full run: 3,298 passed, 11 disclosed
skips, two dependency deprecation warnings, 328.73 seconds. An unchanged native rerun after stack
registration passed producer, independent execution and final consumer. This historical evidence does
not cover the amended mapping or test file and is not reused as current proof.

## Review corrections and valid failing-before evidence

Added specification deltas first for official category roots, rejected-package import isolation,
effective operator-selected built-ins and reconciliation of shipped categorized routing in disabled mode.
The first review test invocation had a collection syntax error; subsequent draft category fixtures lacked
required grouping fields and failed manifest validation before registration. Both are discarded as proof.

Corrected all six category manifests to their valid canonical bundle/group fields and repeated the probes
before final production edits. Command: `.venv/bin/pytest -q -o addopts=''`
`tests/unit/security/test_module_command_squatting.py`.

- Against historical implementation facb690: 14 actual assertion/behavior failures, nine passes,
  zero skips, 1.79 seconds. Twelve category-root cases, import-shadow execution and effective-root
  compatibility reproduce the remaining gaps.
- Against protected baseline 4e7c38c, with the existing disabled-grouping bootstrap control also selected:
  17 actual assertion/behavior failures, seven passes, zero skips, 1.36 seconds. This includes the
  original missing-category and permanent-core/symlink vulnerabilities.

Signed proposal/test history is rebuilt from protected dev so no production change precedes the current
native authored boundary. The earlier authored replay 9fef6a3f contains draft fixtures and is superseded;
its hosted run is not accepted as current proof. Corrected tests must stay byte-identical after native RED.

The amended mapping digest is
`sha256:a9ba0dfde727a2a82f037212ebe5c6eeacd2574602e7d6ca9e4e3900cbdeb95c`.
The human owner explicitly approved recording acceptance as djm81 after confirmation that all 14 remaining
behavior failures will be fixed. The old acceptance is not carried across a changed mapping digest.

## Passing-after

The corrected security and registry/category-routing/bootstrap selection passes 99 tests, zero skips,
two existing dependency warnings, 7.58 seconds. Rejected packages are excluded before schema, bridge,
protocol, active-import and category-mount side effects. All six official category root names are denied
to project packages in both modes. Core command authority uses effective operator-selected discovery;
other built-in integrity exemptions remain bound to the running package tree. Removed flat bundle shims
are not restored. Those results are historical; the exact current atomic proof and full suite are recorded below.

## Independent gates and limits

The first implementation passed frozen delivery/uv lock, all three security audits, trust register,
license gate and strict module signatures; no dependency payload changed. All four project version
sources agree at 0.55.7. Strict PyPI-ahead was 0.55.7 > 0.55.4. BasedPyright reported zero errors and
1,522 baseline warnings; Ruff, Semgrep and blocking Bandit findings were clean. The expanded candidate
must rerun applicable gates. No skip, threshold, signature check, fixture pin or acceptance requirement is
weakened. A new test type warning was fixed through a typed monkeypatch path replacement, without suppression.

First-implementation broad review and independent merged-baseline review each contained five warnings,
five information findings and zero errors, with zero new findings. Narrow unchanged-baseline exceptions
covered public discovery naming, typed parser duplication, deliberate propagation/None branches and unrelated
release-fixture styles. Expanded code review must verify that no new findings remain; current tests are clean.

## Exact atomic selector correction

The released provider requires each selected RED node to fail with an exact test identity, including parameter IDs when
used.
Run 38175451297 is discarded because positive-only controls passed in RED and parameter expansions did not
match the declared node IDs. The accepted mapping digest and selector names remain unchanged. Each exact
case now checks a rejected workspace/external boundary together with its supported counterpart; the same
assertions run in RED and final, without stage flags or artificial failure. Parameter combinations execute
inside the selected case, with isolated registries and monkeypatch contexts. Full independent tests also
retain all six root names and both modes. Corrected native authored proof now passes; final-head execution and required
checks remain pending.

## Historical corrected native authored boundary and local candidate

Signed authored head `ea99fac1cb95aa7942dc7ffc571e7907bd113b74`, tree
`4e64ab987ae639dd6eee3270579270c1fed369a6`, precedes all current production edits.
[Native authored run 38176059675](https://github.com/nold-ai/specfact-cli/actions/runs/38176059675)
produces gate_decision=pass, observed_maturity=red, failing-first-proven, and no findings.
All ten exact selectors fail genuinely. The producer job failing is expected at authored maturity.
The report binds protected merge base 4e7c38c, the exact source SHA/tree, both selected test file hashes,
complete plan and aggregate mapping. Both selected test files are byte-identical in the final candidate.
The approved source mapping remains a9ba0dfd. djm81's authorized exact-head grant is comment 6113926468;
authority run 38176059763 attempt 2 succeeds. Neither this grant nor authored RED is final execution proof.

Fresh atomic full smart run: 3,299 passed, ten disclosed skips, two existing dependency deprecation
warnings, 170.28 seconds, 64% coverage. A subsequent small extraction of the pre-side-effect package
filter removes a newly introduced CC13 complexity warning; security/bootstrap controls pass again
(23 passed, zero skips, 2.79 seconds). All behavior and native selected test bytes remain unchanged.
Broad final review scores 92 with zero new findings: its 13 findings equal the ten independently measured
merged-baseline findings plus the three independently measured category-test type warnings. Narrow
unchanged-baseline exceptions retain the existing public discovery naming, parser shapes, deliberate
exception/None paths, unrelated release-fixture styles and category `commands` unknown types. The
reported unused `_clear_registry` is an unchanged pytest autouse fixture invoked by pytest, so deleting
it would remove necessary isolation. No warning is suppressed or silently treated as a new-code pass.

Current frozen lock/export parity, all three advisory audits, dependency-trust register, normal full
license scan, strict four-module signature verification, four version sources, strict PyPI-ahead and
repository lint/type-error threshold all pass. Current native final execution, the complete hosted
3.11–3.13 wheel/runtime matrix, required checks and external review remain pending at final publication.

## Final flat-mode and spec-routing review amendment (2026-10-12)

A further review identifies missing category-less reserved-name controls and a remaining obsolete spec
flat-shim requirement. Reconcile the existing collision requirement as MODIFIED, retaining its scenario
name and actual spec api routing, then add probes before any further production edits. Core names and
all six official category roots are rejected through the actual flat path in explicit legacy mode.
The spec compatibility probe executes an eligible bundle-native app through its real api subgroup;
initial incorrect single-command fixtures are corrected to the shipped native-group shape and are not proof.

Expanded mapping sha256:3dc2def04ee75c873f493cab0f33976f80cfedbf0b24b9fa84ff1fd1136ac871 adds one
executable spec-routing requirement. All eleven exact selectors genuinely fail against protected baseline
code (1.09 seconds, zero passes/skips). The implemented candidate's ten security functions pass (0.59
seconds, zero skips). Fresh full suite: 3,301 passed, nine disclosed skips, two existing dependency warnings,
193.16 seconds, 64% coverage. Final test-only review has zero findings. Current source mapping needs fresh
human acceptance: accepted a9ba0dfd is historical for this amendment and is not silently relabeled.
Fresh signed authored native RED and final execution remain mandatory; published a63156e1's green checks
cover its earlier accepted mapping. The separate protective prerequisite #760 must integrate before final
stack restacking; coherent project version and native proof will be refreshed on that protected baseline.

## Final exact reserved-name mapping (2026-10-12)

Final source mapping: sha256:e550f23e9423463f15e629e32071ec664655bc307a165af3a3961225e2f7276f.
Nine independent parameter IDs exercise category-less init, module, upgrade, project, backlog, code,
spec, govern and requirements claims in explicit legacy mode. The unchanged released provider accepts
all twenty exact selectors. Against an isolated immutable 4e7c38c archive, all twenty genuinely fail:
zero passes, errors or skips, and the protected JUnit plugin records exactly the mapped node IDs.
The current implemented security file passes all nineteen controls. Fresh full suite: 3,310 passed, nine disclosed
skips, two existing dependency warnings, 161.27 seconds,
64% coverage. Native authored RED and final execution must be regenerated after prerequisite #760.
Earlier a9ba0dfd acceptance and ea99fac1/a63156e1 native evidence remain historical. They do not cover
this final digest or the expanded test-file hash. Owner djm81 approved this exact mapping and the separate prerequisite
grants on 2026-10-12; genuine acceptance is recorded.

## Import-free eligibility review correction

A new external review correctly identifies `_build_bundle_to_group()` importing category modules whose
module bodies initialize apps during eligibility. Update the no-side-effect spec first, then a real
import-observation control fails against published a63156e1 (0.89 seconds). Admission now reuses the
existing `CATEGORY_TO_GROUP_COMMAND` constant, and the builder mapping reads those same root names.
No duplicate policy table or category builder import is needed during rejection. This independent
control is additional to the twenty mapped RED selectors; final selected test-file hashes include it.
Fresh focused/full and code-review results are required after this production correction.

Final frozen-code full run after the import-free correction: 3,311 passed, nine disclosed skips, two
existing dependency deprecation warnings, 168.62 seconds, 64% coverage. The production and both mapped
test-file hashes are checked before/after and unchanged. Final security test hash is
sha256:4228aaab9dffd3ec00b7ea272cc5d2dcabd6bc16c3b9b25e978fe9be7afd4b96. Focused compatibility
passes 86 tests; independent current review introduces zero findings against the measured baseline.
Initial broad-object import observer annotations caused four actual type errors and were corrected
with the real import argument types, without suppression. An intervening full run predates the last
builder-table reduction and is historical; only the frozen final run validates these bytes.

Protective prerequisite is concrete PR #761 (issue #760), with verified signed authored head 436bd0a3
and genuine native RED retained by run 38180902947. It must pass required checks/review and receive
owner merge authorization before this stack consumes protected helper bytes. No stack member merges.
