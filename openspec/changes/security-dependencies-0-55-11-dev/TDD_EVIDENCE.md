# Dev-first failing-before evidence

On 26 October 2026 Europe/Berlin, the unchanged production inputs at dev
`9b5ad1e78430cc0b061cb16de42f73de96f4f312` produced 15 assertion failures,
zero errors and zero skips for this change's 15 mapped cases. The exact JUnit
and execution/input receipt are retained under `requirements-proof/` as
`local-red-behavior-20261026.xml.gz` and its companion receipt. Root inspected each
failure message. The Git cases show rejection false, clone boundary reached
and one clone call, rather than a wheel-installation error.

The gzip transport decompresses to the original immutable XML bytes, SHA-256
`cdbef78a51e9bbf66e43ac826a3cfb23335b06de6092b93ed71e37606d19c407`.
Pytest's raw failure trace contains trailing whitespace. Compression preserves
that report without normalizing its contents or changing formatter rules.

The targeted local runner used Python 3.12.13, pytest 9.1.1 and the exact
hash-pinned test-tool entries extracted from dev's CI export. It loaded normal
repository conftest/configuration with third-party plugin autoload disabled.
GitPython probes installed the exact frozen GitPython/gitdb/smmap wheels with
hash checking, no dependency resolution and isolated `-I -S` execution.

The failures observe the five old package versions, both old public floors,
the old parser record, three missing exact OpenTelemetry admissions, three
metadata submodule paths reaching clone, and two existing advisory exclusions
where the required nine are expected. All recorded inputs stayed unchanged
during execution. No production edit preceded this run.

The first exploratory run had 15 failures and one passing preservation case.
It is retained privately without relabeling. The already-satisfied shared-lane
case was removed from this RED plan and remains an ordinary control. Independent
review also required per-package advisory fixtures, parser hostile-fixture
adaptation and exact deselection bounds before the corrected run. This evidence
uses the corrected tests and mapping; it does not transfer the first run's
identities.

The pinned Requirements lifecycle initially rejected the automatic floor-case
parameter IDs because comparison punctuation is not allowed in selectors.
Explicit `gitpython-floor` and `pycparser-floor` IDs corrected the metadata;
the assertions did not change. The next run had 12 intended assertion failures
and three wheel-installation CalledProcessError failures. Its total of 15
pytest failures did not establish complete behavioral RED. Independent review
caught this distinction. That raw run and receipt remain unchanged and receive
no behavioral acceptance. The separately approved network-enabled run then
produced all 15 intended assertion failures, with unchanged inputs and no
errors or skips. The actual pinned lifecycle accepts planned maturity with no
findings, mapping digest
`sha256:7025a000601cc44c1a1e6168367f2188681471d68ea5f044cfc81a94b734f8ff`
and plan digest
`sha256:dc90453d191b282ba5e47127bf067ee23b475072d7e94a0859c7c6a26677ce3a`.
That planned-only result supplies no native RED or mapping review acceptance.

This is local behavioral failing-before evidence. It is not accepted native CI
RED, an origin attestation, exact-head authority, a production acceptance or
merge readiness. Native bootstrap remains blocked before tests by the base's
expired pycparser 2.22 review. No renewal or check waiver is claimed.

Passing-after, full quality gates, genuine accepted native evidence, independent
final review, CI-only Git signatures and actual forge readiness remain pending.

## Test-prefix quality correction

On 26 October 2026 Europe/Berlin, the normal Code Review identified duplicated
trust fixtures and unknown member types inherited by the edited audit tests.
The correction groups the five unchanged hostile fixture oracles and adds
fixture/function annotations. Mapping YAML indentation changes parsed no data.
A fresh independent review accepted these exact changes and their local results.

The distinct `local-red-quality` run again produced 15 intended assertion
failures, zero errors and zero skips. Its receipt binds all 13 input hashes.
The separate `local-controls-quality` run passed 20 cases, including all nine
original MCP scenarios, the grouped hostile fixtures and ordinary clone paths.
These reports remain private local evidence and replace no native identity.

The actual normal SpecFact Code Review run
`review-f821c36e-2ff9-43f9-8f4c-1a403be11ec1` reports PASS with zero findings.
Direct yamllint of the new YAML files passes. The repository-wide YAML hook
prints inherited findings and returns success incorrectly; full YAML cleanliness
is not claimed. That wrapper defect remains tracked separately in
[issue #781](https://github.com/nold-ai/specfact-cli/issues/781).

The local test prefix has passed normal hooks. Its unsigned source snapshot is
not a published branch or accepted commit signature. A bounded create-only CI
signer must produce and verify the delivered tree with dev as its sole parent.

## Current native prefix and fixed transfer regression

On 30 October 2026 Europe/Berlin, signed test source
`22b2fa7bd763b18ada1bfd1a9ea482a624f34cca` received genuine Linux proof in
[run 41082128288](https://github.com/nold-ai/.github/actions/runs/41082128288),
attempt 1. Auxiliary executor `7b6b5fc1af7b57c2eb5a3546b7578a81175e4dfa`
is a distinct identity. Independent packet review accepted 21 intended
assertion failures, zero errors/passes/skips, all 35 unchanged source identities
and complete cleanup of all five owned roots. The report digest is
`befa58f55bad15689605659f8fd209ec853e0831bc99a3532da1ca9264f50e58`.
Original artifact 12988969594 has ZIP SHA-256
`ae9f1bd8efb862d2b03f9c584cded897e1ac0d945a3b60265347670d21bcab79`.
This is current development failing-first evidence. Protected origin, adoption
and final-head readiness remain separate and unaccepted. Historical15 evidence
is retained as historical evidence.

The new portable `test_fixed786_native_run.py` exercises the existing late-RED
owner with a retained public GitHub run object. The fixture SHA-256 is
`df109a62bd249f55dd25b6d3d22ba5a5b92d0d8d0815334ee424b0b9ab89a072`.
Before runtime changes, the actual-record admission case fails with the intended
AssertionError and all 13 refusal controls pass, with zero setup/collection
errors or skips. The test SHA-256 is
`160e6f5a249a1f118b160a5b5692f808d34a56bfa047bbc38c9c212bbc98a544`;
the unchanged owner SHA-256 is
`de31b828f21ed0bfb580a8d261a3a475a62f61864ecdaae3a0eb551d7184b928`.
This replay unit grants no native, CLI transfer, origin or owner authority.

The private run-only candidate passes its frozen 14-case unit and has an exact
independent review. It is not installed in this test-first checkpoint. The public
route must remain unregistered until complete packet, signature, provenance,
origin and exact-final-head authority checks are implemented and reviewed.
The seven selected R2 tests and their Requirements mapping remain unchanged.
The matching internal wiki source is missing; mirror update and graph rebuild
remain an explicit follow-up. No merge or protected adoption is authorized here.

The first normal checkpoint hook rejected the test mutation chain for complexity.
A fixed run/manifest update table retains the same 14 cases without that chain.
The historical hook failure is retained; no check or finding was waived.

The normal test-first commit `74e1924bec949b318879e6b118a48680a24b9b06`
passed enforced hooks. Its remaining test type warnings and low-complexity length
notice are corrected by explicit update-table types and a per-case pytest
manifest fixture. The corrected test hash is
`78398fbc40ade63be039e1217bee498c17072b67a5e50b22f263dc4685340d2b`.
A fresh local before run retains one intended failure and 13 passing refusal
controls, with no setup errors or skips. No selected R2 proof input changed.

## Fixed run admission after the normal TEST checkpoints

The installed existing owner has SHA-256
`1f07ed9d3b885d6939cedf273e2db2af3ba80f3b5c0212e1f8f65980dadbea4e`.
It admits the fixed auxiliary run separately from its R2 subject and preserves
historical admission for validated inputs. No public route is registered.
The portable test hash is
`abd3471e97e8fce961bbbc6b22fa991644af9d3bf2cc59f97e8b59c06ad09d94`.
The final before run has one intended assertion failure and 13 passing controls;
the after run passes all 14 cases and all three existing historical loader
regressions, 17 total. Changed-file lint reports zero errors, warnings or notes.
SpecFact Code Review reports PASS with zero findings. Independent exact review
`b30f5ae497b12a7e4c0385156e403621f5bfbe2400528588e1319f1d6ceeedf5`
was read completely and its 45 input hashes were verified.

The quality correction retains finite data in the existing owner and restores
its cyclomatic complexity from 18 to the historical value 10. It adds no helper,
registry, API, waiver or protected capability. The remaining packet, live-source,
origin, final-head authority and three-consumer gates remain mandatory.

## Fixed packet portable regression before implementation

On 30 October 2026 Europe/Berlin, the portable packet regression against the
unchanged owner `1f07ed9d3b885d6939cedf273e2db2af3ba80f3b5c0212e1f8f65980dadbea4e`
produces two intended acceptance assertion failures and 19 passing controls.
There are no collection errors or skips. The test retains the authenticated
report, planning envelope, aggregate plan and JUnit bytes without normalization.
The test SHA-256 is
`0a267e07795c9950b0d401e5f0664538b87ed662b40b8e0dca3c6bd3f037a6ca`.

The report selector list is sorted, while the actual aggregate plan and JUnit
retain execution order. These distinct orders must each be checked directly.
The existing owner still refuses the new fixed schema and canonical RED report.
A private candidate passes the frozen 21-case regression. Its initial ordering
error is retained privately as one failed acceptance and 20 passing controls.
No runtime candidate is installed in this TEST checkpoint. This unit supplies
no new native, origin, protected adoption or final-head authority. The matching
internal wiki source is unavailable, so the recorded mirror follow-up remains.

## Owner-selected 0.55.12 TEST refresh

On 30 October 2026 the owner selected “Use 0.55.12; refresh version-bound
evidence.” The version checker remains unchanged. The active proposal/design
was updated first; the existing version test then changed only its expected
string from0.55.11 to0.55.12. The actual four production version declarations
and dependency inputs remain unchanged in this isolated TEST source.

The existing version test fails with its intended AssertionError, actual
0.55.11 versus expected0.55.12, with zero setup errors or skips. This is local
failing-before evidence for the version assertion only. It is not fresh native
RED, API or signing evidence. Source is isolated directly on signed R2; the
completed private CODE candidate and its normal history are preserved outside
this test-only branch. No CODE-bearing snapshot is called preproduction RED.

The version assertion shares a whole selected test file with a native case.
Trusted C checks whole-file identities and every intervening commit, so native34
remains immutable historical R2 evidence. A fresh signed test source and actual
native packet are required for this new hash, preserving all twenty-one mapped
selectors, unchanged source components and every original gate and limit.
No old grant, artifact, raw result or native acceptance is transferred.

The matching internal wiki source is absent. Its existing mirror follow-up
remains open. No sibling write or wiki update is claimed. No merge.

The first unpublished TEST checkpoint067d8ec5 passed normal hooks but exposed
an existing full-file naming warning in the invalid-UTF8 test. Its original
commit/diff and review remain retained. The final TEST checkpoint corrects
only that unmapped test's name; its body and assertions are unchanged. All
twenty-one selected case names and mappings remain unchanged. The independent
review also corrected the proposal's source-scope sentence to name only the
two authorized canonical version constants.

Three informational readability recommendations are retained explicitly: the
fresh-consumer test keeps its named command observations, the frozen-graph
test keeps its explicit package and advisory records, and the UTF8-refusal
test keeps its actual CLI argument vector and two output assertions. These
finite test shapes are clearer than another generic fixture or wrapper.
No warning, rule, report, configuration or enforcement threshold is suppressed.
