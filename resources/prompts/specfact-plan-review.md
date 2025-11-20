---
description: "Review plan bundle to identify and resolve ambiguities, fill gaps, and prepare for promotion"
---

# SpecFact Review Plan Bundle Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact plan review` before any analysis - execute the CLI command before any other operations
2. **NEVER write code**: Do not implement review logic - the CLI handles this
3. **NEVER create YAML/JSON directly**: All plan bundle updates must be CLI-generated
4. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata - use it, don't bypass its validation
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate or recreate it - use the CLI output as the source of truth
6. **NEVER manipulate internal code**: Do NOT use Python code to directly modify PlanBundle objects, Feature objects, Clarification objects, or any internal data structures. The CLI is THE interface - use it exclusively.
7. **No internal knowledge required**: You should NOT need to know about internal implementation details (PlanBundle model, Feature class, AmbiguityScanner, etc.). All operations must be performed via CLI commands.
8. **NEVER read artifacts directly**: Do NOT read plan bundle files directly to extract information unless for display purposes (e.g., showing plan details to user). Use CLI commands (`specfact plan review --list-questions`, `specfact plan select`) to get plan information.

### What Happens If You Don't Follow This

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures
- ❌ Works only in Copilot mode, fails in CI/CD
- ❌ Breaks when CLI internals change
- ❌ Requires knowledge of internal code structure

### Available CLI Commands for Plan Updates

**For updating idea section (OPTIONAL - business metadata)**:

- `specfact plan update-idea --title <title> --narrative <narrative> --target-users <users> --value-hypothesis <hypothesis> --constraints <constraints> --plan <path>`
  - Updates idea section metadata (optional business context, not technical implementation)
  - **Note**: Idea section is OPTIONAL - provides business context and metadata
  - All parameters are optional - use only what you need
  - Works in CI/CD, Copilot, and interactive modes
  - Example: `specfact plan update-idea --target-users "Developers, DevOps" --value-hypothesis "Reduce technical debt" --constraints "Python 3.11+, Maintain backward compatibility"`

**For updating features**:

- `specfact plan update-feature --key <key> --title <title> --outcomes <outcomes> --acceptance <acceptance> --constraints <constraints> --confidence <confidence> --draft/--no-draft --plan <path>`
  - **Boolean flags**: `--draft` sets True, `--no-draft` sets False, omit to leave unchanged
  - ❌ **WRONG**: `--draft true` or `--draft false` (Typer boolean flags don't accept values)
  - ✅ **CORRECT**: `--draft` (sets True) or `--no-draft` (sets False)
  - Updates existing feature metadata (title, outcomes, acceptance criteria, constraints, confidence, draft status)
  - Works in CI/CD, Copilot, and interactive modes
  - Example: `specfact plan update-feature --key FEATURE-001 --title "New Title" --outcomes "Outcome 1, Outcome 2"`

**For adding features**:

- `specfact plan add-feature --key <key> --title <title> --outcomes <outcomes> --acceptance <acceptance> --plan <path>`

**For adding stories**:

- `specfact plan add-story --feature <feature-key> --key <story-key> --title <title> --acceptance <acceptance> --story-points <points> --value-points <points> --plan <path>`

**For updating stories**:

- `specfact plan update-story --feature <feature-key> --key <story-key> --title <title> --acceptance <acceptance> --story-points <points> --value-points <points> --confidence <confidence> --draft/--no-draft --plan <path>`
  - **Boolean flags**: `--draft` sets True, `--no-draft` sets False, omit to leave unchanged
  - ❌ **WRONG**: `--draft true` or `--draft false` (Typer boolean flags don't accept values)
  - ✅ **CORRECT**: `--draft` (sets True) or `--no-draft` (sets False)
  - Updates existing story metadata (title, acceptance criteria, story points, value points, confidence, draft status)
  - Works in CI/CD, Copilot, and interactive modes
  - Example: `specfact plan update-story --feature FEATURE-001 --key STORY-001 --acceptance "Given X, When Y, Then Z" --story-points 5`

**❌ FORBIDDEN**: Direct Python code manipulation like:

```python
# ❌ NEVER DO THIS:
from specfact_cli.models.plan import PlanBundle, Feature
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

## Goal

Review a plan bundle to identify ambiguities, missing information, and unknowns. Systematically resolve these through targeted questions to make the plan ready for promotion (draft → review → approved).

**Note**: This review workflow is expected to run BEFORE promoting from `draft` to `review` stage. If the user explicitly states they are skipping review (e.g., exploratory spike), you may proceed, but must warn that promotion readiness may be incomplete.

**Automatic Enrichment Strategy**:

The CLI now supports automatic enrichment via `--auto-enrich` flag. Use this when:

1. **User explicitly requests enrichment**: "enrich", "auto-fix", "improve quality", "fix vague criteria"
2. **Plan quality indicators suggest it**: Vague acceptance criteria, incomplete requirements, generic tasks detected
3. **After Spec-Kit sync**: If user mentions issues from `/speckit.analyze` (vague acceptance criteria, incomplete requirements)

**Enrichment Workflow**:

1. **Run with `--auto-enrich`**: Execute `specfact plan review --auto-enrich` to automatically fix common issues
2. **Review enrichment results**: Analyze what was enhanced and verify improvements
3. **LLM reasoning**: Use your reasoning to:
   - Verify enhancements are contextually appropriate
   - Identify any generic improvements that need refinement
   - Suggest specific manual improvements for edge cases
4. **Follow-up enrichment**: If auto-enrichment made generic improvements, use CLI commands to refine them:
   - `specfact plan update-feature` to add specific file paths, method names, or component references to feature-level acceptance criteria
   - `specfact plan update-story` to refine story-level acceptance criteria with specific actions, method calls, and testable assertions
   - `specfact plan update-feature` to add domain-specific constraints

**Example Enrichment Flow**:

```bash
# Step 1: Auto-enrich to fix common issues
specfact plan review --auto-enrich --plan <plan_path>

# Step 2: LLM analyzes results and suggests refinements
# "Auto-enrichment enhanced 8 acceptance criteria. The Given/When/Then format is good,
#  but we should make the 'When' clause more specific. For example, 'When they interact
#  with the system' could be 'When they call the configure() method with valid parameters'."

# Step 3: Manual refinement using CLI commands
specfact plan update-feature --key FEATURE-001 --acceptance "Given a developer wants to configure Git operations, When they call the configure() method with valid parameters, Then the configuration is validated and stored" --plan <plan_path>
```

## Operating Constraints

**STRICTLY READ-WRITE**: This command modifies plan bundle metadata and content. All updates must be performed by the specfact CLI.

**Command**: `specfact plan review [--auto-enrich]`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag. Mode is detected from:

- Environment variables (`SPECFACT_MODE`)
- CoPilot API availability
- IDE integration (VS Code/Cursor with CoPilot)
- Defaults to CI/CD mode if none detected

**Mode-Specific Behavior**:

- **CLI Mode**: Interactive Q&A with free-text input, simple multiple-choice when applicable
- **Copilot Mode**: Reasoning-enhanced questions with recommendations, similar to Spec-Kit clarify

**Auto-Enrichment Feature**:

The `--auto-enrich` flag automatically enhances the plan bundle before scanning for ambiguities:

- **Vague acceptance criteria** (e.g., "is implemented", "is functional", "works") → Converted to testable Given/When/Then format
- **Incomplete requirements** (e.g., "System MUST Helper class") → Enhanced with verbs and actions (e.g., "System MUST provide a Helper class for [feature] operations")
- **Generic tasks** (e.g., "Implement [story]") → Enhanced with implementation details (file paths, methods, components)

**⚠️ IMPORTANT LIMITATION**: Auto-enrichment creates **generic templates** (e.g., "Given a user wants to use {story}, When they interact with the system, Then {story} works correctly"). These are NOT testable and MUST be refined by LLM with code-specific details. The LLM MUST automatically refine all generic criteria after auto-enrichment runs (see "LLM Post-Enrichment Analysis & Automatic Refinement" section below).

**When to Use Auto-Enrichment**:

- **Before first review**: Use `--auto-enrich` when reviewing a plan bundle imported from code or Spec-Kit to automatically fix common quality issues
- **After sync from Spec-Kit**: If `/speckit.analyze` reports vague acceptance criteria or incomplete requirements, use `--auto-enrich` to fix them automatically
- **Before promotion**: Use `--auto-enrich` to improve plan quality before promoting from `draft` to `review` stage
- **LLM Reasoning**: In Copilot mode, analyze the plan bundle first, then decide if auto-enrichment would be beneficial based on the coverage summary

## What This Command Does

The `specfact plan review` command:

1. **Analyzes** the plan bundle for ambiguities using a structured taxonomy
2. **Identifies** missing information, unclear requirements, and unknowns
3. **Asks** targeted questions (max 5 per session) to resolve ambiguities
4. **Integrates** answers back into the plan bundle incrementally
5. **Validates** plan bundle structure after each update
6. **Reports** coverage summary and promotion readiness

## Execution Steps

### ⚠️ **CRITICAL: Copilot Mode Workflow**

In Copilot mode, follow this three-phase workflow:

1. **Phase 1: Get Questions** - Execute `specfact plan review --list-questions` to get questions in JSON format
2. **Phase 2: Ask User** - Present questions to user one at a time, collect answers
3. **Phase 3: Feed Answers** - Write answers to a JSON file, then execute `specfact plan review --answers answers.json` to integrate answers

**⚠️ IMPORTANT**: Always use a JSON file path (not inline JSON string) to avoid parsing issues and ensure proper formatting.

**Never create clarifications directly in YAML**. Always use the CLI to integrate answers.

### 1. Parse Arguments and Load Plan Bundle

**Parse user input** to extract:

- Plan bundle path (default: active plan or latest in `.specfact/plans/`)
- Max questions per session (default: 5)
- Category focus (optional, to focus on specific taxonomy category)
- Auto-enrichment flag (if user requests automatic enrichment or if plan appears to need it)

**LLM Reasoning for Auto-Enrichment**:

In Copilot mode, you should **reason about whether auto-enrichment is needed**:

1. **Check if plan was imported from code or Spec-Kit**: If the user mentions "after sync" or "imported from code", auto-enrichment is likely beneficial
2. **Analyze plan quality indicators**: If you see patterns like:
   - Vague acceptance criteria ("is implemented", "is functional")
   - Incomplete requirements ("System MUST Helper class")
   - Generic tasks without implementation details
   Then suggest using `--auto-enrich`
3. **User intent**: If user explicitly requests "enrich", "improve", "fix vague criteria", or mentions issues from `/speckit.analyze`, use `--auto-enrich`

**Decision Flow**:

```text
IF user mentions "after sync" OR "imported" OR "vague criteria" OR "incomplete requirements":
    → Use --auto-enrich flag
ELSE IF plan appears to have quality issues (based on initial scan):
    → Suggest --auto-enrich to user and wait for confirmation
ELSE:
    → Proceed with normal review (no auto-enrichment)
```

**WAIT STATE**: If plan path is unclear, ask the user:

```text
"Which plan bundle would you like to review?
(Enter path, 'active plan', or 'latest')
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

**In Copilot Mode**: Use `--list-questions` to get questions in structured format:

```bash
# Get questions as JSON (for Copilot mode)
specfact plan review --list-questions --plan <plan_path> --max-questions 5

# With auto-enrichment (if needed)
specfact plan review --auto-enrich --list-questions --plan <plan_path> --max-questions 5
```

**In CI/CD Mode**: Use `--non-interactive` flag:

```bash
# Non-interactive mode (for automation)
specfact plan review --non-interactive --plan <plan_path> --answers '{"Q001": "answer1", "Q002": "answer2"}'

# With auto-enrichment
specfact plan review --auto-enrich --non-interactive --plan <plan_path> --answers '{"Q001": "answer1"}'
```

**Capture from CLI**:

- Plan bundle loaded successfully
- **Deduplication summary**: "✓ Removed N duplicate features from plan bundle" (if duplicates were found)
- Current stage (should be `draft` for review)
- Existing clarifications (if any)
- **Auto-enrichment summary** (if `--auto-enrich` was used):
  - Features updated
  - Stories updated
  - Acceptance criteria enhanced
  - Requirements enhanced
  - Tasks enhanced
  - List of changes made
- Questions list (if `--list-questions` used)
- **Coverage Summary**: Pay special attention to Partial categories - they indicate areas that could be enriched but don't block promotion

**⚠️ CRITICAL: Automatic Refinement After Auto-Enrichment**:

**If auto-enrichment was used, you MUST automatically refine generic acceptance criteria BEFORE proceeding with questions.**

**Step 1: Identify Generic Criteria** (from auto-enrichment output):

Look for patterns in the "Changes made" list:

- Generic templates: "Given a user wants to use {story}, When they interact with the system, Then {story} works correctly"
- Vague actions: "interact with the system", "perform the action", "access the system"
- Vague outcomes: "works correctly", "is functional", "works as expected"

**Step 2: Research Codebase** (for each story with generic criteria):

- Find the actual class and method names
- Identify method signatures and parameters
- Check test files for actual test patterns
- Understand return values and assertions

**Step 3: Generate Code-Specific Criteria** (replace generic with specific):

- Replace "interact with the system" → specific method calls with parameters
- Replace "works correctly" → specific return values, state changes, or assertions
- Add class names, method signatures, file paths where relevant

**Step 4: Apply Refinements** (use CLI commands):

```bash
# For story-level acceptance criteria, use update-story:
specfact plan update-story --feature <feature-key> --key <story-key> --acceptance "<refined-code-specific-criteria>" --plan <path>

# For feature-level acceptance criteria, use update-feature:
specfact plan update-feature --key <feature-key> --acceptance "<refined-code-specific-criteria>" --plan <path>
```

**Step 5: Verify** (before proceeding):

- All generic criteria replaced with code-specific criteria
- All criteria mention specific methods, classes, or file paths
- All criteria are testable (can be verified with automated tests)

**Only after Step 5 is complete, proceed with questions.**

**Understanding Deduplication**:

The CLI automatically deduplicates features during review using normalized key matching:

1. **Exact matches**: Features with identical normalized keys are automatically deduplicated
   - Example: `FEATURE-001` and `001_FEATURE_NAME` normalize to the same key
2. **Prefix matches**: Abbreviated class names vs full Spec-Kit directory names
   - Example: `FEATURE-IDEINTEGRATION` (from code analysis) vs `041_IDE_INTEGRATION_SYSTEM` (from Spec-Kit)
   - Only matches when at least one key has a numbered prefix (Spec-Kit origin) to avoid false positives
   - Requires minimum 10 characters, 6+ character difference, and <75% length ratio

**LLM Semantic Deduplication**:

After automated deduplication, you should review the plan bundle for **semantic/logical duplicates** that automated matching might miss:

1. **Review feature titles and descriptions**: Look for features that represent the same functionality with different names
   - Example: "Git Operations Manager" vs "Git Operations Handler" (both handle git operations)
   - Example: "Telemetry Settings" vs "Telemetry Configuration" (both configure telemetry)
2. **Check feature stories**: Features with overlapping or identical user stories may be duplicates
3. **Analyze acceptance criteria**: Features with similar acceptance criteria covering the same functionality
4. **Check code references**: If multiple features reference the same code files/modules, they might be the same feature
5. **Suggest consolidation**: When semantic duplicates are found:
   - Use `specfact plan update-feature` to merge information into one feature
   - Use `specfact plan add-feature` to create a consolidated feature if needed
   - Document which features were consolidated and why

**Example Semantic Duplicate Detection**:

```text
After review, analyze the plan bundle and identify:
- Features with similar titles but different keys
- Features covering the same code modules
- Features with overlapping user stories or acceptance criteria
- Features that represent the same functionality

If semantic duplicates are found, suggest consolidation:
"Found semantic duplicates: FEATURE-GITOPERATIONS and FEATURE-GITOPERATIONSHANDLER
both cover git operations. Should I consolidate these into a single feature?"
```

**Understanding Auto-Enrichment Output**:

When `--auto-enrich` is used, the CLI will output:

```bash
Auto-enriching plan bundle (enhancing vague acceptance criteria, incomplete requirements, generic tasks)...
✓ Auto-enriched plan bundle: 2 features, 5 stories updated
  - Enhanced 8 acceptance criteria
  - Enhanced 3 requirements
  - Enhanced 4 tasks

Changes made:
  - Feature FEATURE-001: Enhanced requirement 'System MUST Helper class' → 'System MUST provide a Helper class for git operations operations'
  - Story STORY-001: Enhanced acceptance criteria 'is implemented' → 'Given a developer wants to use configure git operations, When they interact with the system, Then configure git operations is functional and verified'
  ...
```

**Understanding CLI Output**:

When the CLI reports "No critical ambiguities detected. Plan is ready for promotion" but shows ⚠️ Partial categories, this means:

- **Critical categories** (Functional Scope, Feature Completeness, Constraints) are all Clear or Partial (not Missing)
- **Partial categories** are not critical enough to block promotion, but enrichment would improve plan quality
- The plan can be promoted, but consider enriching Partial categories for better completeness

**LLM Post-Enrichment Analysis & Automatic Refinement**:

**⚠️ CRITICAL**: After auto-enrichment runs, you MUST automatically refine the generic acceptance criteria with code-specific, testable details. The auto-enrichment creates generic templates (e.g., "Given a user wants to use {story}, When they interact with the system, Then {story} works correctly"), but these are NOT testable. You should IMMEDIATELY replace them with specific, code-based criteria.

**Why This Matters**:

- **Generic criteria are NOT testable**: "When they interact with the system" cannot be verified
- **Test-based criteria are better**: "When extract_article_viii_evidence() is called" is specific and testable
- **Auto-enrichment makes things worse**: It replaces test-based criteria with generic templates
- **LLM reasoning is required**: Only LLM can understand codebase context and create specific criteria

**Automatic Refinement Workflow (MANDATORY after auto-enrichment)**:

1. **Parse auto-enrichment output**: Identify which acceptance criteria were enhanced (look for generic patterns like "interact with the system", "works correctly", "is functional and verified")
2. **Research codebase context**: For each enhanced story, find the actual:
   - Class names and method signatures (e.g., `ContractFirstTestManager.extract_article_viii_evidence()`)
   - File paths and module structure (e.g., `src/specfact_cli/enrichers/plan_enricher.py`)
   - Test patterns and validation logic (check test files for actual test cases)
   - Actual behavior and return values (e.g., returns `dict` with `'status'` key)
3. **Generate code-specific criteria**: Replace generic templates with specific, testable criteria:
   - **Generic (BAD)**: "Given a user wants to use as a developer, i can configure contract first test manager, When they interact with the system, Then as a developer, i can configure contract first test manager works correctly"
   - **Code-specific (GOOD)**: "Given a ContractFirstTestManager instance is available, When extract_article_viii_evidence(repo_path: Path) is called, Then the method returns a dict with 'status' key equal to 'PASS' or 'FAIL' and 'frameworks_detected' list"
4. **Apply refinements automatically**: Use `specfact plan update-feature` to replace ALL generic criteria with code-specific ones BEFORE asking questions
5. **Verify testability**: Ensure all refined criteria can be verified with automated tests (include specific method names, parameters, return values, assertions)

**Example Automatic Refinement Process**:

```markdown
1. Auto-enrichment enhanced: "is implemented" → "Given a user wants to use configure git operations, When they interact with the system, Then configure git operations works correctly"

2. LLM Analysis:
   - Story: "As a developer, I can configure Contract First Test Manager"
   - Feature: "Contract First Test Manager"
   - Research codebase: Find `ContractFirstTestManager` class and its methods

3. Codebase Research:
   - Find: `src/specfact_cli/enrichers/plan_enricher.py` with `PlanEnricher` class
   - Methods: `enrich_plan()`, `_enhance_vague_acceptance_criteria()`, etc.
   - Test patterns: Check test files for actual test cases

4. Generate Code-Specific Criteria:
   - "Given a developer wants to configure Contract First Test Manager, When they call `PlanEnricher.enrich_plan(plan_bundle: PlanBundle)` with a valid plan bundle, Then the method returns an enrichment summary dict with 'features_updated' and 'stories_updated' counts"

5. Apply via CLI:
   ```bash
   # For story-level acceptance criteria:
   specfact plan update-story --feature FEATURE-CONTRACTFIRSTTESTMANAGER --key STORY-001 --acceptance "Given a developer wants to configure Contract First Test Manager, When they call PlanEnricher.enrich_plan(plan_bundle: PlanBundle) with a valid plan bundle, Then the method returns an enrichment summary dict with 'features_updated' and 'stories_updated' counts" --plan <path>
   
   # For feature-level acceptance criteria:
   specfact plan update-feature --key FEATURE-CONTRACTFIRSTTESTMANAGER --acceptance "Given a developer wants to configure Contract First Test Manager, When they call PlanEnricher.enrich_plan(plan_bundle: PlanBundle) with a valid plan bundle, Then the method returns an enrichment summary dict with 'features_updated' and 'stories_updated' counts" --plan <path>
   ```

**When to Apply Automatic Refinement**:

- **MANDATORY after auto-enrichment**: If `--auto-enrich` was used, you MUST automatically refine ALL generic criteria BEFORE asking questions. Do not proceed with questions until generic criteria are replaced.
- **During review**: When questions ask about vague acceptance criteria, provide code-specific refinements immediately
- **Before promotion**: Ensure all acceptance criteria are code-specific and testable (no generic placeholders)

**Refinement Priority**:

1. **High Priority (Do First)**: Criteria containing generic patterns:
   - "interact with the system"
   - "works correctly" / "works as expected" / "is functional"
   - "perform the action"
   - "access the system"
   - Any criteria that doesn't mention specific methods, classes, or file paths

2. **Medium Priority**: Criteria that are testable but could be more specific:
   - Add method signatures
   - Add parameter types
   - Add return value assertions
   - Add file path references

3. **Low Priority**: Criteria that are already code-specific:
   - Preserve test-based criteria (don't replace with generic)
   - Only enhance if missing important details

**Refinement Quality Checklist**:

- ✅ **Specific method names**: Include actual class.method() signatures
- ✅ **Specific file paths**: Reference actual code locations when relevant
- ✅ **Testable outcomes**: Include specific return values, state changes, or observable behaviors
- ✅ **Domain-specific**: Use terminology from the actual codebase
- ✅ **No generic placeholders**: Avoid "interact with the system", "works correctly", "is functional"

### 2. Get Questions from CLI (Copilot Mode) or Analyze Directly (Interactive Mode)

**⚠️ CRITICAL**: In Copilot mode, you MUST use `--list-questions` to get questions from the CLI, then ask the user, then feed answers back via `--answers`.

**Step 2a: Get Questions (Copilot Mode)**:

```bash
# Execute CLI to get questions in JSON format
specfact plan review --list-questions --plan <plan_path> --max-questions 5
```

**Parse JSON output**:

```json
{
  "questions": [
    {
      "id": "Q001",
      "category": "Feature/Story Completeness",
      "question": "What user stories are needed for feature FEATURE-IDEINTEGRATION?",
      "impact": 0.9,
      "uncertainty": 0.8,
      "related_sections": ["features.FEATURE-IDEINTEGRATION.stories"]
    },
    ...
  ],
  "total": 5
}
```

**Step 2b: Analyze Plan Bundle for Ambiguities (Interactive Mode Only)**:

**CLI Mode**: The CLI performs structured ambiguity scan using taxonomy categories:

1. **Functional Scope & Behavior**
   - Core user goals & success criteria
   - Explicit out-of-scope declarations
   - User roles / personas differentiation

2. **Domain & Data Model**
   - Entities, attributes, relationships
   - Identity & uniqueness rules
   - Lifecycle/state transitions
   - Data volume / scale assumptions

3. **Interaction & UX Flow**
   - Critical user journeys / sequences
   - Error/empty/loading states
   - Accessibility or localization notes

4. **Non-Functional Quality Attributes**
   - Performance (latency, throughput targets)
   - Scalability (horizontal/vertical, limits)
   - Reliability & availability (uptime, recovery expectations)
   - Observability (logging, metrics, tracing signals)
   - Security & privacy (authN/Z, data protection, threat assumptions)
   - Compliance / regulatory constraints (if any)

5. **Integration & External Dependencies**
   - External services/APIs and failure modes
   - Data import/export formats
   - Protocol/versioning assumptions

6. **Edge Cases & Failure Handling**
   - Negative scenarios
   - Rate limiting / throttling
   - Conflict resolution (e.g., concurrent edits)

7. **Constraints & Tradeoffs**
   - Technical constraints (language, storage, hosting)
   - Explicit tradeoffs or rejected alternatives

8. **Terminology & Consistency**
   - Canonical glossary terms
   - Avoided synonyms / deprecated terms

9. **Completion Signals**
   - Acceptance criteria testability
   - Measurable Definition of Done style indicators

10. **Feature/Story Completeness**
    - Missing acceptance criteria
    - Unclear story outcomes
    - Incomplete feature constraints

**For each category**, mark status: **Clear** / **Partial** / **Missing**

**Copilot Mode**: In addition to CLI analysis, you can:

- Research codebase for additional context
- Analyze similar implementations for best practices
- Provide reasoning for question prioritization

### 3. Generate Question Queue

**Prioritize questions** by (Impact × Uncertainty) heuristic:

- Maximum 5 questions per session
- Only include questions whose answers materially impact:
  - Architecture decisions
  - Data modeling
  - Task decomposition
  - Test design
  - UX behavior
  - Operational readiness
  - Compliance validation

**Exclude**:

- Questions already answered in existing clarifications
- Trivial stylistic preferences
- Plan-level execution details (unless blocking correctness)
- Speculative tech stack questions (unless blocking functional clarity)

**If no valid questions exist**, analyze the coverage summary:

**Understanding Coverage Status**:

- **✅ Clear**: Category has no ambiguities or all findings are resolved
- **⚠️ Partial**: Category has some findings, but they're not high-priority enough to generate questions (low impact × uncertainty score)
- **❌ Missing**: Category has critical findings that block promotion (high impact × uncertainty)

**Critical vs Important Categories**:

- **Critical categories** (block promotion if Missing):
  - Functional Scope & Behavior
  - Feature/Story Completeness
  - Constraints & Tradeoffs

- **Important categories** (warn if Missing or Partial, but don't block):
  - Domain & Data Model
  - Interaction & UX Flow
  - Integration & External Dependencies
  - Edge Cases & Failure Handling
  - Completion Signals

**When No Questions Are Generated**:

1. **If Partial categories exist**: Explain what "Partial" means and provide enrichment guidance:
   - **Partial = Some gaps exist but not critical enough for questions**
   - **Action**: Use CLI commands to manually enrich these categories (see "Manual Enrichment" section below)
   - **Example**: If "Completion Signals: Partial", many stories have acceptance criteria but they're not testable (missing "must", "should", "verify", "validate", "check" keywords)

2. **If Missing critical categories**: Report warning and suggest using `specfact plan update-idea` or `specfact plan update-feature` to fill gaps
   - **Note**: Idea section is OPTIONAL - provides business context, not technical implementation
   - Report: "No high-priority questions generated, but missing critical categories detected. Consider using `specfact plan update-idea` to add optional business metadata."

3. **If all categories are Clear**: Report: "No critical ambiguities detected. Plan is ready for promotion."

**Spec-Kit Sync Integration**:

If the user mentions they plan to sync to Spec-Kit later (e.g., "I'll sync to spec-kit after review"), you should:

1. **Reassure them**: The `specfact sync spec-kit` command automatically generates all required Spec-Kit fields:
   - Frontmatter (Feature Branch, Created date, Status) in spec.md
   - INVSEST criteria in spec.md
   - Scenarios (Primary, Alternate, Exception, Recovery) in spec.md
   - Constitution Check (Article VII, VIII, IX) in plan.md
   - Phases (Phase 0, 1, 2, -1) in plan.md and tasks.md
   - Technology Stack in plan.md
   - Story mappings ([US1], [US2]) in tasks.md

2. **Focus on plan bundle enrichment**: During review, focus on enriching the plan bundle itself (acceptance criteria, constraints, stories) rather than worrying about Spec-Kit-specific formatting

3. **Explain the workflow**:
   - Review enriches plan bundle → Sync generates complete Spec-Kit artifacts → Optional customization if needed

**Enrichment Strategy for Partial Categories**:

When categories are marked as "Partial", use this two-phase approach:

**Phase 1: Automatic Enrichment** (use `--auto-enrich` flag):

- **Completion Signals (Partial)**: Auto-enriches vague acceptance criteria ("is implemented", "is functional") → Given/When/Then format
- **Feature Completeness (Partial)**: Auto-enriches incomplete requirements ("System MUST Helper class") → Complete requirements with verbs
- **Feature Completeness (Partial)**: Auto-enriches generic tasks → Tasks with implementation details

**Phase 2: LLM-Enhanced Manual Refinement** (after auto-enrichment):

After auto-enrichment, use LLM reasoning to refine generic improvements:

- **Completion Signals (Partial)**: Review auto-enriched Given/When/Then scenarios and refine with specific actions:
  - Generic: "When they interact with the system"
  - Refined: "When they call the `configure()` method with valid parameters"
  - Use: `specfact plan update-story --feature <feature-key> --key <story-key> --acceptance "<refined criteria>" --plan <path>` for story-level criteria
  - Use: `specfact plan update-feature --key <key> --acceptance "<refined criteria>" --plan <path>` for feature-level criteria

- **Edge Cases (Partial)**: Add domain-specific edge cases:
  - Use `specfact plan update-feature` to add edge case acceptance criteria
  - Add keywords like "edge", "corner", "boundary", "limit", "invalid", "null", "empty"
  - Example: Add "Given invalid Git repository path, When configure() is called, Then system returns clear error message"

- **Integration (Partial)**: Add specific external dependency constraints:
  - Use `specfact plan update-feature --constraints` to add external dependency constraints
  - Example: `--constraints "API rate limits: 100 req/min, Timeout: 30s, Retry: 3 attempts"`

- **Data Model (Partial)**: Add specific data model constraints:
  - Use `specfact plan update-feature --constraints` to add data model constraints
  - Example: `--constraints "Entity uniqueness: email must be unique, Max records: 10,000 per user"`

- **Interaction/UX (Partial)**: Add specific error handling scenarios:
  - Use `specfact plan update-feature` to add error handling acceptance criteria
  - Add keywords like "error", "empty", "invalid", "validation", "failure"
  - Example: Add "Given user submits invalid input, When validation runs, Then system displays clear error message with field-specific guidance"

**LLM Reasoning for Refinement**:

When refining auto-enriched content, consider:

1. **Context from codebase**: Research the actual codebase structure to suggest accurate file paths, method names, and component references
2. **Domain knowledge**: Use domain-specific terminology and patterns appropriate for the feature
3. **Testability**: Ensure refined acceptance criteria are truly testable (can be verified with automated tests)
4. **Specificity**: Replace generic placeholders with specific, actionable details

### 4. Sequential Questioning Loop

**⚠️ CRITICAL**: In Copilot mode, you MUST:

1. Get questions via `--list-questions` (already done in Step 2a)
2. Ask the user each question (this step)
3. Collect all answers
4. Feed answers back to CLI via `--answers` (Step 5)

**Present EXACTLY ONE question at a time.**

#### CLI Mode Format

**For multiple-choice questions**:

```text
Q: [Question text]

Options:
A) [Option A description]
B) [Option B description]
C) [Option C description]
D) [Option D description] (if needed)
E) [Option E description] (if needed)
F) [Free text answer (<=5 words)]

Enter option letter (A-F) or provide your own short answer:
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]
```

**For short-answer questions**:

```text
Q: [Question text]

Format: Short answer (<=5 words)

Enter your answer:
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]
```

#### Copilot Mode Format

**For multiple-choice questions**:

```text
**Recommended:** Option [X] - <reasoning (1-2 sentences explaining why this is the best choice)>

| Option | Description |
|--------|-------------|
| A | <Option A description> |
| B | <Option B description> |
| C | <Option C description> |
| D | <Option D description> (if needed) |
| E | <Option E description> (if needed) |
| Short | Provide a different short answer (<=5 words) |

You can reply with the option letter (e.g., "A"), accept the recommendation by saying "yes" or "recommended", or provide your own short answer.
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]
```

**For short-answer questions**:

```text
**Suggested:** <your proposed answer> - <brief reasoning>

Format: Short answer (<=5 words). You can accept the suggestion by saying "yes" or "suggested", or provide your own answer.
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]
```

**After user answers**:

- If user replies with "yes", "recommended", or "suggested", use your previously stated recommendation/suggestion as the answer
- Otherwise, validate the answer (maps to option or fits <=5 word constraint)
- If ambiguous, ask for quick disambiguation (same question, don't advance)
- Once satisfactory, record answer and move to next question

**Stop asking when**:

- All critical ambiguities resolved early (remaining queued items become unnecessary), OR
- User signals completion ("done", "good", "no more"), OR
- You reach 5 asked questions

**Never reveal future queued questions in advance.**

### 5. Feed Answers Back to CLI (Copilot Mode) or Integrate Directly (Interactive Mode)

**⚠️ CRITICAL**: In Copilot mode, after collecting all answers from the user, you MUST feed them back to the CLI using `--answers`:

**Step 1: Create answers JSON file** (ALWAYS use file, not inline JSON):

```bash
# Create answers.json file with all answers
cat > answers.json << 'EOF'
{
  "Q001": "Developers, DevOps engineers",
  "Q002": "Yes",
  "Q003": "Yes",
  "Q004": "Yes",
  "Q005": "Yes"
}
EOF
```

**Step 2: Feed answers to CLI** (using file path - RECOMMENDED):

```bash
# Feed all answers back to CLI (Copilot mode) - using file path (RECOMMENDED)
specfact plan review --plan <plan_path> --answers answers.json
```

**⚠️ AVOID inline JSON strings** - They can cause parsing issues with special characters, quotes, and Rich markup:

```bash
# ❌ NOT RECOMMENDED: Inline JSON string (may have parsing issues)
specfact plan review --plan <plan_path> --answers '{"Q001": "answer1", "Q002": "answer2"}'
```

**Format**: The `--answers` parameter accepts either:

- **✅ JSON file path** (RECOMMENDED): Path to a JSON file containing question_id -> answer mappings
  - More reliable parsing
  - Easier to validate JSON syntax
  - Avoids shell escaping issues
  - Better for complex answers with special characters
  
- **⚠️ JSON string** (NOT RECOMMENDED): Direct JSON object (may have Rich markup parsing issues, shell escaping problems)
  - Only use for simple, single-answer cases
  - Requires careful quote escaping
  - Can fail with special characters

**JSON Structure**:

- Keys: Question IDs (e.g., "Q001", "Q002")
- Values: Answer strings (≤5 words recommended)

**⚠️ CRITICAL: Boolean-Like Answer Values**:

When providing answers that are boolean-like strings (e.g., "Yes", "No", "True", "False", "On", "Off"), ensure they are:

1. **Always quoted in JSON**: Use `"Yes"` not `Yes` (JSON requires quotes for strings)
2. **Provided as strings**: Never use JSON booleans `true`/`false` - always use string values `"Yes"`/`"No"`

**❌ WRONG** (causes YAML validation errors):

```json
{
  "Q001": "Developers, DevOps engineers",
  "Q002": true,  // ❌ JSON boolean - will cause validation error
  "Q003": Yes    // ❌ Unquoted string - invalid JSON
}
```

**✅ CORRECT**:

```json
{
  "Q001": "Developers, DevOps engineers",
  "Q002": "Yes",  // ✅ Quoted string
  "Q003": "No"    // ✅ Quoted string
}
```

**Why This Matters**:

- YAML parsers interpret unquoted "Yes", "No", "True", "False", "On", "Off" as boolean values
- The CLI expects all answers to be strings (validated with `isinstance(answer, str)`)
- Boolean values in JSON will cause validation errors: "Answer for Q002 must be a non-empty string"
- The YAML serializer now automatically quotes boolean-like strings, but JSON parsing must still provide strings

**Example JSON file** (`answers.json`):

```json
{
  "Q001": "Developers, DevOps engineers",
  "Q002": "Yes",
  "Q003": "Yes",
  "Q004": "Yes",
  "Q005": "Yes"
}
```

**Usage**:

```bash
# ✅ RECOMMENDED: Using file path
specfact plan review --plan <plan_path> --answers answers.json

# ⚠️ NOT RECOMMENDED: Using JSON string (only for simple cases)
specfact plan review --plan <plan_path> --answers '{"Q001": "answer1"}'
```

**Validation After Feeding Answers**:

After feeding answers, always verify the plan bundle is valid:

```bash
# Verify plan bundle is valid (should not show validation errors)
specfact plan review --plan <plan_path> --list-questions --max-questions 1
```

If you see validation errors like "Input should be a valid string", check:

1. All answers in JSON file are quoted strings (not booleans)
2. JSON file syntax is valid (use `python3 -m json.tool answers.json` to validate)
3. No unquoted boolean-like strings ("Yes", "No", "True", "False")

**In Interactive Mode**: The CLI automatically integrates answers after each question.

**After CLI processes answers** (Copilot mode), the CLI will:

1. **Update plan bundle sections** based on answer:
   - **Functional ambiguity** → `features[].acceptance[]` or `idea.narrative`
   - **Data model** → `features[].constraints[]` or new feature
   - **Non-functional** → `features[].constraints[]` or `idea.constraints[]`
   - **Edge cases** → `features[].acceptance[]` or `stories[].acceptance[]`
   - **Terminology** → Normalize across plan bundle

2. **Add clarification to plan bundle**:
   - Ensure `clarifications.sessions[]` exists
   - Create session for today's date if not present
   - Add clarification with:
     - Unique ID (Q001, Q002, etc.)
     - Category
     - Question text
     - Answer
     - Integration points (e.g., `["features.FEATURE-001.acceptance"]`)
     - Timestamp

3. **Save plan bundle** (CLI automatically saves after each integration)

4. **Validate plan bundle**:
   - Structure is valid
   - No contradictory statements
   - Terminology consistency
   - Clarifications properly formatted

**Preserve formatting**: Do not reorder unrelated sections; keep heading hierarchy intact.

**Keep each integration minimal and testable** (avoid narrative drift).

### 6. Validation

**After EACH write plus final pass**:

- Clarifications session contains exactly one entry per accepted answer (no duplicates)
- Total asked (accepted) questions ≤ 5
- Updated sections contain no lingering vague placeholders
- No contradictory earlier statement remains
- Plan bundle structure is valid
- Terminology consistency: same canonical term used across all updated sections

### 7. Report Completion

**After questioning loop ends or early termination**:

**If questions were asked and answered**:

```markdown
✓ Review complete!

**Questions Asked**: 3
**Plan Bundle**: `.specfact/plans/specfact-import-test.2025-11-17T12-21-48.bundle.yaml`
**Sections Touched**:
- `features.FEATURE-001.acceptance`
- `features.FEATURE-002.constraints`
- `idea.constraints`

**Coverage Summary**:

| Category | Status | Notes |
|----------|--------|-------|
| Functional Scope | ✅ Clear | Resolved (was Partial, now addressed) |
| Data Model | ✅ Clear | Already sufficient |
| Non-Functional | ✅ Clear | Resolved (was Missing, now addressed) |
| Edge Cases | ⚠️ Partial | Deferred (exceeds question quota, see enrichment guide) |
| Completion Signals | ⚠️ Partial | Some stories need testable acceptance criteria |
| Terminology | ✅ Clear | Already sufficient |

**Next Steps**:
- Plan is ready for promotion to `review` stage
- Run: `/specfact-cli/specfact-plan-promote review`
- Optional: Enrich Partial categories using CLI commands (see Manual Enrichment section)
```

**If no questions were generated but Partial categories exist**:

```markdown
✓ Review analysis complete!

**Plan Bundle**: `.specfact/plans/specfact-import-test.2025-11-17T12-21-48.bundle.yaml`
**Status**: No critical ambiguities detected (all critical categories are Clear)

**Coverage Summary**:

| Category | Status | Meaning |
|----------|--------|---------|
| Functional Scope | ✅ Clear | No ambiguities detected |
| Data Model | ⚠️ Partial | Some features mention data but lack constraints (not critical) |
| Interaction/UX | ⚠️ Partial | Some stories mention UX but lack error handling (not critical) |
| Integration | ⚠️ Partial | Some features mention integration but lack constraints (not critical) |
| Edge Cases | ⚠️ Partial | Some stories have <3 acceptance criteria (not critical) |
| Completion Signals | ⚠️ Partial | Some acceptance criteria are not testable (not critical) |
| Constraints | ✅ Clear | No ambiguities detected |

**Understanding "Partial" Status**:

⚠️ **Partial** means the category has some gaps, but they're not high-priority enough to generate questions. The plan can still be promoted, but enrichment would improve quality.

**Enrichment Options**:

- **Automatic Enrichment** (recommended first step): Use `--auto-enrich` flag to automatically fix vague acceptance criteria, incomplete requirements, and generic tasks

  ```bash
  specfact plan review --auto-enrich --plan <plan_path>
  ```

- **LLM-Enhanced Refinement** (after auto-enrichment): Use LLM reasoning to:

  - Review auto-enrichment results and verify contextually appropriate improvements
  - Identify generic improvements that need domain-specific refinement
  - Suggest specific manual improvements using CLI commands

- **Manual Enrichment**: Use `specfact plan update-feature` commands to add missing constraints/acceptance criteria with specific details

- **Defer**: Proceed with promotion and enrich later during implementation (not recommended if Partial categories are high-impact)

**Next Steps**:

- Plan can be promoted (no critical blockers)
- Optional: Run enrichment to improve Partial categories
- Run: `/specfact-cli/specfact-plan-promote review`

**If Outstanding or Deferred remain**:

- Recommend whether to proceed to promotion or run review again
- Flag high-impact deferred items with rationale
- Explain what "Partial" means and when enrichment is recommended vs optional

## Guidelines

### Question Quality

- **High Impact**: Questions that materially affect implementation or validation
- **Actionable**: Answers that can be integrated into plan bundle sections
- **Focused**: One question per ambiguity, not multiple related questions
- **Testable**: Answers that lead to measurable acceptance criteria

### Integration Quality

- **Immediate**: Integrate after each answer, don't batch
- **Atomic**: Save plan bundle after each integration
- **Minimal**: Keep integrations concise and testable
- **Consistent**: Use same terminology across all sections

### Promotion Readiness

A plan is ready for promotion when:

- All critical ambiguities resolved
- Acceptance criteria are testable
- Constraints are explicit and measurable
- Terminology is consistent
- No contradictory statements remain

### LLM Reasoning for Continuous Improvement

**After auto-enrichment, use LLM reasoning to further improve the plan**:

1. **Analyze Enrichment Quality**:
   - Review each enhanced acceptance criteria: Is the Given/When/Then scenario specific enough?
   - Check enhanced requirements: Do they capture the full intent with appropriate verbs?
   - Evaluate task enhancements: Are file paths and method names accurate for the codebase?

2. **Identify Generic Patterns**:
   - Look for placeholder text like "interact with the system" → Suggest specific actions
   - Find generic file paths like "src/specfact_cli/..." → Research actual codebase structure
   - Detect vague component names → Suggest specific class/function names from codebase

3. **Research Codebase Context**:
   - Search for actual file paths, method names, and component structures
   - Identify domain-specific patterns and terminology
   - Understand the actual implementation approach to suggest accurate refinements

4. **Propose Specific Refinements**:
   - Use `specfact plan update-feature` to refine generic Given/When/Then scenarios
   - Add specific file paths, method names, or component references to tasks
   - Enhance requirements with domain-specific details

5. **Validate Improvements**:
   - Ensure all refinements are testable and measurable
   - Verify terminology consistency across all enhancements
   - Check that refinements align with codebase structure and patterns

## Troubleshooting

### Common Errors and Solutions

#### Error: "Plan validation failed: Validation error: Input should be a valid string"

**Cause**: Answers in clarifications section are stored as booleans instead of strings.

**Symptoms**:

- Error message: `clarifications.sessions.0.questions.X.answer: Input should be a valid string`
- Plan bundle fails to load or validate

**Solution**:

1. **Check JSON file format**:

   ```bash
   # Validate JSON syntax
   python3 -m json.tool answers.json
   ```

2. **Ensure all answers are quoted strings**:

   ```json
   {
     "Q001": "Developers, DevOps engineers",  // ✅ Quoted string
     "Q002": "Yes",  // ✅ Quoted string (not true or unquoted Yes)
     "Q003": "No"    // ✅ Quoted string (not false or unquoted No)
   }
   ```

3. **Fix existing plan bundle** (if already corrupted):

   ```bash
   # Use sed to quote unquoted "Yes" values in YAML
   sed -i "s/^      answer: Yes$/      answer: 'Yes'/" .specfact/plans/<plan>.bundle.yaml
   sed -i "s/^      answer: No$/      answer: 'No'/" .specfact/plans/<plan>.bundle.yaml
   ```

4. **Verify fix**:

   ```bash
   # Check that all answers are strings
   python3 -c "import yaml; data = yaml.safe_load(open('.specfact/plans/<plan>.bundle.yaml')); print('All strings:', all(isinstance(q['answer'], str) for s in data['clarifications']['sessions'] for q in s['questions']))"
   ```

#### Error: "Invalid JSON in --answers"

**Cause**: JSON syntax error in answers file or inline JSON string.

**Solution**:

1. **Validate JSON syntax**:

   ```bash
   python3 -m json.tool answers.json
   ```

2. **Check for common issues**:
   - Missing quotes around string values
   - Trailing commas
   - Unclosed brackets or braces
   - Special characters not escaped

3. **Use file path instead of inline JSON** (recommended):

   ```bash
   # ✅ Better: Use file
   specfact plan review --answers answers.json
   
   # ⚠️ Avoid: Inline JSON (can have escaping issues)
   specfact plan review --answers '{"Q001": "answer"}'
   ```

#### Error: "Answer for Q002 must be a non-empty string"

**Cause**: Answer value is not a string (e.g., boolean `true`/`false` or `null`).

**Solution**:

1. **Ensure all answers are strings in JSON**:

   ```json
   {
     "Q002": "Yes"  // ✅ String
   }
   ```

   Not:

   ```json
   {
     "Q002": true   // ❌ Boolean
     "Q002": null   // ❌ Null
   }
   ```

2. **Validate before feeding to CLI**:

   ```bash
   # Check all values are strings
   python3 -c "import json; data = json.load(open('answers.json')); print('All strings:', all(isinstance(v, str) for v in data.values()))"
   ```

#### Error: "Feature 'FEATURE-001' not found in plan"

**Cause**: Feature key doesn't exist in plan bundle.

**Solution**:

1. **List available features**:

   ```bash
   specfact plan select --list-features
   ```

2. **Use correct feature key** (case-sensitive, exact match required)

#### Error: "Story 'STORY-001' not found in feature 'FEATURE-001'"

**Cause**: Story key doesn't exist in the specified feature.

**Solution**:

1. **List stories in feature**:

   ```bash
   # Check plan bundle YAML for story keys
   grep -A 5 "key: FEATURE-001" .specfact/plans/<plan>.bundle.yaml | grep "key: STORY"
   ```

2. **Use correct story key** (case-sensitive, exact match required)

### Prevention Checklist

Before feeding answers to CLI:

- [ ] **JSON file syntax is valid** (use `python3 -m json.tool` to validate)
- [ ] **All answer values are quoted strings** (not booleans, not null)
- [ ] **Boolean-like strings are quoted** ("Yes", "No", "True", "False", "On", "Off")
- [ ] **Using file path** (not inline JSON string) for complex answers
- [ ] **No trailing commas** in JSON
- [ ] **All question IDs match** (Q001, Q002, etc. from `--list-questions` output)

After feeding answers:

- [ ] **Plan bundle validates** (run `specfact plan review --list-questions --max-questions 1`)
- [ ] **No validation errors** in CLI output
- [ ] **All clarifications saved** (check `clarifications.sessions` in YAML)

**Example LLM Reasoning Process**:

```text
1. Auto-enrichment enhanced: "is implemented" → "Given a developer wants to use configure git operations, When they interact with the system, Then configure git operations is functional and verified"

2. LLM Analysis:

   - ✅ Given clause is contextually appropriate
   - ⚠️ When clause is too generic ("interact with the system")
   - ✅ Then clause captures the outcome

3. Codebase Research:

   - Search for Git operations configuration methods
   - Find: `src/specfact_cli/utils/git_operations.py` with `configure()` method
   - Identify: Method signature `configure(repo_path: Path, config: dict) -> bool`

4. Proposed Refinement:

   - "Given a developer wants to configure Git operations, When they call configure(repo_path, config) with valid parameters, Then the method returns True and configuration is persisted"

5. Execute Refinement:

   ```bash
   specfact plan update-feature --key FEATURE-001 --acceptance "Given a developer wants to configure Git operations, When they call configure(repo_path, config) with valid parameters, Then the method returns True and configuration is persisted" --plan <path>
   ```

**Continuous Improvement Loop**:

1. Run `--auto-enrich` to fix common issues automatically
2. Use LLM reasoning to analyze enrichment results
3. Research codebase for specific details
4. Propose and execute refinements using CLI commands
5. Re-run review to verify improvements
6. Iterate until plan quality meets promotion standards

## Context

{ARGS}

--- End Command ---
