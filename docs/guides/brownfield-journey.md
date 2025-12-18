---
layout: default
title: Brownfield Modernization Journey
permalink: /brownfield-journey/
---

# Brownfield Modernization Journey

> **Complete step-by-step workflow for modernizing legacy Python code with SpecFact CLI**

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow. Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE. No platform to learn, no vendor lock-in.

---

## Overview

This guide walks you through the complete brownfield modernization journey:

1. **Understand** - Extract specs from legacy code
2. **Protect** - Add contracts to critical paths
3. **Discover** - Find hidden edge cases
4. **Modernize** - Refactor safely with contract safety net
5. **Validate** - Verify modernization success

**Time investment:** 26-44 hours (vs. 220-350 hours manual)  
**ROI:** 87% time saved, $26,000-$45,000 cost avoided

---

## Phase 1: Understand Your Legacy Code

### Step 1.1: Extract Specs Automatically

**CLI-First Integration**: Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE. See [Integration Showcases](../examples/integration-showcases/) for real examples.

```bash
# Analyze your legacy codebase
specfact import from-code --bundle legacy-api --repo ./legacy-app
```

**What happens:**

- SpecFact analyzes all Python files
- Extracts features, user stories, and business logic
- Generates dependency graphs
- Creates plan bundle with extracted specs

**Output:**

```text
✅ Analyzed 47 Python files
✅ Extracted 23 features
✅ Generated 112 user stories
⏱️  Completed in 8.2 seconds
```

**Time saved:** 60-120 hours of manual documentation → **8 seconds**

**💡 Tip**: After importing, the CLI may suggest generating a bootstrap constitution for Spec-Kit integration. This auto-generates a constitution from your repository analysis:

```bash
# If suggested, accept to auto-generate
# Or run manually:
specfact constitution bootstrap --repo .
```

This is especially useful if you plan to sync with Spec-Kit later.

### Step 1.2: Review Extracted Specs

```bash
# Review the extracted plan using CLI commands
specfact plan review --bundle legacy-api
```

**What to look for:**

- High-confidence features (95%+) - These are well-understood
- Low-confidence features (<70%) - These need manual review
- Missing features - May indicate incomplete extraction
- Edge cases - Already discovered by CrossHair

### Step 1.3: Validate Extraction Quality

```bash
# Compare extracted plan to your understanding (bundle directory paths)
specfact plan compare \
  --manual .specfact/projects/manual-plan \
  --auto .specfact/projects/your-project
```

**What you get:**

- Deviations between manual and auto-derived plans
- Missing features in extraction
- Extra features in extraction (may be undocumented functionality)

---

## Phase 2: Protect Critical Paths

### Step 2.1: Identify Critical Functions

**Criteria for "critical":**

- High business value (payment, authentication, data processing)
- High risk (production bugs would be costly)
- Complex logic (hard to understand, easy to break)
- Frequently called (high impact if broken)

**Review extracted plan:**

```bash
# Review plan using CLI commands
specfact plan review --bundle legacy-api
```

### Step 2.2: Add Contracts Incrementally

#### Week 1: Start with 3-5 critical functions

```python
# Example: Add contracts to payment processing
import icontract

@icontract.require(lambda amount: amount > 0, "Amount must be positive")
@icontract.require(lambda currency: currency in ['USD', 'EUR', 'GBP'])
@icontract.ensure(lambda result: result.status in ['SUCCESS', 'FAILED'])
def process_payment(user_id, amount, currency):
    # Legacy code with contracts
    ...
```

#### Week 2: Expand to 10-15 functions

#### Week 3: Add contracts to all public APIs

#### Week 4+: Add contracts to internal functions as needed

### Step 2.3: Start in Shadow Mode

**Shadow mode** observes violations without blocking:

```bash
# Run in shadow mode (observe only)
specfact enforce --mode shadow
```

**Benefits:**

- See violations without breaking workflow
- Understand contract behavior before enforcing
- Build confidence gradually

**Graduation path:**

1. **Shadow mode** (Week 1) - Observe only
2. **Warn mode** (Week 2) - Log violations, don't block
3. **Block mode** (Week 3+) - Raise exceptions on violations

---

## Phase 3: Discover Hidden Edge Cases

### Step 3.1: Run CrossHair on Critical Functions

```bash
# Discover edge cases in payment processing
hatch run contract-explore src/payment.py
```

**What CrossHair does:**

- Explores all possible code paths symbolically
- Finds inputs that violate contracts
- Generates concrete test cases for violations

**Example output:**

```text
❌ Postcondition violation found:
   Function: process_payment
   Input: amount=0.0, currency='USD'
   Issue: Amount must be positive (got 0.0)

```

### Step 3.2: Fix Discovered Edge Cases

```python
# Add validation for edge cases
@icontract.require(
    lambda amount: amount > 0 and amount <= 1000000,
    "Amount must be between 0 and 1,000,000"
)
def process_payment(...):
    # Now handles edge cases discovered by CrossHair
    ...
```

### Step 3.3: Document Edge Cases

**Keep notes on:**

- Edge cases discovered
- Contract violations found
- Fixes applied
- Test cases generated

**Why this matters:**

- Prevents regressions in future refactoring
- Documents hidden business rules
- Helps new team members understand code

---

## Phase 4: Modernize Safely

### Step 4.1: Refactor Incrementally

**One function at a time:**

1. Add contracts to function (if not already done)
2. Run CrossHair to discover edge cases
3. Refactor function implementation
4. Verify contracts still pass
5. Move to next function

**Example:**

```python
# Before: Legacy implementation
@icontract.require(lambda amount: amount > 0)
def process_payment(user_id, amount, currency):
    # 80 lines of legacy code
    ...

# After: Modernized implementation (same contracts)
@icontract.require(lambda amount: amount > 0)
def process_payment(user_id, amount, currency):
    # Modernized code (same contracts protect behavior)
    payment_service = PaymentService()
    return payment_service.process(user_id, amount, currency)
```

### Step 4.2: Catch Regressions Automatically

**Contracts catch violations during refactoring:**

```python
# During modernization, accidentally break contract:
process_payment(user_id=-1, amount=-50, currency="XYZ")

# Runtime enforcement catches it:
# ❌ ContractViolation: Amount must be positive (got -50)
#    → Fix the bug before it reaches production!

```

### Step 4.3: Verify Modernization Success

```bash
# Run contract validation
hatch run contract-test-full

# Check for violations
specfact enforce --mode block
```

**Success criteria:**

- ✅ All contracts pass
- ✅ No new violations introduced
- ✅ Edge cases still handled
- ✅ Performance acceptable

---

## Phase 5: Validate and Measure

### Step 5.1: Measure ROI

**Track metrics:**

- Time saved on documentation
- Bugs prevented during modernization
- Edge cases discovered
- Developer onboarding time reduction

**Example metrics:**

- Documentation: 87% time saved (8 hours vs. 60 hours)
- Bugs prevented: 4 production bugs
- Edge cases: 6 discovered automatically
- Onboarding: 60% faster (3-5 days vs. 2-3 weeks)

### Step 5.2: Document Success

**Create case study:**

- Problem statement
- Solution approach
- Quantified results
- Lessons learned

**Why this matters:**

- Validates approach for future projects
- Helps other teams learn from your experience
- Builds confidence in brownfield modernization

---

## Real-World Example: Complete Journey

### The Problem

Legacy Django app:

- 47 Python files
- No documentation
- No type hints
- No tests
- 15 undocumented API endpoints

### The Journey

#### Week 1: Understand

- Ran `specfact import from-code --bundle legacy-api --repo .` → 23 features extracted in 8 seconds
- Reviewed extracted plan → Identified 5 critical features
- Time: 2 hours (vs. 60 hours manual)

#### Week 2: Protect

- Added contracts to 5 critical functions
- Started in shadow mode → Observed 3 violations
- Time: 16 hours

#### Week 3: Discover

- Ran CrossHair on critical functions → Discovered 6 edge cases
- Fixed edge cases → Added validation
- Time: 4 hours

#### Week 4: Modernize

- Refactored 5 critical functions with contract safety net
- Caught 4 regressions automatically (contracts prevented bugs)
- Time: 24 hours

#### Week 5: Validate

- All contracts passing
- No production bugs from modernization
- New developers productive in 3 days (vs. 2-3 weeks)

### The Results

- ✅ **87% time saved** on documentation (8 hours vs. 60 hours)
- ✅ **4 production bugs prevented** during modernization
- ✅ **6 edge cases discovered** automatically
- ✅ **60% faster onboarding** (3-5 days vs. 2-3 weeks)
- ✅ **Zero downtime** modernization

**ROI:** $42,000 saved, 5-week acceleration

---

## Best Practices

### 1. Start Small

- Don't try to contract everything at once
- Start with 3-5 critical functions
- Expand incrementally

### 2. Use Shadow Mode First

- Observe violations before enforcing
- Build confidence gradually
- Graduate to warn → block mode

### 3. Run CrossHair Early

- Discover edge cases before refactoring
- Fix issues proactively
- Document findings

### 4. Refactor Incrementally

- One function at a time
- Verify contracts after each refactor
- Don't rush

### 5. Document Everything

- Edge cases discovered
- Contract violations found
- Fixes applied
- Lessons learned

---

## Common Pitfalls

### ❌ Trying to Contract Everything at Once

**Problem:** Overwhelming, slows down development

**Solution:** Start with 3-5 critical functions, expand incrementally

### ❌ Skipping Shadow Mode

**Problem:** Too many violations, breaks workflow

**Solution:** Always start in shadow mode, graduate gradually

### ❌ Ignoring CrossHair Findings

**Problem:** Edge cases discovered but not fixed

**Solution:** Fix edge cases before refactoring

### ❌ Refactoring Too Aggressively

**Problem:** Breaking changes, contract violations

**Solution:** Refactor incrementally, verify contracts after each change

---

## Next Steps

1. **[Integration Showcases](../examples/integration-showcases/)** - See real bugs fixed via VS Code, Cursor, GitHub Actions integrations
2. **[Brownfield Engineer Guide](brownfield-engineer.md)** - Complete persona guide
3. **[ROI Calculator](brownfield-roi.md)** - Calculate your savings
4. **[Examples](../examples/)** - Real-world brownfield examples
5. **[FAQ](brownfield-faq.md)** - More brownfield questions

---

## Support

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 [hello@noldai.com](mailto:hello@noldai.com)

---

**Happy modernizing!** 🚀
