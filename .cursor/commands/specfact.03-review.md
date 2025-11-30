# SpecFact Review Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Review project bundle to identify and resolve ambiguities, missing information, and unclear requirements. Asks targeted questions to make the bundle ready for promotion through development stages.

**When to use:**

- After creating or importing a plan bundle
- Before promoting to review/approved stages
- When plan needs clarification or enrichment

**Quick Example:**

```bash
/specfact.03-review legacy-api
/specfact.03-review legacy-api --max-questions 3 --category "Functional Scope"
```

## Parameters

### Target/Input

- `bundle NAME` (required argument) - Project bundle name (e.g., legacy-api, auth-module)
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

- Extract bundle name (required)
- Extract optional parameters (max-questions, category, etc.)

### Step 2: Execute CLI

```bash
# Interactive review
specfact plan review <bundle-name> [--max-questions <n>] [--category <category>]

# Non-interactive with answers
specfact plan review <bundle-name> --no-interactive --answers '{"Q001": "answer1", "Q002": "answer2"}'

# List questions only
specfact plan review <bundle-name> --list-questions

# List findings
specfact plan review <bundle-name> --list-findings --findings-format json
```

### Step 3: Present Results

- Display questions asked and answers provided
- Show sections touched by clarifications
- Present coverage summary by category
- Suggest next steps (promotion, additional review)

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

1. **ALWAYS execute CLI first**: Run `specfact plan review` before any analysis
2. **ALWAYS use non-interactive mode for CI/CD**: Use `--no-interactive` flag in Copilot environments
3. **NEVER modify .specfact folder directly**: All operations must go through CLI
4. **NEVER create YAML/JSON directly**: All plan updates must be CLI-generated
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate it

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
# Interactive review
/specfact.03-review legacy-api

# Review with question limit
/specfact.03-review legacy-api --max-questions 3

# Review specific category
/specfact.03-review legacy-api --category "Functional Scope"

# Non-interactive with answers
/specfact.03-review legacy-api --no-interactive --answers '{"Q001": "answer1", "Q002": "answer2"}'

# List questions for LLM processing
/specfact.03-review legacy-api --list-questions

# List all findings
/specfact.03-review legacy-api --list-findings --findings-format json

# Auto-enrich mode
/specfact.03-review legacy-api --auto-enrich
```

## Context

{ARGS}
