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
- `--auto-enrich` - Automatically enrich vague acceptance criteria. Default: False

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

#### Option B: Apply enrichment via import (only if bundle needs regeneration)

```bash
specfact import from-code [<bundle-name>] --repo . --enrichment enrichment-report.md
```

**Note**: Only use Option B if you need to regenerate the bundle. For most cases, use Option A or manually update `idea.yaml` based on enrichment recommendations.

### Step 5: Present Results

- Display Q&A, sections touched, coverage summary (initial/updated)
- Note: Clarifications don't affect hash (stable across review sessions)
- If enrichment report was created, summarize what was addressed

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:** Execute CLI first, use `--no-interactive` in CI/CD, never modify `.specfact/` directly, use CLI output as grounding.

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

**Typical workflow when enrichment is needed:**

1. **Get findings**: `specfact plan review --list-findings --findings-format json`
2. **Analyze findings**: Review missing information (target_users, value_hypothesis, etc.)
3. **Create enrichment report**: Write Markdown file addressing findings
4. **Apply enrichment**:
   - **Preferred**: Use enrichment to create `--answers` JSON and run `plan review --answers`
   - **Alternative**: If bundle needs regeneration, use `import from-code --enrichment`
5. **Verify**: Run `plan review` again to confirm improvements

## Context

{ARGS}
