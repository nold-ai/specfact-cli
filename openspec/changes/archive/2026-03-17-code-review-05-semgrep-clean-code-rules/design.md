# Design: Semgrep Custom Clean Code Rules

## semgrep_runner.py

```python
cmd = ["semgrep", "--config", ".semgrep/clean_code.yaml", "--json"] + [str(f) for f in files]
result = subprocess.run(cmd, capture_output=True, text=True)
data = json.loads(result.stdout)
```

Filter results to provided file list. Map each semgrep result to `ReviewFinding`.

Rule ID → category mapping:
```python
SEMGREP_RULE_CATEGORY = {
    "get-modify-same-method": "clean_code",
    "unguarded-nested-access": "clean_code",
    "cross-layer-call": "architecture",
    "module-level-network": "architecture",
    "print-in-src": "architecture",
}
```

## clean_code.yaml Rule Structure

Each rule follows the semgrep YAML format:

```yaml
rules:
  - id: unguarded-nested-access
    message: "Unguarded nested attribute access (a.b.c) — add a None check or early return"
    severity: WARNING
    languages: [python]
    patterns:
      - pattern: $A.$B.$C
      - pattern-not: |
          if $A.$B:
              ...
      - pattern-not: |
          if $A and $A.$B:
              ...
```

## Fixture Files

For each rule, two fixture files:
- `bad_<rule>.py` — contains the anti-pattern; semgrep MUST report a finding
- `good_<rule>.py` — clean equivalent; semgrep MUST NOT report a finding

Unit tests run semgrep against each fixture pair and assert fire/no-fire.

## Config Path Resolution

The runner resolves `.semgrep/clean_code.yaml` relative to the module package root. When running outside the package (e.g., during e2e tests), the path is resolved from the installed module's data directory.
