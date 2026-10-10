# Focused repair evidence

## Authorship and acceptance

The human approved this focused #747 repair on 2026-10-09 Europe/Berlin. The mapping
acceptance record identifies the actual coding agent that inspected these scenarios;
it is not a human member grant and does not satisfy Trusted Requirements Authority.

## Before repair

After defining this scoped specification and JWT regression tests, the exact unchanged
analyzer fixture was restored. Existing Python 3.12.13 / pytest 9.1.1 executed:

`python -m pytest tests/unit/security/test_frozen_jwt_compatibility.py tests/unit/versioning/test_analyzer.py -q --no-cov --junitxml=<local-red-junit>`

Result: 3 failed, 2 passed in 0.97 seconds. All three analyzer tests fail because fixture
initialization stages .git/config before production analyzer assertions. The existing
host environment already has PyJWT 2.15.1, urllib3 2.8.0, virtualenv 21.14.6 and Semgrep
1.180.0; this run is fixture failing evidence and JWT control evidence, not a frozen
baseline security reproduction or candidate graph acceptance. Retain the baseline-lock
host CI RED artifact before publishing repaired inputs.

Native selected planned evidence passed against the immutable released module fixture.
Strict selected OpenSpec passed. No dependency input or production code has changed in
this tests/spec publication. Final, artifact, consumer, full quality and Python matrix
results are pending and must be recorded separately.

## Initial hosted authored snapshot (rejected)

Signed commit f6c41baa9201f48a3af9536b855907c191ff6463 ran Requirements Evidence
37857823201 and retained artifact 11584408763, digest
sha256:39afadcfa7915d981c15a58ea515b0720db724d0c0894f89c47e5a72bfc366e1.
Its pytest outcomes were 1 failed (JWT option mutation), 4 passed. The producer correctly
rejected passing selectors as RED; observed maturity is incomplete, not accepted RED.
This run cannot authorize final proof. The frozen validator's analyzer outcomes differ
from local and full Hatch-based CI; preserve both rather than claiming equivalent scopes.

Hosted type checking also caught four options-dictionary annotation errors in the new
tests. Correct them with the library's declared Options type and validate before using
a replacement authored snapshot. Preserve the original diagnostic artifact.

## Replacement authored checks

The replacement mapping binds only the regression that fails on the frozen validator.
The ordinary JWT control and three analyzer cases remain independently required tests,
with inspection retaining their actual execution outcomes. They are not mislabeled as
native RED/final execution proof. The agent acceptance binds the per-source digest.

Strict selected OpenSpec, staged native test-authored planning, Markdown lint, Ruff
check/format and staged diff whitespace checks passed. BasedPyright using the declared
project and explicit Python 3.12 environment analyzed 671 files with zero errors and
zero diagnostics in the new test (1,526 existing repository warnings). The nested local
SpecFact review returned nine unknown-member warnings for jwt/pytest in the new test;
these do not reproduce with the explicit interpreter. This is a documented local
import-context limitation, not permission to ignore hosted or final review findings.
Contract input detection found no authored contract changes. Hosted replacement RED
and all repaired-input checks remain pending.

## Accepted JWT RED and independently discovered cache lifecycle

Authored head 0fd1d1935c26f1577b0248653a926fb5b8f2ea60, run 37859074381, artifact
11585460994 (sha256:4f842f820f0350461a80a7f4cfab8cfe236bdb62b93c69b82527cf728147ef60)
has native observed/required red, passed verdict. Producer/final delivery still fails
by design at the authored phase; the accepted RED report is not merge-ready evidence.

The candidate five-package graph and corrected analyzer fixture passed the five focused
repository tests. Eight independent boundary probes passed. Both frozen audits, native
trust/license and export parity passed; the nearest consumer batch had 174 passing cases
and an unavailable smoke fixture. Supplying the immutable fixture separately made that
direct-launcher smoke pass. OSS Semgrep scan/gate has zero current findings; Bandit has
zero medium/high findings and retains existing low findings. Explicit-interpreter type
checking has zero errors and no new JWT diagnostics. These are preliminary candidate
checks; final stable-source checks and hosted matrix remain required.

The fresh read-only reviewer confirmed inherited seed logs use the same cache paths in
old/new virtualenv. An inert persisted entry was still selected by 21.11.0. Upgrading
rejects new unverified downloads but does not sanitize previously compromised external
Hatch/user caches. The repository smoke fallback must use isolated app data; no shared
user-cache deletion is authorized or performed.

After adding the cache scenario and caller regression, the unchanged caller failed the
new test in 0.77 seconds: its captured virtualenv command omitted isolated app data and
periodic-update suppression. Preserve this genuine failure and republish authored proof
with unchanged locks/fixture/caller. Native RED/final mapping now contains both failing
JWT and cache-caller regressions; acceptance is rebound. Old RED cannot substitute for
this revised mapping.

## Accepted combined RED and repaired-input checks (9 October 2026, Europe/Berlin)

The unchanged caller/locks/fixture authored commit
`24a67a043f133c5b03ca8f9845d586b57a288d81` (tree
`cf9dff7de058a011d6c92e55bbeb70da81f97db8`) has accepted native RED for both mapped
regressions: run `37859922355`, producer job `113592935499`, artifact `11586300680`,
digest `sha256:a221cdf9fc884acf9f1c66c922fe988c590406aed54b8ec8d709efd97ecaed1e`.
Observed/required maturity is red with a passed producer verdict. The intentionally
failing authored delivery run does not establish green final verification.

The repaired graph changes exactly five of 184 resolved packages: PyJWT 2.15.1,
urllib3 2.8.0, virtualenv 21.11.0, Semgrep 1.179.0 and python-discovery 1.6.0. Semgrep's
nearest compatible release is necessary for the PyJWT constraint; discovery is required
by virtualenv. The Semgrep sentinel follows its exact lock while preserving floor/MCP
and no-waiver assertions. No release, module pin, trust exception or gate is changed.

Exact source/wheel hashes and public Socket artifact alerts were reviewed before the
five candidate wheels were installed. Provenance subject/publisher metadata matched
the reviewed artifacts; cryptographic attestation verification was not performed and
Semgrep source provenance was unavailable. Virtualenv's license alert was reconciled
against its MIT LICENSE, metadata and third-party notices. Semgrep's optional Pro
installer remains outside the repository's OSS invocation; this is not a universal
dependency-safety claim. Existing external caches are not silently sanitized.

The exact hash-installed Python 3.12.13 candidate executed the two native selectors:
2 passed in 0.70 seconds. Pytest emitted two record_property/xunit2 compatibility
warnings; the native executor's identity properties remain present. This local
pre-publication execution is not immutable-commit final reconciliation. Hosted final
Requirements proof, exact-head human authority and all effective CI remain required.

Eight JWT/seeding/option-injection boundary probes passed, including blocked metadata,
missing/mismatched digest rejection, a matched wheel control and ordinary seed fallback.
Seven additional urllib3 probes passed in 0.08 seconds: bounded chunk-size/trailer reads,
deflate EOF with alternate trailing payloads, proxy-context identity enforcement and
ordinary chunk/deflate/default TLS behavior. Inert data and mocked download/wrap calls
exercise those boundaries without executing malicious artifacts or claiming live TLS
integration coverage. Nearest consumer checks retain their separate outcomes above.

Final scoped Ruff format/check, full repository Ruff checks, safe-write guard, explicit
project BasedPyright (671 files, zero errors, 1,526 baseline warnings), reviewed frozen
export parity and `uv lock --check` passed. The first delivery check could not access
the sandboxed default uv cache; the isolated-cache rerun passed. Scoped YAML lint passed
after semantic-preserving formatting: parsed mapping and acceptance digest are unchanged.
Repository-wide YAML output retains unrelated existing errors despite the wrapper's
zero exit code; do not present that wrapper exit as a clean YAML result. Strict selected
OpenSpec passed; applicable all-change validation retains the unrelated governance delta
failure (39/40). Module signing/version and release checks are unchanged-scope controls.

### Explicit local review dispositions

Complete final SpecFact review `review-7ed23a21-a7ab-48be-bb21-8f5a9fcbbb9e` at
2026-10-08T23:49:45Z returned zero errors, three warnings and four information findings.
The following rare exceptions preserve concrete evidence; they do not waive CI or
independent producers:

- `banned-generic-public-names` matches any public name containing `data`. It matches
  the specific cache regression's `seed_app_data` and the unchanged malformed-authority
  test's `metadata_failure`; neither is a generic API name. Preserve descriptive tests
  and the Git-bound authored selector rather than weakening or editing the rule.
- GitPython's `IndexFile.add` has an unknown `fprogress` callback annotation. The same
  diagnostic reproduces on the exact dev fixture with the explicit candidate interpreter;
  changing the staging root adds no type-safety regression. Its argument remains list[str].
- Four AST length suggestions concern byte-equivalent function bodies from dev: rootless
  demo creation, registry construction, fresh-consumer proof and malformed-authority
  rejection. Explicit fixture/command assembly preserves observable setup and assertions;
  no behavior-preserving simplification is demonstrated by line count alone.

### Full local test scope and environment-specific rerun

`SMART_TEST_USE_HATCH=false python tools/smart_test_coverage.py run --level full` on the
initially hash-installed candidate returned 3,201 passed, 11 skipped, four failed and six errors
in 157.72 seconds. Network/cache/home-write restrictions explain the smoke, fixture
acquisition, export and startup failures; a smart-runner unit test also inherited the
override and asserted the default Hatch path. Preserve this failed run, not a full PASS.
The five owning test files were rerun directly without that override, with network and
isolated uv-cache access: 144 passed, two warnings in 51.90 seconds. This recheck covers
every failed/errored case without changing tests to accommodate the local restrictions.
Nested Hatch invocations in this broad scope subsequently changed 34 installed versions,
including Semgrep 1.180.0. Therefore these broad results are not proof of a stable frozen
graph throughout execution. Restore the hash-installed candidate and rerun the isolated
native selectors and focused security controls; hosted frozen delivery/matrix remain
authoritative. No dependency input is changed by this disposable-environment drift.
Hosted full-suite and matrix results are still independent required evidence.

The restored hash-installed graph then passed seven repository regressions in 1.07
seconds, fifteen isolated boundary/control probes in 0.58 seconds, and the native
two-selector executor in 0.53 seconds. Both final advisory gates passed. Review initially
could not load macOS trust anchors and later reported absent type/lint tools; neither
run was accepted as complete. The final run used the reviewed certifi trust bundle,
committed npm BasedPyright and separately hash-locked lint tools with the frozen Python
interpreter. No TLS verification was disabled. Semantic-only YAML formatting retained
the accepted source mapping digest
`sha256:d7740714ca372a5fc9758b11010c15a8c6c4cc46f07be41810dc5d53a1ad787d`.

Hosted/current final review can introduce actionable findings and remains a separate gate.
Original #748 and broader #747 tasks stay open. Final publication, integration and #755
baseline refresh remain unchecked until actually executed.

## Process-boundary proof replay (9 October 2026, Europe/Berlin)

The first signed repair candidate 2ad2b5adf9c90c27086cfcbed9b2730d697c3079
retains its implementation and evidence. Final provenance rejected its direct runtime
import as changed proof support (`stale-red-proof`). It is not accepted final proof.
Use the existing process-boundary integration-test pattern: the parent freezes the same
cache, pip-install and launcher assertions; a bounded child exercises the runtime script.
No verifier, producer, trust policy or CI gate is changed. The selected cache test now
lives in its own file so unrelated direct imports cannot alter the proof-support closure.

A temporary local probe of exactly the same child command observed missing isolated-cache
flags on the dev script and both flags on the candidate. Before retaining new RED, this
replayed authored snapshot has unchanged dev locks, fixture and runtime caller. Old RED
remains historical evidence; the revised mapping needs fresh authored acceptance/RED.
The prior candidate's passing checks are historical, not current-head final results.

The internal wiki mirror was updated in the authoring host and its graph rebuilt on
9 October 2026. The isolated cloud review checkout lacks that sibling repository.

- [ ] After integration, refresh the mirror's merged/dependency status and rebuild the
  graph from the internal repository root; if unavailable, retain this follow-up.

Revised parent regression executed on the unchanged dev caller: one genuine assertion
failure in 0.54 seconds (missing isolated-cache arguments). New JWT/process-boundary
tests have zero explicit-project type errors/warnings. Public #747 now records the
owner-approved focused implementation slice without replacing #748's broader plan.
The hierarchy cache refreshed successfully with 53 issues.

## Accepted process-boundary RED and final repair

Fresh authored commit `2b64c8c6a169db7c61f7355cb6ddf61a464be62e`, tree
`5f7bd033ed70120ebd63b97981bb576f9adea4ec`, ran hosted Requirements `37863114131`,
producer job `113603337985`, artifact `11586716892`, byte digest
`sha256:23b81974d50ffb80c4ca81dbcdec922f9207a2c59603f1965695893430568057`.
Its two mapped selectors have accepted observed/required RED with passed verdict and
no findings. Authored-phase final delivery is intentionally not green.

Only after reading this authentic report, reapply the same five screened package
updates, coherent export, fixture staging root, Semgrep sentinel and isolated runtime
caller from the preserved first candidate. The selected parent test files and mapping
remain unchanged through the final repair. This is the fifth shared correction batch;
the earlier first candidate and rejected final provenance are retained.

Current source mapping digest:
`sha256:21363424683cbe97c5f674bddee60aee7a808d5b6adafbbf5eb159c148e53591`.
Hosted final authority, proof, ordinary checks and current reviews remain required.
The old first candidate's green ordinary CI is not substituted for current-head CI.

Replayed pre-publication checks: seven repository regressions passed in 1.04 seconds;
both native selectors passed in 0.48 seconds. Final SpecFact self-review
`review-9cc9cce0-b38f-4ae2-a302-d24bb42442f6` at 2026-10-09T00:11:34Z has zero errors,
two reproduced baseline warnings and four unchanged AST suggestions, with the explicit
dispositions above. The isolated parent/JWT tests have zero diagnostics. Whole-project
BasedPyright analyzed 672 files with zero errors and 1,526 baseline warnings. Ruff
check/format, scoped YAML, coherent frozen export and strict selected OpenSpec passed.
The sandboxed export attempt could not resolve the package index; permitted-access
reexecution passed. Applicable all-change validation remains 39/40 with the known
unrelated governance delta failure. No canonical-spec placeholder failures are counted
as change validation. Hosted/current final checks and reconciliation are still pending.

## Sixth correction batch: delivery target isolation (9 October 2026, Europe/Berlin)

The human explicitly approved one additional bounded batch after five were consumed.
Published candidate `d4835e5633b5889de0467dcd227494b34932ce23` passes ordinary hosted
CI, including the full Python 3.12 suite and security audit; local final reconciliation
is verified. Fresh hosted execution in run `37863820202` still imports the trusted base
PyJWT 2.13.0 and fails the original JWT regression. Neither the local result nor the
passing producer establishes hosted final completion. No member grant was posted for
this candidate.

The approved test-harness patch isolates the hash-pinned delivery package rather than
changing the trusted verifier. Preparation reproduced the 2.13.0 caller-options mutation
and passed both cases against 2.15.1 in 0.77 seconds. This is preparation evidence, not
accepted native RED. Restore the five production/lock/fixture files to unchanged dev
for the authored phase, retain the same requirement/case identities, and obtain fresh
hosted RED before reapplying the screened repair. Earlier RED remains historical.
The selected parent assertions and tests must remain unchanged from this fresh RED
through final publication. Missing uv, network, hashes or execution fail the probe.

Authored local execution of both mapped probes against unchanged dev produced two
genuine assertion failures in 0.64 seconds. The isolated JWT probe observed the seven
leaked disabled claim options; the cache probe observed missing isolation arguments.
Explicit-project type checking of the revised JWT file has zero errors/warnings; Ruff
check and selected strict OpenSpec pass. These results supplement the forthcoming
accepted hosted RED rather than replacing it.

The revised scoped self-review completed with zero blocking findings. Its one AST
advisory suggests collapsing the low-branch probe function. Retain the explicit
subprocess argument lists: hash enforcement, binary-only/no-dependency installation,
isolated Python and bounded timeouts are independent, auditable security obligations.
Reducing those lists to one line would obscure them without removing behavior.
Markdown lint passed after removing added duplicate blank lines. The internal mirror
was updated and its graph rebuilt for this approved probe design. An initial local
staged planner attempt could not create the shared Git index lock under the sandbox;
this was unavailable local evidence, not a valid native result.

Authored run `37896045048` on `85b69ed9f7e73c27a790ef596e8c713f6cf6cdd3`
contains both genuine assertion failures but its producer rejects binding with
`prior-red-proof-invalid`. The test-only tree still descended from earlier production
commits, which the unchanged binder rejects across history. Preserve that rejected
artifact and authored head; publish the same tested assertions from unchanged dev
without those production ancestors. Reverting production bytes does not establish
a test-only provenance chain. No acceptance or native proof is manufactured.

## Accepted isolated-delivery RED and sixth final correction

The clean authored commit `0f9d114be7e4fd70083d0c1a101590c2ab9ca06d`, tree `6f0c67bc1618219aa1b621f6f2548166ca0c895e`, has
accepted hosted RED in run `37896570864`, artifact `11600054315`, ZIP
byte digest `sha256:b30ddc50df79e0ceb1465baaec8f3ab8872f60e5b4f9c4d458c470651d4befa0`. Its retained report is passed/pass, observed and
required RED, with no findings. Both selected tests have genuine failures. The
unchanged producer and binder attest the test-only source history.

Only after reading this report, reapply the same five screened package changes,
coherent export, fixture staging root, Semgrep sentinel and isolated caller from the
preserved repair. The approved package probe and cache parent tests, mapping and
acceptance record remain unchanged from this authenticated RED through final repair.
This final publication consumes the sixth owner-authorized correction batch. The
rejected earlier authored chain and all five prior batches remain accounted for.
Current-head hosted final execution, authority and completed reviews are still
required; preceding ordinary CI and local checks cannot establish overall green.

Final pre-publication scoped suite: 25 tests passed in 2.23 seconds; both unchanged
native selectors pass. Ruff check/format, project BasedPyright (zero errors),
Markdown lint, selected strict OpenSpec, frozen export parity and uv lock check
passed. All-change validation retains only the previously recorded governance delta
failure (39/40). Final self-review completed with zero blocking findings: the same
two baseline warnings and four unchanged AST suggestions, plus the explicitly
disposed delivery-probe readability advisory. The earlier warning dispositions
and the explicit security-argument rationale apply; no finding is silently waived.
Hosted current-head checks and native final reconciliation remain independent gates.

## Authored remaining Python slice (10 October 2026, Europe/Berlin)

Current dev 553b46f01c6581c96dc92133b6e77404c8df7cd9 retains merged #756
proof, tests and frozen fixes. The owner approved the five retained PRs and
0.55.5 release preparation. #747 metadata, #748 planning scope and the internal
wiki were reconciled before dependency inputs changed. Earlier evidence remains
historical; no previous RED is reused for the new containment requirement.

The isolated Python 3.12.13 baseline was populated by uv sync --frozen --all-extras
and reused by Hatch through HATCH_ENV_TYPE_VIRTUAL_PATH=.venv. The unchanged
GitPython 3.1.61 delivery wheel reached the mocked clone boundary for ../outside;
no real clone or outside write occurred. The new containment regression and the
updated backend/release expectations returned three failures in 1.70 seconds.
The final authored containment test still fails after flag-list simplification.
The two frozen audits returned PASS; they do not cover every upstream disclosure:
GitHub's reviewed GHSA-59cr-6r3x-644w still requires GitPython 3.1.62.

Strict selected OpenSpec and staged native test-authored planning passed. The
acceptance identifies codex:/root as implementation agent and is not a human
Trusted Requirements Authority grant. Ruff formatting/checks and explicit-project
BasedPyright passed with zero errors and 1,526 existing warnings. Scoped YAML
lint passes; the full wrapper reports unrelated archived-YAML failures despite
its zero exit code. No authored contract changed; contract detection returned its
unchanged result. Hosted RED, candidate execution and current final CI remain pending.

The first local review returned zero errors, one baseline naming warning and
three AST suggestions. The new probe's static install flags were factored into
a descriptive immutable tuple to reduce its function length without relaxing
hash/index/no-dependency controls. The baseline warning and two baseline AST
suggestions at test_release_promotion_security_gates.py:506/243 are byte-equivalent
to dev and were already explicitly dispositioned in #756 above; preserve those
assertions and source identities rather than altering unrelated historical proof.

Exact wheel/gem hashes match registry metadata. Package source comparisons match
upstream tags, with GitPython's sole generated __version__ substitution reconciled
against its release metadata. All five selected packages have MIT/BSD licenses.
No candidate package has yet executed. Public Socket screening of GitPython 3.1.62
shows network/shell/filesystem/URL capabilities. Hatchling 1.32.4 reports a medium
potential-vulnerability alert for its code-version source plugin; that file is
byte-identical to the installed 1.32.0 source. This repository supplies a static
project.version, no dynamic version and no code-source configuration. The scoped
triage finds no new reachable code-version input in this build. This is not a
universal safety claim, alert dismissal or security-policy exception. Current
repository Socket checks and an explicit alert disposition remain release gates.

A fresh registry check also found GitPython 3.2.0 and upstream additional security
fixes. Its global advisory records are currently unavailable. The version decision
was returned to the owner; 3.2.0 has not been installed or silently substituted.

## Python stack implementation evidence (10 October 2026)

The user approved GitPython 3.2.0 after validation. Its exact wheel SHA-256 is
`bd70c5ec05cd2b797423e7eb312147d2458d3cca92085888fba2213f85905537`;
the sdist is `fb92310af6844d96adc95ca066ed2e617c00e1dbd146a326626c81e72e18cc2e`.
GitHub authenticates the 3.2.0 tag signature and commit
`6a7180a9dfcb276755a8af99dd78155f775a6b14`. All 37 wheel Python files match
that tag except the expected generated version substitution. The wheel metadata
states BSD-3-Clause, Python >=3.8 and gitdb >=4.0.1,<5. Repository consumers use
GitCmdObjectDB; no explicit GitDB backend was found. The tagged changelog lists
six additional security fixes; missing global advisory API records do not negate
those upstream fixes. Source: <https://github.com/gitpython-developers/GitPython/blob/3.2.0/doc/source/changes.rst>.

The final authored containment probe failed on locked 3.1.61 before adoption
(`gitpython-red-amended.log`, one failure). After the targeted refresh, the
containment/JWT/delivery/release/versioning suite passed all 42 tests. The only
package version changes in uv.lock are GitPython, Hatchling and project metadata;
PyJWT 2.15.1, Semgrep 1.179.0 and virtualenv 21.11.0 remain unchanged.

A real offline source build failed with both the unchanged parent backend 1.32.0
and reviewed 1.32.4: the sdist omitted the wheel's forced bundle-mapper inclusion.
The new actual-build regression failed before adding `/modules/bundle-mapper` to
the sdist include list and passed afterward (one test, 0.81 seconds). The rebuilt
wheel retains byte-identical module metadata; no signed asset changed. Both
release artifacts now build using the hash-installed backend without resolution.

One built wheel installs and exercises init/config/commit/branch/checkout/diff and
ChangeAnalyzer consumers on Python 3.11.15, 3.12.13 and 3.13.14. CLI/package metadata
is 0.55.5 and GitPython is 3.2.0. Extra `uv pip check` reported existing Z3 5.0.0.0
wheel-platform metadata incompatibility (`macosx_13_3_arm64`) although imports and
consumers pass; this advisory result is retained, not claimed green. The repository
CI wheel protocol does not use that extra check. No Z3 version or policy changed.

Both frozen advisory audits, graph/export parity, uv lock check, dependency trust,
version sources, strict PyPI-ahead (latest 0.55.4), format, typing, lint, Bandit,
Semgrep (zero findings) and all four strict module signatures pass locally.
The initial license scan found test-installed Pylint in the shared validation
environment; restoring the frozen graph yields zero license violations. The
initial smart run observed 32 failures and one error after test-environment drift
and externally injected module roots. Fresh scoped reproduction passes 31 tests;
the full rerun uses child-install version constraints and the immutable fixture
without the extra module-roots variable. Its final result is recorded separately.
Repository-wide YAML emits existing archived/other-change errors; changed YAML
is independently linted. Changed-test self review now has zero findings; previous
unchanged #756 findings retain their documented historical disposition.

Socket artifact views for GitPython 3.2.0 wheel and sdist show shell/filesystem/URL
capabilities. Hatchling 1.32.4 retains a potential-vulnerability alert for its
configuration-selected code version plugin. The flagged file is byte-identical
with backend 1.32.0 and this project uses static version metadata, but this source
triage does not replace the protected Socket verdict or create an exception.

Hosted Requirements run 38085488787 on authored head
`d3461301618dd76501c30498bf365e0a65d77697` stopped with `acceptance-missing`
for 15 active sources before execution. It is authenticated diagnostic evidence,
not native RED proof. Local planned and test-authored gates pass using the pinned
fixture and actual agent acceptance; no human authority was fabricated. Final
protected Requirements and Socket eligibility remain necessary before merge.

## Compatible JSON layer evidence (10 October 2026)

PR #727 starts from the signed Python implementation. The authored JSON floor
check fails on the parent declaration (one real failure in `727-red.log`) and
passes after declaring `>= 2.21.2`, `< 3` (all 17 documentation-script tests pass).
Bundler 2.3.5 regenerated the lock conservatively; removing its incidental local
macOS platform leaves only the JSON dependency bound changed. Locked JSON 2.21.2
and Jekyll 4.4.1 and all resolved package versions remain unchanged. JSON 3 is
explicitly deferred because Jekyll 4.4.1 requires JSON 2.x. The documentation
security and compatibility scenarios are authored before the following Ruby
behavior probes and implementation.

The completed parent smart rerun reports 3210 passed, 13 skipped and one failed
marketplace direct-launcher integration test. That test attempts to resolve a
companion module against latest annotated-doc 0.0.5, conflicting with the frozen
0.0.4 constraint. No exception or unlocked dependency update is introduced; this
required gate remains unresolved. Hosted Requirements approval and protected
Socket eligibility also remain pending; local agent acceptance is not human
authority.

## Redirect layer evidence (10 October 2026)

The real Jekyll output probe fails on redirect-from 0.16.0 because an unsafe
JavaScript scheme is rendered (`752-red.log`). The earlier combined fixture
also exposed a control-character scheme parser crash; that diagnostic is retained
separately. Only redirect-from 0.17.0 and its declaration change in the generated
parent-relative delivery lock. The hash-verified reviewed gem is installed from
a local cache using a disposable platform lock; delivery inputs stay Linux-only.
The same output probe passes at root and `/preview`, covering JavaScript/data
scheme rejection, browser-normalized controls, ordinary redirect maps, external
URLs, HTML attributes and JSON-script targets. The new read-only PR workflow
installs the frozen docs bundle, runs probes and builds both deployment paths.

The #727 self-review reports zero errors, 20 warnings and one information item.
Every finding points outside the modified JSON-floor function; those functions
are byte-identical to dev (dynamic import typing, existing duplicate loaders,
generic test fixture class name and long navigation fixture). Record a narrow
unchanged-baseline exception for this dependency-only layer rather than alter
those unrelated tests or old proof. New JSON assertions have no finding.

## Feed layer evidence (10 October 2026)

With the unchanged parent feed 0.17.0, the language probe fails its attribute
injection assertion and the independent CDATA probe fails to parse actual output
(`754-language-red.log`, `754-cdata-red.log`). Only feed 0.18.0 and its declared
patch floor change in the conservatively regenerated lock. Its reviewed SHA-256
`8e6829f455b8764a8fa1bbb198d0ebb3525128dacc6ffe9d15f4df7388bc3647`
is checked before the local frozen installation. Language values round-trip in
feed, alternate-link and entry attributes without injected attributes. Content
and summary CDATA preserve the terminator text, and feed URLs honor the base URL.
All feed and inherited redirect probes pass at root and `/preview`; both full
Jekyll builds also succeed. Existing Minima/Sass deprecation warnings remain
baseline output. The PR workflow runs both feed cases with the inherited checks.

Published Python head 6ccc37a2 has successful hosted Tests/Compatibility, all
Python launcher/wheel matrix jobs, reproducible installed-package/SBOM evidence,
both advisory audits, dependency trust/licenses, independent analysis, signatures,
quality and both Socket checks (run 38086498399). Requirements execution/authority
remain failed (run 38086498423); those failures cannot be replaced by local proof.

## Relative-link layer evidence (10 October 2026)

The same-site rebuild probe fails on locked relative-links 0.8.0 because target
URLs remain cached (`753-red.log`). The conservatively generated parent-relative
lock changes only relative-links to 0.9.1 and its declaration. The reviewed gem
SHA-256 `6d5d70578c669ef9ee4c67f617d91497e0506fe5c1a059e484a900e18efb202e`
is checked before installation. All inherited security probes and relative-link
checks pass at root and `/preview`, including included navigation attributes,
Markdown/nested links, fragments, external URLs and a changed target on rebuild.
Both full-site builds pass. This compatibility update is recorded under Fixed,
separately from redirect/feed/JSON/GitPython security changes. Python locks and
the single 0.55.5 release version stay inherited from #744.

## Final stack verification and publication checkpoint (10 October 2026)

Native stack #757 is registered in the approved five-PR order. Exact action
commits and selected Ruby artifact hash checks now make the final documentation
workflow reproducible before candidate installation. See REVIEW_AND_PROMOTION.md
for dispositions, immutable source identities, release checklist and rollback.

The isolated verifier bug is reproduced by starting pytest with -I -S and the
explicit trusted site path: sysconfig points to the base interpreter. Resolving
the actual gitdb/smmap distribution roots repairs this without importing the
candidate in the parent or changing its hash/no-dependency install controls.
The same corrected test fails on frozen GitPython 3.1.61 (clone boundary reached)
and passes on 3.2.0. Native authored run 38087626467 records RED gate pass; final
run 38087716606 records verified gate pass. Their overall authored failure is
expected while RED is retained for final reconciliation. Original failed runs
remain historical evidence.

GitHub initially rejected the commit email against the signing key. Re-signing
uses its verified <djm81@users.noreply.github.com> identity and changes no tree.
Native RED run 38088121368 binds the same probe to verified authored e9950388;
current final 76a42fc8 replays it. Protected authority remains rejected; no human
role is fabricated. The full local smart run retains 25 failed, 3189 passed, nine
skipped and one error caused by in-process marketplace beartype replacement.
Frozen sync restores the environment; audits, parity, trust/licenses, independent
analysis, strict signatures, version gates and focused security/build/docs probes
pass. Installing the committed npm runner repairs the initial missing-tool type
and lint diagnostics (zero errors, 1526 unchanged project type warnings). These
partial results do not complete the outstanding readiness tasks.
