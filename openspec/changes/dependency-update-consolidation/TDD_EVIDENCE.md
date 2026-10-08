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
