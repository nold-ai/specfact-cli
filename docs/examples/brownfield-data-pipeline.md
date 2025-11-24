# Brownfield Example: Modernizing Legacy Data Pipeline

> **Complete walkthrough: From undocumented ETL pipeline to contract-enforced data processing**

---

## The Problem

You inherited a 5-year-old Python data pipeline with:

- ❌ No documentation
- ❌ No type hints
- ❌ No data validation
- ❌ Critical ETL jobs (can't risk breaking)
- ❌ Business logic embedded in transformations
- ❌ Original developers have left

**Challenge:** Modernize from Python 2.7 → 3.12 without breaking production ETL jobs.

---

## Step 1: Reverse Engineer Data Pipeline

> **Note**: This example demonstrates the complete hard-SDD workflow, including SDD manifest creation, validation, and plan promotion gates. The SDD manifest serves as your "hard spec" - a canonical reference that prevents drift during modernization.

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow. Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE.

### Extract Specs from Legacy Pipeline

```bash
# Analyze the legacy data pipeline
specfact import from-code \
  --repo ./legacy-etl-pipeline \
  --name customer-etl \
  --language python

```

### Output

```text
✅ Analyzed 34 Python files
✅ Extracted 18 ETL jobs:

   - JOB-001: Customer Data Import (95% confidence)
   - JOB-002: Order Data Transformation (92% confidence)
   - JOB-003: Payment Data Aggregation (88% confidence)
   ...
✅ Generated 67 user stories from pipeline code
✅ Detected 6 edge cases with CrossHair symbolic execution
⏱️  Completed in 7.5 seconds
```

### What You Get

**Auto-generated pipeline documentation:**

```yaml
features:

  - key: JOB-002
    name: Order Data Transformation
    description: Transform raw order data into normalized format
    stories:

      - key: STORY-002-001
        title: Transform order records
        description: Transform order data with validation
        acceptance_criteria:

          - Input: Raw order records (CSV/JSON)
          - Validation: Order ID must be positive integer
          - Validation: Amount must be positive decimal
          - Output: Normalized order records
```

---

## Step 2: Create Hard SDD Manifest

After extracting the plan, create a hard SDD manifest:

```bash
# Create SDD manifest from the extracted plan
specfact plan harden
```

### Output

```text
✅ SDD manifest created: .specfact/sdd.yaml

📋 SDD Summary:
   WHY: Modernize legacy ETL pipeline with zero data corruption
   WHAT: 18 ETL jobs, 67 stories extracted from legacy code
   HOW: Runtime contracts, data validation, incremental enforcement

🔗 Linked to plan: customer-etl (hash: ghi789jkl012...)
📊 Coverage thresholds:
   - Contracts per story: 1.0 (minimum)
   - Invariants per feature: 2.0 (minimum)
   - Architecture facets: 3 (minimum)
```

---

## Step 3: Validate SDD Before Modernization

Validate that your SDD manifest matches your plan:

```bash
# Validate SDD manifest against plan
specfact enforce sdd
```

### Output

```text
✅ Hash match verified
✅ Contracts/story: 1.1 (threshold: 1.0) ✓
✅ Invariants/feature: 2.3 (threshold: 2.0) ✓
✅ Architecture facets: 4 (threshold: 3) ✓

✅ SDD validation passed
```

---

## Step 4: Promote Plan with SDD Validation

Promote your plan to "review" stage (requires valid SDD):

```bash
# Promote plan to review stage
specfact plan promote --stage review
```

**Why this matters**: Plan promotion enforces SDD presence, ensuring you have a hard spec before starting modernization work.

---

## Step 5: Add Contracts to Data Transformations

### Before: Undocumented Legacy Transformation

```python
# transformations/orders.py (legacy code)
def transform_order(raw_order):
    """Transform raw order data"""
    order_id = raw_order.get('id')
    amount = float(raw_order.get('amount', 0))
    customer_id = raw_order.get('customer_id')
    
    # 50 lines of legacy transformation logic
    # Hidden business rules:
    # - Order ID must be positive integer
    # - Amount must be positive decimal
    # - Customer ID must be valid
    ...
    
    return {
        'order_id': order_id,
        'amount': amount,
        'customer_id': customer_id,
        'status': 'processed'
    }

```

### After: Contract-Enforced Transformation

```python
# transformations/orders.py (modernized with contracts)
import icontract
from typing import Dict, Any

@icontract.require(
    lambda raw_order: isinstance(raw_order.get('id'), int) and raw_order['id'] > 0,
    "Order ID must be positive integer"
)
@icontract.require(
    lambda raw_order: float(raw_order.get('amount', 0)) > 0,
    "Order amount must be positive decimal"
)
@icontract.require(
    lambda raw_order: raw_order.get('customer_id') is not None,
    "Customer ID must be present"
)
@icontract.ensure(
    lambda result: 'order_id' in result and 'amount' in result,
    "Result must contain order_id and amount"
)
def transform_order(raw_order: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw order data with runtime contract enforcement"""
    order_id = raw_order['id']
    amount = float(raw_order['amount'])
    customer_id = raw_order['customer_id']
    
    # Same 50 lines of legacy transformation logic
    # Now with runtime enforcement
    
    return {
        'order_id': order_id,
        'amount': amount,
        'customer_id': customer_id,
        'status': 'processed'
    }
```

### Re-validate SDD After Adding Contracts

After adding contracts, re-validate your SDD:

```bash
specfact enforce sdd
```

---

## Step 6: Discover Data Edge Cases

### Run CrossHair on Data Transformations

```bash
# Discover edge cases in order transformation
hatch run contract-explore transformations/orders.py

```

### CrossHair Output

```text
🔍 Exploring contracts in transformations/orders.py...

❌ Precondition violation found:
   Function: transform_order
   Input: raw_order={'id': 0, 'amount': '100.50', 'customer_id': 123}
   Issue: Order ID must be positive integer (got 0)
   
❌ Precondition violation found:
   Function: transform_order
   Input: raw_order={'id': 456, 'amount': '-50.00', 'customer_id': 123}
   Issue: Order amount must be positive decimal (got -50.0)
   
✅ Contract exploration complete
   - 2 violations found
   - 0 false positives
   - Time: 10.2 seconds

```

### Add Data Validation

```python
# Add data validation based on CrossHair findings
@icontract.require(
    lambda raw_order: isinstance(raw_order.get('id'), int) and raw_order['id'] > 0,
    "Order ID must be positive integer"
)
@icontract.require(
    lambda raw_order: isinstance(raw_order.get('amount'), (int, float, str)) and 
                      float(raw_order.get('amount', 0)) > 0,
    "Order amount must be positive decimal"
)
def transform_order(raw_order: Dict[str, Any]) -> Dict[str, Any]:
    """Transform with enhanced validation"""
    # Handle string amounts (common in CSV imports)
    amount = float(raw_order['amount']) if isinstance(raw_order['amount'], str) else raw_order['amount']
    ...
```

---

## Step 7: Modernize Pipeline Safely

### Refactor with Contract Safety Net

```python
# Modernized version (same contracts)
@icontract.require(...)  # Same contracts as before
def transform_order(raw_order: Dict[str, Any]) -> Dict[str, Any]:
    """Modernized order transformation with contract safety net"""
    
    # Modernized implementation (Python 3.12)
    order_id: int = raw_order['id']
    amount: float = float(raw_order['amount']) if isinstance(raw_order['amount'], str) else raw_order['amount']
    customer_id: int = raw_order['customer_id']
    
    # Modernized transformation logic
    transformed = OrderTransformer().transform(
        order_id=order_id,
        amount=amount,
        customer_id=customer_id
    )
    
    return {
        'order_id': transformed.order_id,
        'amount': transformed.amount,
        'customer_id': transformed.customer_id,
        'status': 'processed'
    }

```

### Catch Data Pipeline Regressions

```python
# During modernization, accidentally break contract:
# Missing amount validation in refactored code

# Runtime enforcement catches it:
# ❌ ContractViolation: Order amount must be positive decimal (got -50.0)
#    at transform_order() call from etl_job.py:142
#    → Prevented data corruption in production ETL!
```

---

## Results

### Quantified Outcomes

| Metric | Before SpecFact | After SpecFact | Improvement |
|--------|----------------|----------------|-------------|
| **Pipeline documentation** | 0% (none) | 100% (auto-generated) | **∞ improvement** |
| **Data validation** | Manual (error-prone) | Automated (contracts) | **100% coverage** |
| **Edge cases discovered** | 0-2 (manual) | 6 (CrossHair) | **3x more** |
| **Data corruption prevented** | 0 (no safety net) | 11 incidents | **∞ improvement** |
| **Migration time** | 8 weeks (cautious) | 3 weeks (confident) | **62% faster** |

### Case Study: Customer ETL Pipeline

**Challenge:**

- 5-year-old Python data pipeline (12K LOC)
- No documentation, original developers left
- Needed modernization from Python 2.7 → 3.12
- Fear of breaking critical ETL jobs

**Solution:**

1. Ran `specfact import from-code` → 47 features extracted in 12 seconds
2. Added contracts to 23 critical data transformation functions
3. CrossHair discovered 6 edge cases in legacy validation logic
4. Enforced contracts during migration, blocked 11 regressions

**Results:**

- ✅ 87% faster documentation (8 hours vs. 60 hours manual)
- ✅ 11 production bugs prevented during migration
- ✅ Zero downtime migration completed in 3 weeks vs. estimated 8 weeks
- ✅ New team members productive in days vs. weeks

**ROI:** $42,000 saved, 5-week acceleration

---

## Integration with Your Workflow

SpecFact CLI integrates seamlessly with your existing tools:

- **VS Code**: Use pre-commit hooks to catch breaking changes before commit
- **Cursor**: AI assistant workflows catch regressions during refactoring
- **GitHub Actions**: CI/CD integration blocks bad code from merging
- **Pre-commit hooks**: Local validation prevents breaking changes
- **Any IDE**: Pure CLI-first approach—works with any editor

**See real examples**: [Integration Showcases](../integration-showcases/) - 5 complete examples showing bugs fixed via integrations

## Key Takeaways

### What Worked Well

1. ✅ **code2spec** extracted pipeline structure automatically
2. ✅ **SDD manifest** created hard spec reference, preventing drift
3. ✅ **SDD validation** ensured coverage thresholds before modernization
4. ✅ **Plan promotion gates** required SDD presence, enforcing discipline
5. ✅ **Contracts** enforced data validation at runtime
6. ✅ **CrossHair** discovered edge cases in data transformations
7. ✅ **Incremental modernization** reduced risk
8. ✅ **CLI-first integration** - Works offline, no account required, no vendor lock-in

### Lessons Learned

1. **Start with critical jobs** - Maximum impact, minimum risk
2. **Validate data early** - Contracts catch bad data before processing
3. **Test edge cases** - Run CrossHair on data transformations
4. **Monitor in production** - Keep contracts enabled to catch regressions

---

## Next Steps

1. **[Integration Showcases](../integration-showcases/)** - See real bugs fixed via VS Code, Cursor, GitHub Actions integrations
2. **[Brownfield Engineer Guide](../guides/brownfield-engineer.md)** - Complete modernization workflow
3. **[Django Example](brownfield-django-modernization.md)** - Web app modernization
4. **[Flask API Example](brownfield-flask-api.md)** - API modernization

---

**Questions?** [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions) | [hello@noldai.com](mailto:hello@noldai.com)
