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

Validate an OpenAPI/AsyncAPI specification:

```bash
# Basic validation
specfact spec validate api/openapi.yaml

# With backward compatibility check
specfact spec validate api/openapi.yaml --previous api/openapi.v1.yaml
```

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

Auto-generate contract tests from specification:

```bash
# Generate to default location (.specfact/specmatic-tests/)
specfact spec generate-tests api/openapi.yaml

# Generate to custom location
specfact spec generate-tests api/openapi.yaml --output tests/specmatic/
```

### Run Mock Server

Start a mock server for development:

```bash
# Auto-detect spec file
specfact spec mock

# Specify spec file and port
specfact spec mock --spec api/openapi.yaml --port 9000

# Use examples mode (less strict)
specfact spec mock --spec api/openapi.yaml --examples
```

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
specfact import from-code --bundle legacy-api --repo .
# Automatically validates any openapi.yaml or asyncapi.yaml files found
```

### Enforce Command

SDD enforcement includes Specmatic validation:

```bash
specfact enforce sdd legacy-api
# Validates API specifications as part of enforcement checks
```

### Sync Command

Repository sync validates specs after synchronization:

```bash
specfact sync repository --repo .
# Validates API specifications after sync completes
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
# 💡 Tip: Run 'specfact spec mock' to start a mock server for development
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

### Example 3: Development Workflow

```bash
# 1. Validate spec
specfact spec validate api/openapi.yaml

# 2. Start mock server
specfact spec mock --spec api/openapi.yaml --port 9000

# 3. In another terminal, test against mock
curl http://localhost:9000/api/users

# 4. Generate tests
specfact spec generate-tests api/openapi.yaml --output tests/
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
