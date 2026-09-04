# Change Validation

## Repository and issue reality

- Validation date: 2026-09-04 Europe/Berlin
- Baseline: `origin/dev` at
  `1d9491595eb4ba0d6cc55823710d9d2e36a21b16`
- Issue: nold-ai/specfact-cli#710, open and assigned to `djm81`
- Parent: #692
- Labels: `bug`, `openspec`, `QA`, `security`
- Project: SpecFact CLI, status `In Progress`
- Duplicate search: draft PRs #711 and #712 were retained for immutable proof
  history but closed as superseded by the clean implementation PR #713.

## Scope and dependency validation

- PR #706 proves the no-Python path: final review exits successfully, then the
  unconditional strict artifact upload fails (run `33913920761`, final job
  `101156814880`).
- Missing reports for real Python targets must remain fatal; only the proven
  no-target path may skip upload.
- PR #706 stays limited to its existing three release-finalization files.
- The existing `0.55.4` version and release notes own this unreleased patch
  transaction; another version bump would be incorrect.

## Verification status

- Strict OpenSpec validation: passed (`openspec validate
  fix-final-requirements-review-artifact --strict`)
- Focused failing-before evidence: passed as an expected RED (`3 failed`)
- Test-authored mapping: accepted by unedited repository-member comment
  `5545980847` at mapping digest
  `sha256:e7354c1071e98cab25b4990b410a40d68865fb57911371b02046d62b50c2c0c1`
- Focused passing-after evidence: passed (`3 passed`; full workflow contract
  file `58 passed`)
- Full local quality/security/release gates: passed (`3,118` tests passed,
  `9` skipped; strict OpenSpec `178/178`; actionlint; changed-file yamllint;
  docs; lint; type-check; both frozen pip-audit graphs; Semgrep and baseline
  gate; Bandit; license; reproducible delivery; version; module signatures)
- GitHub Requirements and ready-for-review checks: pending the frozen-head push
- Independent review: prior selector coverage and draft-PR wording findings
  fixed; deletion-only alert classified as a false positive against the accepted
  R07 diff/file-review ownership contract, with the attempted blocking behavior
  removed before this clean PR

## Review dispositions

- The suggested additional mapped assertion for loop/filter/empty-check
  ordering is deferred as future mutation-hardening, not a defect in this
  change. The inherited R07 contract test already authenticates the
  NUL-delimited collection and existing-file filter fragments; the current
  workflow places the completed loop before the empty-target exit; and an
  independent security review verified metadata-only, deletion-only, mixed,
  present-target, reviewer-failure, and missing-artifact paths. Altering the
  approved selector bytes after the immutable RED run would invalidate the
  accepted mapping and proof without correcting current behavior.
- The three unchanged Code Review generic-name warnings refer to approved #708
  pytest selector names, not public APIs. Renaming them would alter previously
  approved selector identities outside #710 without improving behavior, so the
  existing names are retained as a narrow clean-code exception.
- The approved mapping rationale's shorthand “Python-changing pull requests”
  is governed by its more precise observable: strict artifact enforcement
  applies when an existing Python review target is present. The proposal now
  uses that exact R07 wording; the accepted mapping bytes remain unchanged.
