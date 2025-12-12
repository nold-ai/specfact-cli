# Integration Showcases: Bugs Fixed via CLI Integrations

> **Core USP**: SpecFact CLI works seamlessly with VS Code, Cursor, GitHub Actions, and any agentic workflow. This document showcases real examples of bugs that were caught and fixed through different integration points.

---

## Overview

SpecFact CLI works with your existing tools—no new platform to learn. These examples show real bugs that were caught through different integrations.

### What You Need

- **Python 3.11+** installed
- **SpecFact CLI** installed (via `pip install specfact-cli` or `uvx specfact-cli@latest`)
- **Your favorite IDE** (VS Code, Cursor, etc.) or CI/CD system

### Integration Points Covered

- ✅ **VS Code** - Catch bugs before you commit
- ✅ **Cursor** - Validate AI suggestions automatically
- ✅ **GitHub Actions** - Block bad code from merging
- ✅ **Pre-commit Hooks** - Check code locally before pushing
- ✅ **AI Assistants** - Find edge cases AI might miss

---

## Example 1: VS Code Integration - Caught Async Bug Before Commit

### The Problem

A developer was refactoring a legacy Django view to use async/await. The code looked correct but had a subtle async bug that would cause race conditions in production.

**Original Code**:

```python
# views.py - Legacy Django view being modernized
def process_payment(request):
    user = get_user(request.user_id)
    payment = create_payment(user.id, request.amount)
    send_notification(user.email, payment.id)  # ⚠️ Blocking call in async context
    return JsonResponse({"status": "success"})
```

### The Integration

**Setup** (one-time, takes 2 minutes):

1. Install SpecFact CLI: `pip install specfact-cli` or use `uvx specfact-cli@latest`
2. Add a pre-commit hook to check code before commits:

```bash
# .git/hooks/pre-commit
#!/bin/sh
specfact --no-banner enforce stage --preset balanced
```

**What This Does**: Runs SpecFact validation automatically before every commit. If it finds issues, the commit is blocked.

### What SpecFact Caught

```bash
🚫 Contract Violation: Blocking I/O in async context
   File: views.py:45
   Function: process_payment
   Issue: send_notification() is a blocking call
   Severity: HIGH
   Fix: Use async version or move to background task
```

### The Fix

```python
# Fixed code
async def process_payment(request):
    user = await get_user_async(request.user_id)
    payment = await create_payment_async(user.id, request.amount)
    await send_notification_async(user.email, payment.id)  # ✅ Async call
    return JsonResponse({"status": "success"})
```

### Result

- ✅ **Bug caught**: Before commit (local validation)
- ✅ **Time saved**: Prevented production race condition
- ✅ **Integration**: VS Code + pre-commit hook
- ✅ **No platform required**: Pure CLI integration

---

## Example 2: Cursor Integration - Prevented Regression During Refactoring

### The Problem

A developer was using Cursor AI to refactor a legacy data pipeline. The AI assistant suggested changes that looked correct but would have broken a critical edge case.

**Original Code**:

```python
# pipeline.py - Legacy data processing
def process_data(data: list[dict]) -> dict:
    if not data:
        return {"status": "empty", "count": 0}
    
    # Critical: handles None values in data
    filtered = [d for d in data if d is not None and d.get("value") is not None]
    
    if len(filtered) == 0:
        return {"status": "no_valid_data", "count": 0}
    
    return {
        "status": "success",
        "count": len(filtered),
        "total": sum(d["value"] for d in filtered)
    }
```

### The Integration

**Setup** (one-time):

1. Install SpecFact CLI: `pip install specfact-cli`
2. Initialize SpecFact in your project: `specfact init`
3. Use the slash command in Cursor: `/specfact.03-review legacy-api`

**What This Does**: When Cursor suggests code changes, SpecFact checks if they break existing contracts or introduce regressions.

### What SpecFact Caught

The AI suggested removing the `None` check, which would have broken the edge case:

```bash
🚫 Contract Violation: Missing None check
   File: pipeline.py:12
   Function: process_data
   Issue: Suggested code removes None check, breaking edge case
   Severity: HIGH
   Contract: Must handle None values in input data
   Fix: Keep None check or add explicit contract
```

### The Fix

```python
# AI suggestion rejected, kept original with contract
@icontract.require(lambda data: isinstance(data, list))
@icontract.ensure(lambda result: result["count"] >= 0)
def process_data(data: list[dict]) -> dict:
    if not data:
        return {"status": "empty", "count": 0}
    
    # Contract enforces None handling
    filtered = [d for d in data if d is not None and d.get("value") is not None]
    
    if len(filtered) == 0:
        return {"status": "no_valid_data", "count": 0}
    
    return {
        "status": "success",
        "count": len(filtered),
        "total": sum(d["value"] for d in filtered)
    }
```

### Result

- ✅ **Regression prevented**: Edge case preserved
- ✅ **AI validation**: Cursor suggestions validated before acceptance
- ✅ **Integration**: Cursor + SpecFact CLI
- ✅ **Contract enforcement**: Runtime guarantees maintained

---

## Example 3: GitHub Actions Integration - Blocked Merge with Type Error

### The Problem

A developer submitted a PR that added a new feature but introduced a type mismatch that would cause runtime errors.

**PR Code**:

```python
# api.py - New endpoint added
def get_user_stats(user_id: str) -> dict:
    user = User.objects.get(id=user_id)
    stats = calculate_stats(user)  # Returns int, not dict
    return stats  # ⚠️ Type mismatch: int vs dict
```

### The Integration

**Setup** (add to your GitHub repository):

Create `.github/workflows/specfact-enforce.yml`:

```yaml
name: SpecFact Validation

on:
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
      - name: Install SpecFact CLI
        run: pip install specfact-cli
      - name: Configure Enforcement
        run: specfact --no-banner enforce stage --preset balanced
      - name: Run SpecFact Validation
        run: specfact --no-banner repro --repo . --budget 90
```

**What This Does**:

1. **Configure Enforcement**: Sets enforcement mode to `balanced` (blocks HIGH severity violations, warns on MEDIUM)
2. **Run Validation**: Executes `specfact repro` which runs validation checks:

   **Always runs**:
   - Linting (ruff) - checks code style and common Python issues
   - Type checking (basedpyright) - validates type annotations and type safety

   **Conditionally runs** (only if present):
   - Contract exploration (CrossHair) - if `src/` directory exists (symbolic execution to find counterexamples)
   - Async patterns (semgrep) - if `tools/semgrep/async.yml` exists (requires semgrep installed)
   - Property tests (pytest) - if `tests/contracts/` directory exists
   - Smoke tests (pytest) - if `tests/smoke/` directory exists

   **Note**: `repro` does not perform runtime contract validation (checking `@icontract` decorators at runtime). It runs static analysis tools (linting, type checking) and symbolic execution (CrossHair) for contract exploration.

**Expected Output**:

```text
Running validation suite...
Repository: .
Time budget: 90s

⠙ Running validation checks...

Validation Results

                              Check Summary                              
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Check                            ┃ Tool         ┃ Status   ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ Linting (ruff)                   │ ruff         │ ✗ FAILED │ 0.03s    │
│ Type checking (basedpyright)     │ basedpyright │ ✗ FAILED │ 1.12s    │
│ Contract exploration (CrossHair) │ crosshair    │ ✗ FAILED │ 0.58s    │
└──────────────────────────────────┴──────────────┴──────────┴──────────┘

Summary:
  Total checks: 3
  Passed: 0
  Failed: 3
  Total duration: 1.73s

Report written to: .specfact/projects/<bundle-name>/reports/enforcement/report-<timestamp>.yaml

✗ Some validations failed
```

If SpecFact finds violations that trigger enforcement rules, the workflow fails (exit code 1) and the PR is blocked from merging.

### What SpecFact Caught

```bash
🚫 Contract Violation: Return type mismatch
   File: api.py:45
   Function: get_user_stats
   Issue: Function returns int, but contract requires dict
   Severity: HIGH
   Contract: @ensure(lambda result: isinstance(result, dict))
   Fix: Return dict with stats, not raw int
```

### The Fix

```python
# Fixed code
@icontract.ensure(lambda result: isinstance(result, dict))
def get_user_stats(user_id: str) -> dict:
    user = User.objects.get(id=user_id)
    stats_value = calculate_stats(user)
    return {"stats": stats_value}  # ✅ Returns dict
```

### Result

- ✅ **Merge blocked**: PR failed CI check
- ✅ **Type safety**: Runtime type error prevented
- ✅ **Integration**: GitHub Actions + SpecFact CLI
- ✅ **Automated**: No manual review needed

---

## Example 4: Pre-commit Hook - Caught Undocumented Breaking Change

### The Problem

A developer modified a legacy function's signature without updating callers, breaking backward compatibility.

**Modified Code**:

```python
# legacy.py - Function signature changed
def process_order(order_id: str, user_id: str) -> dict:  # ⚠️ Added required user_id
    # ... implementation
```

**Caller Code** (not updated):

```python
# caller.py - Still using old signature
result = process_order(order_id="123")  # ⚠️ Missing user_id
```

### The Integration

**Setup** (one-time):

1. Configure enforcement: `specfact --no-banner enforce stage --preset balanced`
2. Add pre-commit hook:

```bash
# .git/hooks/pre-commit
#!/bin/sh
# Import current code to create a new plan for comparison
# Use bundle name "auto-derived" so plan compare --code-vs-plan can find it
specfact --no-banner import from-code auto-derived --repo . --output-format yaml > /dev/null 2>&1

# Compare: uses active plan (set via plan select) as manual, latest auto-derived plan as auto
specfact --no-banner plan compare --code-vs-plan
```

**What This Does**: Before you commit, SpecFact imports your current code to create a new plan, then compares it against the baseline plan. If it detects breaking changes with HIGH severity, the commit is blocked (based on enforcement configuration).

### What SpecFact Caught

```bash
🚫 Contract Violation: Breaking change detected
   File: legacy.py:12
   Function: process_order
   Issue: Signature changed from (order_id) to (order_id, user_id)
   Severity: HIGH
   Impact: 3 callers will break
   Fix: Make user_id optional or update all callers
```

### The Fix

```python
# Fixed: Made user_id optional to maintain backward compatibility
def process_order(order_id: str, user_id: str | None = None) -> dict:
    if user_id is None:
        # Legacy behavior
        user_id = get_default_user_id()
    # ... implementation
```

### Result

- ✅ **Breaking change caught**: Before commit
- ✅ **Backward compatibility**: Maintained
- ✅ **Integration**: Pre-commit hook + SpecFact CLI
- ✅ **Local validation**: No CI delay

---

## Example 5: Agentic Workflow - CrossHair Found Edge Case

### The Problem

A developer was using an AI coding assistant to add input validation. The code looked correct but had an edge case that would cause division by zero.

**AI-Generated Code**:

```python
# validator.py - AI-generated validation
def validate_and_calculate(data: dict) -> float:
    value = data.get("value", 0)
    divisor = data.get("divisor", 1)
    return value / divisor  # ⚠️ Edge case: divisor could be 0
```

### The Integration

**Setup** (when using AI assistants):

1. Install SpecFact CLI: `pip install specfact-cli`
2. Use the slash command in your AI assistant: `/specfact-contract-test-exploration`

**What This Does**: Uses mathematical proof (not guessing) to find edge cases that AI might miss, like division by zero or None handling issues.

### What SpecFact Caught

**CrossHair Symbolic Execution** discovered the edge case:

```bash
🔍 CrossHair Exploration: Found counterexample
   File: validator.py:5
   Function: validate_and_calculate
   Issue: Division by zero when divisor=0
   Counterexample: {"value": 10, "divisor": 0}
   Severity: HIGH
   Fix: Add divisor != 0 check
```

### The Fix

```python
# Fixed with contract
@icontract.require(lambda data: data.get("divisor", 1) != 0)
def validate_and_calculate(data: dict) -> float:
    value = data.get("value", 0)
    divisor = data.get("divisor", 1)
    return value / divisor  # ✅ Contract ensures divisor != 0
```

### Result

- ✅ **Edge case found**: Mathematical proof, not LLM guess
- ✅ **Symbolic execution**: CrossHair discovered counterexample
- ✅ **Integration**: Agentic workflow + SpecFact CLI
- ✅ **Formal verification**: Deterministic, not probabilistic

---

## Integration Patterns

### Pattern 1: Pre-commit Validation

**Best For**: Catching issues before they enter the repository

**Setup**:

```bash
# .git/hooks/pre-commit
#!/bin/sh
specfact --no-banner enforce stage --preset balanced
```

**Benefits**:

- ✅ Fast feedback (runs locally)
- ✅ Prevents bad commits
- ✅ Works with any IDE or editor

### Pattern 2: CI/CD Integration

**Best For**: Automated validation in pull requests

**Setup** (GitHub Actions example):

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.11"
    cache: "pip"
- name: Install SpecFact CLI
  run: pip install specfact-cli
- name: Configure Enforcement
  run: specfact --no-banner enforce stage --preset balanced
- name: Run SpecFact Validation
  run: specfact --no-banner repro --repo . --budget 90
```

**Benefits**:

- ✅ Blocks merges automatically
- ✅ Same checks for everyone on the team
- ✅ No manual code review needed for these issues

### Pattern 3: IDE Integration

**Best For**: Real-time validation while coding

**Setup** (VS Code example):

```json
// .vscode/tasks.json
{
  "label": "SpecFact Validate",
  "type": "shell",
  "command": "specfact --no-banner enforce stage --preset balanced"
}
```

**Benefits**:

- ✅ Immediate feedback as you code
- ✅ Works with any editor (VS Code, Cursor, etc.)
- ✅ No special extension needed

### Pattern 4: AI Assistant Integration

**Best For**: Validating AI-generated code suggestions

**Setup**:

1. Install SpecFact: `pip install specfact-cli`
2. Initialize: `specfact init` (creates slash commands for your IDE)
3. Use slash commands like `/specfact.03-review legacy-api` in Cursor or GitHub Copilot

**Benefits**:

- ✅ Catches bugs in AI suggestions
- ✅ Prevents AI from making mistakes
- ✅ Uses formal proof, not guessing

---

## Key Takeaways

### ✅ What Makes These Integrations Work

1. **CLI-First Design**: Works with any tool, no platform lock-in
2. **Standard Exit Codes**: Integrates with any CI/CD system
3. **Fast Execution**: < 10 seconds for most validations
4. **Formal Guarantees**: Runtime contracts + symbolic execution
5. **Zero Configuration**: Works out of the box

### ✅ Bugs Caught That Other Tools Missed

- **Async bugs**: Blocking calls in async context
- **Type mismatches**: Runtime type errors
- **Breaking changes**: Backward compatibility issues
- **Edge cases**: Division by zero, None handling
- **Contract violations**: Missing preconditions/postconditions

### ✅ Integration Benefits

- **VS Code**: Pre-commit validation, no extension needed
- **Cursor**: AI suggestion validation
- **GitHub Actions**: Automated merge blocking
- **Pre-commit**: Local validation before commits
- **Agentic Workflows**: Formal verification of AI code

---

## Next Steps

1. **Try an Integration**: Pick your IDE/CI and add SpecFact validation
2. **Share Your Example**: Document bugs you catch via integrations
3. **Contribute**: Add integration examples to this document

---

## Related Documentation

- **[Getting Started](../getting-started/README.md)** - Installation and setup
- **[IDE Integration](../guides/ide-integration.md)** - Set up integrations
- **[Use Cases](../guides/use-cases.md)** - More real-world scenarios
- **[Dogfooding Example](dogfooding-specfact-cli.md)** - SpecFact analyzing itself

---

**Remember**: SpecFact CLI's core USP is **seamless integration** into your existing workflow. These examples show how different integrations caught real bugs that other tools missed. Start with one integration, then expand as you see value.
