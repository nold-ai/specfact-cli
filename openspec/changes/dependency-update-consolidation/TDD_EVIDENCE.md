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
