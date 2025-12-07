# Dual-Stack Enrichment Pattern - Technical Specification

**Status**: ✅ **IMPLEMENTED** (v0.13.0+)  
**Last Updated**: 2025-12-02

---

## Overview

The Dual-Stack Enrichment Pattern is a technical architecture that enforces CLI-first principles while allowing LLM enrichment in AI IDE environments. It ensures all artifacts are CLI-generated and validated, preventing format drift and ensuring consistency.

## Architecture

### Stack 1: CLI (REQUIRED)

**Purpose**: Generate and validate all artifacts

**Capabilities**:

- Tool execution (ruff, pylint, basedpyright, mypy, semgrep, specmatic)
- Bundle management (create, load, save, validate structure)
- Metadata management (timestamps, hashes, telemetry)
- Planning operations (init, add-feature, add-story, update-idea, update-feature)
- AST/Semgrep-based analysis (code structure, patterns, relationships)
- Specmatic validation (OpenAPI/AsyncAPI contract validation)
- Format validation (YAML/JSON schema compliance)
- Source tracking and drift detection

**Limitations**:

- ❌ Cannot generate code (no LLM available)
- ❌ Cannot do reasoning (no semantic understanding)

### Stack 2: LLM (OPTIONAL, AI IDE Only)

**Purpose**: Add semantic understanding and generate code

**Capabilities**:

- Code generation (requires LLM reasoning)
- Code enhancement (contracts, refactoring, improvements)
- Semantic understanding (business logic, context, priorities)
- Plan enrichment (missing features, confidence adjustments, business context)
- Code reasoning (why decisions were made, trade-offs, constraints)

**Access**: Only via AI IDE slash prompts (Cursor, CoPilot, etc.)

## Validation Loop Pattern

### Implementation

The validation loop pattern is implemented in:

- `src/specfact_cli/commands/generate.py`:
  - `generate_contracts_prompt()` - Generates structured prompts
  - `apply_enhanced_contracts()` - Validates and applies enhanced code

### Validation Steps

1. **Syntax Validation**: `python -m py_compile`
2. **File Size Check**: Enhanced file must be >= original file size
3. **AST Structure Comparison**: Logical structure integrity check
4. **Contract Imports Verification**: Required imports present
5. **Code Quality Checks**: ruff, pylint, basedpyright, mypy (if available)
6. **Test Execution**: Run tests via specfact (contract-test)

### Retry Mechanism

- Maximum 3 attempts
- CLI provides detailed error feedback after each attempt
- LLM fixes issues in temporary file
- Re-validate until success or max attempts reached

## CLI Metadata

### Metadata Structure

```python
@dataclass
class CLIArtifactMetadata:
    cli_generated: bool = True
    cli_version: str | None = None
    generated_at: str | None = None
    generated_by: str = "specfact-cli"
```

### Metadata Detection

The `cli_first_validator.py` module provides:

- `is_cli_generated()` - Check if artifact was CLI-generated
- `extract_cli_metadata()` - Extract CLI metadata from artifact
- `validate_artifact_format()` - Validate artifact format
- `detect_direct_manipulation()` - Detect files that may have been directly manipulated

## Enforcement Rules

### For Slash Commands

1. Every slash command MUST execute the specfact CLI at least once
2. Artifacts are ALWAYS CLI-generated (never LLM-generated directly)
3. Enrichment is additive (LLM adds context, CLI validates and creates)
4. Code generation MUST follow validation loop pattern (temp file → validate → apply)

### For CLI Commands

1. All write operations go through CLI
2. Never modify `.specfact/` folder directly
3. Always use `--no-interactive` flag in CI/CD environments
4. Use file reading tools for display only, CLI commands for writes

## Implementation Status

### ✅ Implemented

- Contract enhancement workflow (`generate contracts-prompt` / `contracts-apply`)
- Validation loop pattern with retry mechanism
- CLI metadata detection utilities
- Prompt templates with dual-stack workflow documentation

### ⏳ Pending

- Code generation workflow (`generate code-prompt` / `code-apply`)
- Plan enrichment workflow (`plan enrich-prompt` / `enrich-apply`)
- CLI metadata injection into all generated artifacts
- Enhanced validation logic for format consistency

## Testing

### Unit Tests

- `tests/unit/validators/test_cli_first_validator.py` - CLI-first validation utilities
- 23 test cases covering metadata extraction, format validation, and detection

### Integration Tests

- Contract enhancement workflow tests in `tests/integration/test_generate_contracts.py`
- Validation loop pattern tests in `tests/integration/test_contracts_apply.py`

## Related Code

- `src/specfact_cli/validators/cli_first_validator.py` - Validation utilities
- `src/specfact_cli/commands/generate.py` - Contract enhancement commands
- `resources/prompts/shared/cli-enforcement.md` - CLI enforcement rules
- `resources/prompts/specfact.*.md` - Slash command prompts with dual-stack workflow

---

## Related Documentation

- **[Dual-Stack Enrichment Guide](../guides/dual-stack-enrichment.md)** - End-user guide
- **[CLI Enforcement Rules](../reference/cli-enforcement.md)** - Enforcement rules
- **[Operational Modes](../reference/modes.md)** - CI/CD vs Copilot modes
