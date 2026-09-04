# Change Validation

## Repository and issue reality

- Validation date: 2026-09-04 Europe/Berlin
- Baseline: `origin/dev` at
  `6486fd4b654f4897dbf4ecbbe1eca1e50ea19fbf`
- Issue: nold-ai/specfact-cli#708, open and assigned to `djm81`
- Parent: #692
- Labels: `bug`, `openspec`, `QA`, `security`
- Project: SpecFact CLI, status `In Progress`
- Duplicate search: no open issue or active change covers step-scoped removal of
  pull-request routing state from CI test processes.

## Scope and dependency validation

- The production version checker must retain its existing GitHub base-reference
  behavior.
- GitHub's Variables reference confirms default `GITHUB_*` variables cannot be
  overridden through workflow `env`; the design therefore uses shell-level
  removal inside only the two test steps.
- PR #706 intentionally removes the test-helper workaround and contains no test
  or workflow diff.
- The existing R08 bounded replay design remains the long-term proof-model
  replacement and is not duplicated or modified by this change.
- The existing `0.55.4` version and release notes already own this unreleased
  patch transaction; another version bump would be incorrect.

## Verification status

- Strict OpenSpec validation: passed (`openspec validate
  fix-ci-test-environment-isolation --strict`)
- Focused failing-before evidence: passed (`3 failed` as expected locally and
  in GitHub run `33910361233`)
- Focused passing-after evidence: passed (`5 passed`, starting from inherited
  `GITHUB_BASE_REF=main` and crossing the exact Bash removal boundary)
- Full quality/security/release gates: pending
- Independent review: pending

## Code-review disposition

- `banned-generic-public-names` on the three mapped pytest selectors is a false
  positive. The functions are tests rather than public APIs, and “test process”
  names the exact isolation boundary in the approved mapping and specification.
  Renaming them would invalidate the accepted mapping without improving the
  production interface.
