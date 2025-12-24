---
description: Import codebase → plan bundle. CLI extracts routes/schemas/relationships. LLM enriches with context.
---

# SpecFact Import Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Import codebase → plan bundle. CLI extracts routes/schemas/relationships/contracts. LLM enriches context/"why"/completeness.

## Parameters

**Target/Input**: `--bundle NAME` (optional, defaults to active plan), `--repo PATH`, `--entry-point PATH`, `--enrichment PATH`  
**Output/Results**: `--report PATH`  
**Behavior/Options**: `--shadow-only`, `--enrich-for-speckit/--no-enrich-for-speckit` (default: enabled, uses PlanEnricher for consistent enrichment)  
**Advanced/Configuration**: `--confidence FLOAT` (0.0-1.0), `--key-format FORMAT` (classname|sequential)

## Workflow

1. **Execute CLI**: `specfact [GLOBAL OPTIONS] import from-code [<bundle>] --repo <path> [options]`
   - CLI extracts: routes (FastAPI/Flask/Django), schemas (Pydantic), relationships, contracts (OpenAPI scaffolds), source tracking
   - Uses active plan if bundle not specified
   - Note: `--no-interactive` is a global option and must appear before the subcommand (e.g., `specfact --no-interactive import from-code ...`).
   - **Auto-enrichment enabled by default**: Automatically enhances vague acceptance criteria, incomplete requirements, and generic tasks using PlanEnricher (same logic as `plan review --auto-enrich`)
   - Use `--no-enrich-for-speckit` to disable auto-enrichment
   - **Contract extraction**: OpenAPI contracts are extracted automatically **only** for features with `source_tracking.implementation_files` and detectable API endpoints (FastAPI/Flask patterns). For enrichment-added features or Django apps, use `specfact contract init` after enrichment (see Phase 4)

2. **LLM Enrichment** (Copilot-only, before applying `--enrichment`):
   - Read CLI artifacts: `.specfact/projects/<bundle>/enrichment_context.md`, feature YAMLs, contract scaffolds, and brownfield reports
   - Scan the codebase within `--entry-point` (and adjacent modules) to identify missing features, dependencies, and behavior; do **not** rely solely on AST-derived YAML
   - Compare code findings vs CLI artifacts, then add missing features/stories, reasoning, and acceptance criteria (each added feature must include at least one story)
   - Save the enrichment report to `.specfact/projects/<bundle-name>/reports/enrichment/<bundle-name>-<timestamp>.enrichment.md` (bundle-specific, Phase 8.5)
   - **CRITICAL**: Follow the exact enrichment report format (see "Enrichment Report Format" section below) to ensure successful parsing

3. **Present**: Bundle location, report path, summary (features/stories/contracts/relationships)

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

- Execute CLI first - never create artifacts directly
- Use the global `--no-interactive` flag in CI/CD environments (must appear before the subcommand)
- Never modify `.specfact/` directly
- Use CLI output as grounding for validation
- Code generation requires LLM (only via AI IDE slash prompts, not CLI-only)

## Dual-Stack Workflow (Copilot Mode)

When in copilot mode, follow this three-phase workflow:

### Phase 1: CLI Grounding (REQUIRED)

```bash
# Execute CLI to get structured output
specfact --no-interactive import from-code [<bundle>] --repo <path>
```

**Capture**:

- CLI-generated artifacts (plan bundles, reports)
- Metadata (timestamps, confidence scores)
- Telemetry (execution time, file counts)

### Phase 2: LLM Enrichment (OPTIONAL, Copilot Only)

**Purpose**: Add semantic understanding to CLI output

**What to do**:

- Read CLI-generated artifacts (use file reading tools for display only)
- Scan the codebase within `--entry-point` for missing features/behavior and compare against CLI artifacts
- Identify missing features/stories and add reasoning/acceptance criteria (no direct edits to `.specfact/`)
- Suggest confidence adjustments and extract business context
- **CRITICAL**: Generate enrichment report in the exact format specified below (see "Enrichment Report Format" section)

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly (use CLI commands to update)
- ❌ Bypass CLI validation
- ❌ Write to `.specfact/` folder directly (always use CLI)
- ❌ Use direct file manipulation tools for writing (use CLI commands)
- ❌ Deviate from the enrichment report format (will cause parsing failures)

**Output**: Generate enrichment report (Markdown) saved to `.specfact/projects/<bundle-name>/reports/enrichment/` (bundle-specific, Phase 8.5)

**Enrichment Report Format** (REQUIRED for successful parsing):

The enrichment parser expects a specific Markdown format. Follow this structure exactly:

```markdown
# [Bundle Name] Enrichment Report

**Date**: YYYY-MM-DDTHH:MM:SS  
**Bundle**: <bundle-name>

---

## Missing Features

1. **Feature Title** (Key: FEATURE-XXX)
   - Confidence: 0.85
   - Outcomes: outcome1, outcome2, outcome3
   - Stories:
     1. Story title here
        - Acceptance: criterion1, criterion2, criterion3
     2. Another story title
        - Acceptance: criterion1, criterion2

2. **Another Feature** (Key: FEATURE-YYY)
   - Confidence: 0.80
   - Outcomes: outcome1, outcome2
   - Stories:
     1. Story title
        - Acceptance: criterion1, criterion2, criterion3

## Confidence Adjustments

- FEATURE-EXISTING-KEY: 0.90 (reason: improved understanding after code review)

## Business Context

- Priority: High priority feature for core functionality
- Constraint: Must support both REST and GraphQL APIs
- Risk: Potential performance issues with large datasets
```

**Format Requirements**:

1. **Section Header**: Must use `## Missing Features` (case-insensitive, but prefer this exact format)
2. **Feature Format**:
   - Numbered list: `1. **Feature Title** (Key: FEATURE-XXX)`
   - **Bold title** is required (use `**Title**`)
   - **Key in parentheses**: `(Key: FEATURE-XXX)` - must be uppercase, alphanumeric with hyphens/underscores
   - Fields on separate lines with `-` prefix:
     - `- Confidence: 0.85` (float between 0.0-1.0)
     - `- Outcomes: comma-separated or line-separated list`
     - `- Stories:` (required - each feature must have at least one story)
3. **Stories Format**:
   - Numbered list under `Stories:` section: `1. Story title`
   - **Indentation**: Stories must be indented (2-4 spaces) under the feature
   - **Acceptance Criteria**: `- Acceptance: criterion1, criterion2, criterion3`
     - Can be comma-separated on one line
     - Or multi-line (each criterion on new line)
     - Must start with `- Acceptance:`
4. **Optional Sections**:
   - `## Confidence Adjustments`: List existing features with confidence updates
   - `## Business Context`: Priorities, constraints, risks (bullet points)
5. **File Naming**: `<bundle-name>-<timestamp>.enrichment.md` (e.g., `djangogoat-2025-12-23T23-50-00.enrichment.md`)

**Example** (working format):

```markdown
## Missing Features

1. **User Authentication** (Key: FEATURE-USER-AUTHENTICATION)
   - Confidence: 0.85
   - Outcomes: User registration, login, profile management
   - Stories:
     1. User can sign up for new account
        - Acceptance: sign_up view processes POST requests, creates User automatically, user is logged in after signup, redirects to profile page
     2. User can log in with credentials
        - Acceptance: log_in view authenticates username/password, on success user is logged in and redirected, on failure error message is displayed
```

**Common Mistakes to Avoid**:

- ❌ Missing `(Key: FEATURE-XXX)` - parser needs this to identify features
- ❌ Missing `Stories:` section - every feature must have at least one story
- ❌ Stories not indented - parser expects indented numbered lists
- ❌ Missing `- Acceptance:` prefix - acceptance criteria won't be parsed
- ❌ Using bullet points (`-`) instead of numbers (`1.`) for stories
- ❌ Feature title not in bold (`**Title**`) - parser may not extract title correctly

### Phase 3: CLI Artifact Creation (REQUIRED)

```bash
# Use enrichment to update plan via CLI
specfact --no-interactive import from-code [<bundle>] --repo <path> --enrichment <enrichment-report>
```

**Result**: Final artifacts are CLI-generated with validated enrichments

**Note**: If code generation is needed, use the validation loop pattern (see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code))

### Phase 4: OpenAPI Contract Generation (REQUIRED for Sidecar Validation)

**When contracts are generated automatically:**

The `import from-code` command attempts to extract OpenAPI contracts automatically, but **only if**:

1. Features have `source_tracking.implementation_files` (AST-detected features)
2. The OpenAPI extractor finds API endpoints (FastAPI/Flask patterns like `@app.get`, `@router.post`, `@app.route`)

**When contracts are NOT generated:**

Contracts are **NOT** generated automatically when:

- Features were added via enrichment (no `source_tracking.implementation_files`)
- Django applications (Django `path()` patterns are not detected by the extractor)
- Features without API endpoints (models, utilities, middleware, etc.)
- Framework SDKs or libraries without web endpoints

**How to generate contracts manually:**

For features that need OpenAPI contracts (e.g., for sidecar validation with CrossHair), use:

```bash
# Generate contract for a single feature
specfact --no-interactive contract init --bundle <bundle-name> --feature <FEATURE_KEY> --repo <path>

# Example: Generate contracts for all enrichment-added features
specfact --no-interactive contract init --bundle djangogoat-validation --feature FEATURE-USER-AUTHENTICATION --repo .
specfact --no-interactive contract init --bundle djangogoat-validation --feature FEATURE-NOTES-MANAGEMENT --repo .
# ... repeat for each feature that needs a contract
```

**When to apply contract generation:**

- **After Phase 3** (enrichment applied): Check which features have contracts in `.specfact/projects/<bundle>/contracts/`
- **Before sidecar validation**: All features that will be analyzed by CrossHair/Specmatic need OpenAPI contracts
- **For Django apps**: Always generate contracts manually after enrichment, as Django URL patterns are not auto-detected

**Verification:**

```bash
# Check which features have contracts
ls .specfact/projects/<bundle>/contracts/*.yaml

# Compare with total features
ls .specfact/projects/<bundle>/features/*.yaml
```

If the contract count is less than the feature count, generate missing contracts using `contract init`.

## Expected Output

**Success**: Bundle location, report path, summary (features/stories/contracts/relationships)  
**Error**: Missing bundle name or bundle already exists

## Common Patterns

```bash
/specfact.01-import --repo .                    # Uses active plan, auto-enrichment enabled by default
/specfact.01-import --bundle legacy-api --repo . # Auto-enrichment enabled
/specfact.01-import --repo . --no-enrich-for-speckit  # Disable auto-enrichment
/specfact.01-import --repo . --entry-point src/auth/
/specfact.01-import --repo . --enrichment report.md
```

## Context

{ARGS}
