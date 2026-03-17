# Design: Ruff and Radon Tool Runners

## Runner Pattern

Both runners follow the same pattern:
1. Accept a `files: list[Path]` parameter (validated by `@require`)
2. Invoke the external tool via `subprocess.run` with JSON output
3. Parse the JSON output
4. Map each finding to a `ReviewFinding` using the category/severity table
5. Return `list[ReviewFinding]`
6. On parse error or tool unavailability: return `[ReviewFinding(category="tool_error", ...)]`

## Ruff Runner

```python
cmd = ["ruff", "check", "--output-format", "json"] + [str(f) for f in files]
result = subprocess.run(cmd, capture_output=True, text=True)
data = json.loads(result.stdout)
```

Rule prefix → category mapping:
```python
RULE_CATEGORY_MAP = {
    "S": "security",     # Bandit security rules
    "C9": "clean_code",  # McCabe complexity
    "E": "style",        # pycodestyle errors
    "F": "style",        # pyflakes
    "I": "style",        # isort
    "W": "style",        # pycodestyle warnings
}
```

Fixable detection: ruff JSON includes `"fix": {"applicability": "safe"}` — map to `fixable=True`.

## Radon Runner

```python
cmd = ["radon", "cc", "-j"] + [str(f) for f in files]
result = subprocess.run(cmd, capture_output=True, text=True)
data = json.loads(result.stdout)
```

For each function block with complexity > 12:
```python
severity = "warning" if complexity <= 15 else "error"
```

## Test Strategy (TDD-first)

Unit tests mock `subprocess.run` to return fixture JSON:
- `test_ruff_runner.py`: fixture outputs for S603, C901, E501; test category mapping, filter, tool_error
- `test_radon_runner.py`: fixture outputs for complexity 13, 16, 10; test severity thresholds

Tests run before implementation files exist (TDD-first).
