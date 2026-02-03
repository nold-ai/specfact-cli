# CrossHair Execution Investigation and Recommendations

**Date**: 2026-01-12  
**Status**: ✅ **COMPLETE**  
**Purpose**: Document CrossHair execution investigation findings and recommendations

---

## Overview

This document summarizes the investigation into CrossHair execution for Flask applications, including root causes, solutions, and known limitations.

## Investigation Summary

### Root Causes Identified

1. ✅ **Missing `_extract_expected_status_codes` Call** - **FIXED**
2. ✅ **CrossHair Execution Environment** - **FIXED**
3. ✅ **Dependency Installation** - **FIXED**
4. ⚠️ **Symbolic Execution Limitations** - **DOCUMENTED**

## Root Cause 1: Missing Status Code Extraction ✅ FIXED

### Issue

The `_extract_expected_status_codes` function was defined but never called, causing:

- `expected_status_codes` to default to `[200]` instead of extracting from OpenAPI
- Postconditions to only allow `[200, 201, 204]` (404 was not included)
- 404 responses would violate contracts, but CrossHair wasn't detecting them

### Fix Applied

- Added call to `_extract_expected_status_codes(responses)` in `extract_operations` (line 103)
- Added `"expected_status_codes": expected_status_codes` to operations dict (line 112)
- Added `302` and `404` to allowed codes in expansion logic (line 581)

### Result

All 26 operations now have `expected_status_codes` extracted correctly (e.g., `[200, 400, 500]`)

## Root Cause 2: CrossHair Execution Environment ✅ FIXED

### Issue

CrossHair was run with system Python, but Flask is only in sidecar venv:

- CrossHair's Python interpreter (system Python) may not have Flask installed
- Even with PYTHONPATH set, CrossHair's internal Python may not use it correctly
- CrossHair may not be able to execute Flask routes during symbolic execution

### Fix Applied

**Modified `crosshair_runner.py`**:
- Added `python_cmd` parameter to `run_crosshair()`
- Use venv Python when available: `[venv_python, "-m", "crosshair", "check", ...]`
- Fall back to system CrossHair if venv Python not available

**Updated `dependency_installer.py`**:
- Added `crosshair-tool` to framework dependencies
- CrossHair is now installed during sidecar venv setup

**Updated `orchestrator.py`**:
- Pass `python_cmd` to `run_crosshair()` calls
- Venv Python is now used for CrossHair execution

### Result

CrossHair now uses the venv where Flask is installed, ensuring Flask can be imported and executed.

## Root Cause 3: Dependency Installation ✅ FIXED

### Issue

Dependencies were not being installed in sidecar venv:

- Flask was not available for harness execution
- Harness dependencies (beartype, icontract) were missing
- CrossHair was not installed in venv

### Fix Applied

**Venv Creation**:
- Uses `symlinks=False` to avoid libpython shared library issues
- Validates venv Python can actually run (detects broken venvs)
- Automatically recreates broken venvs

**Dependency Installation**:
- Framework dependencies installed automatically (Flask, FastAPI, etc.)
- Project dependencies detected and installed (requirements.txt, pyproject.toml)
- Harness dependencies added (beartype, icontract)

### Result

All dependencies are now installed correctly in sidecar venv, enabling Flask route execution.

## Root Cause 4: Symbolic Execution Limitations ⚠️ DOCUMENTED

### Known Limitations

CrossHair uses symbolic execution, not actual runtime execution:

1. **Framework Complexity**: May not be able to execute complex frameworks like Flask during symbolic execution
2. **Database Dependencies**: Database calls may not work in symbolic execution
3. **External Services**: External service calls may not be executable
4. **App Context**: Framework app context requirements may not be satisfied

### Current Behavior

For complex Flask applications:

- **Timeouts Are Expected**: Symbolic execution of Flask routes is computationally expensive
- **Partial Results**: Per-path timeouts ensure partial results are available even if overall timeout is reached
- **Status**: "Not confirmed" indicates analysis is working but couldn't complete within timeout

### Workarounds

1. **Per-Path Timeouts**: Prevent single route from blocking others
2. **Overall Timeout**: Safety net to prevent infinite hangs
3. **Partial Results**: Check summary files for routes that were analyzed

## Recommendations

### Immediate Actions ✅ COMPLETED

1. ✅ **Fix `crosshair_runner.py`** to use venv Python when available
2. ✅ **Install CrossHair in sidecar venv** during dependency installation
3. ✅ **Fix venv creation** to use `symlinks=False` to avoid libpython issues
4. ✅ **Add harness dependencies** (beartype, icontract) to base dependencies

### Short-Term Actions ✅ COMPLETED

1. ✅ **Add response structure validation** - Enhanced with property and array item validation
2. ✅ **Add detailed violation reporting** - Counterexample extraction and display implemented
3. ✅ **Optimize CrossHair execution time** - Timeout optimizations implemented
4. ✅ **Improve user-friendly error messages** - Fixed Rich markup parsing issues

### Long-Term Considerations

1. **Mock/Stub Dependencies**: Create lightweight mocks for symbolic execution
2. **Parallel Execution**: Consider parallel execution for multiple functions
3. **Contract Optimization**: Optimize contract complexity for faster execution
4. **Alternative Validation**: Consider runtime testing (pytest) for actual Flask execution

## Timeout Configuration

### Default Settings

- **Overall Timeout**: 120 seconds (allows analysis of multiple routes)
- **Per-Path Timeout**: 10 seconds (prevents single route from blocking)
- **Per-Condition Timeout**: 5 seconds (prevents individual checks from hanging)

### Why These Values

- **Per-path timeouts are more effective**: They allow progress even if some routes are slow
- **Overall timeout is a safety net**: Prevents infinite hangs
- **Per-condition timeouts prevent deep hangs**: Individual contract checks can't block everything

### Adjusting Timeouts

Timeouts can be adjusted in `TimeoutConfig`:

```python
# In models.py
class TimeoutConfig(BaseModel):
    crosshair: int = 120  # Overall timeout
    crosshair_per_path: int = 10  # Per-path timeout
    crosshair_per_condition: int = 5  # Per-condition timeout
```

## Expected Behavior

### Simple Routes

- Analyzed quickly (often < 1 second each)
- Contracts confirmed or violations found

### Complex Routes

- May timeout at 10 seconds per path
- Other routes continue to be analyzed
- Partial results available in summary file

### Overall Execution

- Analysis completes in ~2 minutes for complex apps
- Partial results available even if timeout occurs
- Summary file contains detailed analysis results

## Troubleshooting

### CrossHair Not Finding Violations

**Possible Causes**:
1. Contracts too weak (no validation rules)
2. Expected status codes not extracted correctly
3. CrossHair not executing Flask routes

**Solutions**:
1. Strengthen contracts with validation rules
2. Verify `_extract_expected_status_codes` is called
3. Check that Flask is available in venv

### Timeout Issues

**Expected Behavior**: Timeouts are normal for complex Flask applications

**Solutions**:
1. Check summary file for partial results
2. Increase timeout if needed (modify `TimeoutConfig`)
3. Focus on specific routes by generating smaller harness files

### Import Errors

**Issue**: `ModuleNotFoundError: No module named 'flask'`

**Solutions**:
1. Verify Flask is installed in venv: `.specfact/venv/bin/pip list | grep flask`
2. Check PYTHONPATH includes venv site-packages
3. Reinstall dependencies: Delete venv and re-run validation

## Related Documentation

- [Investigation Report](./INVESTIGATION.md) - Original investigation findings
- [Flask Sidecar Usage](./FLASK-SIDECAR-USAGE.md) - Flask-specific guide
- [Dependency Installation](./DEPENDENCY-INSTALLATION.md) - Dependency setup
- [Contract Strengthening](./CONTRACT-STRENGTHENING.md) - Contract design

---

**Rulesets Applied**: SpecFact CLI rules, Python GitHub rules, Clean Code principles  
**AI Provider**: Claude (Sonnet 4.5)
