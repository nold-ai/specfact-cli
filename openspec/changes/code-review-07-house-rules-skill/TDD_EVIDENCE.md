# TDD Evidence: code-review-07-house-rules-skill

## Pre-implementation failing run

- **Timestamp**: 2026-03-16 10:27:00 +0000
- **Command**:
  `hatch run test -- tests/unit/specfact_code_review/rules/test_updater.py -v`
- **Result**: failed during collection

### Failure summary

- `ModuleNotFoundError: No module named 'specfact_code_review.rules'`

This is the expected red-phase failure before implementing the new `rules`
package, updater, and CLI command surface.

## Status

Red phase complete. Production implementation may now begin.

## Post-implementation passing run

- **Timestamp**: 2026-03-16 10:30:00 +0000
- **Command**:
  `hatch run test -- tests/unit/specfact_code_review/rules/test_updater.py -v`
- **Result**: pass

### Passing summary

- The new `specfact_code_review.rules` package imports cleanly and wires into the
  existing `review` command surface.
- The updater algorithm now covers thresholded rule surfacing, stale-rule
  pruning, version/timestamp updates, mirror generation, and the 35-line hard
  cap.
- The command-level scenarios for `rules show`, `rules init`, and `rules update`
  pass in the targeted test suite.

## Repository validation

- **Passing gates**:
  - `hatch run format`
  - `hatch run type-check`
  - `hatch run lint`
  - `hatch run yaml-lint`
  - `hatch run contract-test`
  - `hatch run smart-test`
  - `hatch run test`
- **Blocked gate**:
  - `hatch run verify-modules-signature --require-signature --enforce-version-bump`
    fails because no signing key is configured in the local environment, so the
    manifest can only be refreshed in checksum-only mode.

## Manual command verification

- Direct bundle-command invocation from the updated local source confirms:
  - `rules init` creates `skills/specfact-code-review/SKILL.md`
  - `rules show` prints the generated skill verbatim
  - `rules update` increments the version, surfaces `C901` from ledger history,
    and mirrors the result to `.cursor/rules/house_rules.mdc`
- The outer `specfact code review rules ...` wrapper in this environment still
  resolves the previously bundled stub subgroup, so end-to-end CLI refresh
  remains pending separate module-bundle bootstrap/signature availability.
