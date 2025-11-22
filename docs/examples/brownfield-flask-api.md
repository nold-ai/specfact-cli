# Brownfield Example: Modernizing Legacy Flask API

> **Complete walkthrough: From undocumented Flask API to contract-enforced modern service**

---

## The Problem

You inherited a 2-year-old Flask REST API with:

- ❌ No OpenAPI/Swagger documentation
- ❌ No type hints
- ❌ No request validation
- ❌ 12 undocumented API endpoints
- ❌ Business logic mixed with route handlers
- ❌ No error handling standards

---

## Step 1: Reverse Engineer API Endpoints

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow. Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE.

### Extract Specs from Legacy Flask Code

```bash
# Analyze the legacy Flask API
specfact import from-code \
  --repo ./legacy-flask-api \
  --name customer-api \
  --language python

```

### Output

```text
✅ Analyzed 28 Python files
✅ Extracted 12 API endpoints:

   - POST /api/v1/users (User Registration)
   - GET /api/v1/users/{id} (Get User)
   - POST /api/v1/orders (Create Order)
   - PUT /api/v1/orders/{id} (Update Order)
   ...
✅ Generated 45 user stories from route handlers
✅ Detected 4 edge cases with CrossHair symbolic execution
⏱️  Completed in 6.8 seconds
```

### What You Get

**Auto-generated API documentation** from route handlers:

```yaml
features:

  - key: FEATURE-003
    name: Order Management API
    description: REST API for order management
    stories:

      - key: STORY-003-001
        title: Create order via POST /api/v1/orders
        description: Create new order with items and customer ID
        acceptance_criteria:

          - Request body must contain items array
          - Each item must have product_id and quantity
          - Customer ID must be valid integer
          - Returns order object with status
```

---

## Step 2: Add Contracts to API Endpoints

### Before: Undocumented Legacy Route

```python
# routes/orders.py (legacy code)
@app.route('/api/v1/orders', methods=['POST'])
def create_order():
    """Create new order"""
    data = request.get_json()
    customer_id = data.get('customer_id')
    items = data.get('items', [])
    
    # 60 lines of legacy order creation logic
    # Hidden business rules:
    # - Customer ID must be positive integer
    # - Items must be non-empty array
    # - Each item must have product_id and quantity > 0
    ...
    
    return jsonify({'order_id': order.id, 'status': 'created'}), 201

```

### After: Contract-Enforced Route

```python
# routes/orders.py (modernized with contracts)
import icontract
from typing import List, Dict
from flask import request, jsonify

@icontract.require(
    lambda data: isinstance(data.get('customer_id'), int) and data['customer_id'] > 0,
    "Customer ID must be positive integer"
)
@icontract.require(
    lambda data: isinstance(data.get('items'), list) and len(data['items']) > 0,
    "Items must be non-empty array"
)
@icontract.require(
    lambda data: all(
        isinstance(item, dict) and 
        'product_id' in item and 
        'quantity' in item and 
        item['quantity'] > 0
        for item in data.get('items', [])
    ),
    "Each item must have product_id and quantity > 0"
)
@icontract.ensure(
    lambda result: result[1] == 201,
    "Must return 201 status code"
)
@icontract.ensure(
    lambda result: 'order_id' in result[0].json,
    "Response must contain order_id"
)
def create_order():
    """Create new order with runtime contract enforcement"""
    data = request.get_json()
    customer_id = data['customer_id']
    items = data['items']
    
    # Same 60 lines of legacy order creation logic
    # Now with runtime enforcement
    
    return jsonify({'order_id': order.id, 'status': 'created'}), 201
```

---

## Step 3: Discover API Edge Cases

### Run CrossHair on API Endpoints

```bash
# Discover edge cases in order creation
hatch run contract-explore routes/orders.py

```

### CrossHair Output

```text
🔍 Exploring contracts in routes/orders.py...

❌ Precondition violation found:
   Function: create_order
   Input: data={'customer_id': 0, 'items': [...]}
   Issue: Customer ID must be positive integer (got 0)
   
❌ Precondition violation found:
   Function: create_order
   Input: data={'customer_id': 123, 'items': []}
   Issue: Items must be non-empty array (got [])
   
✅ Contract exploration complete
   - 2 violations found
   - 0 false positives
   - Time: 8.5 seconds

```

### Add Request Validation

```python
# Add Flask request validation based on CrossHair findings
from flask import request
from marshmallow import Schema, fields, ValidationError

class CreateOrderSchema(Schema):
    customer_id = fields.Int(required=True, validate=lambda x: x > 0)
    items = fields.List(
        fields.Dict(keys=fields.Str(), values=fields.Raw()),
        required=True,
        validate=lambda x: len(x) > 0
    )

@app.route('/api/v1/orders', methods=['POST'])
@icontract.require(...)  # Keep contracts for runtime enforcement
def create_order():
    """Create new order with request validation + contract enforcement"""
    try:
        data = CreateOrderSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    
    # Process order with validated data
    ...
```

---

## Step 4: Modernize API Safely

### Refactor with Contract Safety Net

```python
# Modernized version (same contracts)
@icontract.require(...)  # Same contracts as before
def create_order():
    """Modernized order creation with contract safety net"""
    
    # Modernized implementation
    data = CreateOrderSchema().load(request.get_json())
    order_service = OrderService()
    
    try:
        order = order_service.create_order(
            customer_id=data['customer_id'],
            items=data['items']
        )
        return jsonify({
            'order_id': order.id,
            'status': order.status
        }), 201
    except OrderCreationError as e:
        return jsonify({'error': str(e)}), 400

```

### Catch API Regressions

```python
# During modernization, accidentally break contract:
# Missing customer_id validation in refactored code

# Runtime enforcement catches it:
# ❌ ContractViolation: Customer ID must be positive integer (got 0)
#    at create_order() call from test_api.py:42
#    → Prevented API bug from reaching production!
```

---

## Results

### Quantified Outcomes

| Metric | Before SpecFact | After SpecFact | Improvement |
|--------|----------------|----------------|-------------|
| **API documentation** | 0% (none) | 100% (auto-generated) | **∞ improvement** |
| **Request validation** | Manual (error-prone) | Automated (contracts) | **100% coverage** |
| **Edge cases discovered** | 0-1 (manual) | 4 (CrossHair) | **4x more** |
| **API bugs prevented** | 0 (no safety net) | 3 bugs | **∞ improvement** |
| **Refactoring time** | 4-6 weeks (cautious) | 2-3 weeks (confident) | **50% faster** |

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

1. ✅ **code2spec** extracted API endpoints automatically
2. ✅ **Contracts** enforced request validation at runtime
3. ✅ **CrossHair** discovered edge cases in API inputs
4. ✅ **Incremental modernization** reduced risk
5. ✅ **CLI-first integration** - Works offline, no account required, no vendor lock-in

### Lessons Learned

1. **Start with high-traffic endpoints** - Maximum impact
2. **Combine validation + contracts** - Request validation + runtime enforcement
3. **Test edge cases early** - Run CrossHair before refactoring
4. **Document API changes** - Keep changelog of modernized endpoints

---

## Next Steps

1. **[Integration Showcases](../integration-showcases/)** - See real bugs fixed via VS Code, Cursor, GitHub Actions integrations
2. **[Brownfield Engineer Guide](../guides/brownfield-engineer.md)** - Complete modernization workflow
3. **[Django Example](brownfield-django-modernization.md)** - Web app modernization
4. **[Data Pipeline Example](brownfield-data-pipeline.md)** - ETL modernization

---

**Questions?** [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions) | [hello@noldai.com](mailto:hello@noldai.com)
