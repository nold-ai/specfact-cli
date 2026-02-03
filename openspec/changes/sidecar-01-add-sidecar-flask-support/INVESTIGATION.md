# CrossHair Flask Execution Investigation

## Summary

Investigation into why CrossHair isn't detecting violations for Flask routes that return 404/302 instead of expected 200 responses.

## Findings

### 1. Missing `_extract_expected_status_codes` Call ✅ FIXED

**Issue**: The `_extract_expected_status_codes` function was defined but never called in `extract_operations`, causing:

- `expected_status_codes` to default to `[200]` instead of extracting from OpenAPI
- Postconditions to only allow `[200, 201, 204]` (404 was not included)
- 404 responses would violate contracts, but CrossHair wasn't detecting them

**Fix Applied**:

- Added call to `_extract_expected_status_codes(responses)` in `extract_operations` (line 103)
- Added `"expected_status_codes": expected_status_codes` to operations dict (line 112)
- Added `302` and `404` to allowed codes in expansion logic (line 581)

**Result**: All 26 operations now have `expected_status_codes` extracted correctly (e.g., `[200, 400, 500]`)

### 2. CrossHair Execution Environment

**Current Implementation**:

- CrossHair is run via `crosshair check` command (system CrossHair)
- `PYTHONPATH` is set to include sidecar venv's site-packages
- But CrossHair's own Python interpreter (system Python) may not have Flask installed

**Key Code** (`crosshair_runner.py`):

```python
base_cmd = ["crosshair", "check", str(source_path)]
# PYTHONPATH is set, but CrossHair uses system Python
env["PYTHONPATH"] = pythonpath
```

**Issue**: CrossHair's Python interpreter needs Flask to be importable, but:

- System Python may not have Flask
- Even with PYTHONPATH set, CrossHair's internal Python may not use it correctly
- CrossHair may not be able to execute Flask routes during symbolic execution

### 3. Sidecar Venv Status ✅ WORKING

**Verification**:

- Sidecar venv exists at `.specfact/venv/`
- Flask and SQLAlchemy are installed in venv
- Flask routes can be executed successfully in venv:

  ```python
  ✅ Flask route executed: GET / -> 302
  ✅ Flask app available: True
  ✅ Test client available: True
  ```

### 4. Potential Solutions

#### Option A: Run CrossHair with Venv Python (Recommended)

Modify `crosshair_runner.py` to use venv Python when available:

```python
# If python_cmd is set (venv Python), use it to run CrossHair
if python_cmd and Path(python_cmd).exists():
    base_cmd = [python_cmd, "-m", "crosshair", "check", str(source_path)]
else:
    base_cmd = ["crosshair", "check", str(source_path)]
```

**Pros**:

- Ensures CrossHair uses Python with Flask installed
- Matches the environment where harness was generated

**Cons**:

- Requires CrossHair to be installed in venv
- May need to install CrossHair in sidecar venv

#### Option B: Install CrossHair in Sidecar Venv

Add CrossHair to dependency installation in `dependency_installer.py`:

```python
def _get_framework_dependencies(framework_type: FrameworkType | None) -> list[str]:
    base_deps = []
    if framework_type == FrameworkType.FLASK:
        base_deps = ["flask", "werkzeug"]
    # Add CrossHair for contract validation
    base_deps.append("crosshair-tool")
    return base_deps
```

#### Option C: Mock/Stub Flask Dependencies for CrossHair

Create lightweight mocks that CrossHair can execute:

- Mock Flask app context
- Mock test client
- Return deterministic responses

**Pros**:

- Works even if Flask isn't available
- Faster symbolic execution

**Cons**:

- May miss real bugs that depend on Flask internals
- Requires maintaining mock code

### 5. CrossHair Symbolic Execution Limitations

**Known Limitations**:

- CrossHair uses symbolic execution, not actual runtime execution
- May not be able to execute complex frameworks like Flask during symbolic execution
- Database dependencies, external services, and app context may not work
- May need to mock/stub these dependencies

**Hypothesis**: CrossHair may not be executing Flask routes during symbolic execution due to:

1. Flask app context requirements
2. Database dependencies (SQLAlchemy)
3. External service dependencies
4. Complex framework initialization

### 6. Next Steps

1. **Test Option A**: Modify `crosshair_runner.py` to use venv Python
2. **Verify CrossHair Execution**: Run CrossHair on a simple harness function and check if it can import Flask
3. **Check CrossHair Output**: Review verbose CrossHair output to see if it's actually executing Flask code
4. **Consider Mocking**: If CrossHair can't execute Flask, create lightweight mocks for symbolic execution
5. **Alternative Validation**: Consider using runtime testing (pytest) for actual Flask execution, and CrossHair for simpler contract validation

## Recommendations

1. **Immediate**: Fix `crosshair_runner.py` to use venv Python when available
2. **Short-term**: Install CrossHair in sidecar venv during dependency installation
3. **Long-term**: Investigate if CrossHair can actually execute Flask routes, or if mocking is needed

## Related Files

- `src/specfact_cli/validators/sidecar/harness_generator.py` - Harness generation
- `src/specfact_cli/validators/sidecar/crosshair_runner.py` - CrossHair execution
- `src/specfact_cli/validators/sidecar/orchestrator.py` - Orchestration
- `src/specfact_cli/validators/sidecar/dependency_installer.py` - Dependency installation
