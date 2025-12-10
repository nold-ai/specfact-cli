# Dual-Stack Enrichment Pattern

**Status**: ✅ **AVAILABLE** (v0.13.0+)  
**Last Updated**: 2025-12-02

---

## Overview

The **Dual-Stack Enrichment Pattern** is SpecFact's approach to combining CLI automation with AI IDE (LLM) capabilities. It ensures that all artifacts are CLI-generated and validated, while allowing LLMs to add semantic understanding and enhancements.

## Core Principle

**ALWAYS use the SpecFact CLI as the primary tool**. LLM enrichment is a **secondary layer** that enhances CLI output with semantic understanding, but **never replaces CLI artifact creation**.

## CLI vs LLM Capabilities

### CLI-Only Operations (CI/CD Mode - No LLM Required)

The CLI can perform these operations **without LLM**:

- ✅ Tool execution (ruff, pylint, basedpyright, mypy, semgrep, specmatic)
- ✅ Bundle management (create, load, save, validate structure)
- ✅ Metadata management (timestamps, hashes, telemetry)
- ✅ Planning operations (init, add-feature, add-story, update-idea, update-feature)
- ✅ AST/Semgrep-based analysis (code structure, patterns, relationships)
- ✅ Specmatic validation (OpenAPI/AsyncAPI contract validation)
- ✅ Format validation (YAML/JSON schema compliance)
- ✅ Source tracking and drift detection

**CRITICAL LIMITATIONS**:

- ❌ **CANNOT generate code** - No LLM available in CLI-only mode
- ❌ **CANNOT do reasoning** - No semantic understanding without LLM

### LLM-Required Operations (AI IDE Mode - Via Slash Prompts)

These operations **require LLM** and are only available via AI IDE slash prompts:

- ✅ Code generation (requires LLM reasoning)
- ✅ Code enhancement (contracts, refactoring, improvements)
- ✅ Semantic understanding (business logic, context, priorities)
- ✅ Plan enrichment (missing features, confidence adjustments, business context)
- ✅ Code reasoning (why decisions were made, trade-offs, constraints)

**Access**: Only available via AI IDE slash prompts (Cursor, CoPilot, etc.)  
**Pattern**: Slash prompt → LLM generates → CLI validates → Apply if valid

## Three-Phase Workflow

When working with AI IDE slash prompts, follow this three-phase workflow:

### Phase 1: CLI Grounding (REQUIRED)

```bash
# Execute CLI to get structured output
specfact <command> [options] --no-interactive
```

**Capture**:

- CLI-generated artifacts (plan bundles, reports)
- Metadata (timestamps, confidence scores)
- Telemetry (execution time, file counts)

### Phase 2: LLM Enrichment (OPTIONAL, Copilot Only)

**Purpose**: Add semantic understanding to CLI output

**What to do**:

- Read CLI-generated artifacts (use file reading tools for display only)
- Research codebase for additional context
- Identify missing features/stories
- Suggest confidence adjustments
- Extract business context

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly (use CLI commands to update)
- ❌ Bypass CLI validation
- ❌ Write to `.specfact/` folder directly (always use CLI)
- ❌ Use direct file manipulation tools for writing (use CLI commands)

**Output**: Generate enrichment report (Markdown) saved to `.specfact/projects/<bundle-name>/reports/enrichment/` (bundle-specific, Phase 8.5)

### Phase 3: CLI Artifact Creation (REQUIRED)

```bash
# Use enrichment to update plan via CLI
specfact plan update-feature [--bundle <name>] [options] --no-interactive
```

**Result**: Final artifacts are CLI-generated with validated enrichments

## Standard Validation Loop Pattern (For LLM-Generated Code)

When generating or enhancing code via LLM, **ALWAYS** follow this pattern:

```
1. CLI Prompt Generation (Required)
   ↓
   CLI generates structured prompt → saved to .specfact/prompts/
   (e.g., `generate contracts-prompt`, future: `generate code-prompt`)

2. LLM Execution (Required - AI IDE Only)
   ↓
   LLM reads prompt → generates enhanced code → writes to TEMPORARY file
   (NEVER writes directly to original artifacts)
   Pattern: `enhanced_<filename>.py` or `generated_<feature>.py`

3. CLI Validation Loop (Required, up to N retries)
   ↓
   CLI validates temp file with all relevant tools:
   - Syntax validation (py_compile)
   - File size check (must be >= original)
   - AST structure comparison (preserve functions/classes)
   - Contract imports verification
   - Code quality checks (ruff, pylint, basedpyright, mypy)
   - Test execution (contract-test, pytest)
   ↓
   If validation fails:
   - CLI provides detailed error feedback
   - LLM fixes issues in temp file
   - Re-validate (max 3 attempts)
   ↓
   If validation succeeds:
   - CLI applies changes to original file
   - CLI removes temporary file
   - CLI updates metadata/telemetry
```

**This pattern must be used for**:

- ✅ Contract enhancement (`generate contracts-prompt` / `contracts-apply`) - Already implemented
- ⏳ Code generation (future: `generate code-prompt` / `code-apply`) - Needs implementation
- ⏳ Plan enrichment (future: `plan enrich-prompt` / `enrich-apply`) - Needs implementation
- ⏳ Any LLM-enhanced artifact modification - Needs implementation

## Example: Contract Enhancement Workflow

This is a real example of the validation loop pattern in action:

### Step 1: Generate Prompt

```bash
specfact generate contracts-prompt src/auth/login.py --apply beartype,icontract --bundle legacy-api
```

**Result**: Prompt saved to `.specfact/projects/legacy-api/prompts/enhance-login-beartype-icontract.md`

### Step 2: LLM Enhances Code

1. AI IDE reads the prompt file
2. AI IDE reads the original file (`src/auth/login.py`)
3. AI IDE generates enhanced code with contracts
4. AI IDE writes to temporary file: `enhanced_login.py`
5. **DO NOT modify original file directly**

### Step 3: Validate and Apply

```bash
specfact generate contracts-apply enhanced_login.py --original src/auth/login.py
```

**Validation includes**:

- Syntax validation
- File size check
- AST structure comparison
- Contract imports verification
- Code quality checks
- Test execution

**If validation fails**:

- Review error messages
- Fix issues in `enhanced_login.py`
- Re-run validation (up to 3 attempts)

**If validation succeeds**:

- CLI applies changes to `src/auth/login.py`
- CLI removes `enhanced_login.py`
- CLI updates metadata/telemetry

## Why This Pattern?

### Benefits

- ✅ **Format Consistency**: All artifacts match CLI schema versions
- ✅ **Traceability**: CLI metadata tracks who/what/when
- ✅ **Validation**: CLI ensures schema compliance
- ✅ **Reliability**: Works in both Copilot and CI/CD
- ✅ **No Format Drift**: CLI-generated artifacts always match current schema

### What Happens If You Don't Follow

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures
- ❌ Works only in Copilot mode, fails in CI/CD
- ❌ Code generation attempts in CLI-only mode will fail (no LLM available)

## Rules

1. **Execute CLI First**: Always run CLI commands before any analysis
2. **Use CLI for Writes**: All write operations must go through CLI
3. **Read for Display Only**: Use file reading tools for display/analysis only
4. **Never Modify .specfact/**: Do not create/modify files in `.specfact/` directly
5. **Never Bypass Validation**: CLI ensures schema compliance and metadata
6. **Code Generation Requires LLM**: Code generation is only possible via AI IDE slash prompts, not CLI-only
7. **Use Validation Loop**: All LLM-generated code must follow the validation loop pattern

## Available CLI Commands

- `specfact plan init <bundle-name>` - Initialize project bundle
- `specfact plan select <bundle-name>` - Set active plan (used as default for other commands)
- `specfact import from-code [<bundle-name>] --repo <path>` - Import from codebase (uses active plan if bundle not specified)
- `specfact plan review [<bundle-name>]` - Review plan (uses active plan if bundle not specified)
- `specfact plan harden [<bundle-name>]` - Create SDD manifest (uses active plan if bundle not specified)
- `specfact enforce sdd [<bundle-name>]` - Validate SDD (uses active plan if bundle not specified)
- `specfact generate contracts-prompt <file> --apply <contracts>` - Generate contract enhancement prompt
- `specfact generate contracts-apply <enhanced-file> --original <original-file>` - Validate and apply enhanced code
- `specfact sync bridge --adapter <adapter> --repo <path>` - Sync with external tools
- See [Command Reference](../reference/commands.md) for full list

**Note**: Most commands now support active plan fallback. If `--bundle` is not specified, commands automatically use the active plan set via `plan select`. This improves workflow efficiency in AI IDE environments.

---

## Related Documentation

- **[CLI Enforcement Rules](../reference/cli-enforcement.md)** - Detailed enforcement rules
- **[Operational Modes](../reference/modes.md)** - CI/CD vs Copilot modes
- **[IDE Integration](ide-integration.md)** - Setting up slash commands
- **[Command Reference](../reference/commands.md)** - Complete command reference
