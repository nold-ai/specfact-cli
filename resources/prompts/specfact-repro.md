---
description: "Run validation suite for reproducibility and contract compliance"
---

# SpecFact Repro Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact repro` before any analysis - execute the CLI command before any other operations
2. **NEVER write code**: Do not implement validation logic - the CLI handles this
3. **NEVER create YAML/JSON directly**: All validation reports must be CLI-generated
4. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata - use it, don't bypass its validation
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate or recreate it - use the CLI output as the source of truth
6. **NEVER manipulate internal code**: Do NOT use Python code to directly modify validation results or any internal data structures. The CLI is THE interface - use it exclusively.
7. **No internal knowledge required**: You should NOT need to know about internal implementation details (ReproChecker, validation tools, etc.). All operations must be performed via CLI commands.
8. **NEVER read artifacts directly**: Do NOT read validation report files directly to extract information unless for display purposes. Use CLI output to get validation results.

### What Happens If You Don't Follow This

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures
- ❌ Works only in Copilot mode, fails in CI/CD
- ❌ Breaks when CLI internals change
- ❌ Requires knowledge of internal code structure

## ⏸️ Wait States: User Input Required

**When user input is required, you MUST wait for the user's response.**

### Wait State Rules

1. **Never assume**: If input is missing, ask and wait
2. **Never continue**: Do not proceed until user responds
3. **Be explicit**: Clearly state what information you need
4. **Provide options**: Give examples or default suggestions

## Goal

Run full validation suite for reproducibility and contract compliance. This command executes comprehensive validation checks including linting, type checking, contract exploration, and tests.

## Operating Constraints

**STRICTLY READ-ONLY**: This command runs validation checks and generates reports. It does not modify the codebase (unless `--fix` is used for auto-fixes).

**Command**: `specfact repro`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag.

## What This Command Does

The `specfact repro` command:

1. **Runs** comprehensive validation checks:
   - Lint checks (ruff)
   - Async patterns (semgrep)
   - Type checking (basedpyright)
   - Contract exploration (CrossHair)
   - Property tests (pytest tests/contracts/)
   - Smoke tests (pytest tests/smoke/)

2. **Displays** validation results in a summary table
3. **Generates** validation report (YAML format)
4. **Returns** appropriate exit codes (0=success, 1=failed, 2=timeout)

## Execution Steps

### 1. Parse Arguments and Validate Input

**Parse user input** to extract:

- Repository path (optional, default: `.`)
- Verbose output (optional, default: `false`)
- Time budget (optional, default: `120` seconds)
- Fail-fast (optional, default: `false`)
- Auto-fix (optional, default: `false`)
- Output path (optional, default: `.specfact/reports/enforcement/report-<timestamp>.yaml`)

**WAIT STATE**: If user wants to run validation but hasn't specified options, ask:

```text
"Validation suite options:
- Repository path (default: current directory)
- Time budget in seconds (default: 120)
- Fail-fast: Stop on first failure (default: false)
- Auto-fix: Apply auto-fixes where available (default: false)
- Verbose: Show detailed output (default: false)

Proceed with defaults or specify options?
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

### 2. Execute Repro Command

**Execute CLI command**:

```bash
# Basic usage (default options)
specfact repro

# With verbose output
specfact repro --verbose

# With custom budget and fail-fast
specfact repro --budget 180 --fail-fast

# With auto-fix enabled
specfact repro --fix

# With custom output path
specfact repro --out .specfact/reports/custom-report.yaml

# Full example
specfact repro \
  --repo . \
  --verbose \
  --budget 180 \
  --fail-fast \
  --fix \
  --out .specfact/reports/enforcement/report.yaml
```

**Capture from CLI**:

- Validation checks running (progress indicator)
- Check summary table (Check, Tool, Status, Duration)
- Summary statistics (Total checks, Passed, Failed, Timeout, Skipped)
- Report written to output path
- Exit code (0=success, 1=failed, 2=timeout)

### 3. Handle Errors

**Common errors**:

- **Validation failures**: CLI will report failed checks in summary table
- **Timeout**: CLI will report timeout if budget is exceeded (exit code 2)
- **Repository not found**: CLI will report error if repository path doesn't exist

### 4. Report Completion

**After successful execution**:

```markdown
✓ Validation suite completed!

**Summary**:
- Total checks: 6
- Passed: 5
- Failed: 1
- Timeout: 0
- Skipped: 0
- Total duration: 45.23s

**Check Results**:

| Check | Tool | Status | Duration |
|-------|------|--------|----------|
| Lint | ruff | ✓ PASSED | 2.34s |
| Async Patterns | semgrep | ✓ PASSED | 5.67s |
| Type Check | basedpyright | ✓ PASSED | 8.12s |
| Contract Exploration | CrossHair | ✓ PASSED | 25.45s |
| Property Tests | pytest | ✓ PASSED | 3.21s |
| Smoke Tests | pytest | ✗ FAILED | 0.44s |

**Report**: `.specfact/reports/enforcement/report-2025-01-17T14-30-00.yaml`

**Next Steps**:
- Review failed checks (use --verbose for details)
- Fix issues and re-run validation
- Configure enforcement: `/specfact-cli/specfact-enforce`
```

**If validation failed**:

```markdown
✗ Validation suite failed!

**Failed Checks**: 1
**Exit Code**: 1

**Failed Checks**:
- Smoke Tests (pytest): Test failures detected

**Next Steps**:
- Run with --verbose to see detailed error messages
- Fix issues and re-run validation
- Use --fix to apply auto-fixes where available
```

## Guidelines

### Validation Checks

**Lint Checks (ruff)**:

- Code style and formatting
- Common Python issues
- Import organization

**Async Patterns (semgrep)**:

- Async/await anti-patterns
- Potential race conditions
- Async best practices

**Type Checking (basedpyright)**:

- Type annotation compliance
- Type safety issues
- Missing type hints

**Contract Exploration (CrossHair)**:

- Contract violation detection
- Edge case discovery
- Property validation

**Property Tests (pytest tests/contracts/)**:

- Contract-based tests
- Property-based testing
- Contract compliance

**Smoke Tests (pytest tests/smoke/)**:

- Basic functionality tests
- Integration smoke tests
- Quick validation

### Time Budget

- Default: 120 seconds
- Used for contract exploration and long-running checks
- Exceeding budget results in timeout (exit code 2)
- Increase budget for large codebases

### Auto-Fix

- Applies Semgrep auto-fixes where available
- Does not modify code for other checks
- Review changes before committing

### Best Practices

- Run validation before committing changes
- Use `--fail-fast` in CI/CD to stop on first failure
- Use `--verbose` for debugging failed checks
- Review validation reports to track improvements
- Set appropriate time budget for your codebase size

## Context

{ARGS}

--- End Command ---
