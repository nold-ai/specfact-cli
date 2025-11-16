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

### Extract Specs from Legacy Code

```bash
# Analyze the legacy Django app
specfact import from-code \
  --repo ./legacy-django-app \
  --name customer-portal \
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

**Auto-generated plan bundle** (`contracts/plans/plan.bundle.yaml`):

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

## Step 2: Add Contracts to Critical Paths

### Identify Critical Functions

Review the extracted plan to identify high-risk functions:

```bash
# Review extracted plan
cat contracts/plans/plan.bundle.yaml | grep -A 10 "FEATURE-002"

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

---

## Step 3: Discover Hidden Edge Cases

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

## Step 4: Prevent Regressions During Modernization

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

## Key Takeaways

### What Worked Well

1. ✅ **code2spec extraction** provided immediate value (< 10 seconds)
2. ✅ **Runtime contracts** prevented 4 production bugs during refactoring
3. ✅ **CrossHair** discovered 6 edge cases manual testing missed
4. ✅ **Incremental approach** (shadow → warn → block) reduced risk

### Lessons Learned

1. **Start with critical paths** - Don't try to contract everything at once
2. **Use shadow mode first** - Observe violations before enforcing
3. **Run CrossHair early** - Discover edge cases before refactoring
4. **Document findings** - Keep notes on violations and edge cases

---

## Next Steps

1. **[Brownfield Engineer Guide](../guides/brownfield-engineer.md)** - Complete modernization workflow
2. **[ROI Calculator](../guides/brownfield-roi.md)** - Calculate your savings
3. **[Flask API Example](brownfield-flask-api.md)** - Another brownfield scenario
4. **[Data Pipeline Example](brownfield-data-pipeline.md)** - ETL modernization

---

**Questions?** [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions) | [hello@noldai.com](mailto:hello@noldai.com)
