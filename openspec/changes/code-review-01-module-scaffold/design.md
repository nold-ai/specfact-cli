# Design: specfact-code-review Module Scaffold

## Architecture Overview

The module follows the standard `specfact-cli-modules` package pattern:
- `module-package.yaml` defines the module metadata and `bundle_group_command: code`
- `review/app.py` is the Typer extension entrypoint registered by the CLI registry
- `run/findings.py` contains the Pydantic data models (`ReviewFinding`, `ReviewReport`)
- `run/scorer.py` contains the pure scoring algorithm

## Module Registration

The `bundle_group_command: code` field tells the CLI registry to merge this module's Typer app into the existing `specfact code` command group via `_merge_typer_apps`. The review subgroup is added as:

```
specfact code
  └── review     ← added by this module
        ├── run
        ├── ledger
        └── rules
```

## ReviewReport Governance-01 Alignment

`ReviewReport` wraps the standard governance-01 evidence envelope fields. Mapping:

| Review concept | governance-01 field |
|---|---|
| verdict PASS | `overall_verdict = "PASS"` |
| verdict WARN | `overall_verdict = "PASS_WITH_ADVISORY"` |
| verdict BLOCK | `overall_verdict = "FAIL"` |
| PASS/WARN → exit 0 | `ci_exit_code = 0` |
| BLOCK → exit 1 | `ci_exit_code = 1` |

Review-specific extensions (`score`, `reward_delta`, `findings[]`, `summary`, `house_rules_updates`) live alongside standard fields without overriding them.

## Scoring Algorithm

```python
base_score = 100

# Deductions
for finding in findings:
    if finding.severity == "error" and not finding.fixable:
        score -= 15
    elif finding.severity == "error" and finding.fixable:
        score -= 5
    elif finding.severity == "warning":
        score -= 2
    elif finding.severity == "info":
        score -= 1

# Bonuses (applied once per run)
if zero_loc_violations: score += 5
if zero_complexity_violations: score += 5
if all_apis_have_icontract: score += 5
if coverage_90_plus: score += 5
if no_new_suppressions: score += 5

score = max(0, min(120, score))
reward_delta = score - 80  # range: -80..+20
```

## Verdict Logic

```python
# Blocking error overrides score
if any(f.severity == "error" and not f.fixable for f in findings):
    verdict = "FAIL"
elif score >= 70:
    verdict = "PASS"
elif score >= 50:
    verdict = "PASS_WITH_ADVISORY"
else:
    verdict = "FAIL"
```

## File Locations (in specfact-cli-modules)

```
packages/specfact-code-review/
├── module-package.yaml
└── src/specfact_code_review/
    ├── __init__.py
    ├── review/
    │   ├── __init__.py
    │   ├── app.py          ← module extension entrypoint
    │   └── commands.py     ← review subgroup wiring
    └── run/
        ├── __init__.py
        ├── findings.py     ← ReviewFinding, ReviewReport
        ├── scorer.py       ← scoring algorithm
        └── commands.py     ← review run command (stub; completed in SP-008)
```

## Contract Strategy

All public APIs in this change receive:
- `@beartype` — runtime type enforcement
- `@require` — preconditions on inputs
- `@ensure` — postconditions on outputs

Scorer is a pure function: `@require(findings is a list)` + `@ensure(0 <= result.score <= 120)`.

## Testing Strategy (TDD-first)

1. Write `test_findings.py` — test `ReviewFinding` field validation and defaults
2. Write `test_scorer.py` — test all scoring scenarios and bonus conditions
3. Run tests → expect failure (files don't exist yet)
4. Create `findings.py` and `scorer.py` until tests pass
5. Run `hatch run contract-test` to validate icontract decorators
