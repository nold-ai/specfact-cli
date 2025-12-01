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
- `--auto-enrich` - Automatically enrich vague acceptance criteria. Default: False

### Advanced/Configuration

- `--max-questions INT` - Maximum questions per session. Default: 5 (range: 1-10)

## Workflow

### Step 1: Parse Arguments

- Extract bundle name (defaults to active plan if not specified)
- Extract optional parameters (max-questions, category, etc.)

### Step 2: Execute CLI

```bash
specfact plan review [<bundle-name>] [--max-questions <n>] [--category <category>] [--list-questions] [--list-findings] [--answers JSON]
# Uses active plan if bundle not specified
```

### Step 3: Present Results

- Display Q&A, sections touched, coverage summary (initial/updated)
- Note: Clarifications don't affect hash (stable across review sessions)

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
/specfact.03-review                                    # Uses active plan
/specfact.03-review legacy-api                         # Specific bundle
/specfact.03-review --max-questions 3                  # Limit questions
/specfact.03-review --category "Functional Scope"      # Focus category
/specfact.03-review --list-questions                   # JSON output
/specfact.03-review --auto-enrich                     # Auto-enrichment
```

## Context

{ARGS}
