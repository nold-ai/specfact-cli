# Design: basedpyright and pylint Runners

## basedpyright Runner

```python
cmd = ["basedpyright", "--outputjson", "--project", "."] + [str(f) for f in files]
result = subprocess.run(cmd, capture_output=True, text=True)
data = json.loads(result.stdout)
```

basedpyright JSON output format:

```json
{
  "generalDiagnostics": [
    {"file": "...", "range": {"start": {"line": N}}, "severity": "error", "message": "..."}
  ]
}
```

Filter: only include diagnostics where `diagnostic["file"]` matches one of the provided files.
Severity mapping: basedpyright `"error"` → `severity="error"`, `"warning"` → `severity="warning"`, `"information"` → `severity="info"`.

## pylint Runner

```python
cmd = ["pylint", "--output-format", "json"] + [str(f) for f in files]
result = subprocess.run(cmd, capture_output=True, text=True)
data = json.loads(result.stdout)
```

pylint JSON: list of dicts with `{"message-id": "W0702", "path": "...", "line": N, "message": "..."}`.

Message ID → category mapping:

```python
PYLINT_CATEGORY_MAP = {
    "W0702": "architecture",  # bare-except
    "W0703": "architecture",  # broad-except
    "C0325": "style",         # superfluous-parens
    "W1505": "architecture",  # deprecated-method
}
```

Default: unmapped message IDs → `category="style"`.

## File Filtering

Both runners run on the full project for accuracy but filter results to return only findings for files in the `files` parameter. This is necessary because basedpyright requires a project context; running it on a single file without context produces incomplete results.

## Test Strategy

Tests mock `subprocess.run` return values. Key test cases:

- basedpyright: error diagnostic, warning diagnostic, non-provided file filtered out
- pylint: W0702 → architecture, W0703 → architecture, unknown ID → style
