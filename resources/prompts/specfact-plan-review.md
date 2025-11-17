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

**Automatic Enrichment Requests**: If the user requests automatic enrichment (e.g., "enrich missing details automatically"), you should:

1. Identify Partial categories from the coverage summary
2. Use CLI commands to enrich the most impactful Partial categories
3. Focus on high-value improvements (Completion Signals, Edge Cases)
4. Report what was enriched and what remains Partial
5. Explain that Partial categories don't block promotion but enrichment improves quality

## Operating Constraints

**STRICTLY READ-WRITE**: This command modifies plan bundle metadata and content. All updates must be performed by the specfact CLI.

**Command**: `specfact plan review`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag. Mode is detected from:

- Environment variables (`SPECFACT_MODE`)
- CoPilot API availability
- IDE integration (VS Code/Cursor with CoPilot)
- Defaults to CI/CD mode if none detected

**Mode-Specific Behavior**:

- **CLI Mode**: Interactive Q&A with free-text input, simple multiple-choice when applicable
- **Copilot Mode**: Reasoning-enhanced questions with recommendations, similar to Spec-Kit clarify

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
3. **Phase 3: Feed Answers** - Execute `specfact plan review --answers '{"Q001": "answer1", ...}'` to integrate answers

**Never create clarifications directly in YAML**. Always use the CLI to integrate answers.

### 1. Parse Arguments and Load Plan Bundle

**Parse user input** to extract:

- Plan bundle path (default: active plan or latest in `.specfact/plans/`)
- Max questions per session (default: 5)
- Category focus (optional, to focus on specific taxonomy category)

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
```

**In CI/CD Mode**: Use `--non-interactive` flag:

```bash
# Non-interactive mode (for automation)
specfact plan review --non-interactive --plan <plan_path> --answers '{"Q001": "answer1", "Q002": "answer2"}'
```

**Capture from CLI**:

- Plan bundle loaded successfully
- Current stage (should be `draft` for review)
- Existing clarifications (if any)
- Questions list (if `--list-questions` used)
- **Coverage Summary**: Pay special attention to Partial categories - they indicate areas that could be enriched but don't block promotion

**Understanding CLI Output**:

When the CLI reports "No critical ambiguities detected. Plan is ready for promotion" but shows ⚠️ Partial categories, this means:

- **Critical categories** (Functional Scope, Feature Completeness, Constraints) are all Clear or Partial (not Missing)
- **Partial categories** are not critical enough to block promotion, but enrichment would improve plan quality
- The plan can be promoted, but consider enriching Partial categories for better completeness

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

**Manual Enrichment for Partial Categories**:

When categories are marked as "Partial", you can enrich them using CLI commands:

- **Completion Signals (Partial)**: Stories have acceptance criteria but they're not testable
  - Use `specfact plan update-feature` to add testable acceptance criteria with keywords like "must", "should", "verify", "validate", "check"
  - Example: Change "Get contract-first test status" → "Must verify contract-first test status is returned correctly"

- **Edge Cases (Partial)**: Stories have <3 acceptance criteria and no edge case keywords
  - Use `specfact plan update-feature` to add edge case acceptance criteria
  - Add keywords like "edge", "corner", "boundary", "limit", "invalid", "null", "empty"
  - Example: Add "Must handle null input gracefully" or "Must validate boundary conditions"

- **Integration (Partial)**: Features mention integration keywords but lack constraints
  - Use `specfact plan update-feature --constraints` to add external dependency constraints
  - Example: `--constraints "API rate limits: 100 req/min, Timeout: 30s, Retry: 3 attempts"`

- **Data Model (Partial)**: Features mention data keywords but lack constraints
  - Use `specfact plan update-feature --constraints` to add data model constraints
  - Example: `--constraints "Entity uniqueness: email must be unique, Max records: 10,000 per user"`

- **Interaction/UX (Partial)**: Stories mention UX keywords but lack error handling
  - Use `specfact plan update-feature` to add error handling acceptance criteria
  - Add keywords like "error", "empty", "invalid", "validation", "failure"
  - Example: Add "Must display clear error message on invalid input"

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

```bash
# Feed all answers back to CLI (Copilot mode) - using file path (recommended)
specfact plan review --plan <plan_path> --answers answers.json

# Alternative: using JSON string (may have Rich markup parsing issues)
specfact plan review --plan <plan_path> --answers '{"Q001": "answer1", "Q002": "answer2", "Q003": "answer3"}'
```

**Format**: The `--answers` parameter accepts either:

- **JSON file path**: Path to a JSON file containing question_id -> answer mappings
- **JSON string**: Direct JSON object (may have Rich markup parsing issues, prefer file path)

**JSON Structure**:

- Keys: Question IDs (e.g., "Q001", "Q002")
- Values: Answer strings (≤5 words recommended)

**Example JSON file** (`answers.json`):

```json
{
  "Q001": "Test narrative answer",
  "Q002": "Test story answer"
}
```

**Usage**:

```bash
# Using file path (recommended)
specfact plan review --plan <plan_path> --answers answers.json

# Using JSON string (may have parsing issues)
specfact plan review --plan <plan_path> --answers '{"Q001": "answer1"}'
```

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

1. **Automatic Enrichment** (if user requested): Use CLI commands to enrich Partial categories (see Manual Enrichment section)
2. **Manual Enrichment**: Use `specfact plan update-feature` commands to add missing constraints/acceptance criteria
3. **Defer**: Proceed with promotion and enrich later during implementation

**Next Steps**:
- Plan can be promoted (no critical blockers)
- Optional: Run enrichment to improve Partial categories
- Run: `/specfact-cli/specfact-plan-promote review`
```

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

## Context

{ARGS}

--- End Command ---
