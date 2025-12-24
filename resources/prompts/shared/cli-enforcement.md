# CLI Usage Enforcement Rules

## Core Principle

**ALWAYS use SpecFact CLI commands. Never create artifacts directly.**

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

## LLM Grounding Rules

- Treat CLI artifacts as the source of truth for keys, structure, and metadata.
- Scan the codebase only when asked to infer missing behavior/context or explain deviations; respect `--entry-point` scope when provided.
- Use codebase findings to propose updates via CLI (enrichment report, plan update commands), never to rewrite artifacts directly.

## Rules

1. **Execute CLI First**: Always run CLI commands before any analysis
2. **Use CLI for Writes**: All write operations must go through CLI
3. **Read for Display Only**: Use file reading tools for display/analysis only
4. **Never Modify .specfact/**: Do not create/modify files in `.specfact/` directly
5. **Never Bypass Validation**: CLI ensures schema compliance and metadata
6. **Code Generation Requires LLM**: Code generation is only possible via AI IDE slash prompts, not CLI-only

## Standard Validation Loop Pattern (For LLM-Generated Code)

When generating or enhancing code via LLM, **ALWAYS** follow this pattern:

```text
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

## What Happens If You Don't Follow

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures
- ❌ Works only in Copilot mode, fails in CI/CD
- ❌ Code generation attempts in CLI-only mode will fail (no LLM available)

## Available CLI Commands

- `specfact plan init <bundle-name>` - Initialize project bundle
- `specfact plan select <bundle-name>` - Set active plan (used as default for other commands)
- `specfact import from-code [<bundle-name>] --repo <path>` - Import from codebase (uses active plan if bundle not specified)
- `specfact plan review [<bundle-name>]` - Review plan (uses active plan if bundle not specified)
- `specfact plan harden [<bundle-name>]` - Create SDD manifest (uses active plan if bundle not specified)
- `specfact enforce sdd [<bundle-name>]` - Validate SDD (uses active plan if bundle not specified)
- `specfact sync bridge --adapter <adapter> --repo <path>` - Sync with external tools
- See [Command Reference](../../docs/reference/commands.md) for full list

**Note**: Most commands now support active plan fallback. If `--bundle` is not specified, commands automatically use the active plan set via `plan select`. This improves workflow efficiency in AI IDE environments.
