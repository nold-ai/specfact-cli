# TDD Evidence — code-review-zero-findings

## Pre-fix Baseline (Task 1.3)

**Command:** `hatch run specfact code review run --scope full --json --out /tmp/baseline-review.json`
**Timestamp:** 2026-03-18 21:31:57 UTC
**Result:** `overall_verdict: FAIL`

### Baseline Summary

| Category     | Count |
|-------------|-------|
| type_safety  | 1600  |
| architecture | 352   |
| contracts    | 291   |
| clean_code   | 279   |
| tool_error   | 1     |
| **TOTAL**    | **2523** |

### Top Rules

| Rule                      | Count |
|--------------------------|-------|
| reportUnknownMemberType   | 1515  |
| print-in-src              | 352   |
| MISSING_ICONTRACT         | 291   |
| reportAttributeAccessIssue| 58    |
| CC16                      | 28    |
| CC14 (warning)            | 25    |
| CC13 (warning)            | 24    |
| CC15 (warning)            | 22    |
| CC17                      | 20    |
| reportUnsupportedDunderAll| 17    |

**Score:** 0 | **reward_delta:** -80

---

## Failing Test Run (Task 2.6)

**Design note:** `tests/unit/specfact_cli/test_dogfood_self_review.py` skips in
`TEST_MODE=true` (always set by `conftest.py`) to protect CI from a slow live
60-second review run. The "failing evidence" is therefore the baseline review
result above — 2522 findings on the pre-fix codebase — which the tests would
assert against if run outside TEST_MODE.

**Proxy evidence command (pre-fix):**
```
hatch run specfact code review run --scope full --json --out /tmp/baseline-review.json
```
**Timestamp:** 2026-03-18 21:31:57 UTC
**Result:** FAIL — 2522 findings, overall_verdict: FAIL
  - test_review_overall_verdict_pass → would FAIL (verdict=FAIL, not PASS)
  - test_zero_basedpyright_unknown_member_type → would FAIL (1515 findings)
  - test_zero_semgrep_print_in_src → would FAIL (352 findings)
  - test_zero_missing_icontract → would FAIL (291 findings)
  - test_zero_radon_cc_error_band → would FAIL (202 CC>=16 findings)
  - test_zero_tool_errors → PASS (tool_error fixed by .pylintrc in task 1.4)

---

## Post-fix Passing Run (Task 7.3)

**Command:** TBD
**Timestamp:** TBD
**Expected Result:** `overall_verdict: PASS`, 0 findings

---

## Intermediate Branch Checkpoint (2026-03-18)

**Command:** `python3 -m pytest tests/unit/specfact_cli/test_dogfood_self_review.py -q`
**Timestamp:** 2026-03-18 22:58:00 UTC
**Result:** PASS (expected skips under `TEST_MODE=true`)
  - 6 tests collected
  - 6 tests skipped by design because CI test mode suppresses the live review invocation

**Command:** `basedpyright --outputjson modules/bundle-mapper/src/app.py scripts/verify-bundle-published.py`
**Timestamp:** 2026-03-18 22:56:00 UTC
**Result:** PASS with 0 errors, 2 warnings
  - fixed `reportCallIssue` mismatches in `modules/bundle-mapper/src/app.py`
  - fixed `reportOptionalMemberAccess` issues in `scripts/verify-bundle-published.py`

**Command:** `basedpyright --outputjson <branch-touched light files>`
**Timestamp:** 2026-03-18 22:59:00 UTC
**Result:** PASS with 0 errors, 1103 warnings
  - branch-local hard errors reduced from 5 to 0 in the touched light-file set
  - largest remaining warning clusters are `module_registry/src/commands.py`, `adapters/ado.py`, `adapters/github.py`, and `cli.py`
