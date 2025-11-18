---
description: Import plan bundle from existing codebase (one-way import from repository).
---
# SpecFact Import From Code Command (brownfield integration on existing projects)

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Interactive Flow

**Step 1**: Check if `--name` is provided in user input or arguments.

- **If provided**: Use the provided name (it will be automatically sanitized)
- **If missing**: **Ask the user interactively** for a meaningful plan name:
  - Prompt: "What name would you like to use for this plan? (e.g., 'API Client v2', 'User Authentication', 'Payment Processing')"
  - Wait for user response
  - The name will be automatically sanitized (lowercased, spaces/special chars removed) for filesystem persistence
  - Example: User provides "API Client v2" → saved as `api-client-v2.2025-11-04T23-19-31.bundle.yaml`

**Step 2**: Proceed with import using the plan name (either provided or obtained from user).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact import from-code` before any analysis - execute the CLI command before any other operations
2. **NEVER write code**: Do not implement import logic - the CLI handles this
3. **NEVER create YAML/JSON directly**: All artifacts must be CLI-generated
4. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata - use it, don't bypass its validation
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate or recreate it - use the CLI output as the source of truth
6. **NEVER manipulate internal code**: Do NOT use Python code to directly modify PlanBundle objects, Feature objects, or any internal data structures. The CLI is THE interface - use it exclusively.
7. **No internal knowledge required**: You should NOT need to know about internal implementation details (PlanBundle model, Feature class, EnrichmentParser, etc.). All operations must be performed via CLI commands.
8. **NEVER read artifacts directly**: Do NOT read plan bundle files directly to extract information unless for enrichment analysis (Phase 2). Use CLI commands to get plan information. After enrichment, always apply via CLI using `--enrichment` flag.

### What Happens If You Don't Follow This

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures
- ❌ Works only in Copilot mode, fails in CI/CD
- ❌ Breaks when CLI internals change
- ❌ Requires knowledge of internal code structure

### Available CLI Commands for Plan Updates

**For updating features** (after enrichment):

- `specfact plan update-feature --key <key> --title <title> --outcomes <outcomes> --acceptance <acceptance> --constraints <constraints> --confidence <confidence> --draft <true/false> --plan <path>`
  - Updates existing feature metadata (title, outcomes, acceptance criteria, constraints, confidence, draft status)
  - Works in CI/CD, Copilot, and interactive modes
  - Example: `specfact plan update-feature --key FEATURE-001 --title "New Title" --outcomes "Outcome 1, Outcome 2"`

**For adding features**:

- `specfact plan add-feature --key <key> --title <title> --outcomes <outcomes> --acceptance <acceptance> --plan <path>`

**For adding stories**:

- `specfact plan add-story --feature <feature-key> --key <story-key> --title <title> --acceptance <acceptance> --story-points <points> --value-points <points> --plan <path>`

**❌ FORBIDDEN**: Direct Python code manipulation like:

```python
# ❌ NEVER DO THIS:
from specfact_cli.models.plan import PlanBundle, Feature
from specfact_cli.generators.plan_generator import PlanGenerator
plan_bundle.features[0].title = "New Title"  # Direct manipulation
generator.generate(plan_bundle, plan_path)  # Bypassing CLI
```

**✅ CORRECT**: Use CLI commands:

```bash
# ✅ ALWAYS DO THIS:
specfact plan update-feature --key FEATURE-001 --title "New Title" --plan <path>
```

## ⏸️ Wait States: User Input Required

**When user input is required, you MUST wait for the user's response.**

### Wait State Rules

1. **Never assume**: If input is missing, ask and wait
2. **Never continue**: Do not proceed until user responds
3. **Be explicit**: Clearly state what information you need
4. **Provide options**: Give examples or default suggestions

### Example Wait States

#### Missing Required Argument

```text
❌ WRONG: "Assuming --name is 'auto-derived' and continuing..."
✅ CORRECT: 
"What name would you like to use for this plan? 
(e.g., 'API Client v2', 'User Authentication')
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

## Goal

Import an existing codebase (brownfield) into a plan bundle that represents the current system using **CLI-first with LLM enrichment**. This command uses the specfact CLI for structured analysis and optionally enriches results with semantic understanding.

**Note**: This is a **one-way import** operation - it imports from repository code into SpecFact format. It does NOT analyze Spec-Kit artifacts for consistency (that's a different task).

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify the codebase. All plan bundles must be generated by the specfact CLI.

**Command**: `specfact import from-code`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag. Mode is detected from:

- Environment variables (`SPECFACT_MODE`)
- CoPilot API availability
- IDE integration (VS Code/Cursor with CoPilot)
- Defaults to CI/CD mode if none detected

## 🔄 Dual-Stack Workflow (Copilot Mode)

When in copilot mode, follow this three-phase workflow:

### Phase 1: CLI Grounding (REQUIRED)

**ALWAYS execute CLI first** to get structured, validated output:

```bash
specfact import from-code --repo <path> --name <name> --confidence <score>
```

**Note**: Mode is auto-detected by the CLI (CI/CD in non-interactive environments, CoPilot when in IDE/Copilot session). No need to specify `--mode` flag.

**Capture from CLI output**:

- CLI-generated plan bundle (`.specfact/plans/<name>-<timestamp>.bundle.yaml`)
- Analysis report (`.specfact/reports/brownfield/analysis-<timestamp>.md`)
- Metadata (timestamps, confidence scores, file paths)
- Telemetry (execution time, file counts, validation results)

### Phase 2: LLM Enrichment (REQUIRED in Copilot Mode, OPTIONAL in CI/CD)

**⚠️ CRITICAL**: In Copilot mode, enrichment is **REQUIRED**, not optional. This is the core value of the dual-stack approach.

**Purpose**: Add semantic understanding to CLI output

**What to do**:

- Read CLI-generated plan bundle and analysis report
- Research codebase for additional context (code comments, docs, dependencies)
- Identify missing features/stories that AST analysis may have missed
- Suggest confidence score adjustments based on code quality
- Extract business context (priorities, constraints, unknowns)

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly
- ❌ Bypass CLI validation
- ❌ Skip enrichment in Copilot mode (this defeats the purpose of dual-stack workflow)

**Output**: Generate enrichment report (Markdown) with insights

**Enrichment Report Location**:

- Extract the plan bundle path from CLI output (e.g., `.specfact/plans/specfact-import-test.2025-11-17T12-21-48.bundle.yaml`)
- Derive enrichment report path by:
  - Taking the plan bundle filename (e.g., `specfact-import-test.2025-11-17T12-21-48.bundle.yaml`)
  - Replacing `.bundle.yaml` with `.enrichment.md` (e.g., `specfact-import-test.2025-11-17T12-21-48.enrichment.md`)
  - Placing it in `.specfact/reports/enrichment/` directory
- Full path example: `.specfact/reports/enrichment/specfact-import-test.2025-11-17T12-21-48.enrichment.md`
- **Ensure the directory exists**: Create `.specfact/reports/enrichment/` if it doesn't exist

### Phase 3: CLI Artifact Creation (REQUIRED)

**⚠️ CRITICAL**: If enrichment was generated in Phase 2 (which should always happen in Copilot mode), you MUST apply it via CLI using the `--enrichment` flag. Do not skip this step.

**Apply enrichments via CLI using the `--enrichment` flag**:

```bash
# Apply enrichment report to refine the auto-detected plan bundle
specfact import from-code --repo <path> --name <name> --enrichment <enrichment-report-path>
```

**The `--enrichment` flag**:

- Accepts a path to a Markdown enrichment report
- Applies missing features discovered by LLM
- Adjusts confidence scores for existing features
- Adds business context (priorities, constraints, unknowns)
- Validates and writes the enriched plan bundle via CLI

**Enrichment report format** (Markdown):

```markdown
## Missing Features

1. **IDE Integration Feature** (Key: FEATURE-IDEINTEGRATION)
   - Confidence: 0.85
   - Outcomes: Enables slash command support for VS Code/Cursor
   - Reason: AST missed because it's spread across multiple modules
   - **Stories** (REQUIRED - at least one story per feature):
     1. **As a developer, I can use slash commands in IDE**
        - Title: IDE Slash Command Support
        - Acceptance:
          - Slash commands are available in IDE command palette
          - Commands execute specfact CLI correctly
        - Tasks:
          - Implement command registration
          - Add command handlers
        - Story Points: 5
        - Value Points: 8

## Confidence Adjustments

- FEATURE-ANALYZEAGENT → 0.95 (strong semantic understanding capabilities)
- FEATURE-SPECKITSYNC → 0.9 (well-implemented bidirectional sync)

## Business Context

- Priority: "Core CLI tool for contract-driven development"
- Constraint: "Must support both CI/CD and Copilot modes"
```

**Result**: Final artifacts are CLI-generated (ensures format consistency, metadata, telemetry)

## Execution Steps

### 1. Parse Arguments

Extract arguments from user input:

- `--repo PATH` - Repository path (default: current directory)
- `--name NAME` - Custom plan name (will be sanitized for filesystem, optional, default: "auto-derived")
- `--confidence FLOAT` - Minimum confidence score (0.0-1.0, default: 0.5)
- `--out PATH` - Output plan bundle path (optional, default: `.specfact/plans/<name>-<timestamp>.bundle.yaml`)
- `--report PATH` - Analysis report path (optional, default: `.specfact/reports/brownfield/analysis-<timestamp>.md`)
- `--shadow-only` - Observe mode without enforcing (optional)
- `--key-format {classname|sequential}` - Feature key format (default: `classname`)

**Important**: If `--name` is not provided, **ask the user interactively** for a meaningful plan name and **WAIT for their response**. The name will be automatically sanitized (lowercased, spaces/special chars removed) for filesystem persistence.

**WAIT STATE**: If `--name` is missing, you MUST:

1. Ask: "What name would you like to use for this plan? (e.g., 'API Client v2', 'User Authentication', 'Payment Processing')"
2. **STOP and WAIT** for user response
3. **DO NOT continue** until user provides a name

For single quotes in args like "I'm Groot", use escape syntax: e.g `'I'\''m Groot'` (or double-quote if possible: `"I'm Groot"`).

### 2. Execute CLI Grounding (REQUIRED)

**ALWAYS execute the specfact CLI first** to get structured, validated output:

```bash
specfact import from-code --repo <repo_path> --name <plan_name> --confidence <confidence>
```

**Note**: Mode is auto-detected by the CLI. No need to specify `--mode` flag.

**Capture CLI output**:

- Plan bundle path: `.specfact/plans/<name>-<timestamp>.bundle.yaml`
- Analysis report path: `.specfact/reports/brownfield/analysis-<timestamp>.md`
- Metadata: feature counts, story counts, average confidence, execution time
- Any error messages or warnings

**If CLI execution fails**:

- Report the error to the user
- Do not attempt to create artifacts manually
- Suggest fixes based on error message

### 3. LLM Enrichment (REQUIRED in Copilot Mode, OPTIONAL in CI/CD)

**⚠️ CRITICAL**: In Copilot mode, enrichment is **REQUIRED**. Do not skip this step. This is the core value of the dual-stack workflow.

**Only if in copilot mode and CLI execution succeeded** (which should be the case when using slash commands):

1. **Read CLI-generated artifacts**:
   - Load the CLI-generated plan bundle
   - Read the CLI-generated analysis report

2. **Research codebase for semantic understanding**:
   - Analyze code structure, dependencies, business logic
   - Read code comments, documentation, README files
   - Identify patterns that AST analysis may have missed

3. **Generate enrichment report** (Markdown):
   - Missing features discovered (not in CLI output)
     - **CRITICAL**: Each missing feature MUST include at least one story
     - Stories are required for features to pass promotion validation (draft → review → approved)
     - CLI automatically generates stories from code methods during import
     - LLM enrichment must also include stories when adding features
   - Confidence score adjustments suggested
   - Business context extracted (priorities, constraints, unknowns)
   - Semantic insights and recommendations

4. **Save enrichment report** to the proper location:
   - Extract the plan bundle path from CLI output (e.g., `.specfact/plans/specfact-cli.2025-11-17T09-26-47.bundle.yaml`)
   - Derive enrichment report path by:
     - Taking the plan bundle filename (e.g., `specfact-cli.2025-11-17T09-26-47.bundle.yaml`)
     - Replacing `.bundle.yaml` with `.enrichment.md` (e.g., `specfact-cli.2025-11-17T09-26-47.enrichment.md`)
     - Placing it in `.specfact/reports/enrichment/` directory
   - Full path example: `.specfact/reports/enrichment/specfact-cli.2025-11-17T09-26-47.enrichment.md`
   - **Ensure the directory exists**: Create `.specfact/reports/enrichment/` if it doesn't exist

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI-generated plan bundle directly
- ❌ Bypass CLI validation

### 4. CLI Artifact Creation (REQUIRED)

**Final artifacts MUST be CLI-generated**:

**If enrichment was generated**:

1. **Save enrichment report** to the enrichment reports directory with a name that matches the plan bundle:
   - Location: `.specfact/reports/enrichment/`
   - Naming: Use the same name and timestamp as the plan bundle, replacing `.bundle.yaml` with `.enrichment.md`
   - Example: If plan bundle is `specfact-cli.2025-11-17T09-26-47.bundle.yaml`, save enrichment as `specfact-cli.2025-11-17T09-26-47.enrichment.md`
   - Full path: `.specfact/reports/enrichment/specfact-cli.2025-11-17T09-26-47.enrichment.md`

2. **Execute CLI with `--enrichment` flag**:

   ```bash
   specfact import from-code --repo <repo_path> --name <plan_name> --enrichment <enrichment-report-path>
   ```

3. **The CLI will**:
   - Load the original plan bundle (if it exists, derived from enrichment report path)
   - Parse the enrichment report
   - Apply missing features to the plan bundle
   - Adjust confidence scores
   - Add business context
   - Validate and write the enriched plan bundle as a **new file** with clear naming:
     - Format: `<name>.<original-timestamp>.enriched.<enrichment-timestamp>.bundle.yaml`
     - Example: `specfact-cli.2025-11-17T09-26-47.enriched.2025-11-17T11-15-29.bundle.yaml`
     - The original plan bundle remains unchanged
     - The enriched plan is stored as a separate file for comparison and versioning

**If no enrichment**:

- Use CLI-generated artifacts as-is from Phase 2

**Result**: All artifacts are CLI-generated (ensures format consistency, metadata, telemetry)

**Enriched Plan Naming Convention**:

- When enrichment is applied, the CLI creates a new enriched plan bundle with a clear label
- Original plan: `<name>.<timestamp>.bundle.yaml` (e.g., `specfact-cli.2025-11-17T09-26-47.bundle.yaml`)
- Enriched plan: `<name>.<original-timestamp>.enriched.<enrichment-timestamp>.bundle.yaml` (e.g., `specfact-cli.2025-11-17T09-26-47.enriched.2025-11-17T11-15-29.bundle.yaml`)
- Both plans are stored in `.specfact/plans/` for comparison and versioning
- The original plan remains unchanged, allowing you to compare before/after enrichment

### 5. Generate Import Report (Optional)

If `--report` is provided, generate a Markdown import report:

- Repository path and timestamp
- Confidence threshold used
- Feature/story counts and average confidence
- Detailed feature descriptions
- Recommendations and insights

### 6. Present Results

**Present the CLI-generated plan bundle** to the user:

- **Plan bundle location**: Show where the CLI wrote the YAML file
- **Original plan** (if enrichment was applied): Show the original plan bundle path
- **Enriched plan** (if enrichment was applied): Show the enriched plan bundle path with clear naming
- **Feature summary**: List features from CLI output with confidence scores
- **Story summary**: List stories from CLI output per feature
- **CLI metadata**: Execution time, file counts, validation results
- **Enrichment insights** (if enrichment was generated): Additional findings, missing features, confidence adjustments

**Example Output**:

```markdown
✓ Import complete!

Original plan: specfact-cli.2025-11-17T09-26-47.bundle.yaml
Enriched plan: specfact-cli.2025-11-17T09-26-47.enriched.2025-11-17T11-15-29.bundle.yaml

CLI Analysis Results:
- Features identified: 19
- Stories extracted: 45
- Average confidence: 0.72
- Execution time: 12.3s

Features (from CLI):
- User Authentication (Confidence: 0.85)
- Payment Processing (Confidence: 0.78)
- ...

LLM Enrichment Insights (optional):
- Missing feature discovered: "User Onboarding Flow" (Confidence: 0.85)
- Confidence adjustment: "User Authentication" → 0.90 (strong test coverage)
- Business context: "Critical for user onboarding" (from code comments)
```

## Output Format

### Plan Bundle Structure (Complete Example)

```yaml
version: "1.0"
product:
  themes:
    - "Security"
    - "User Management"
  releases: []
features:
  - key: "FEATURE-001"
    title: "User Authentication"
    outcomes:
      - "Secure login"
      - "Session management"
    acceptance:
      - "Users can log in"
      - "Sessions persist"
    constraints: []
    confidence: 0.85
    draft: false
    stories:
      - key: "STORY-001"
        title: "Login API"
        acceptance:
          - "API returns JWT token"
        tags: []
        confidence: 0.90
        draft: false
metadata:
  stage: "draft"
```

### Import Report Structure

```markdown
# Brownfield Import Report

**Repository**: `/path/to/repo`
**Timestamp**: `2025-11-02T12:00:00Z`
**Confidence Threshold**: `0.5`

## Summary

- **Features Identified**: 5
- **Stories Identified**: 12
- **Average Confidence**: 0.72

## Features

### FEATURE-001: User Authentication (Confidence: 0.85)
...
```

## Guidelines

### CLI-First with LLM Enrichment

**Primary workflow**:

1. **Execute CLI first**: Always run `specfact import from-code` to get structured output
2. **Use CLI output as grounding**: Parse CLI-generated artifacts, don't regenerate them
3. **Enrich with semantic understanding** (optional): Add insights, missing features, context
4. **Final artifacts are CLI-generated**: Ensure format consistency and metadata

**LLM enrichment** (REQUIRED in copilot mode, optional in CI/CD):

- **In Copilot Mode**: Enrichment is REQUIRED - this is the core value of dual-stack workflow
- Read CLI-generated plan bundle and analysis report
- Research codebase for additional context
- Identify missing features/stories
- Suggest confidence adjustments
- Extract business context
- **Always generate and save enrichment report** when in Copilot mode

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly
- ❌ Bypass CLI validation

### Feature Identification

- Group related functionality into logical features (from business logic, not just structure)
- Use code organization (modules, packages) as guidance
- Prefer broader features over granular ones
- Assign meaningful titles based on code purpose and business intent

### Feature Key Naming

- **Format**: `FEATURE-{CLASSNAME}` (e.g., `FEATURE-CONTRACTFIRSTTESTMANAGER` for class `ContractFirstTestManager`)
- **Note**: This format differs from manually created plans which may use `000_FEATURE_NAME` or `FEATURE-001` formats
- When comparing with existing plans, normalize keys by removing prefixes and underscores

### Feature Scope

- **Auto-derived plans** only include **implemented features** from the codebase (classes that exist in source code)
- **Main plans** may include **planned features** that don't exist as classes yet
- **Expected discrepancy**: If main plan has 66 features and auto-derived has 32, this means:
  - 32 features are implemented (found in codebase)
  - 34 features are planned but not yet implemented

### Confidence Scoring

- **High (0.8-1.0)**: Clear evidence from code structure, tests, and commit history
- **Medium (0.5-0.8)**: Moderate evidence from code structure or tests
- **Low (0.0-0.5)**: Weak evidence, inferred from patterns
- **Threshold**: Only include features/stories above threshold

### Classes That Don't Generate Features

Classes are skipped if:

- Private classes (starting with `_`) or test classes (starting with `Test`)
- Confidence score < 0.5 (no docstring, no stories, or poor documentation)
- No methods can be grouped into stories (methods don't match CRUD/validation/processing patterns)

### Error Handling

- **Missing repository**: Report error and exit
- **Invalid confidence**: Report error and use default (0.5)
- **Permission errors**: Report error and exit gracefully
- **Malformed code**: Continue with best-effort analysis
- **File write errors**: Report error and suggest manual creation

### YAML Generation Guidelines

**When generating YAML**:

- Use proper YAML formatting (2-space indentation, no flow style)
- Preserve string quotes where needed (use `"` for strings with special characters)
- Use proper list indentation (2 spaces for lists, 4 spaces for nested items)
- Ensure all required fields are present (version, features, product)
- Use ISO 8601 timestamp format for filenames: `YYYY-MM-DDTHH-MM-SS`

**Plan Bundle Structure**:

- Must include `version: "1.0"`
- Must include `product` with at least `themes: []` and `releases: []`
- Must include `features: []` (can be empty if no features found)
- Optional: `idea`, `business`, `metadata`
- Each feature must have `key`, `title`, `confidence`, `draft`
- Each story must have `key`, `title`, `confidence`, `draft`

## Expected Behavior

**This command imports features from existing code, not planned features.**

When comparing imported plans with main plans:

- **Imported plans** contain only **implemented features** (classes that exist in the codebase)
- **Main plans** may contain **planned features** (features that don't exist as classes yet)
- **Key naming difference**: Imported plans use `FEATURE-CLASSNAME`, main plans may use `000_FEATURE_NAME` or `FEATURE-001`

To compare plans, normalize feature keys by removing prefixes and underscores, then match by normalized key.

**Important**: This is a **one-way import** - it imports from code into SpecFact format. It does NOT perform consistency checking on Spec-Kit artifacts. For Spec-Kit artifact consistency checking, use Spec-Kit's `/speckit.analyze` command instead.

## Constitution Bootstrap (Optional)

After a brownfield import, the CLI may suggest generating a bootstrap constitution for Spec-Kit integration:

**If constitution is missing or minimal**:

- The CLI will suggest: "Generate bootstrap constitution from repository analysis?"
- **Recommended**: Accept the suggestion to auto-generate a constitution from your repository
- **Command**: `specfact constitution bootstrap --repo .`
- **What it does**: Analyzes your repository (README.md, pyproject.toml, .cursor/rules/, docs/rules/) and generates a bootstrap constitution
- **Next steps**: Review the generated constitution, then run `specfact sync spec-kit` to sync with Spec-Kit artifacts

**If you decline the suggestion**:

- You can run `specfact constitution bootstrap --repo .` manually later
- Or use `/speckit.constitution` command in your AI assistant for manual creation

**Validation**:

- After generating or updating the constitution, run `specfact constitution validate` to check completeness
- The constitution must be populated (not just template placeholders) before syncing with Spec-Kit

## Context

{ARGS}
