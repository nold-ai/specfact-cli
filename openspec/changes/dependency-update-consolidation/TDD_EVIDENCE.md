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
