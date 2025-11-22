# Guide for Legacy Modernization Engineers

> **Complete walkthrough for modernizing legacy Python code with SpecFact CLI**

---

## Your Challenge

You're responsible for modernizing a legacy Python system that:

- Has minimal or no documentation
- Was built by developers who have left
- Contains critical business logic you can't risk breaking
- Needs migration to modern Python, cloud infrastructure, or microservices

**Sound familiar?** You're not alone. 70% of IT budgets are consumed by legacy maintenance, and the legacy modernization market is $25B+ and growing.

---

## SpecFact for Brownfield: Your Safety Net

SpecFact CLI is designed specifically for your situation. It provides:

1. **Automated spec extraction** (code2spec) - Understand what your code does in < 10 seconds
2. **Runtime contract enforcement** - Prevent regressions during modernization
3. **Symbolic execution** - Discover hidden edge cases with CrossHair
4. **Formal guarantees** - Mathematical verification, not probabilistic LLM suggestions
5. **CLI-first integration** - Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE. Works offline, no account required, no vendor lock-in.

---

## Step 1: Understand What You Have

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow. Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE. No platform to learn, no vendor lock-in.

### Extract Specs from Legacy Code

```bash
# Analyze your legacy codebase
specfact import from-code --repo ./legacy-app --name customer-system

# For large codebases or multi-project repos, analyze specific modules:
specfact import from-code --repo ./legacy-app --entry-point src/core --name core-module
specfact import from-code --repo ./legacy-app --entry-point src/api --name api-module
```

**What you get:**

- ✅ Auto-generated feature map of existing functionality
- ✅ Extracted user stories from code patterns
- ✅ Dependency graph showing module relationships
- ✅ Business logic documentation from function signatures
- ✅ Edge cases discovered via symbolic execution

**Example output:**

```text
✅ Analyzed 47 Python files
✅ Extracted 23 features:

   - FEATURE-001: User Authentication (95% confidence)
   - FEATURE-002: Payment Processing (92% confidence)
   - FEATURE-003: Order Management (88% confidence)
   ...
✅ Generated 112 user stories from existing code patterns
✅ Detected 6 edge cases with CrossHair symbolic execution
⏱️  Completed in 8.2 seconds
```

**Time saved:** 60-120 hours of manual documentation work → **8 seconds**

**💡 Partial Repository Coverage:**

For large codebases or monorepos with multiple projects, you can analyze specific subdirectories using `--entry-point`:

```bash
# Analyze only the core module
specfact import from-code --repo . --entry-point src/core --name core-plan

# Analyze only the API service
specfact import from-code --repo . --entry-point projects/api-service --name api-plan
```

This enables:

- **Faster analysis** - Focus on specific modules for quicker feedback
- **Incremental modernization** - Modernize one module at a time
- **Multi-plan support** - Create separate plan bundles for different projects/modules
- **Better organization** - Keep plans organized by project boundaries

**💡 Tip**: After importing, the CLI may suggest generating a bootstrap constitution for Spec-Kit integration. This auto-generates a constitution from your repository analysis:

```bash
# If suggested, accept to auto-generate
# Or run manually:
specfact constitution bootstrap --repo .
```

This is especially useful if you plan to sync with Spec-Kit later.

---

## Step 2: Add Contracts to Critical Paths

### Identify Critical Functions

SpecFact helps you identify which functions are critical (high risk, high business value):

```bash
# Review extracted plan to identify critical paths
cat contracts/plans/plan.bundle.yaml
```

### Add Runtime Contracts

Add contract decorators to critical functions:

```python
# Before: Undocumented legacy function
def process_payment(user_id, amount, currency):
    # 80 lines of legacy code with hidden business rules
    ...

# After: Contract-enforced function
import icontract

@icontract.require(lambda amount: amount > 0, "Payment amount must be positive")
@icontract.require(lambda currency: currency in ['USD', 'EUR', 'GBP'])
@icontract.ensure(lambda result: result.status in ['SUCCESS', 'FAILED'])
def process_payment(user_id, amount, currency):
    # Same 80 lines of legacy code
    # Now with runtime enforcement
    ...
```

**What this gives you:**

- ✅ Runtime validation catches invalid inputs immediately
- ✅ Prevents regressions during refactoring
- ✅ Documents expected behavior (executable documentation)
- ✅ CrossHair discovers edge cases automatically

---

## Step 3: Modernize with Confidence

### Refactor Safely

With contracts in place, you can refactor knowing that violations will be caught:

```python
# Refactored version (same contracts)
@icontract.require(lambda amount: amount > 0, "Payment amount must be positive")
@icontract.require(lambda currency: currency in ['USD', 'EUR', 'GBP'])
@icontract.ensure(lambda result: result.status in ['SUCCESS', 'FAILED'])
def process_payment(user_id, amount, currency):
    # Modernized implementation
    # If contract violated → exception raised immediately
    ...

```

### Catch Regressions Automatically

```python
# During modernization, accidentally break contract:
process_payment(user_id=-1, amount=-50, currency="XYZ")

# Runtime enforcement catches it:
# ❌ ContractViolation: Payment amount must be positive (got -50)
#    at process_payment() call from refactored checkout.py:142
#    → Prevented production bug during modernization!
```

---

## Step 4: Discover Hidden Edge Cases

### CrossHair Symbolic Execution

SpecFact uses CrossHair to discover edge cases that manual testing misses:

```python
# Legacy function with hidden edge case
@icontract.require(lambda numbers: len(numbers) > 0)
@icontract.ensure(lambda numbers, result: len(numbers) == 0 or min(numbers) > result)
def remove_smallest(numbers: List[int]) -> int:
    """Remove and return smallest number from list"""
    smallest = min(numbers)
    numbers.remove(smallest)
    return smallest

# CrossHair finds counterexample:
# Input: [3, 3, 5] → After removal: [3, 5], min=3, returned=3
# ❌ Postcondition violated: min(numbers) > result fails when duplicates exist!
# CrossHair generates concrete failing input: [3, 3, 5]
```

**Why this matters:**

- ✅ Discovers edge cases LLMs miss
- ✅ Mathematical proof of violations (not probabilistic)
- ✅ Generates concrete test inputs automatically
- ✅ Prevents production bugs before they happen

---

## Real-World Example: Django Legacy App

### The Problem

You inherited a 3-year-old Django app with:

- No documentation
- No type hints
- No tests
- 15 undocumented API endpoints
- Business logic buried in views

### The Solution

```bash
# Step 1: Extract specs
specfact import from-code --repo ./legacy-django-app --name customer-portal

# Output:
✅ Analyzed 47 Python files
✅ Extracted 23 features (API endpoints, background jobs, integrations)
✅ Generated 112 user stories from existing code patterns
✅ Time: 8 seconds
```

### The Results

- ✅ Legacy app fully documented in < 10 minutes
- ✅ Prevented 4 production bugs during refactoring
- ✅ New developers onboard 60% faster
- ✅ CrossHair discovered 6 hidden edge cases

---

## ROI: Time and Cost Savings

### Manual Approach

| Task | Time Investment | Cost (@$150/hr) |
|------|----------------|-----------------|
| Manually document 50-file legacy app | 80-120 hours | $12,000-$18,000 |
| Write tests for undocumented code | 100-150 hours | $15,000-$22,500 |
| Debug regression during refactor | 40-80 hours | $6,000-$12,000 |
| **TOTAL** | **220-350 hours** | **$33,000-$52,500** |

### SpecFact Automated Approach

| Task | Time Investment | Cost (@$150/hr) |
|------|----------------|-----------------|
| Run code2spec extraction | 10 minutes | $25 |
| Review and refine extracted specs | 8-16 hours | $1,200-$2,400 |
| Add contracts to critical paths | 16-24 hours | $2,400-$3,600 |
| CrossHair edge case discovery | 2-4 hours | $300-$600 |
| **TOTAL** | **26-44 hours** | **$3,925-$6,625** |

### ROI: **87% time saved, $26,000-$45,000 cost avoided**

---

## Integration with Your Workflow

SpecFact CLI integrates seamlessly with your existing tools:

- **VS Code**: Use pre-commit hooks to catch breaking changes before commit
- **Cursor**: AI assistant workflows catch regressions during refactoring
- **GitHub Actions**: CI/CD integration blocks bad code from merging
- **Pre-commit hooks**: Local validation prevents breaking changes
- **Any IDE**: Pure CLI-first approach—works with any editor

**See real examples**: [Integration Showcases](../examples/integration-showcases/) - 5 complete examples showing bugs fixed via integrations

## Best Practices

### 1. Start with Shadow Mode

Begin in shadow mode to observe without blocking:

```bash
specfact import from-code --repo . --shadow-only
```

### 2. Add Contracts Incrementally

Don't try to contract everything at once:

1. **Week 1**: Add contracts to 3-5 critical functions
2. **Week 2**: Expand to 10-15 functions
3. **Week 3**: Add contracts to all public APIs
4. **Week 4+**: Add contracts to internal functions as needed

### 3. Use CrossHair for Edge Case Discovery

Run CrossHair on critical functions before refactoring:

```bash
hatch run contract-explore src/payment.py
```

### 4. Document Your Findings

Keep notes on:

- Edge cases discovered
- Contract violations caught
- Time saved on documentation
- Bugs prevented during modernization

---

## Common Questions

### Can SpecFact analyze code with no docstrings?

**Yes.** code2spec analyzes:

- Function signatures and type hints
- Code patterns and control flow
- Existing validation logic
- Module dependencies

No docstrings needed.

### What if the legacy code has no type hints?

**SpecFact infers types** from usage patterns and generates specs. You can add type hints incrementally as part of modernization.

### Can SpecFact handle obfuscated or minified code?

**Limited.** SpecFact works best with:

- Source code (not compiled bytecode)
- Readable variable names

For heavily obfuscated code, consider deobfuscation first.

### Will contracts slow down my code?

**Minimal impact.** Contract checks are fast (microseconds per call). For high-performance code, you can disable contracts in production while keeping them in tests.

---

## Next Steps

1. **[Integration Showcases](../examples/integration-showcases/)** - See real bugs fixed via VS Code, Cursor, GitHub Actions integrations
2. **[ROI Calculator](brownfield-roi.md)** - Calculate your time and cost savings
3. **[Brownfield Journey](brownfield-journey.md)** - Complete modernization workflow
4. **[Examples](../examples/)** - Real-world brownfield examples
5. **[FAQ](../brownfield-faq.md)** - More brownfield-specific questions

---

## Support

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 [hello@noldai.com](mailto:hello@noldai.com)

---

**Happy modernizing!** 🚀
