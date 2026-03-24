---
layout: default
title: Contract Testing Workflow
permalink: /guides/contract-testing-workflow/
description: Practical contract testing workflow guidance for SpecFact users and developers.
---

# Contract Testing Workflow - Simple Guide for Developers


> Modules docs handoff: this page remains in the core docs set as release-line overview content.
> Canonical bundle-specific deep guidance now lives in the canonical modules docs site, currently
> published at `https://modules.specfact.io/`.

## Quick Start: Verify Your Contract

The easiest way to verify your OpenAPI contract works is with a single command:

```bash
# Validate a specific contract bundle
specfact spec validate --bundle my-api --feature FEATURE-001

# Validate all contracts in a bundle
specfact spec validate --bundle my-api
```

**What this does:**

1. ✅ Validates your contract schema
2. ✅ Generates examples from the contract
3. ✅ Starts a mock server
4. ✅ Tests connectivity

**That's it!** Your contract is verified and ready to use. The mock server keeps running so you can test your client code.

## What You Can Do Without a Real API

### ✅ Contract Validation (No API Needed)

Use `spec validate` to ensure your contract is correct:

```bash
specfact spec validate --bundle my-api --feature FEATURE-001
```

**Output:**

```
```

Step 1: Validating contracts...
✓ FEATURE-001: Valid (13 endpoints)

Step 2: Generating examples...
✓ FEATURE-001: Examples generated

Step 3: Starting mock server for FEATURE-001...
✓ Mock server started at <http://localhost:9000>

Step 4: Testing connectivity...
✓ Health check passed: UP

✓ Contract verification complete!

Summary:
  • Contracts validated: 1
  • Examples generated: 1
  • Mock server: <http://localhost:9000>

```

### ✅ Mock Server for Development

Start a mock server that generates responses from your contract:

```bash
# Start mock server with examples
specfact spec mock --bundle my-api --feature FEATURE-001 --examples

# Or use the validate command (starts mock server automatically)
specfact spec validate --bundle my-api --feature FEATURE-001
```

**Use cases:**

- Frontend development without backend
- Client library testing
- Integration testing (test your client against the contract)

### ✅ Contract Validation

Validate that your contract schema is correct:

```bash
# Validate a specific contract
specfact spec validate --bundle my-api --feature FEATURE-001

# Check test coverage across all contracts
specfact spec generate-tests --bundle my-api
```

## Complete Workflow Examples

### Example 1: New Contract Development

```bash
# 1. Set up validation for a new bundle
specfact spec validate --bundle my-api

# 2. Edit the contract file
# Edit: .specfact/projects/my-api/contracts/FEATURE-001.openapi.yaml

# 3. Validate everything works
specfact spec validate --bundle my-api --feature FEATURE-001

# 4. Test your client code against the mock server
curl http://localhost:9000/api/endpoint
```

### Example 2: CI/CD Pipeline

```bash
# Validate contracts without starting mock server
specfact spec validate --bundle my-api --skip-mock --no-interactive

# Or just validate
specfact spec validate --bundle my-api --no-interactive
```

### Example 3: Multiple Contracts

```bash
# Validate all contracts in a bundle
specfact spec validate --bundle my-api

# Generate tests from contracts
specfact spec generate-tests --bundle my-api
```

## What Requires a Real API

### ❌ Contract Testing Against Real Implementation

The `specmatic test` command requires a **real API implementation**:

```bash
# This REQUIRES a running API
specmatic test \
  --spec .specfact/projects/my-api/contracts/FEATURE-001.openapi.yaml \
  --host http://localhost:8000
```

**When to use:**

- After implementing your API
- To verify your implementation matches the contract
- In integration tests

**Workflow:**

```bash
# 1. Generate test files
specfact spec generate-tests --bundle my-api --feature FEATURE-001

# 2. Start your real API
python -m uvicorn main:app --port 8000

# 3. Run contract tests
specmatic test \
  --spec .specfact/projects/my-api/contracts/FEATURE-001.openapi.yaml \
  --host http://localhost:8000
```

## Command Reference

### `spec validate` - All-in-One Verification

The simplest way to verify your contract:

```bash
specfact spec validate [OPTIONS]

Options:
  --bundle TEXT          Project bundle name
  --feature TEXT         Feature key (optional - verifies all if not specified)
  --port INTEGER         Port for mock server (default: 9000)
  --skip-mock            Skip mock server (only validate)
  --no-interactive       Non-interactive mode (CI/CD)
```

**What it does:**

1. Validates contract schema
2. Generates examples
3. Starts mock server (unless `--skip-mock`)
4. Tests connectivity

### `spec validate` - Schema Validation

```bash
specfact spec validate --bundle my-api --feature FEATURE-001
```

Validates the OpenAPI schema structure.

### `spec mock` - Mock Server

```bash
specfact spec mock --bundle my-api --feature FEATURE-001 --examples
```

Starts a mock server that generates responses from your contract.

### `spec generate-tests` - Generate Tests

```bash
specfact spec generate-tests --bundle my-api --feature FEATURE-001
```

Generates test files that can be run against a real API.

## Key Insights

| Task | Requires Real API? | Command |
|------|-------------------|---------|
| **Contract Validation** | ❌ No | `spec validate` |
| **Schema Validation** | ❌ No | `spec validate` |
| **Mock Server** | ❌ No | `spec mock` |
| **Example Generation** | ❌ No | `spec validate` (automatic) |
| **Contract Testing** | ✅ Yes | `specmatic test` (after `spec generate-tests`) |

## Troubleshooting

### Mock Server Won't Start

```bash
# Check if Specmatic is installed
npx specmatic --version

# Install if needed
npm install -g @specmatic/specmatic
```

### Contract Validation Fails

```bash
# Check contract file syntax
cat .specfact/projects/my-api/contracts/FEATURE-001.openapi.yaml

# Validate manually
specfact spec validate --bundle my-api --feature FEATURE-001
```

### Examples Not Generated

Examples are generated automatically from your OpenAPI schema. If generation fails:

- Check that your schema has proper request/response definitions
- Ensure data types are properly defined
- Run `spec validate` to see detailed error messages

## Best Practices

1. **Start with `spec validate`** - It does everything you need
2. **Use mock servers for development** - No need to wait for backend
3. **Validate in CI/CD** - Use `--skip-mock --no-interactive` for fast validation
4. **Test against real API** - Use `specmatic test` after implementation

## Next Steps

- Read the [API Reference](../reference/commands.md) for detailed command options
- Check [Architecture Documentation](../architecture/overview.md) for bundle management
- See [Agile/Scrum Workflows](../guides/agile-scrum-workflows.md) for team collaboration
