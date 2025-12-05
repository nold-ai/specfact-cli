# Specmatic Integration Guide

> **API Contract Testing with Specmatic**  
> Validate OpenAPI/AsyncAPI specifications, check backward compatibility, and run mock servers

---

## Overview

SpecFact CLI integrates with **Specmatic** to provide service-level contract testing for API specifications. This complements SpecFact's code-level contracts (icontract, beartype, CrossHair) by adding API contract validation.

**What Specmatic adds:**

- ✅ **OpenAPI/AsyncAPI validation** - Validate specification structure and examples
- ✅ **Backward compatibility checking** - Detect breaking changes between spec versions
- ✅ **Mock server generation** - Run development mock servers from specifications
- ✅ **Test suite generation** - Auto-generate contract tests from specs

---

## Quick Reference: When to Use What

| Command | Purpose | Output | When to Use |
|---------|---------|--------|-------------|
| `spec validate` | **Check if spec is valid** | Validation report (console) | Before committing spec changes, verify spec correctness |
| `spec generate-tests` | **Create tests to validate API** | Test files (on disk) | To test your API implementation matches the spec |
| `spec mock` | **Run mock server** | Running server | Test client code, frontend development |
| `spec backward-compat` | **Check breaking changes** | Compatibility report | When updating API versions |

**Key Difference:**

- `validate` = "Is my spec file correct?" (checks the specification itself)
- `generate-tests` = "Create tests to verify my API matches the spec" (creates executable tests)

**Typical Workflow:**

```bash
# 1. Validate spec is correct
specfact spec validate --bundle my-api

# 2. Generate tests from spec
specfact spec generate-tests --bundle my-api --output tests/

# 3. Run tests against your API
specmatic test --spec ... --host http://localhost:8000
```

---

## Installation

**Important**: Specmatic is a **Java CLI tool**, not a Python package. It must be installed separately.

### Install Specmatic

Visit the [Specmatic download page](https://docs.specmatic.io/download.html) for detailed installation instructions.

**Quick install options:**

```bash
# Option 1: Direct installation (requires Java 17+)
# macOS/Linux
curl https://docs.specmatic.io/install-specmatic.sh | bash

# Windows (PowerShell)
irm https://docs.specmatic.io/install-specmatic.ps1 | iex

# Option 2: Via npm/npx (requires Java/JRE and Node.js)
# Run directly without installation
npx specmatic --version

# Option 3: macOS (Homebrew)
brew install specmatic

# Verify installation
specmatic --version
```

**Note**: SpecFact CLI automatically detects Specmatic whether it's installed directly or available via `npx`. If you have Java/JRE installed, you can use `npx specmatic` without a separate installation.

### Verify Integration

SpecFact CLI will automatically detect if Specmatic is available:

```bash
# Check if Specmatic is detected
specfact spec validate --help

# If Specmatic is not installed, you'll see:
# ✗ Specmatic not available: Specmatic CLI not found. Install from: https://docs.specmatic.io/
```

---

## Commands

### Validate Specification

Validate an OpenAPI/AsyncAPI specification. Can validate a single file or all contracts in a project bundle:

```bash
# Validate a single spec file
specfact spec validate api/openapi.yaml

# With backward compatibility check
specfact spec validate api/openapi.yaml --previous api/openapi.v1.yaml

# Validate all contracts in active bundle (interactive selection)
specfact spec validate

# Validate all contracts in specific bundle
specfact spec validate --bundle legacy-api

# Non-interactive: validate all contracts in active bundle
specfact spec validate --bundle legacy-api --no-interactive
```

**CLI-First Pattern**: The command uses the active plan (from `specfact plan select`) as default, or you can specify `--bundle`. Never requires direct `.specfact` paths - always use the CLI interface.

**What it checks:**

- Schema structure validation
- Example generation test
- Backward compatibility (if previous version provided)

### Check Backward Compatibility

Compare two specification versions:

```bash
specfact spec backward-compat api/openapi.v1.yaml api/openapi.v2.yaml
```

**Output:**

- ✓ Compatible - No breaking changes detected
- ✗ Breaking changes - Lists incompatible changes

### Generate Test Suite

Auto-generate contract tests from specification. Can generate for a single file or all contracts in a bundle:

```bash
# Generate for a single spec file
specfact spec generate-tests api/openapi.yaml

# Generate to custom location
specfact spec generate-tests api/openapi.yaml --output tests/specmatic/

# Generate tests for all contracts in active bundle
specfact spec generate-tests --bundle legacy-api

# Generate tests for all contracts in specific bundle
specfact spec generate-tests --bundle legacy-api --output tests/contract/
```

**CLI-First Pattern**: Uses active plan as default, or specify `--bundle`. Never requires direct `.specfact` paths.

### What Can You Do With Generated Tests?

The tests generated by `spec generate-tests` are **executable contract tests** that validate your API implementation against your OpenAPI/AsyncAPI specification. Here's a complete walkthrough:

#### Understanding Generated Tests

When you run `specfact spec generate-tests`, Specmatic creates test files that:

- **Validate request format**: Check that requests match the spec (headers, body, query params)
- **Validate response format**: Verify responses match the spec (status codes, headers, body schema)
- **Test all endpoints**: Ensure all endpoints defined in the spec are implemented
- **Check data types**: Validate that data types and constraints are respected
- **Property-based testing**: Automatically generate diverse test data to find edge cases

#### Step-by-Step: Using Generated Tests

**Step 1: Generate Tests from Your Contract**

```bash
# Generate tests for all contracts in your bundle
specfact spec generate-tests --bundle my-api --output tests/contract/

# Output:
# [1/5] Generating test suite from: .specfact/projects/my-api/contracts/api.openapi.yaml
# ✓ Test suite generated: tests/contract/
# ...
# ✓ Generated tests for 5 contract(s)
```

**Step 2: Review Generated Test Files**

The tests are generated in the output directory (default: `.specfact/specmatic-tests/`):

```bash
# Check what was generated
ls -la tests/contract/
# Output shows Specmatic test files (format depends on Specmatic version)
```

**Step 3: Start Your API Server**

Before running tests, start your API implementation:

```bash
# Example: Start FastAPI server
python -m uvicorn main:app --port 8000

# Or Flask
python app.py

# Or any other API server
# Make sure it's running on the expected host/port
```

**Step 4: Run Tests Against Your API**

Use Specmatic's test runner to execute the generated tests:

```bash
# Run tests against your running API
specmatic test \
  --spec .specfact/projects/my-api/contracts/api.openapi.yaml \
  --host http://localhost:8000

# Output:
# ✓ GET /api/users - Request/Response match contract
# ✓ POST /api/users - Request/Response match contract
# ✗ GET /api/products - Response missing required field 'price'
# ...
```

**Step 5: Fix Issues and Re-run**

If tests fail, fix your API implementation and re-run:

```bash
# Fix the API code
# ... make changes ...

# Restart API server
python -m uvicorn main:app --port 8000

# Re-run tests
specmatic test --spec ... --host http://localhost:8000
```

#### Complete Example: Contract-Driven Development Workflow

Here's a full workflow from contract to tested implementation:

```bash
# 1. Import existing code and extract contracts
specfact import from-code --bundle user-api --repo .

# 2. Validate contracts are correct
specfact spec validate --bundle user-api

# Output:
# [1/3] Validating specification: contracts/user-api.openapi.yaml
# ✓ Specification is valid: user-api.openapi.yaml
# ...

# 3. Generate tests from validated contracts
specfact spec generate-tests --bundle user-api --output tests/contract/

# Output:
# [1/3] Generating test suite from: contracts/user-api.openapi.yaml
# ✓ Test suite generated: tests/contract/
# ✓ Generated tests for 3 contract(s)

# 4. Start your API server
python -m uvicorn api.main:app --port 8000 &
sleep 3  # Wait for server to start

# 5. Run contract tests
specmatic test \
  --spec .specfact/projects/user-api/contracts/user-api.openapi.yaml \
  --host http://localhost:8000

# Output:
# Running contract tests...
# ✓ GET /api/users - Passed
# ✓ POST /api/users - Passed
# ✓ GET /api/users/{id} - Passed
# All tests passed! ✓
```

#### CI/CD Integration Example

Add contract testing to your CI/CD pipeline:

```yaml
# .github/workflows/contract-tests.yml
name: Contract Tests

on: [push, pull_request]

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Specmatic
        run: |
          curl https://docs.specmatic.io/install-specmatic.sh | bash
          
      - name: Install SpecFact CLI
        run: pip install specfact-cli
        
      - name: Generate contract tests
        run: |
          specfact spec generate-tests \
            --bundle my-api \
            --output tests/contract/ \
            --no-interactive
            
      - name: Start API server
        run: |
          python -m uvicorn main:app --port 8000 &
          sleep 5
          
      - name: Run contract tests
        run: |
          specmatic test \
            --spec .specfact/projects/my-api/contracts/api.openapi.yaml \
            --host http://localhost:8000
```

#### Testing Against Mock Servers

You can also test your client code against Specmatic mock servers:

```bash
# Terminal 1: Start mock server
specfact spec mock --bundle my-api --port 9000

# Terminal 2: Run your client code against mock
python client.py  # Your client code that calls the API

# The mock server:
# - Validates requests match the spec
# - Returns spec-compliant responses
# - Helps test client code without a real API
```

#### Benefits of Using Generated Tests

1. **Automated Validation**: Catch contract violations automatically
2. **Early Detection**: Find issues before deployment
3. **Documentation**: Tests serve as executable examples
4. **Confidence**: Ensure API changes don't break contracts
5. **Integration Safety**: Prevent breaking changes between services
6. **Property-Based Testing**: Automatically test edge cases and boundary conditions

#### Troubleshooting Test Execution

**Tests fail with "Connection refused":**

```bash
# Make sure your API server is running
curl http://localhost:8000/health  # Test server is up

# Check the host/port in your test command matches your server
specmatic test --spec ... --host http://localhost:8000
```

**Tests fail with "Response doesn't match contract":**

```bash
# Check what the actual response is
curl -v http://localhost:8000/api/users

# Compare with your OpenAPI spec
# Fix your API implementation to match the spec
```

**Tests pass but you want to see details:**

```bash
# Use verbose mode (if supported by Specmatic version)
specmatic test --spec ... --host ... --verbose
```

### Run Mock Server

Start a mock server for development. Can use a single spec file or select from bundle contracts:

```bash
# Auto-detect spec file from current directory
specfact spec mock

# Specify spec file and port
specfact spec mock --spec api/openapi.yaml --port 9000

# Use examples mode (less strict)
specfact spec mock --spec api/openapi.yaml --examples

# Select contract from active bundle (interactive)
specfact spec mock --bundle legacy-api

# Use specific bundle (non-interactive, uses first contract)
specfact spec mock --bundle legacy-api --no-interactive
```

**CLI-First Pattern**: Uses active plan as default, or specify `--bundle`. Interactive selection when multiple contracts available.

**Mock server features:**

- Serves API endpoints based on specification
- Validates requests against spec
- Returns example responses
- Press Ctrl+C to stop

---

## Integration with Other Commands

Specmatic validation is automatically integrated into:

### Import Command

When importing code, SpecFact auto-detects and validates OpenAPI/AsyncAPI specs:

```bash
# Import with bundle (uses active plan if --bundle not specified)
specfact import from-code --bundle legacy-api --repo .

# Automatically validates:
# - Repo-level OpenAPI/AsyncAPI specs (openapi.yaml, asyncapi.yaml)
# - Bundle contract files referenced in features
# - Suggests starting mock server if API specs found
```

### Enforce Command

SDD enforcement includes Specmatic validation for all contracts referenced in the bundle:

```bash
# Enforce SDD (uses active plan if --bundle not specified)
specfact enforce sdd --bundle legacy-api

# Automatically validates:
# - All contract files referenced in bundle features
# - Includes validation results in enforcement report
# - Reports deviations for invalid contracts
```

### Sync Command

Repository sync validates specs before synchronization:

```bash
# Sync bridge (uses active plan if --bundle not specified)
specfact sync bridge --bundle legacy-api --repo .

# Automatically validates:
# - OpenAPI/AsyncAPI specs before sync operation
# - Prevents syncing invalid contracts
# - Reports validation errors before proceeding
```

---

## How It Works

### Architecture

```text
┌─────────────────────────────────────────────────────────┐
│              SpecFact Complete Stack                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 1: Code-Level Contracts (Current)                │
│  ├─ icontract: Function preconditions/postconditions   │
│  ├─ beartype: Runtime type validation                   │
│  └─ CrossHair: Symbolic execution & counterexamples    │
│                                                          │
│  Layer 2: Service-Level Contracts (Specmatic)          │
│  ├─ OpenAPI/AsyncAPI validation                         │
│  ├─ Backward compatibility checking                    │
│  ├─ Mock server for development                        │
│  └─ Contract testing automation                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Integration Pattern

SpecFact calls Specmatic via subprocess:

1. **Check availability** - Verifies Specmatic CLI is in PATH
2. **Execute command** - Runs Specmatic CLI with appropriate arguments
3. **Parse results** - Extracts validation results and errors
4. **Display output** - Shows results in SpecFact's rich console format

---

## Examples

### Example 1: Validate API Spec During Import

```bash
# Project has openapi.yaml
specfact import from-code --bundle api-service --repo .

# Output:
# ✓ Import complete!
# 🔍 Found 1 API specification file(s)
# Validating openapi.yaml with Specmatic...
#   ✓ openapi.yaml is valid
# Validated 3 bundle contract(s), 0 failed.
# 💡 Tip: Run 'specfact spec mock --bundle api-service' to start a mock server for development
```

### Example 2: Check Breaking Changes

```bash
# Compare API versions
specfact spec backward-compat api/v1/openapi.yaml api/v2/openapi.yaml

# Output:
# ✗ Breaking changes detected
# Breaking Changes:
#   - Removed endpoint /api/v1/users
#   - Changed response schema for /api/v1/products
```

### Example 3: Development Workflow with Bundle

```bash
# 1. Set active bundle
specfact plan select api-service

# 2. Validate all contracts in bundle (interactive selection)
specfact spec validate
# Shows list of contracts, select by number or 'all'

# 3. Start mock server from bundle (interactive selection)
specfact spec mock --bundle api-service --port 9000

# 4. In another terminal, test against mock
curl http://localhost:9000/api/users

# 5. Generate tests for all contracts
specfact spec generate-tests --bundle api-service --output tests/
```

### Example 4: CI/CD Workflow (Non-Interactive)

```bash
# 1. Validate all contracts in bundle (non-interactive)
specfact spec validate --bundle api-service --no-interactive

# 2. Generate tests for all contracts
specfact spec generate-tests --bundle api-service --output tests/ --no-interactive

# 3. Run generated tests
pytest tests/specmatic/
```

---

## Troubleshooting

### Specmatic Not Found

**Error:**

```text
✗ Specmatic not available: Specmatic CLI not found. Install from: https://docs.specmatic.io/
```

**Solution:**

1. Install Specmatic from [https://docs.specmatic.io/](https://docs.specmatic.io/)
2. Ensure `specmatic` is in your PATH
3. Verify with: `specmatic --version`

### Validation Failures

**Error:**

```text
✗ Specification validation failed
Errors:
  - Schema validation failed: missing required field 'info'
```

**Solution:**

1. Check your OpenAPI/AsyncAPI spec format
2. Validate with: `specmatic validate your-spec.yaml`
3. Review Specmatic documentation for spec requirements

### Mock Server Won't Start

**Error:**

```text
✗ Failed to start mock server: Port 9000 already in use
```

**Solution:**

1. Use a different port: `specfact spec mock --port 9001`
2. Stop the existing server on that port
3. Check for other processes: `lsof -i :9000`

---

## Best Practices

1. **Validate early** - Run `specfact spec validate` before committing spec changes
2. **Check compatibility** - Use `specfact spec backward-compat` when updating API versions
3. **Use mock servers** - Start mock servers during development to test integrations
4. **Generate tests** - Auto-generate tests for CI/CD pipelines
5. **Integrate in workflows** - Let SpecFact auto-validate specs during import/enforce/sync

---

## Related Documentation

- **[Specmatic Official Docs](https://docs.specmatic.io/)** - Specmatic documentation
- **[OpenAPI Specification](https://swagger.io/specification/)** - OpenAPI spec format
- **[AsyncAPI Specification](https://www.asyncapi.com/)** - AsyncAPI spec format
- **[Command Reference](../reference/commands.md#spec-commands)** - Full command documentation

---

**Note**: Specmatic is an external tool and must be installed separately. SpecFact CLI provides integration but does not include Specmatic itself.
