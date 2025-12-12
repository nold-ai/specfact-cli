# Specmatic API Reference

> **API Reference for Specmatic Integration**  
> Complete reference for Specmatic functions, classes, and integration points

---

## Overview

The Specmatic integration module (`specfact_cli.integrations.specmatic`) provides functions and classes for validating OpenAPI/AsyncAPI specifications, checking backward compatibility, generating test suites, and running mock servers using Specmatic.

**Module**: `specfact_cli.integrations.specmatic`

---

## Functions

### `check_specmatic_available() -> tuple[bool, str | None]`

Check if Specmatic CLI is available (either directly or via npx).

**Returns**:

- `tuple[bool, str | None]`: `(is_available, error_message)`
  - `is_available`: `True` if Specmatic is available, `False` otherwise
  - `error_message`: Error message if not available, `None` if available

**Example**:

```python
from specfact_cli.integrations.specmatic import check_specmatic_available

is_available, error_msg = check_specmatic_available()
if is_available:
    print("Specmatic is available")
else:
    print(f"Specmatic not available: {error_msg}")
```

---

### `validate_spec_with_specmatic(spec_path: Path, previous_version: Path | None = None) -> SpecValidationResult`

Validate OpenAPI/AsyncAPI specification using Specmatic.

**Parameters**:

- `spec_path` (Path): Path to OpenAPI/AsyncAPI specification file
- `previous_version` (Path | None, optional): Optional path to previous version for backward compatibility check

**Returns**:

- `SpecValidationResult`: Validation result with status and details

**Raises**:

- No exceptions (returns result with `is_valid=False` if validation fails)

**Example**:

```python
from pathlib import Path
from specfact_cli.integrations.specmatic import validate_spec_with_specmatic
import asyncio

spec_path = Path("api/openapi.yaml")
result = asyncio.run(validate_spec_with_specmatic(spec_path))

if result.is_valid:
    print("Specification is valid")
else:
    print(f"Validation failed: {result.errors}")
```

**Validation Checks**:

1. **Schema Validation**: Validates OpenAPI/AsyncAPI schema structure
2. **Example Generation**: Tests that examples can be generated from the spec
3. **Backward Compatibility** (if `previous_version` provided): Checks for breaking changes

---

### `check_backward_compatibility(old_spec: Path, new_spec: Path) -> tuple[bool, list[str]]`

Check backward compatibility between two spec versions.

**Parameters**:

- `old_spec` (Path): Path to old specification version
- `new_spec` (Path): Path to new specification version

**Returns**:

- `tuple[bool, list[str]]`: `(is_compatible, breaking_changes)`
  - `is_compatible`: `True` if backward compatible, `False` otherwise
  - `breaking_changes`: List of breaking change descriptions

**Raises**:

- No exceptions (returns `(False, [])` if check fails)

**Example**:

```python
from pathlib import Path
from specfact_cli.integrations.specmatic import check_backward_compatibility
import asyncio

old_spec = Path("api/openapi.v1.yaml")
new_spec = Path("api/openapi.v2.yaml")

is_compatible, breaking_changes = asyncio.run(
    check_backward_compatibility(old_spec, new_spec)
)

if is_compatible:
    print("Specifications are backward compatible")
else:
    print(f"Breaking changes: {breaking_changes}")
```

---

### `generate_specmatic_tests(spec_path: Path, output_dir: Path | None = None) -> Path`

Generate Specmatic test suite from specification.

**Parameters**:

- `spec_path` (Path): Path to OpenAPI/AsyncAPI specification
- `output_dir` (Path | None, optional): Optional output directory (default: `.specfact/specmatic-tests/`)

**Returns**:

- `Path`: Path to generated test directory

**Raises**:

- `RuntimeError`: If Specmatic is not available or test generation fails

**Example**:

```python
from pathlib import Path
from specfact_cli.integrations.specmatic import generate_specmatic_tests
import asyncio

spec_path = Path("api/openapi.yaml")
output_dir = Path("tests/specmatic")

test_dir = asyncio.run(generate_specmatic_tests(spec_path, output_dir))
print(f"Tests generated in: {test_dir}")
```

---

### `create_mock_server(spec_path: Path, port: int = 9000, strict_mode: bool = True) -> MockServer`

Create Specmatic mock server from specification.

**Parameters**:

- `spec_path` (Path): Path to OpenAPI/AsyncAPI specification
- `port` (int, optional): Port number for mock server (default: 9000)
- `strict_mode` (bool, optional): Use strict validation mode (default: True)

**Returns**:

- `MockServer`: Mock server instance

**Raises**:

- `RuntimeError`: If Specmatic is not available or mock server fails to start

**Example**:

```python
from pathlib import Path
from specfact_cli.integrations.specmatic import create_mock_server
import asyncio

spec_path = Path("api/openapi.yaml")
mock_server = asyncio.run(create_mock_server(spec_path, port=8080))

print(f"Mock server running at http://localhost:{mock_server.port}")
# ... use mock server ...
mock_server.stop()
```

---

## Classes

### `SpecValidationResult`

Result of Specmatic validation.

**Attributes**:

- `is_valid` (bool): Overall validation status
- `schema_valid` (bool): Schema validation status
- `examples_valid` (bool): Example generation validation status
- `backward_compatible` (bool | None): Backward compatibility status (None if not checked)
- `errors` (list[str]): List of error messages
- `warnings` (list[str]): List of warning messages
- `breaking_changes` (list[str]): List of breaking changes (if backward compatibility checked)

**Methods**:

- `to_dict() -> dict[str, Any]`: Convert to dictionary
- `to_json(indent: int = 2) -> str`: Convert to JSON string

**Example**:

```python
from specfact_cli.integrations.specmatic import SpecValidationResult

result = SpecValidationResult(
    is_valid=True,
    schema_valid=True,
    examples_valid=True,
    backward_compatible=True,
)

print(result.to_json())
# {
#   "is_valid": true,
#   "schema_valid": true,
#   "examples_valid": true,
#   "backward_compatible": true,
#   "errors": [],
#   "warnings": [],
#   "breaking_changes": []
# }
```

---

### `MockServer`

Mock server instance.

**Attributes**:

- `port` (int): Port number
- `process` (subprocess.Popen[str] | None): Process handle (None if not running)
- `spec_path` (Path | None): Path to specification file

**Methods**:

- `is_running() -> bool`: Check if mock server is running
- `stop() -> None`: Stop the mock server

**Example**:

```python
from specfact_cli.integrations.specmatic import MockServer

mock_server = MockServer(port=9000, spec_path=Path("api/openapi.yaml"))

if mock_server.is_running():
    print("Mock server is running")
    mock_server.stop()
```

---

## Integration Points

### Import Command Integration

The `import from-code` command automatically validates bundle contracts with Specmatic after import.

**Location**: `specfact_cli.commands.import_cmd._validate_bundle_contracts()`

**Behavior**:

- Validates all contracts referenced in bundle features
- Shows validation results in console output
- Suggests mock server if contracts are found

**Example Output**:

```
🔍 Validating 3 contract(s) in bundle with Specmatic...
Validating contracts/FEATURE-001.openapi.yaml (from FEATURE-001)...
  ✓ FEATURE-001.openapi.yaml is valid
💡 Tip: Run 'specfact spec mock' to start a mock server for development
```

---

### Enforce Command Integration

The `enforce sdd` command validates bundle contracts and reports failures as deviations.

**Location**: `specfact_cli.commands.enforce.enforce_sdd()`

**Behavior**:

- Validates contracts referenced in bundle features
- Reports validation failures as `CONTRACT_VIOLATION` deviations
- Includes validation results in enforcement report

**Example Output**:

```
Validating API contracts with Specmatic...
Found 2 contract(s) referenced in bundle
Validating contracts/FEATURE-001.openapi.yaml (from FEATURE-001)...
  ⚠ FEATURE-001.openapi.yaml has validation issues
    - Schema validation failed: Invalid schema
```

---

### Sync Command Integration

The `sync bridge` command validates contracts before sync operation.

**Location**: `specfact_cli.commands.sync.sync_bridge()`

**Behavior**:

- Validates contracts in bundle before sync
- Checks backward compatibility (if previous versions stored)
- Continues with sync even if validation fails (with warning)

**Example Output**:

```
🔍 Validating OpenAPI contracts before sync...
Validating 2 contract(s)...
Validating contracts/FEATURE-001.openapi.yaml...
  ✓ FEATURE-001.openapi.yaml is valid
✓ All contracts validated successfully
```

---

## Error Handling

All functions handle errors gracefully:

- **Specmatic Not Available**: Functions return appropriate error states or raise `RuntimeError` with helpful messages
- **Validation Failures**: Return `SpecValidationResult` with `is_valid=False` and error details
- **Timeout Errors**: Caught and reported in validation results
- **Process Errors**: Mock server creation failures raise `RuntimeError` with details

---

## Command Detection

Specmatic is automatically detected via:

1. **Direct Installation**: `specmatic` command in PATH
2. **NPM/NPX**: `npx specmatic` (requires Java/JRE and Node.js)

The module caches the detection result to avoid repeated checks.

---

## Related Documentation

- **[Specmatic Integration Guide](../guides/specmatic-integration.md)** - User guide with examples
- **[Spec Commands Reference](./commands.md#spec-commands)** - CLI command reference
- **[Specmatic Documentation](https://docs.specmatic.io/)** - Official Specmatic documentation

---

**Last Updated**: 2025-12-05
