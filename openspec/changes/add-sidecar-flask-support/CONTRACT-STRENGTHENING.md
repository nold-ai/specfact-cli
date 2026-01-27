# Contract Strengthening Guidelines

**Date**: 2026-01-12  
**Status**: ✅ **COMPLETE**  
**Purpose**: Guidelines for strengthening OpenAPI contracts for effective bug detection

---

## Overview

Strong contracts are essential for effective bug detection. Weak contracts (empty schemas, no validation rules) result in no bugs being found, while strong contracts enable CrossHair to detect real violations.

## Contract Strength Levels

### Level 1: Basic Structure (Weak)

```yaml
paths:
  /users/{id}:
    get:
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
```

**Issues**:
- No required fields
- No type constraints
- No validation rules
- Cannot detect bugs

### Level 2: Type Constraints (Moderate)

```yaml
paths:
  /users/{id}:
    get:
      parameters:
        - name: id
          in: path
          schema:
            type: integer
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: integer
                  email:
                    type: string
```

**Improvements**:
- Type constraints added
- Still missing required fields
- No validation rules

### Level 3: Full Validation (Strong)

```yaml
paths:
  /users/{id}:
    get:
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
            minimum: 1
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                required: [id, email]
                properties:
                  id:
                    type: integer
                    minimum: 1
                  email:
                    type: string
                    format: email
                    minLength: 5
                    maxLength: 255
        '404':
          description: User not found
```

**Improvements**:
- Required fields specified
- Type constraints with validation
- Multiple response codes
- Format constraints

## Extracting Expected Status Codes

### From OpenAPI Responses

Expected status codes are automatically extracted from OpenAPI `responses` section:

```yaml
responses:
  '200':
    description: Success
  '201':
    description: Created
  '400':
    description: Bad request
  '404':
    description: Not found
  '500':
    description: Server error
```

**Extracted Codes**: `[200, 201, 400, 404, 500]`

### Implementation

The `_extract_expected_status_codes` function extracts all response codes:

```python
def _extract_expected_status_codes(responses: dict[str, Any]) -> list[int]:
    """Extract expected status codes from OpenAPI responses."""
    codes = []
    for status_str, response_data in responses.items():
        try:
            code = int(status_str)
            codes.append(code)
        except ValueError:
            continue
    return sorted(codes) if codes else [200]  # Default to 200
```

### Usage in Harness

Expected status codes are used in harness postconditions:

```python
@ensure(
    lambda result: result.get('status_code') in [200, 201, 204, 302, 404],
    'Response status code must be one of [200, 201, 204, 302, 404]'
)
@ensure(
    lambda result: result.get('status_code') != 500,
    'Server errors (500) indicate bugs'
)
def harness_get_user(*args: Any, **kwargs: Any) -> Any:
    # ...
```

## Response Structure Validation

### Required Fields

Contracts validate that required fields are present:

```yaml
schema:
  type: object
  required: [id, email, name]
  properties:
    id:
      type: integer
    email:
      type: string
    name:
      type: string
```

**Generated Postcondition**:
```python
@ensure(
    lambda result: 'id' in result.get('data', {}) if isinstance(result.get('data'), dict) else True,
    'Response data must contain id'
)
```

### Property Type Validation

Contracts validate property types:

```yaml
properties:
  id:
    type: integer
  email:
    type: string
    format: email
  age:
    type: integer
    minimum: 0
    maximum: 150
```

**Generated Postconditions**:
```python
@ensure(
    lambda result: isinstance(result.get('data', {}).get('id'), int) 
                   if isinstance(result.get('data'), dict) and 'id' in result.get('data', {}) 
                   else True,
    'Response data.id must be an integer'
)
@ensure(
    lambda result: isinstance(result.get('data', {}).get('email'), str)
                   if isinstance(result.get('data'), dict) and 'email' in result.get('data', {})
                   else True,
    'Response data.email must be a string'
)
```

### Array Item Validation

Contracts validate array item types:

```yaml
schema:
  type: array
  items:
    type: object
    required: [id, name]
    properties:
      id:
        type: integer
      name:
        type: string
```

**Generated Postcondition**:
```python
@ensure(
    lambda result: all(isinstance(item, dict) for item in result.get('data', []))
                   if isinstance(result.get('data'), list)
                   else True,
    'Response data array items must be objects'
)
```

## Best Practices

### 1. Extract All Response Codes

Include all possible response codes in OpenAPI contracts:

```yaml
responses:
  '200':  # Success
  '201':  # Created
  '302':  # Redirect
  '400':  # Bad request
  '404':  # Not found
  '500':  # Server error (indicates bug)
```

### 2. Define Response Schemas

Specify complete response schemas:

```yaml
responses:
  '200':
    content:
      application/json:
        schema:
          type: object
          required: [id, email]
          properties:
            id:
              type: integer
            email:
              type: string
              format: email
```

### 3. Add Validation Rules

Include validation constraints:

```yaml
properties:
  email:
    type: string
    format: email
    minLength: 5
    maxLength: 255
  age:
    type: integer
    minimum: 0
    maximum: 150
```

### 4. Use Type Constraints

Specify exact types:

```yaml
properties:
  id:
    type: integer
    minimum: 1
  price:
    type: number
    minimum: 0
  is_active:
    type: boolean
```

### 5. Document Business Rules

Add descriptions for business logic:

```yaml
properties:
  status:
    type: string
    enum: [pending, active, suspended]
    description: User account status
```

## Contract Generation from Code

### Automatic Extraction

Framework extractors automatically extract contracts from code:

- **Flask**: Extracts routes from `@app.route()` decorators
- **FastAPI**: Extracts from Pydantic models and route decorators
- **Django**: Extracts from URL patterns and form classes

### Manual Enhancement

For complex cases, manually enhance contracts:

1. **Analyze Code**: Review route handlers for business logic
2. **Extract Constraints**: Identify validation rules
3. **Update Contracts**: Add constraints to OpenAPI schemas
4. **Test Validation**: Run validation to verify contracts work

## Example: Strengthening a Weak Contract

### Before (Weak)

```yaml
paths:
  /users/{id}:
    get:
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
```

**Issues**: No validation, cannot detect bugs

### After (Strong)

```yaml
paths:
  /users/{id}:
    get:
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
            minimum: 1
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                type: object
                required: [id, email, name]
                properties:
                  id:
                    type: integer
                    minimum: 1
                  email:
                    type: string
                    format: email
                    minLength: 5
                    maxLength: 255
                  name:
                    type: string
                    minLength: 1
                    maxLength: 100
        '404':
          description: User not found
        '500':
          description: Server error (indicates bug)
```

**Improvements**:
- Parameter validation (id must be ≥ 1)
- Required fields specified
- Type constraints with validation
- Multiple response codes
- Format constraints (email)

## Testing Contract Strength

### Validation Results

Strong contracts produce meaningful validation results:

```
CrossHair Results:
  ✓ harness
  CrossHair: 5 confirmed, 2 not confirmed, 1 violations
  Violations:
    - harness_get_user: status_code=500 (violates: status_code != 500)
```

### Weak Contract Results

Weak contracts produce no violations:

```
CrossHair Results:
  ✓ harness
  CrossHair: 0 confirmed, 0 not confirmed, 0 violations
  (No bugs found - contracts too weak)
```

## Related Documentation

- [Flask Sidecar Usage](./FLASK-SIDECAR-USAGE.md) - Flask-specific guide
- [Dependency Installation](./DEPENDENCY-INSTALLATION.md) - Dependency setup
- [CrossHair Execution Investigation](./CROSSHAIR-EXECUTION.md) - Execution details

---

**Rulesets Applied**: SpecFact CLI rules, Python GitHub rules, Clean Code principles  
**AI Provider**: Claude (Sonnet 4.5)
