# Design: review run End-to-End Integration

## Command Interface

```python
@app.command()
@beartype
def run(
    files: list[Path] = typer.Argument(None, help="Files to review. Defaults to git diff HEAD."),
    json_output: bool = typer.Option(False, "--json", help="Emit ReviewReport JSON to stdout"),
    score_only: bool = typer.Option(False, "--score-only", help="Print reward_delta only"),
    no_tests: bool = typer.Option(False, "--no-tests", help="Skip TDD gate"),
    fix: bool = typer.Option(False, "--fix", help="Apply ruff --fix + isort before re-running"),
    rules_path: Optional[Path] = typer.Option(None, "--rules", help="Path to house_rules skill"),
) -> None:
```

## --fix Flow

```
1. Run all tool runners → get initial report
2. Identify auto-fixable findings (finding.fixable == True)
3. Run: ruff --fix <files> && isort <files>
4. Re-run all tool runners → get final report
5. Output final report
```

## Output Modes

- Default: Rich tables grouped by category, summary row, score/verdict line
- `--json`: JSON-serialized `ReviewReport` to stdout (machine-readable)
- `--score-only`: single integer `reward_delta` to stdout

## Rich Table Format

```
┌─────────────────────────────────────────────────────┐
│  Code Review — 3 findings                           │
├─────────────────┬──────────────┬────────────────────┤
│ clean_code (2)                                       │
├──────────┬──────┬────────┬─────┬───────────────────┤
│ File     │ Line │ Tool   │Rule │ Message            │
│ scorer.py│  47  │ ruff   │C901 │ Too complex (13>12)│
│ runner.py│  12  │ radon  │CC   │ Complexity: 14     │
├─────────────────────────────────────────────────────┤
│ Score: 86 (+6)  PASS ✓                              │
└─────────────────────────────────────────────────────┘
```

## cli-val-01 Scenario YAML Format

```yaml
command: specfact code review run
scenarios:
  - name: clean-file-passes
    description: Clean Python file produces PASS verdict
    args: ["tests/fixtures/review/clean_module.py"]
    expected_exit_code: 0
    expected_stdout_contains: "PASS"

  - name: missing-files-arg-uses-git-diff
    description: No files argument falls back to git diff HEAD
    args: []
    expected_exit_code: 0  # or 1 depending on repo state

  - name: invalid-file-path-exits-nonzero
    description: Non-existent file path produces error
    args: ["nonexistent.py"]
    expected_exit_code: 2
    expected_stderr_contains: "not found"
```

## E2E Test

```python
def test_review_run_clean_fixture():
    result = subprocess.run(
        ["specfact", "code", "review", "run", "--json",
         "tests/fixtures/review/clean_module.py"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    report = ReviewReport.model_validate_json(result.stdout)
    assert report.overall_verdict == "PASS"

def test_review_run_dirty_fixture():
    result = subprocess.run(
        ["specfact", "code", "review", "run", "--json",
         "tests/fixtures/review/dirty_module.py"],
        capture_output=True, text=True
    )
    assert result.returncode == 1
    report = ReviewReport.model_validate_json(result.stdout)
    assert report.overall_verdict == "FAIL"
```
