---
description: Analyze contract coverage, generate enhancement prompts, and apply contracts sequentially with careful review.
---

# SpecFact Contract Enhancement Workflow

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Complete contract enhancement workflow: analyze coverage → generate prompts → apply contracts sequentially with careful review.

**When to use:** After codebase analysis, when adding contracts to existing code, improving contract coverage.

**Quick:** `/specfact.07-contracts` (uses active plan) or `/specfact.07-contracts legacy-api`

## Parameters

### Target/Input

- `bundle NAME` (optional argument) - Project bundle name (e.g., legacy-api, auth-module). Default: active plan (set via `plan select`)
- `--repo PATH` - Repository path. Default: current directory (.)
- `--apply CONTRACTS` - Contract types to apply: 'all-contracts', 'beartype', 'icontract', 'crosshair', or comma-separated list. Default: 'all-contracts'
- `--min-priority PRIORITY` - Minimum priority for files to process: 'high', 'medium', 'low'. Default: 'low' (process all files missing contracts)

### Behavior/Options

- `--no-interactive` - Non-interactive mode (for CI/CD). Default: False (interactive mode with careful review)
- `--auto-apply` - Automatically apply contracts after validation (skips confirmation). Default: False (requires confirmation)
- `--batch-size INT` - Number of files to process before pausing for review. Default: 1 (one file at a time for careful review)

## Workflow

### Step 1: Analyze Contract Coverage

**First, identify files missing contracts:**

```bash
specfact analyze contracts --repo <repo-path> --bundle <bundle-name>
# Uses active plan if bundle not specified
```

**Parse the output to identify:**

- Files missing beartype (marked with ✗)
- Files missing icontract (marked with ✗)
- Files missing crosshair (marked with ✗ or dim ✗)
- Files that need attention (prioritized in the table)

**Extract file list:**

- Focus on files marked with ✗ for beartype or icontract
- Crosshair is optional (marked with dim ✗), but can be included if user requests
- Filter out pure data model files (they use Pydantic validation)

**Present summary:**

- Total files analyzed
- Files missing contracts (by type)
- Files recommended for enhancement

### Step 2: Generate Enhancement Prompts

**For each file missing contracts, generate a prompt:**

```bash
specfact generate contracts-prompt <file-path> --apply <contract-types> --bundle <bundle-name>
```

**Important:**

- Generate prompts for ALL files missing contracts (or based on --min-priority)
- Prompts are saved to `.specfact/projects/<bundle-name>/prompts/enhance-<filename>-<contracts>.md`
- If no bundle, prompts saved to `.specfact/prompts/`
- Each prompt file contains instructions for the AI IDE to enhance the file

**Present prompt generation summary:**

- Number of prompts generated
- Location of prompt files
- List of files ready for enhancement

### Step 3: User Review and Selection

**Present files for user selection:**

```text
Files ready for contract enhancement:
1. src/auth/login.py (missing: beartype, icontract)
2. src/api/users.py (missing: beartype, icontract, crosshair)
3. src/utils/helpers.py (missing: beartype)
...

Select files to enhance (comma-separated numbers, 'all', or 'skip'):
```

**Wait for user input:**

- If user selects specific files, process only those
- If user selects 'all', process all files sequentially
- If user selects 'skip', move to next step or exit

**In non-interactive mode:**

- Process all files automatically (or based on --min-priority)
- Still process sequentially (one at a time) for careful validation

### Step 4: Apply Contracts Sequentially

**For each selected file, apply contracts one at a time:**

**4.1: Read the prompt file:**

```bash
# Prompt file location: .specfact/projects/<bundle-name>/prompts/enhance-<filename>-<contracts>.md
# Or: .specfact/prompts/enhance-<filename>-<contracts>.md
```

**4.2: Enhance the code using AI IDE:**

- Read the original file
- Apply contracts according to the prompt instructions
- Write enhanced code to temporary file: `enhanced_<filename>.py`
- **DO NOT modify the original file directly**

**4.3: Validate enhanced code:**

```bash
specfact generate contracts-apply enhanced_<filename>.py --original <original-file-path>
```

**Validation includes:**

- File size check
- Syntax validation
- AST structure comparison
- Contract imports verification
- Code quality checks (ruff, pylint, basedpyright, mypy if available)
- Test execution (scoped to relevant test files)

**4.4: Handle validation results:**

**If validation fails:**

- Review error messages
- Fix issues in enhanced code
- Re-validate (up to 3 attempts)
- If still failing after 3 attempts, skip this file and continue to next

**If validation succeeds:**

- Show diff preview (what will change)
- If `--auto-apply` is False, ask for confirmation:

  ```text
  Validation passed. Apply changes to <original-file>? (y/n):
  ```

- If confirmed (or `--auto-apply` is True), apply changes automatically
- If not confirmed, skip this file and continue to next

#### 4.5: Pause for review (if --batch-size > 1)

After processing `--batch-size` files, pause and show summary:

```text
Processed 3/10 files:
✓ src/auth/login.py - Contracts applied successfully
✓ src/api/users.py - Contracts applied successfully
⏭ src/utils/helpers.py - Skipped (user declined)

Continue with next batch? (y/n):
```

### Step 5: Final Summary

**After all files processed, show final summary:**

```text
Contract Enhancement Complete

Summary:
- Files analyzed: 25
- Files processed: 18
- Files enhanced: 15
- Files skipped: 3
- Files failed: 0

Enhanced files:
✓ src/auth/login.py (beartype, icontract)
✓ src/api/users.py (beartype, icontract, crosshair)
...

Next steps:
1. Verify contract coverage: specfact analyze contracts --bundle <bundle-name>
2. Run full test suite: pytest (or your project's test command)
3. Review changes: git diff
4. Commit enhanced code
```

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

- Execute CLI commands in sequence (analyze → generate → apply)
- Never modify `.specfact/` directly
- Always validate before applying changes
- Process files sequentially for careful review
- Use `--no-interactive` only in CI/CD environments
- Use CLI output as grounding for all operations
- Code generation requires LLM (only via AI IDE slash prompts, not CLI-only)

## Dual-Stack Workflow (Copilot Mode)

This command **already implements** the standard validation loop pattern (see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code)):

### Phase 1: CLI Prompt Generation (REQUIRED)

```bash
# CLI generates structured prompt
specfact generate contracts-prompt <file-path> --apply <contract-types> --bundle <bundle-name>
```

**Result**: Prompt saved to `.specfact/projects/<bundle-name>/prompts/enhance-<filename>-<contracts>.md`

### Phase 2: LLM Execution (REQUIRED - AI IDE Only)

- LLM reads prompt → generates enhanced code → writes to TEMPORARY file (`enhanced_<filename>.py`)
- **NEVER writes directly to original artifacts**

### Phase 3: CLI Validation Loop (REQUIRED, up to 3 retries)

```bash
# CLI validates temp file with all relevant tools
specfact generate contracts-apply enhanced_<filename>.py --original <original-file>
```

**Validation includes**:

- Syntax validation (py_compile)
- File size check (must be >= original)
- AST structure comparison (preserve functions/classes)
- Contract imports verification
- Code quality checks (ruff, pylint, basedpyright, mypy)
- Test execution (contract-test, pytest)

**If validation fails**: CLI provides detailed error feedback → LLM fixes → Re-validate (max 3 attempts)

**If validation succeeds**: CLI applies changes to original file → CLI removes temporary file → CLI updates metadata/telemetry

**This is the standard pattern for all LLM-generated code** - see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code) for details.

## Expected Output

### Step 1: Analysis Results

```text
Contract Coverage Analysis: legacy-api
Repository: /path/to/repo

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ File                                                          ┃ beartype ┃ icontract ┃ crosshair ┃ Coverage ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
│ src/auth/login.py                                             │    ✗     │     ✗     │     ✗     │       0% │
│ src/api/users.py                                              │    ✗     │     ✗     │     ✗     │       0% │
...

Summary:
  Files analyzed: 25
  Files with beartype: 7 (28.0%)
  Files with icontract: 7 (28.0%)
  Files with crosshair: 2 (8.0%)

Found 18 files missing contracts.
```

### Step 2: Prompt Generation

```text
Generating enhancement prompts...

✓ Generated prompt for: src/auth/login.py
  Location: .specfact/projects/legacy-api/prompts/enhance-login.py-all-contracts.md

✓ Generated prompt for: src/api/users.py
  Location: .specfact/projects/legacy-api/prompts/enhance-users.py-all-contracts.md

...

✓ Generated 18 prompts successfully
```

### Step 3: User Selection

```text
Files ready for contract enhancement:
1. src/auth/login.py (missing: beartype, icontract, crosshair)
2. src/api/users.py (missing: beartype, icontract, crosshair)
3. src/utils/helpers.py (missing: beartype)
...

Select files to enhance (comma-separated numbers, 'all', or 'skip'): all
```

### Step 4: Sequential Application

```text
Processing file 1/18: src/auth/login.py

[Reading prompt file...]
[Enhancing code with AI IDE...]
[Writing enhanced code to: enhanced_login.py]

Validating enhanced code...
✓ File size check: passed
✓ Syntax validation: passed
✓ AST structure: passed (15 definitions preserved)
✓ Contract imports: verified
✓ Code quality checks: passed (ruff, pylint)
✓ Tests: 12/12 passed

Diff preview:
+ from beartype import beartype
+ from icontract import require, ensure
...

Apply changes to src/auth/login.py? (y/n): y
✓ Contracts applied successfully

[Pausing for review... Press Enter to continue to next file]
```

## Common Patterns

```bash
/specfact.07-contracts                    # Uses active plan, all-contracts, interactive
/specfact.07-contracts legacy-api          # Specific bundle
/specfact.07-contracts --apply beartype,icontract  # Specific contract types
/specfact.07-contracts --min-priority high  # Only high-priority files
/specfact.07-contracts --batch-size 3      # Process 3 files before pausing
/specfact.07-contracts --auto-apply        # Auto-apply after validation (no confirmation)
/specfact.07-contracts --no-interactive    # CI/CD mode (still sequential for safety)
```

## Important Notes

1. **Sequential Processing**: Files are processed one at a time (or in small batches) to allow careful review
2. **Validation Required**: All enhanced code must pass validation before applying
3. **User Control**: User can skip files, pause between files, or stop the process
4. **Data Model Files**: Pure Pydantic/dataclass files are automatically excluded (they use Pydantic validation)
5. **Prompt Location**: Prompts are saved to bundle-specific directories when bundle is provided
6. **Temporary Files**: Enhanced code is written to temporary files (`enhanced_<filename>.py`) for validation before applying

## Context

{ARGS}
