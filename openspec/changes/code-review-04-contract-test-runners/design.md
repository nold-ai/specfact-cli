# Design: Contract and TDD Gate Runners

## contract_runner.py — AST Scan

Uses Python's `ast` module to scan each provided file. For each function definition at module/class level:
1. Check if the function name starts with `_` → skip (private)
2. Check decorator list for `@require` or `@ensure` (from `icontract`) → skip if present
3. If no icontract decorator found → emit `ReviewFinding(category="contracts", severity="warning", rule="MISSING_ICONTRACT")`

```python
import ast

def scan_for_missing_contracts(path: Path) -> list[ReviewFinding]:
    tree = ast.parse(path.read_text())
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            has_contract = any(
                (isinstance(d, ast.Attribute) and d.attr in ("require", "ensure"))
                or (isinstance(d, ast.Name) and d.id in ("require", "ensure"))
                for d in node.decorator_list
            )
            if not has_contract:
                findings.append(ReviewFinding(...))
    return findings
```

## contract_runner.py — CrossHair Fast Pass

```python
cmd = ["crosshair", "check", "--per_path_timeout", "2"] + [str(f) for f in files]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
```

Parse crosshair output for counterexample lines → emit `ReviewFinding(category="contracts", severity="warning", tool="crosshair")`.

On timeout or binary unavailability: degrade gracefully (log warning, return tool_error finding for crosshair, continue with AST scan results).

## runner.py — Orchestrator

```python
def run_review(files: list[Path], options: ReviewOptions) -> ReviewReport:
    findings = []
    findings.extend(run_ruff(files))
    findings.extend(run_radon(files))
    findings.extend(run_basedpyright(files))
    findings.extend(run_pylint(files))
    findings.extend(run_contract_check(files))
    findings.extend(run_semgrep(files))  # SP-005
    if not options.no_tests:
        findings.extend(run_tdd_gate(files))
    return build_report(files, findings, options)
```

## TDD Gate

Test file discovery:
```python
def expected_test_path(src_file: Path) -> Path:
    # src/specfact_code_review/run/scorer.py
    # → tests/unit/specfact_code_review/run/test_scorer.py
    rel = src_file.relative_to("src")
    return Path("tests/unit") / rel.parent / f"test_{rel.name}"
```

If expected test path does not exist → `TEST_FILE_MISSING` finding, severity=error.
If tests fail or coverage < 80% → testing finding.

## Test Strategy

- `test_contract_runner.py`: test AST scan on fixture files (one with @require, one without)
- `test_runner.py`: mock all sub-runners, verify orchestration calls and merged findings
