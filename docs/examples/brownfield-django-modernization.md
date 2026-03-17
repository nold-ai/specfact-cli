# Brownfield Example: Modernizing Legacy Django Code

> **Complete walkthrough: From undocumented legacy Django app to contract-enforced modern codebase**

---

## The Problem

You inherited a 3-year-old Django app with:

- ❌ No documentation
- ❌ No type hints
- ❌ No tests
- ❌ 15 undocumented API endpoints
- ❌ Business logic buried in views
- ❌ Original developers have left

**Sound familiar?** This is a common brownfield scenario.

---

## Step 1: Reverse Engineer with SpecFact

> **Note**: This example demonstrates the complete hard-SDD workflow, including SDD manifest creation, validation, and plan promotion gates. The SDD manifest serves as your "hard spec" - a canonical reference that prevents drift during modernization.

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow. Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE.

### Extract Specs from Legacy Code

```bash
# Analyze the legacy Django app
specfact code import customer-portal \
  --repo ./legacy-django-app \
  --language python

```

### Output

```text
✅ Analyzed 47 Python files
✅ Extracted 23 features:

   - FEATURE-001: User Authentication (95% confidence)
     - Stories: Login, Logout, Password Reset, Session Management
   - FEATURE-002: Payment Processing (92% confidence)
     - Stories: Process Payment, Refund, Payment History
   - FEATURE-003: Order Management (88% confidence)
     - Stories: Create Order, Update Order, Cancel Order
   ...
✅ Generated 112 user stories from existing code patterns
✅ Dependency graph: 8 modules, 23 dependencies
⏱️  Completed in 8.2 seconds
```

### What You Get

**Auto-generated project bundle** (`.specfact/projects/customer-portal/` - modular structure):

```yaml
features:

  - key: FEATURE-002
    name: Payment Processing
    description: Process payments for customer orders
    stories:

      - key: STORY-002-001
        title: Process payment for order
        description: Process payment with amount and currency
        acceptance_criteria:

          - Amount must be positive decimal
          - Supported currencies: USD, EUR, GBP
          - Returns SUCCESS or FAILED status
```

**Time saved:** 60-120 hours of manual documentation → **8 seconds**

---

## Step 2: Create Hard SDD Manifest

After extracting the plan, create a hard SDD (Spec-Driven Development) manifest that captures WHY, WHAT, and HOW:

```bash
# Create SDD manifest from the extracted plan
specfact govern enforce sdd customer-portal
```

### Output

```text
✅ SDD manifest created: .specfact/projects/<bundle-name>/sdd.yaml

📋 SDD Summary:
   WHY: Modernize legacy Django customer portal with zero downtime
   WHAT: 23 features, 112 stories extracted from legacy code
   HOW: Runtime contracts, symbolic execution, incremental enforcement

🔗 Linked to plan: customer-portal (hash: abc123def456...)
📊 Coverage thresholds:
   - Contracts per story: 1.0 (minimum)
   - Invariants per feature: 2.0 (minimum)
   - Architecture facets: 3 (minimum)

✅ SDD manifest saved to .specfact/projects/<bundle-name>/sdd.yaml
```

### What You Get

**SDD manifest** (`.specfact/projects/<bundle-name>/sdd.yaml`, Phase 8.5) captures:

- **WHY**: Intent, constraints, target users, value hypothesis
- **WHAT**: Capabilities, acceptance criteria, out-of-scope items
- **HOW**: Architecture, invariants, contracts, module boundaries
- **Coverage thresholds**: Minimum contracts/story, invariants/feature, architecture facets
- **Plan linkage**: Hash-linked to plan bundle for drift detection

**Why this matters**: The SDD manifest serves as your "hard spec" - a canonical reference that prevents drift between your plan and implementation during modernization.

---

## Step 3: Validate SDD Before Modernization

Before starting modernization, validate that your SDD manifest matches your plan:

```bash
# Validate SDD manifest against plan
specfact govern enforce sdd customer-portal
```

### Output

```text
✅ Loading SDD manifest: .specfact/projects/customer-portal/sdd.yaml
✅ Loading project bundle: .specfact/projects/customer-portal/

🔍 Validating hash match...
✅ Hash match verified

🔍 Validating coverage thresholds...
✅ Contracts/story: 1.2 (threshold: 1.0) ✓
✅ Invariants/feature: 2.5 (threshold: 2.0) ✓
✅ Architecture facets: 4 (threshold: 3) ✓

✅ SDD validation passed
📄 Report saved to: .specfact/projects/<bundle-name>/reports/enforcement/report-2025-01-23T10-30-45.yaml
```

**If validation fails**, you'll see specific deviations:

```text
❌ SDD validation failed

🔍 Validating coverage thresholds...
⚠️  Contracts/story: 0.8 (threshold: 1.0) - Below threshold
⚠️  Invariants/feature: 1.5 (threshold: 2.0) - Below threshold

📊 Validation report:
   - 2 medium severity deviations
   - Fix: Add contracts to stories or adjust thresholds

💡 Run 'specfact govern enforce sdd <bundle>' to enforce SDD
```

---

## Step 4: Review Plan with SDD Validation

Review your plan to identify ambiguities and ensure SDD compliance:

```bash
# Review plan (automatically checks SDD, bundle name as positional argument)
specfact project devops-flow --stage develop --bundle customer-portal
```

### Output

```text
📋 SpecFact CLI - DevOps Flow (develop stage)

✅ Loading project bundle: .specfact/projects/customer-portal/
✅ Current stage: draft

🔍 Checking SDD manifest...
✅ SDD manifest validated successfully
ℹ️  Found 2 coverage threshold warning(s)

❓ Questions to resolve ambiguities:
   1. Q001: What is the expected response time for payment processing?
   2. Q002: Should password reset emails expire after 24 or 48 hours?
   ...

✅ Review complete: 5 questions identified
```

**SDD integration**: The devops-flow develop stage automatically checks for SDD presence and validates coverage thresholds, warning you if thresholds aren't met.

---

## Step 5: Promote Plan with SDD Validation

Before starting modernization, promote your plan to "review" stage. This requires a valid SDD manifest:

```bash
# Promote plan to review stage (requires SDD, bundle name as positional argument)
specfact project devops-flow --stage review --bundle customer-portal
```

### Output (Success)

```text
📋 SpecFact CLI - DevOps Flow (review stage)

✅ Loading project bundle: .specfact/projects/customer-portal/
✅ Current stage: draft
✅ Target stage: review

🔍 Checking promotion rules...
🔍 Checking SDD manifest...
✅ SDD manifest validated successfully
ℹ️  Found 2 coverage threshold warning(s)

✅ Promoted plan to stage: review
💡 Plan is now ready for modernization work
```

### Output (SDD Missing)

```text
❌ SDD manifest is required for promotion to 'review' or higher stages
💡 Run 'specfact govern enforce sdd <bundle>' to enforce SDD
```

**Why this matters**: Plan promotion now enforces SDD presence, ensuring you have a hard spec before starting modernization work. This prevents drift and ensures coverage thresholds are met.

---

## Step 6: Add Contracts to Critical Paths

### Identify Critical Functions

Review the extracted plan to identify high-risk functions:

```bash
# Review extracted plan using CLI commands
specfact project health-check

```

### Before: Undocumented Legacy Function

```python
# views/payment.py (legacy code)
def process_payment(request, order_id):
    """Process payment for order"""
    order = Order.objects.get(id=order_id)
    amount = float(request.POST.get('amount'))
    currency = request.POST.get('currency')
    
    # 80 lines of legacy payment logic
    # Hidden business rules:
    # - Amount must be positive
    # - Currency must be USD, EUR, or GBP
    # - Returns PaymentResult with status
    ...
    
    return PaymentResult(status='SUCCESS')

```

### After: Contract-Enforced Function

```python
# views/payment.py (modernized with contracts)
import icontract
from typing import Literal

@icontract.require(
    lambda amount: amount > 0,
    "Payment amount must be positive"
)
@icontract.require(
    lambda currency: currency in ['USD', 'EUR', 'GBP'],
    "Currency must be USD, EUR, or GBP"
)
@icontract.ensure(
    lambda result: result.status in ['SUCCESS', 'FAILED'],
    "Payment result must have valid status"
)
def process_payment(
    request,
    order_id: int,
    amount: float,
    currency: Literal['USD', 'EUR', 'GBP']
) -> PaymentResult:
    """Process payment for order with runtime contract enforcement"""
    order = Order.objects.get(id=order_id)
    
    # Same 80 lines of legacy payment logic
    # Now with runtime enforcement
    
    return PaymentResult(status='SUCCESS')
```

**What this gives you:**

- ✅ Runtime validation catches invalid inputs immediately
- ✅ Prevents regressions during refactoring
- ✅ Documents expected behavior (executable documentation)
- ✅ CrossHair discovers edge cases automatically

### Re-validate SDD After Adding Contracts

After adding contracts, re-validate your SDD to ensure coverage thresholds are met:

```bash
# Re-validate SDD after adding contracts
specfact govern enforce sdd customer-portal
```

This ensures your SDD manifest reflects the current state of your codebase and that coverage thresholds are maintained.

---

## Step 7: Discover Hidden Edge Cases

### Run CrossHair Symbolic Execution

```bash
# Discover edge cases in payment processing
hatch run contract-explore views/payment.py

```

### CrossHair Output

```text
🔍 Exploring contracts in views/payment.py...

❌ Postcondition violation found:
   Function: process_payment
   Input: amount=0.0, currency='USD'
   Issue: Amount must be positive (got 0.0)
   
❌ Postcondition violation found:
   Function: process_payment
   Input: amount=-50.0, currency='USD'
   Issue: Amount must be positive (got -50.0)
   
✅ Contract exploration complete
   - 2 violations found
   - 0 false positives
   - Time: 12.3 seconds

```

### Fix Edge Cases

```python
# Add validation for edge cases discovered by CrossHair
@icontract.require(
    lambda amount: amount > 0 and amount <= 1000000,
    "Payment amount must be between 0 and 1,000,000"
)
def process_payment(...):
    # Now handles edge cases discovered by CrossHair
    ...
```

---

## Step 8: Prevent Regressions During Modernization

### Refactor Safely

With contracts in place, refactor knowing violations will be caught:

```python
# Refactored version (same contracts)
@icontract.require(lambda amount: amount > 0, "Payment amount must be positive")
@icontract.require(lambda currency: currency in ['USD', 'EUR', 'GBP'])
@icontract.ensure(lambda result: result.status in ['SUCCESS', 'FAILED'])
def process_payment(request, order_id: int, amount: float, currency: str) -> PaymentResult:
    """Modernized payment processing with contract safety net"""
    
    # Modernized implementation
    order = get_order_or_404(order_id)
    payment_service = PaymentService()
    
    try:
        result = payment_service.process(
            order=order,
            amount=amount,
            currency=currency
        )
        return PaymentResult(status='SUCCESS', transaction_id=result.id)
    except PaymentError as e:
        return PaymentResult(status='FAILED', error=str(e))

```

### Catch Regressions Automatically

```python
# During modernization, accidentally break contract:
process_payment(request, order_id=-1, amount=-50, currency="XYZ")

# Runtime enforcement catches it:
# ❌ ContractViolation: Payment amount must be positive (got -50)
#    at process_payment() call from refactored checkout.py:142
#    → Prevented production bug during modernization!
```

---

## Results

### Quantified Outcomes

| Metric | Before SpecFact | After SpecFact | Improvement |
|--------|----------------|----------------|-------------|
| **Documentation time** | 60-120 hours | 8 seconds | **99.9% faster** |
| **Production bugs prevented** | 0 (no safety net) | 4 bugs | **∞ improvement** |
| **Developer onboarding** | 2-3 weeks | 3-5 days | **60% faster** |
| **Edge cases discovered** | 0-2 (manual) | 6 (CrossHair) | **3x more** |
| **Refactoring confidence** | Low (fear of breaking) | High (contracts catch violations) | **Qualitative improvement** |

### Time and Cost Savings

**Manual approach:**

- Documentation: 80-120 hours ($12,000-$18,000)
- Testing: 100-150 hours ($15,000-$22,500)
- Debugging regressions: 40-80 hours ($6,000-$12,000)
- **Total: 220-350 hours ($33,000-$52,500)**

**SpecFact approach:**

- code2spec extraction: 10 minutes ($25)
- Review and refine specs: 8-16 hours ($1,200-$2,400)
- Add contracts: 16-24 hours ($2,400-$3,600)
- CrossHair edge case discovery: 2-4 hours ($300-$600)
- **Total: 26-44 hours ($3,925-$6,625)**

**ROI: 87% time saved, $26,000-$45,000 cost avoided**

---

## Integration with Your Workflow

SpecFact CLI integrates seamlessly with your existing tools:

- **VS Code**: Use pre-commit hooks to catch breaking changes before commit
- **Cursor**: AI assistant workflows catch regressions during refactoring
- **GitHub Actions**: CI/CD integration blocks bad code from merging
- **Pre-commit hooks**: Local validation prevents breaking changes
- **Any IDE**: Pure CLI-first approach—works with any editor

**See real examples**: [Integration Showcases](integration-showcases/) - 5 complete examples showing bugs fixed via integrations

## Key Takeaways

### What Worked Well

1. ✅ **code2spec extraction** provided immediate value (< 10 seconds)
2. ✅ **SDD manifest** created hard spec reference, preventing drift during modernization
3. ✅ **SDD validation** ensured coverage thresholds before starting work
4. ✅ **Plan promotion gates** required SDD presence, enforcing discipline
5. ✅ **Runtime contracts** prevented 4 production bugs during refactoring
6. ✅ **CrossHair** discovered 6 edge cases manual testing missed
7. ✅ **Incremental approach** (shadow → warn → block) reduced risk
8. ✅ **CLI-first integration** - Works offline, no account required, no vendor lock-in

### Lessons Learned

1. **Start with critical paths** - Don't try to contract everything at once
2. **Use shadow mode first** - Observe violations before enforcing
3. **Run CrossHair early** - Discover edge cases before refactoring
4. **Document findings** - Keep notes on violations and edge cases

---

## Next Steps

1. **[Integration Showcases](integration-showcases/)** - See real bugs fixed via VS Code, Cursor, GitHub Actions integrations
2. **[Brownfield Engineer Guide](../guides/brownfield-engineer.md)** - Complete modernization workflow
3. **[ROI Calculator](../guides/brownfield-roi.md)** - Calculate your savings
4. **[Flask API Example](brownfield-flask-api.md)** - Another brownfield scenario
5. **[Data Pipeline Example](brownfield-data-pipeline.md)** - ETL modernization

---

**Questions?** [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions) | [hello@noldai.com](mailto:hello@noldai.com)
