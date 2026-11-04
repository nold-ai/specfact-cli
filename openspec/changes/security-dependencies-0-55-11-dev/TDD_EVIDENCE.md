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

The normal TEST checkpoint `4146c185160df2f4315147306923ebc3a5bfb754`
passed enforced hooks but reported one naming warning for the generic metadata
fixture. The fixture is renamed to `packet_metadata` without changing any of
the 21 cases. The fresh before result remains two intended failures and
19 controls passing. Its corrected test SHA-256 is
`25b52577bf46c0fdefcdbea55ffddbe9f2240ac26a14425c13e33c159df296c9`.
No review warning is waived.

## Fixed packet validation after the TEST checkpoints

Normal TEST checkpoints `4146c185160df2f4315147306923ebc3a5bfb754` and
`43dc10257925987bdf9729b52a85c2e4adbaab6a` precede this runtime change.
The second metadata fixture name still matched the naming rule's substring
`data`, so the final fixture is `packet_record`. No rule is suppressed.
The final portable test SHA-256 is
`73e27ff983b66f92f23512392a2dc0fb91a42583bdb43529c2ac42788f17e851`.
Its before result remains two intended acceptance failures and 19 controls
passing, without errors or skips.

The installed existing owner SHA-256 is
`1892d4e1db1228a65251878e85d6ef2213ffc388b09d1d6b2923b4ad3bfa5716`.
It accepts only the exact retained manifest and four payload digests. It
checks sorted report selectors separately from plan and JUnit execution
order. It preserves all input bytes, historical behavior and the closed public
route. The final portable packet, fixed run and historical loader tests pass
38 cases. SpecFact Code Review reports PASS with zero findings on the exact
owner and final test.

Independent packet review
`0aad5205b3989714fc4852dc46ad96a73e817bfd6a806f18487934aacd1dee10`
was read completely and all 25 input bindings were verified before runtime
installation. It accepts this exact runtime and the portable test semantics.
The final fixture rename has separate final review. This unit grants no new
native, protected adoption, origin or final-head authority. All three native
consumers and the remaining live authentication gates still require connection.

## Artifact and signed-source regression before implementation

The portable artifact/source test has SHA-256
`5811aacd6c67a6104bde303975429eac56b2deb7561ab177c4016d5f8a571be4`.
Against unchanged owner `1892d4e1db1228a65251878e85d6ef2213ffc388b09d1d6b2923b4ad3bfa5716`,
it produces one intended artifact-admission assertion failure and 78 passing
controls, with no setup errors or skips. The fixed artifact uses the actual
auxiliary artifact name and E34 head rather than the historical name and R2
head assumption. Captured source signature, payload and distinct R2 identity
are exercised through the same unchanged artifact validator signature.

The private candidate passes the same frozen 79 cases and the separate portable
79 cases. No runtime change is installed in this TEST checkpoint. All fixtures
are inert API records. Passing this unit grants no network-origin, protected
adoption, F or fresh owner authority. The matching internal wiki source remains
unavailable and its recorded mirror follow-up remains open.

## Artifact and signed-source validation after TEST

Normal TEST `e57ed972b6934b7e3af30b223b2c50e3bc0f52b3` precedes the
finite artifact/source runtime change. Its normal review reported two duplicate
JSON-fixture warnings. One fresh per-case tuple now loads the three records
without duplicate fixture functions. All 79 cases and mutation predicates remain
unchanged. No warning is waived. The final test SHA-256 is
`ac003f0d5ee2ef450073fcf70f46eb6ab9206399b73017cc23fa676be5cc34d3`.
The final before result is one intended assertion failure and 78 controls
passing. The after result is 79 passing cases, with no errors or skips.

The installed existing owner SHA-256 is
`6f57f4a102d9b7c93e2c1958dc809ad040fc66c62e6f92de705e9f1aa8776abc`.
Only its artifact entry gains a fixed-kind branch and two finite validators.
Historical behavior, signature, public registration, normalization and C
provenance remain unchanged. Artifact E34 and signed source R2 are distinct.
The exact captured signature and signed payload are independently hash-bound.
The derived envelope does not authenticate its own network origin or grant
final-head authority.

Exact independent review
`e7e9efd83f3eb1bf5d52fa0e6a50c1ae81547f02a3e42a8e17e8f97ad6a9ab7b`
was fully read and all 43 input bindings verified. Final fixture review
`d54ef65312f7ea65a0885723396ee95333ffb5eb1d07263239f5a179c616c831`
was fully read and all 20 bindings verified. SpecFact Code Review on the final
owner and test reports PASS with zero findings. Full workflow integration,
canonical forwarding, origin and fresh exact-head authority remain open.

## Canonical transfer regression before implementation

The full-history formatter test is installed at
`tests/proof/test_fixed786_canonical_copy.py`, SHA-256
`91341ec937b08eb5867674b4e016f6afcfcdc5dde9d53ca1500423998f889026`.
It uses actual local C/R2 ancestry, the unchanged real C validator and original
canonical report/XML. Only private routing is patched in formatter cases.
Its event is explicitly derived unit data binding a real local candidate,
not a captured public event, origin or owner grant. Public routing stays closed.

Private grounding first stopped at the existing history guard rejecting
`openspec/CHANGE_ORDER.md`. This is not formatter failing-before evidence.
Git inspection and independent review confirmed that only this eleven-line
documentation insertion lies outside the fixed source's tests and change folder.
The C-to-old-R-to-R2 history has exactly two single-parent commits. A private
one-path history probe then reached the genuine report-byte assertion,
showing the historical normalizer rewrites the already-bound canonical JSON.

The unchanged owner is
`6f57f4a102d9b7c93e2c1958dc809ad040fc66c62e6f92de705e9f1aa8776abc`.
The 16-case private baseline has one history-acceptance assertion failure,
one formatter case blocked earlier at that history guard, and 14 passes.
The history-only probe has one genuine JSON-byte assertion failure and
15 passes. The full private candidate passes all 16 cases. These are local
formatter/history units, with no new native, origin or final authority credit.

Independent exact review
`4328415054f62947031e934f5e91cf822ddf392c278aeb875296741556de02ac`
was fully read and all 33 input bindings verified. It accepts only the exact
fixed-path admission and canonical copying candidate. No runtime candidate is
installed in this TEST checkpoint. The recorded internal wiki mirror follow-up
remains open because its matching source is unavailable.

## Canonical transfer after the normal TEST checkpoint

Normal TEST `9e4b0880c344d35f88cf93edb9eeefa9f5d3d309` precedes runtime
installation. The corrected full-history test SHA-256 is
`760837f750522cd0ac6e79303473db0e1783457206d2a0f36a37ee41bd883d76`.
The original CC13 test warning is fixed by comparing the same seven named
observations as one dictionary. Real Git and C provenance preparation now has
a separate per-case fixture. The baseline remains two failures and 14 passes,
with the formatter blocked at the history guard; the earlier one-path probe
separately establishes its JSON-byte assertion failure. The installed candidate
passes all 16 cases using unchanged real C validation.

Runtime SHA-256 is
`2db085ed0b6d90b9eb8ab90ac8a3fc40ebff16b0f76e2aeb415637261f17f458`.
The exact source-prefix and canonical-copy review above remains applicable.
Final independent cleanup review
`ec792f99a6e815d97baa7d69dfcfb003aa1e947653c1a51decd802782ae0226f`
was fully read and all 20 input bindings verified. It confirms unchanged
runtime, fresh per-case fixtures and every original observation and case.
Public routing remains closed and no native or authority credit is claimed.

### Scoped disposition of informational readability recommendations

The exact raw SpecFact review is retained unchanged. It reports
PASS_WITH_ADVISORY, zero errors, zero warnings and three informational
`ai-bloat.loc-vs-complexity` recommendations with `design_judgment` guidance.
Each asks for inspection and expressly permits keeping an expanded form when
it carries domain clarity. The following narrow dispositions retain the
existing review rules, report, enforcement and all required checks.

- Keep `_normalize` at 43 lines. Its explicit fixed-byte copy and historical
  reconstruction branches share the existing validation and atomic publication
  sequence. A new helper would move those checks without reducing work and
  would make the trust order harder to read. No guard is removed.
- Keep the packet `inputs` fixture at 53 lines after extracting real history
  preparation. It builds three distinct inputs with stdlib JSON and bounded
  fixture copying. A generic writer would hide the artifact, event and argument
  roles. There is no repeated function shape to remove.
- Keep the positive test at 40 lines. Its named observed/expected dictionaries
  preserve all seven checks and produce useful keyed failure diffs. Positional
  compression would remove those diagnostics, while extra assertion helpers
  would add indirection. The CC13 warning is already corrected.

These are documented design dispositions for this finite readability heuristic,
not advisory exceptions, source exemptions or check waivers. The raw three info
findings remain visible. No configuration, suppression or review artifact is
changed to conceal them. All normal and final CI gates remain mandatory.

## Complete connection regression checkpoint

The typed portable nine-case connection tests were derived from the existing
private specification before runtime implementation. Against normal core
`d4973687032a55e31fbf7469de19eb91a6182ae3`, they produce eight intended
interface/static assertion failures and one historical control pass. Failures
cover parser inputs, authentication before normalization, absent exact manifest,
origin-before-producer isolation, all three independent native lanes and the
strict audit caller's missing Berlin timezone. There are no setup/import errors
or skipped cases. These are local interface/static observations, not native,
API, signature, attestation or authority evidence.

A separate isolated-clock child probe using the unchanged real audit gate shows
that 4 November 2026 23:00 UTC is already 5 November in Berlin. UTC incorrectly
keeps the date-based record within its last day; explicit Berlin correctly
refuses it. Host clock and timezone are unchanged. The proposed correction is
only the existing strict CI step's TZ environment, retaining all three commands
and exact original exception identities and expiry.

Three read-only architectural candidates and an independent cross-judge select
the existing signer plus a distinct retained-member COPY. The synthesis fixes
both future artifact and executor/intent hash cycles. Independent judgment
`7b6ca3fd76590b1d5ebf86abce1fba6e4704b93483a3b9b8528367b11e83657c`
was fully read and all thirteen input bindings verified. Its scope permits
local spec/tests/code/review only, not dispatch, protected integration or fresh
exact-final-head authority. No runtime integration is installed in this TEST
checkpoint. The missing matching internal wiki source follow-up remains open.

The first normal TEST hook correctly refused three newly drafted requirement
entities without source mappings. They were uncommitted integration details,
not changes to the original security acceptance requirements. Their contract is
retained in this change's design and private specification; the original spec,
selected tests and source mapping remain byte-exact. No mapping, case, selector,
review rule or Requirements gate is removed or waived. Adding new requirement
identities here would unnecessarily change the already accepted current native
proof subject. The same hook must pass normally after this scope correction.

## Complete connection admission regression tests

The fixed public route now requires authentication before the existing formatter;
the historical route retains its existing inputs. Two obsolete closed-route tests
are replaced by missing-authentication refusals before formatting. Additional
partial-input and fake-origin cases do not establish genuine API or crypto proof.

The independently reviewed complete proposal has an existing consumer dispatch
history check. The review's claim that this owner omitted history is contradicted
by exact source a7b102e368e9df7e2d95699de54bf88e30f2191850ec00450aa44d08627a1e4b.
Its named run is typed strictly, but the history row permits boolean True as
integer attempt one. The actual private predicate tests produce one intended
DID NOT RAISE failure and seven passing controls on that unchanged source.

The workflow's four inline captures do omit history. Executing only their actual
AST run-admission statements with synthetic API records produces twelve intended
DID NOT RAISE failures and four single-run control passes. Combined with the
owner predicate this is thirteen failures and eleven passes, with no setup errors.
An earlier test harness used the wrong heredoc delimiter and failed setup; that
run is retained but supplies no before credit. No real API, signature, attestation,
native execution, authority or readiness claim follows from these local tests.

The correction must retain complete finite history and unique matching executor
run identity, enforce strict field types and preserve every other existing gate.
No new collector, cache, framework, permission or resource change is needed.

## Historical 0.55.11 connection implementation and local acceptance

Normal TEST checkpoint c6ee4c17f70430f499f7746c955b66560fcbc9f1 retains the
three updated test files and this evidence record. Its mandatory hooks pass
with zero errors and warnings. The final source preserves historical scope
order by appending the fixed scope. The first candidate instead prepended it;
the existing historical-index assertion caught that regression before acceptance.

The installed existing owner requires fresh f7 authority, independently verifies
the complete service-signed checkpoint chain and the distinct four-member COPY,
and verifies the isolated same-workflow attested origin before formatting. The
shared capture guard is used independently by origin and all three native lanes.
No new executable owner, index, collector, credential or resource limit is added.
The exact manifest remains the accepted native34 fixture. The seven selected
files and all twenty-one selectors remain byte-exact to signed R2.

All 172 affected local tests pass after the quality decomposition in a separate
environment installed from the reviewed hash-pinned official lock. The original
development environment is preserved. Runtime review has zero errors, zero
warnings and the unchanged `_normalize` informational recommendation already
dispositioned above. The finite 72-line synthetic ledger fixture is retained
under the same informational rule because explicit source, intent, tree and
API records expose the cross-object association; a generic fixture factory
would obscure it. No warning, suppression or enforcement rule is waived.

Independent workflow review SHA256
`d4de04b574b2818263ce81b87334191cffae3a184f75eb86b975807fa8067abf`
and runtime review
`9df5d72213d87ad60298e193177f71df81964cc86bf7724b56ecc06a5c7bb25b`
were read in full; all seventeen and sixteen respective input bindings were
verified before this evidence update. Sixteen narration comments/private
docstrings were removed without executable changes, and each reviewer confirmed
its final exact bytes. Runtime SHA256 is
`90d448dd737651cc11c8d1a901de58b91ab675ba0e9320f0abf35eaee1eadad3`.
Touched workflow Actionlint and all 82 Bash step syntax checks pass. The full
locked BasedPyright check with the actual frozen interpreter reports zero
errors; repository-wide existing warnings remain visible. The earlier default
interpreter lacked dependencies and is retained without a passing claim.

These are local and independent static acceptance only. They do not supply
new native-before evidence, actual API or attestation success, signer dispatch
authority, protected adoption, final-head provenance or current-head CI readiness.
All later exact authority, CI-only signing, three native consumers, three strict
audits, Code Review and required forge checks remain mandatory. No merge.

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

## Current native36 fixture TEST checkpoint

3 November 2026 Europe/Berlin. The preserved twelve normal TEST/CODE units now have honest new descendants above R3, ending cb131af8. Their ordered original/new identities and normal hook logs are retained outside Git. All seven selected whole test files and the proof plugin remain byte-identical to signed R3. Append conflicts retained both original evidence and the owner-selected .12 sections. Intermediate type warnings were resolved by the already preserved next typed-test unit; no finding or hook was waived. Exact raw native JUnit whitespace was retained as authenticated evidence.

Actual36 run41715861806 attempt1/job126195535776 succeeded. Original artifact13269307808 ZIP1885415/SHA0567a53963df112f2ac3f2e2024c1b93c6f9fafc00052ce137c4d5495c07f433 and development13270362279/SHAa91963ba4f2370c72f6b87c1325b6f6563c2dcc0cf26b71651c2f1c4fc52e084 were independently authenticated. Report4a7111e2085bd80fc6950a900b4111f488d07490d47bbf2b34fd79a82ee96ff8 was fully read and root-bound95file/67Git inputs, with original21 assertion failures, Source35,94 preparation receipts,4555 materialization commands and complete5root closure. This supplies refreshed RED/source closure only, not origin or final-head/production readiness.

The existing fixture paths now contain exact actual36 member/API bytes and R3 identities. Legacy filenames retain their history; their contents and manifests explicitly name actual36 and R3. Four COPY outputs remain byte-identical to original36. Metadata SHA256 is e491e7ce89edf6a5c4299dc0d723cb9a3ff90573c062b45269da13f963a65617. Original native34 archives and all consumed operations remain immutable.

After this spec/test refresh, the unchanged existing run owner rejects the actual36 record with the intended test-body AssertionError "Fixed PR786 run admission mismatch for actual-record." Its existing fourteen-case unit records1failure/13passes,0setup errors/skips. This is local admission regression evidence, not another native acquisition or per-guard proof. Production declarations, dependency graph, current owner and workflows are still unapplied here. Next is the finite existing-owner/CODE correction and .12 metadata, then passing evidence, fresh exact review and normal hooks. Preserve every original bound, all three strict audits and the4November expiry. No merge or protected authority is granted.

## Refreshed 0.55.12 implementation and local acceptance

3 November 2026 Europe/Berlin. The complete production patch follows the normal current-native TEST checkpoint. The four canonical versions and only the local uv self-record are 0.55.12. All 183 reviewed registry records and hashes, certifi 2026.10.19, current dev runtime, the unchanged version checker and the seven selected whole test files plus proof plugin remain preserved. The existing proof owner and workflow bind accepted R3, native36, the four exact COPY members and the independently accepted finite signer program and workflow. This changes fixed identities within existing owners and adds no framework or limit increase.

The affected suite records 256 passes and six installation failures. Root reproduced the installer failure as an uv cache-lock temporary-file permission refusal before the probe ran. The exact six isolated hash-pinned GitPython delivery-wheel tests then passed with ordinary cache access, without source or test changes. Together these logs account for all 262 affected cases. Actual CLI invocation reports SpecFact CLI version 0.55.12.

All three unchanged strict audits pass against CI, Code Review and runtime-smoke exports with the exact approved advisory records. MCP 1.29.0 and OpenTelemetry API 1.37.0 remain affected. The original 4 November 2026 inclusive expiry is unchanged and fails closed on 5 November at 00:00 Europe/Berlin. Version-source, reproducible-delivery and uv lock checks pass. The full checker with the actual frozen interpreter reports 712 files, zero errors and 1413 warnings, matching the retained frozen-environment baseline; this is not a warning-free report. No check is skipped or relabeled.

Independent exact review and normal CODE hooks are recorded separately. These local results and accepted native36 source closure do not establish protected origin, final-head authority, the three final native consumers, required current-head CI or forge readiness. Full CI-only signing and later concrete protected adoption and exact-head authority remain separate controlled decisions. No merge is authorized.

## Forward exact signer ref TEST checkpoint

4 November 2026 Europe/Berlin. The consumed14-object CI/CD run41788765186 remains failed/quarantined after acknowledged ref creation and an immediate404 observation. A separate minimal existing-owner readback correction is being prepared without changing native proof inputs. Future exact operation refs are codex/dev786-complete-ci-signer-20261104 and codex/security-dev-complete-candidate-20261104.

With only the three existing integration-fixture ref literals updated, unchanged core owner and workflow at normalCODE2d7814cf produce five intended test-body ValueError failures, zero setup errors/skips. One is the owner's exact intent-ref refusal, and four are the shared workflow capture's fixed786 completed signer refusal for the new branch. This is local Synthetic binding-before evidence, not another native RED run. Existing negative cases and all final success/signature/history checks remain required after CODE. The selected seven whole tests and proof plugin are still byte-identical to signedR3.

The forward CODE will replace only the measured independently reviewed signer digest, two exact intent refs and one shared workflow branch literal. Keep native36/COPY/manifest identities, all other workflow logic, versions, graph, limits, original4Novemberexpiry and the entire14-unit normal source history unchanged. No failed output or old grant is promoted. Later actual signing and protected/final-head gates remain separately controlled; no merge.

## Forward exact signer binding CODE

4 November 2026 Europe/Berlin. After normal TESTaf9ebdb1 and its five intended binding-before ValueErrors, the existing owner now pins corrected signerdfc44d082253e71d0344e0ead08bb846d37ae2010e70dc06506746610ea6e4c8 and the two exact20261104refs. The workflow changes only its shared expected signer head_branch literal. Its permission, successful-run, receipt, signature, complete-history and upload checks remain unchanged. The signer correction passes233Synthetic cases and normal visibility/ref TEST/CODE hooks; the final finite binding CODE is a45baa60. Signer workflow889686/runtimebc64 remain unchanged.

The five affected core suites pass156cases in2.43seconds, including all39workflow integration cases and the original negative controls. Root verifies all seven selected whole proof tests and the proof plugin equal signedR3 and the historical original c6 staged patch remains exact7a2cd3b7. Native36/COPY/source identities, canonical.12versions, registry graph, original4November expiry and all caps remain unchanged. A scoped independent comment review found no new comments or suppressions in the signer or core test diffs; subsequent changes are only exact ref/pin literals and this factual evidence. Fresh independent consolidated CODE review and actual successful CI/CD output acceptance remain required. No signing, failed-output adoption, protected/F authority, PR advance or merge is claimed.

## Current-head CI correction TEST

4 November 2026 Europe/Berlin. Approved CI run41910363451 passed with both uploads. Fresh independent actual-output review92fe802c was fully read and root-bound163files/70Gitobjects/415comparisons before guarded PRR3-to-Fb0184ae8 advancement. Actual F CI passes module signature verification, Docs Review, Contract Validation, type checking, linting and the security audit. Its SAST artifact13362548599/3396bytes/SHA1863d03895040e52506ce34a5cb9cc8c18de34166cf280b6fb497218a90a3321 flags the Git object identity SHA-1 at scripts/requirements_late_red_proof.py:1009, already explicitly non-security. License job126862955274 rejects isolatedPylint4.0.9 because the existing exact license entry still names4.0.7. These are genuine new CI results, not retries or native RED.

The new closest public checks must show the exact isolated package/version succeeds only in its existing code-review-only scope and that only explicitly non-security Git SHA-1 avoids the weak-security-hash rule. All existing MD5 findings and SHA-1 default/security/dynamic cases remain blocking. Official PyPI4.0.9metadata was read4November; its license remains GPLv2-family, with no runtime/module installation approved. The existing declared isolated-tool exception and Phase 2 plan remain the same. No record expiry or advisory selection changes. The internal wiki remains unavailable at the expected mirror path; its existing update/rebuild follow-up remains outstanding.

The corrected pinned-CLI local before run `local-genuine-before-pinned-cli.txt` produced four intended assertion failures and two passing license controls. The SAST assertion identifies exactly the extra nonsecurity Git call. Earlier local CLI attempts were setup failures, including the wrapper selecting a global pysemgrep and a sandboxed log path, and earn no behavior/native RED credit. The corrected command prepends this worktree venv to PATH, sets its existing certifi CA file and a temporary Semgrep log file. No resolver or package changes occurred.

The changed F-root/ref synthetic core fixture produces five intended boundary failures and 34 passing controls before owner/capture changes (`local-anchor-before.txt`). This is local synthetic evidence only. The new normal TEST starts directly at accepted signed F; original native36/R3 packet and whole-file inputs remain untouched.

Actual completed F CI tests (jobs126862955056/126862955415) report eleven/ten failures including six stale test files. The corrected retained-graph and historical-route tests pass 65 cases (`current-CI-contract-corrections.txt`). Pinned pycparser3.12 is retained and2.22 is explicitly refused; no historical investigation is claimed recovered. The stale resolver double now mutates actual Pylint4.0.9 to4.0.8 and asserts the fixture differs before testing rejection. Historical shell test environments explicitly set FIXED786_ACTIVE=false; production uses its existing workflow-level value. Existing isolation, marker, policy exit, frozen-tool and retained-output assertions remain enforced. The CI-only canonical freshness failure comes from the synthetic merge re-reporting already-proven path changes; its fixture now accepts only the pinned C/two-parent/identical-tree presentation, then validates the actual PR parent with unchanged trusted validator and native bytes.
