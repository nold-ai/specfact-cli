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

## Interactive Question Presentation

**CRITICAL**: When presenting questions interactively, **ALWAYS** generate and display multiple answer options in a table format. This makes it easier for users to select appropriate answers.

### Answer Options Format

For each question, generate 3-5 reasonable answer options based on:

- **Code analysis**: Review existing patterns, similar features, error handling approaches
- **Domain knowledge**: Best practices, common scenarios, industry standards
- **Business context**: Product requirements, user needs, feature relationships

**Present options in a numbered table with recommended answer:**

```text
Question 1/5
Category: Interaction & UX Flow
Q: What error/empty states should be handled for story STORY-XXX?

Current Plan Settings:
Story STORY-XXX Acceptance: [current acceptance criteria]

Answer Options:
┌─────┬─────────────────────────────────────────────────────────────────┐
│ No. │ Option                                                          │
├─────┼─────────────────────────────────────────────────────────────────┤
│  1  │ Error handling: Invalid input produces clear error messages     │
│     │ Empty states: Missing data shows "No data available" message    │
│     │ Validation: Required fields validated before processing           │
│     │ ⭐ Recommended (based on code analysis)                         │
├─────┼─────────────────────────────────────────────────────────────────┤
│  2  │ Error handling: Network failures retry with exponential backoff │
│     │ Empty states: Show empty state UI with helpful guidance         │
│     │ Validation: Schema-based validation with clear error messages   │
├─────┼─────────────────────────────────────────────────────────────────┤
│  3  │ Error handling: Errors logged to stderr with exit codes (CLI)   │
│     │ Empty states: Sensible defaults when data is missing            │
│     │ Validation: Covered in OpenAPI contract files                   │
├─────┼─────────────────────────────────────────────────────────────────┤
│  4  │ Not applicable - error handling covered in contract files       │
├─────┼─────────────────────────────────────────────────────────────────┤
│  5  │ [Custom answer - type your own]                                 │
└─────┴─────────────────────────────────────────────────────────────────┘

Your answer (1-5, or type custom answer): [1] ⭐ Recommended
```

**CRITICAL**: Always provide a **recommended answer** (marked with ⭐) based on:

- Code analysis (what the actual implementation does)
- Best practices (industry standards, common patterns)
- Domain knowledge (what makes sense for this feature)

The recommendation helps less-experienced users make informed decisions.

### Guidelines for Answer Options

- **Option 1-3**: Specific, actionable options based on code analysis and domain knowledge
- **Option 4**: "Not applicable" or "Covered elsewhere" when appropriate
- **Option 5**: Always include "[Custom answer - type your own]" as the last option
- **Base options on research**: Review codebase, similar features, existing patterns
- **Make options specific**: Avoid generic responses - be concrete and actionable
- **Use numbered selection**: Allow users to select by number (1-5) or letter (A-E)
- **⭐ Always provide a recommended answer**: Mark one option as recommended (⭐) based on:
  - Code analysis (what the actual implementation does or should do)
  - Best practices (industry standards, common patterns)
  - Domain knowledge (what makes sense for this specific feature)
  - The recommendation helps less-experienced users make informed decisions

## Parameters

### Target/Input

- `bundle NAME` (optional argument) - Project bundle name (e.g., legacy-api, auth-module). Default: active plan (set via `plan select`)
- `--category CATEGORY` - Focus on specific taxonomy category. Default: None (all categories)

### Output/Results

- `--list-questions` - Output questions in JSON format. Default: False
- `--output-questions PATH` - Save questions directly to file (JSON format). Use with `--list-questions` to save instead of stdout. Default: None
- `--list-findings` - Output all findings in structured format. Default: False
- `--output-findings PATH` - Save findings directly to file (JSON/YAML format). Use with `--list-findings` to save instead of stdout. Default: None
- `--findings-format FORMAT` - Output format: json, yaml, or table. Default: json for non-interactive, table for interactive

### Behavior/Options

- `--no-interactive` - Non-interactive mode (for CI/CD). Default: False (interactive mode)
- `--answers JSON` - JSON object with question_id -> answer mappings. Default: None
- `--auto-enrich` - Automatically enrich vague acceptance criteria using PlanEnricher (same enrichment logic as `import from-code`). Default: False (opt-in for review, but import has auto-enrichment enabled by default)

**Important**: `--auto-enrich` will **NOT** resolve partial findings such as:

- Missing error handling specifications ("Interaction & UX Flow" category)
- Vague acceptance criteria requiring domain knowledge ("Completion Signals" category)
- Business context questions requiring human judgment

For these cases, use the **export-to-file → LLM reasoning → import-from-file** workflow (see Step 4).

### Advanced/Configuration

- `--max-questions INT` - Maximum questions per session. Default: 5 (range: 1-10)

  **Important**: This limits the number of questions asked per review session, not the total number of available questions. If there are more questions than the limit, you may need to run the review multiple times to answer all questions. Each session will ask different questions (avoiding duplicates from previous sessions).

## Workflow

### Step 1: Parse Arguments

- Extract bundle name (defaults to active plan if not specified)
- Extract optional parameters (max-questions, category, etc.)

### Step 2: Execute CLI to Export Questions

**CRITICAL**: Always use `/tmp/` for temporary artifacts to avoid polluting the codebase. Never create temporary files in the project root.

**CRITICAL**: Question IDs are generated per run and can change if you re-run review.  
**Do not** re-run `plan review` between exporting questions and applying answers. Always answer using the exact exported questions file for that session.

**Note**: The `--max-questions` parameter (default: 5) limits the number of questions per session, not the total number of available questions. If there are more questions available, you may need to run the review multiple times to answer all questions. Each session will ask different questions (avoiding duplicates from previous sessions).

**Export questions to file for LLM reasoning:**

```bash
# Export questions to file (REQUIRED for LLM enrichment workflow)
# Use /tmp/ to avoid polluting the codebase
specfact plan review [<bundle-name>] --list-questions --output-questions /tmp/questions.json --no-interactive
# Uses active plan if bundle not specified
```

**Optional: Get findings for comprehensive analysis:**

```bash
# Get findings (saves to stdout - can redirect to /tmp/)
# Use /tmp/ to avoid polluting the codebase
# Option 1: Redirect output (includes CLI banner - not recommended)
specfact plan review [<bundle-name>] --list-findings --findings-format json --no-interactive > /tmp/findings.json

# Option 2: Save directly to file (recommended - clean JSON only)
specfact plan review [<bundle-name>] --list-findings --output-findings /tmp/findings.json --no-interactive
```

**Note**: The `--output-questions` option saves questions directly to a file, avoiding the need for complex JSON parsing. The ambiguity scanner now recognizes the simplified format (e.g., "Must verify X works correctly (see contract examples)") as valid and will not flag it as vague.

**Important**: Always use `/tmp/` for temporary files (`questions.json`, `findings.json`, etc.) to keep the project root clean and avoid accidental commits of temporary artifacts.

### Step 3: LLM Reasoning and Answer Generation

**CRITICAL**: For partial findings (missing error handling, vague acceptance criteria, business context), `--auto-enrich` will **NOT** resolve them. You must use LLM reasoning.

**CRITICAL WORKFLOW**: Present questions with answer options **IN THE CHAT**, wait for user selection, then add selected answers to file.

**Workflow:**

1. **Read the exported questions file** (`/tmp/questions.json`):

   - Review all questions in the file
   - Identify which questions require code/feature analysis
   - Determine which questions need domain knowledge or business context

2. **Research codebase and features** (as needed):

   - For error handling questions: Check existing error handling patterns in the codebase
   - For acceptance criteria questions: Review related features and stories
   - For business context questions: Review `idea.yaml`, `product.yaml`, and related documentation

3. **Present questions with answer options IN THE CHAT** (REQUIRED):

   **DO NOT add answers to the file yet!** Present each question with answer options in the chat conversation and wait for user selection.

   For each question:

   - **Generate 3-5 reasonable answer options** based on:
     - Code analysis (existing patterns, similar features)
     - Domain knowledge (best practices, common scenarios)
     - Business context (product requirements, user needs)
   - **Present options in a table format** in the chat with numbered choices:

   ```text
   Question 1/5
   Category: Interaction & UX Flow
   Q: What error/empty states should be handled for story STORY-XXX?

   Current Plan Settings:
   Story STORY-XXX Acceptance: [current acceptance criteria]

   Answer Options:
   ┌─────┬─────────────────────────────────────────────────────────────────┐
   │ No. │ Option                                                          │
   ├─────┼─────────────────────────────────────────────────────────────────┤
   │  1  │ Error handling: Invalid input produces clear error messages     │
   │     │ Empty states: Missing data shows "No data available" message    │
   │     │ Validation: Required fields validated before processing         │
   │     │ ⭐ Recommended (based on code analysis)                         │
   ├─────┼─────────────────────────────────────────────────────────────────┤
   │  2  │ Error handling: Network failures retry with exponential backoff │
   │     │ Empty states: Show empty state UI with helpful guidance         │
   │     │ Validation: Schema-based validation with clear error messages   │
   ├─────┼─────────────────────────────────────────────────────────────────┤
   │  3  │ Error handling: Errors logged to stderr with exit codes (CLI)   │
   │     │ Empty states: Sensible defaults when data is missing            │
   │     │ Validation: Covered in OpenAPI contract files                   │
   ├─────┼─────────────────────────────────────────────────────────────────┤
   │  4  │ Not applicable - error handling covered in contract files       │
   ├─────┼─────────────────────────────────────────────────────────────────┤
   │  5  │ [Custom answer - type your own]                                 │
   └─────┴─────────────────────────────────────────────────────────────────┘

   Your answer (1-5, or type custom answer): [1] ⭐ Recommended
   ```

   - **Wait for user to select an answer** (number 1-5, letter A-E, or custom text)
   - **Option 5 (or last option)** should always be "[Custom answer - type your own]" to allow free-form input
   - **Base options on code analysis** - review similar features, existing error handling patterns, and domain knowledge
   - **Make options specific and actionable** - not generic responses
   - **⭐ Always provide a recommended answer** - mark one option as recommended (⭐) based on code analysis, best practices, and domain knowledge. This helps less-experienced users make informed decisions.
   - **Present one question at a time** and wait for user selection before moving to the next

4. **After user has selected all answers**:

   - **THEN** export the selected answers to a separate file `/tmp/answers.json`
   - Map user selections to the actual answer text (if user selected option 1, use the text from option 1)
   - If user selected a custom answer, use that text directly
   - **Export format**: Create a JSON object with `question_id -> answer` mappings
   - **DO NOT** add answers to the file until user has selected all answers
   - **CRITICAL**: Export answers to `/tmp/answers.json` (not `/tmp/questions.json`) for CLI import

**Example `/tmp/questions.json` structure:**

```json
{
  "questions": [
    {
      "id": "Q001",
      "category": "Interaction & UX Flow",
      "question": "What error/empty states should be handled for story STORY-XXX?",
      "related_sections": ["features.FEATURE-XXX.stories.STORY-XXX.acceptance"]
    }
  ],
  "total": 5
}
```

**Example `/tmp/answers.json` structure (exported after user selections):**

```json
{
  "Q001": "Error handling should include: network failures (retry with exponential backoff), invalid input (clear validation messages), empty results (show 'No data available' message), timeout errors (show progress indicator and allow cancellation). Based on analysis of similar features in the codebase.",
  "Q002": "Answer for question 2 based on code review..."
}
```

**CRITICAL**: Export answers to `/tmp/answers.json` (separate file), not to `/tmp/questions.json`. The CLI expects a file path for `--answers`, not a JSON string extracted from the questions file.

### Step 4: Apply Enrichment via CLI

**REQUIRED workflow for partial findings:**

1. **Export questions to file** (already done in Step 2):

   ```bash
   # Use /tmp/ to avoid polluting the codebase
   specfact plan review [<bundle-name>] --list-questions --output-questions /tmp/questions.json --no-interactive
   ```

2. **LLM reasoning and user selection** (Step 3):

   - LLM presents questions with answer options **IN THE CHAT**
   - User selects answers (1-5, A-E, or custom text)
   - **After user has selected all answers**, LLM adds selected answers to `/tmp/questions.json`

3. **Import answers via CLI** (after user selections are complete):

   ```bash
   # Import answers from exported file
   # Use /tmp/ to avoid polluting the codebase
   specfact plan review [<bundle-name>] --answers /tmp/answers.json --no-interactive
   ```

**CRITICAL**:

- Do NOT add answers to the file until the user has selected all answers
- Present questions in chat, wait for selections
- Export answers to `/tmp/answers.json` (separate file, not `/tmp/questions.json`)
- Import via CLI using the file path: `--answers /tmp/answers.json`

**Alternative approaches** (for non-partial findings only):

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

- **For partial findings**: Always use Option A (export → LLM reasoning → import)
- **For business context only**: Option B (update-idea) may be sufficient
- **For bundle regeneration**: Only use Option C if you need to regenerate the bundle
- **CRITICAL**: Never manually edit `.specfact/` files directly - always use CLI commands
  - This includes `idea.yaml`, `product.yaml`, feature files, story files, etc.
  - Even if a file doesn't exist yet, use CLI commands to create it (e.g., `plan update-idea` will create `idea.yaml` if needed)
  - Direct file modification bypasses validation and can cause inconsistencies

- **Preferred**: Use Option A (answers) or Option B (update-idea) for most cases
- Only use Option C if you need to regenerate the bundle
- **CRITICAL**: Never manually edit `.specfact/` files directly - always use CLI commands
  - This includes `idea.yaml`, `product.yaml`, feature files, story files, etc.
  - Even if a file doesn't exist yet, use CLI commands to create it (e.g., `plan update-idea` will create `idea.yaml` if needed)
  - Direct file modification bypasses validation and can cause inconsistencies

### Step 5: Present Results

- Display Q&A, sections touched, coverage summary (initial/updated)
- Note: Clarifications don't affect hash (stable across review sessions)
- If enrichment report was created, summarize what was addressed

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

- Execute CLI first - never create artifacts directly
- Use `--no-interactive` flag in CI/CD environments
- **NEVER modify `.specfact/` files directly** - always use CLI commands
  - ❌ **DO NOT** edit `idea.yaml`, `product.yaml`, feature files, or any other artifacts directly
  - ❌ **DO NOT** create new artifact files manually (even if they don't exist yet)
  - ✅ **DO** use CLI commands: `plan update-idea`, `plan update-feature`, `plan update-story`, etc.
  - ✅ **DO** use CLI commands to create new artifacts: `plan init`, `plan add-feature`, etc.
- Use CLI output as grounding for validation
- Code generation requires LLM (only via AI IDE slash prompts, not CLI-only)

**Important**: If an artifact file doesn't exist yet, use the appropriate CLI command to create it. Never create or modify `.specfact/` files manually, as this bypasses validation and can cause inconsistencies.

## Dual-Stack Workflow (Copilot Mode)

When in copilot mode, follow this three-phase workflow:

### Phase 1: CLI Grounding (REQUIRED)

```bash
# Option 1: Get findings (redirect to /tmp/ to avoid polluting codebase)
# Option 1: Save findings directly to file (recommended - clean JSON only)
specfact plan review [<bundle-name>] --list-findings --output-findings /tmp/findings.json --no-interactive

# Option 2: Get questions and save directly to /tmp/ (recommended - avoids JSON parsing)
specfact plan review [<bundle-name>] --list-questions --output-questions /tmp/questions.json --no-interactive
```

**Capture**:

- CLI-generated findings (ambiguities, missing information)
- Questions saved directly to file (no complex parsing needed)
- Structured JSON/YAML output for bulk processing
- Metadata (timestamps, confidence scores)

**Note**: Use `--output-questions` to save questions directly to a file. This avoids the need for complex on-the-fly Python code to extract JSON from CLI output.

**CRITICAL**: Always use `/tmp/` for temporary artifacts (`questions.json`, `findings.json`, etc.) to avoid polluting the codebase and prevent accidental commits of temporary files.

### Phase 2: LLM Enrichment (REQUIRED for Partial Findings)

**Purpose**: Add semantic understanding and domain knowledge to CLI findings

**CRITICAL**: `--auto-enrich` will **NOT** resolve partial findings. LLM reasoning is **REQUIRED** for:

- Missing error handling specifications ("Interaction & UX Flow" category)
- Vague acceptance criteria requiring domain knowledge ("Completion Signals" category)
- Business context questions requiring human judgment

**What to do**:

0. **Grounding rule**:
   - Treat CLI-exported questions as the source of truth; consult codebase/docs only to answer them (do not invent new artifacts)
   - **Feature/Story Completeness note**: Answers here are clarifications only. They do **NOT** create stories.  
     For missing stories, use `specfact plan add-story` (or `plan update-story --batch-updates` if stories already exist).

1. **Read exported questions file** (`/tmp/questions.json`):
   - Review all questions and their categories
   - Identify questions requiring code/feature analysis
   - Determine questions needing domain knowledge

2. **Research codebase**:
   - For error handling: Analyze existing error handling patterns
   - For acceptance criteria: Review related features and stories
   - For business context: Review `idea.yaml`, `product.yaml`, documentation

3. **Present questions with answer options IN THE CHAT** (REQUIRED):

   **DO NOT add answers to the file yet!** Present each question with answer options in the chat conversation.

   **For each question:**

   - Generate 3-5 reasonable options based on code analysis and domain knowledge
   - Present in a numbered table (1-5) or lettered table (A-E) **IN THE CHAT**
   - Include a "[Custom answer]" option as the last choice
   - Make options specific and actionable, not generic
   - **Wait for user to select an answer** before moving to the next question

   **Example format (present in chat):**

   ```text
   Question 1/5
   Category: Interaction & UX Flow
   Q: What error/empty states should be handled for story STORY-XXX?

   Answer Options:
   ┌─────┬─────────────────────────────────────────────────────────────┐
   │ No. │ Option                                                      │
   ├─────┼─────────────────────────────────────────────────────────────┤
   │  1  │ [Option based on code analysis - specific and actionable]   │
   │     │ ⭐ Recommended (based on code analysis)                      │
   │  2  │ [Option based on best practices - domain knowledge]         │
   │  3  │ [Option based on similar features - pattern matching]       │
   │  4  │ [Not applicable / covered elsewhere]                        │
   │  5  │ [Custom answer - type your own]                             │
   └─────┴─────────────────────────────────────────────────────────────┘

   Your answer (1-5, or type custom answer): [1] ⭐ Recommended
   ```

4. **After user has selected all answers**:

   - **THEN** add the selected answers to `/tmp/questions.json` in the `answers` object
   - Map user selections (1-5) to the actual answer text from the options
   - If user selected a custom answer, use that text directly
   - **DO NOT** add answers to the file until user has selected all answers

**What NOT to do**:

- ❌ Use `--auto-enrich` expecting it to resolve partial findings
- ❌ Create YAML/JSON artifacts directly (even if they don't exist yet)
- ❌ Modify CLI artifacts directly (use CLI commands to update)
- ❌ Edit `idea.yaml`, `product.yaml`, feature files, or story files manually
- ❌ Create new artifact files manually - use CLI commands instead
- ❌ Bypass CLI validation
- ❌ Write to `.specfact/` folder directly (always use CLI)
- ❌ Create temporary files in project root (always use `/tmp/`)

**Output**: Updated `/tmp/questions.json` file with `answers` object populated

### Phase 3: CLI Artifact Creation (REQUIRED)

**For partial findings (REQUIRED workflow):**

```bash
# Import answers from /tmp/questions.json file
# Use /tmp/ to avoid polluting the codebase
specfact plan review [<bundle-name>] --answers "$(jq -c '.answers' /tmp/questions.json)" --no-interactive
```

**For non-partial findings only:**

```bash
# Use auto-enrich for simple vague criteria (not partial findings)
specfact plan review [<bundle-name>] --auto-enrich --no-interactive

# Or use batch updates for feature updates
specfact plan update-feature [--bundle <name>] --batch-updates <updates.json> --no-interactive
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
/specfact.03-review --list-findings --output-findings /tmp/findings.json  # Save findings to file (clean JSON)

# Interactive review
/specfact.03-review                                    # Uses active plan (default: 5 questions per session)
/specfact.03-review legacy-api                         # Specific bundle
/specfact.03-review --max-questions 3                  # Limit questions per session (may need multiple runs)
/specfact.03-review --category "Functional Scope"      # Focus category
/specfact.03-review --max-questions 10                 # Ask more questions per session (up to 10)

# Non-interactive with answers
/specfact.03-review --answers '{"Q001": "answer"}'     # Provide answers directly
/specfact.03-review --list-questions                   # Output questions as JSON to stdout
/specfact.03-review --list-questions --output-questions /tmp/questions.json  # Save questions to /tmp/

# Auto-enrichment (NOTE: Will NOT resolve partial findings - use export/LLM/import workflow instead)
/specfact.03-review --auto-enrich                     # Auto-enrich simple vague criteria only

# Recommended workflow for partial findings (use /tmp/ to avoid polluting codebase)
/specfact.03-review --list-questions --output-questions /tmp/questions.json  # Export questions (default: 5 per session)
# [LLM reasoning: present questions in chat, wait for user selections, then export answers]
/specfact.03-review --answers /tmp/answers.json                               # Import answers from file
# [Repeat if more questions available - each session asks different questions]
/specfact.03-review --list-questions --output-questions /tmp/questions.json    # Export next batch
/specfact.03-review --answers /tmp/answers.json                               # Import next batch
```

## Enrichment Workflow

**CRITICAL**: `--auto-enrich` will **NOT** resolve partial findings such as:

- Missing error handling specifications ("Interaction & UX Flow" category)
- Vague acceptance criteria requiring domain knowledge ("Completion Signals" category)
- Business context questions requiring human judgment

**For partial findings, use this REQUIRED workflow:**

1. **Export questions to file** (use `/tmp/` to avoid polluting codebase):

   ```bash
   specfact plan review [<bundle-name>] --list-questions --output-questions /tmp/questions.json --no-interactive
   ```

2. **Get findings** (optional, for comprehensive analysis - use `/tmp/`):

   ```bash
   specfact plan review [<bundle-name>] --list-findings --output-findings /tmp/findings.json --no-interactive
   ```

3. **LLM reasoning and user selection** (REQUIRED for partial findings):

   **CRITICAL**: Present questions with answer options **IN THE CHAT**, wait for user selections, then add selected answers to file.

   - Read `/tmp/questions.json` file
   - Research codebase for error handling patterns, feature relationships, domain knowledge
   - **Present each question with answer options IN THE CHAT** (see Step 3 for format)
   - **Wait for user to select answers** (1-5, A-E, or custom text)
   - **After user has selected all answers**, export selected answers to `/tmp/answers.json` (separate file)
   - Map user selections to actual answer text (if user selected option 1, use the text from option 1)
   - **Export format**: Create a JSON object with `question_id -> answer` mappings
   - **DO NOT** export answers to file until user has selected all answers
   - **CRITICAL**: Export to `/tmp/answers.json` (not `/tmp/questions.json`) for CLI import

4. **Import answers via CLI** (after user selections are complete):

   ```bash
   # Import answers from exported file
   specfact plan review [<bundle-name>] --answers /tmp/answers.json --no-interactive
   ```

   **CRITICAL**: Use the file path `/tmp/answers.json` (not a JSON string extracted from `/tmp/questions.json`)

5. **Verify**: Run `plan review` again to confirm improvements

   **Important**: The `--max-questions` parameter (default: 5) limits questions per session, not the total available. If there are more questions, repeat the workflow (Steps 2-4) until all are answered. Each session asks different questions, avoiding duplicates from previous sessions.

**For non-partial findings only:**

- **During import**: Auto-enrichment happens automatically (enabled by default)
- **After import**: Use `specfact plan review --auto-enrich` for simple vague criteria
- **Note**: The scanner now recognizes simplified format (e.g., "Must verify X works correctly (see contract examples)") as valid

**Alternative approaches** (for business context only):

- Use `plan update-idea` to update idea fields directly
- If bundle needs regeneration, use `import from-code --enrichment`

**Note on OpenAPI Contracts:**

After applying enrichment or review updates, check if features need OpenAPI contracts for sidecar validation:

- Features added via enrichment typically don't have contracts (no `source_tracking`)
- Django applications require manual contract generation (Django URL patterns not auto-detected)
- Use `specfact contract init --bundle <bundle> --feature <FEATURE_KEY>` to generate contracts for features that need them

**Enrichment Report Format** (for `import from-code --enrichment`):

When generating enrichment reports for use with `import from-code --enrichment`, follow this exact format:

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

## Context

{ARGS}
