---
description: Review project bundle to identify ambiguities, resolve gaps, and prepare for promotion.
---

# SpecFact Review Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Review project bundle to identify/resolve ambiguities and missing information. Asks targeted questions for promotion readiness.

**When to use:** After import/creation, before promotion, when clarification needed.

**Quick:** `/specfact.03-review` (uses active plan) or `/specfact.03-review legacy-api`

## Parameters

### Target/Input

- `bundle NAME` (optional argument) - Project bundle name (e.g., legacy-api, auth-module). Default: active plan (set via `plan select`)
- `--category CATEGORY` - Focus on specific taxonomy category. Default: None (all categories)

### Output/Results

- `--list-questions` - Output questions in JSON format. Default: False
- `--list-findings` - Output all findings in structured format. Default: False
- `--findings-format FORMAT` - Output format: json, yaml, or table. Default: json for non-interactive, table for interactive

### Behavior/Options

- `--no-interactive` - Non-interactive mode (for CI/CD). Default: False (interactive mode)
- `--answers JSON` - JSON object with question_id -> answer mappings. Default: None
- `--auto-enrich` - Automatically enrich vague acceptance criteria using PlanEnricher (same enrichment logic as `import from-code`). Default: False (opt-in for review, but import has auto-enrichment enabled by default)

### Advanced/Configuration

- `--max-questions INT` - Maximum questions per session. Default: 5 (range: 1-10)

## Workflow

### Step 1: Parse Arguments

- Extract bundle name (defaults to active plan if not specified)
- Extract optional parameters (max-questions, category, etc.)

### Step 2: Execute CLI to Get Findings

**First, get findings to understand what needs enrichment:**

```bash
specfact plan review [<bundle-name>] --list-findings --findings-format json
# Uses active plan if bundle not specified
```

This outputs all ambiguities and missing information in structured format.

### Step 3: Create Enrichment Report (if needed)

Based on the findings, create a Markdown enrichment report that addresses:

- **Business Context**: Priorities, constraints, unknowns
- **Confidence Adjustments**: Feature confidence score updates (if needed)
- **Missing Features**: New features to add (if any)
- **Manual Updates**: Guidance for updating `idea.yaml` fields like `target_users`, `value_hypothesis`, `narrative`

**Enrichment Report Format:**

```markdown
## Business Context

### Priorities
- Priority 1
- Priority 2

### Constraints
- Constraint 1
- Constraint 2

### Unknowns
- Unknown 1
- Unknown 2

## Confidence Adjustments

FEATURE-KEY → 0.95
FEATURE-OTHER → 0.8

## Missing Features

(If any features are missing)

## Recommendations for Manual Updates

### idea.yaml Updates Required

**target_users:**
- Primary: [description]
- Secondary: [description]

**value_hypothesis:**
[Value proposition]

**narrative:**
[Improved narrative]
```

### Step 4: Apply Enrichment

#### Option A: Use enrichment to answer review questions

Create answers JSON from enrichment report and use with review:

```bash
specfact plan review [<bundle-name>] --answers '{"Q001": "answer1", "Q002": "answer2"}'
```

#### Option B: Update idea fields directly via CLI

Use `plan update-idea` to update idea fields from enrichment recommendations:

```bash
specfact plan update-idea --bundle [<bundle-name>] --value-hypothesis "..." --narrative "..." --target-users "..."
```

#### Option C: Apply enrichment via import (only if bundle needs regeneration)

```bash
specfact import from-code [<bundle-name>] --repo . --enrichment enrichment-report.md
```

**Note:**

- **Preferred**: Use Option A (answers) or Option B (update-idea) for most cases
- Only use Option C if you need to regenerate the bundle
- Never manually edit `.specfact/` files directly - always use CLI commands

### Step 5: Present Results

- Display Q&A, sections touched, coverage summary (initial/updated)
- Note: Clarifications don't affect hash (stable across review sessions)
- If enrichment report was created, summarize what was addressed

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

- Execute CLI first - never create artifacts directly
- Use `--no-interactive` flag in CI/CD environments
- Never modify `.specfact/` directly
- Use CLI output as grounding for validation
- Code generation requires LLM (only via AI IDE slash prompts, not CLI-only)

## Dual-Stack Workflow (Copilot Mode)

When in copilot mode, follow this three-phase workflow:

### Phase 1: CLI Grounding (REQUIRED)

```bash
# Execute CLI to get structured output
specfact plan review [<bundle-name>] --list-findings --findings-format json --no-interactive
```

**Capture**:

- CLI-generated findings (ambiguities, missing information)
- Structured JSON/YAML output for bulk processing
- Metadata (timestamps, confidence scores)

### Phase 2: LLM Enrichment (OPTIONAL, Copilot Only)

**Purpose**: Add semantic understanding to CLI findings

**What to do**:

- Read CLI-generated findings (use file reading tools for display only)
- Research codebase for additional context
- Generate enrichment report or batch update file
- Address ambiguities with business context

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly (use CLI commands to update)
- ❌ Bypass CLI validation
- ❌ Write to `.specfact/` folder directly (always use CLI)

**Output**: Generate enrichment report (Markdown) or batch update JSON/YAML file

### Phase 3: CLI Artifact Creation (REQUIRED)

```bash
# Use enrichment to update plan via CLI
specfact plan update-feature [--bundle <name>] --batch-updates <updates.json> --no-interactive
# Or use auto-enrich:
specfact plan review [<bundle-name>] --auto-enrich --no-interactive
```

**Result**: Final artifacts are CLI-generated with validated enrichments

**Note**: If code generation is needed, use the validation loop pattern (see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code))

## Expected Output

### Success

```text
✓ Review complete: 5 question(s) answered

Project Bundle: legacy-api
Questions Asked: 5

Sections Touched:
  • idea.narrative
  • features[FEATURE-001].acceptance
  • features[FEATURE-002].outcomes

Coverage Summary:
  ✅ Functional Scope: clear
  ✅ Technical Constraints: clear
  ⚠️ Business Context: partial
```

### Error (Missing Bundle)

```text
✗ Project bundle 'legacy-api' not found
Create one with: specfact plan init legacy-api
```

## Common Patterns

```bash
# Get findings first
/specfact.03-review --list-findings                    # List all findings
/specfact.03-review --list-findings --findings-format json  # JSON format for enrichment

# Interactive review
/specfact.03-review                                    # Uses active plan
/specfact.03-review legacy-api                         # Specific bundle
/specfact.03-review --max-questions 3                  # Limit questions
/specfact.03-review --category "Functional Scope"      # Focus category

# Non-interactive with answers
/specfact.03-review --answers '{"Q001": "answer"}'     # Provide answers directly
/specfact.03-review --list-questions                   # Output questions as JSON

# Auto-enrichment
/specfact.03-review --auto-enrich                     # Auto-enrich vague criteria
```

## Enrichment Workflow

**Note**: Import command (`specfact import from-code`) has **auto-enrichment enabled by default** using PlanEnricher. Review command requires explicit `--auto-enrich` flag.

**Typical workflow when enrichment is needed:**

1. **Get findings**: `specfact plan review --list-findings --findings-format json`
2. **Analyze findings**: Review missing information (target_users, value_hypothesis, etc.)
3. **Apply automatic enrichment** (if needed):
   - **During import**: Auto-enrichment happens automatically (enabled by default)
   - **After import**: Use `specfact plan review --auto-enrich` to enhance vague criteria
4. **Create enrichment report** (for business context, confidence adjustments, missing features): Write Markdown file addressing findings
5. **Apply manual enrichment**:
   - **Preferred**: Use enrichment to create `--answers` JSON and run `plan review --answers`
   - **Alternative**: Use `plan update-idea` to update idea fields directly
   - **Last resort**: If bundle needs regeneration, use `import from-code --enrichment`
6. **Verify**: Run `plan review` again to confirm improvements

## Context

{ARGS}
