---
description: Initialize a new development plan bundle with idea, product, and features structure.
---
# SpectFact Plan Init Command (greenfield & brownfield)

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Create a new development plan bundle. The plan bundle includes idea, business context, product structure (themes and releases), and initial features with stories.

**Two Approaches:**

1. **Greenfield** - Start from scratch with manual plan creation (interactive prompts)
2. **Brownfield** - Scan existing codebase to import structure (`specfact import from-code`), then refine interactively

The user should choose their approach at the beginning of the interactive flow.

## Operating Constraints

**Command**: `specfact plan init`

## Execution Steps

### 1. Parse Arguments

Extract arguments from user input:

- `--interactive/--no-interactive` - Interactive mode with prompts (default: interactive)
- `--out PATH` - Output plan bundle path (optional, default: `.specfact/plans/main.bundle.yaml`)
- `--scaffold/--no-scaffold` - Create complete `.specfact/` directory structure (default: scaffold)

For single quotes in args like "I'm Groot", use escape syntax: e.g `'I'\''m Groot'` (or double-quote if possible: `"I'm Groot"`).

### 2. Ensure Directory Structure

If `--scaffold` is enabled (default):

- Create `.specfact/` directory structure:
  - `.specfact/plans/` - Plan bundles
  - `.specfact/protocols/` - Protocol definitions (FSM)
  - `.specfact/reports/` - Analysis and comparison reports
  - `.specfact/reports/brownfield/` - Brownfield analysis reports
  - `.specfact/reports/comparison/` - Plan comparison reports
  - `.specfact/reports/enforcement/` - Enforcement reports

If `--no-scaffold`, ensure minimum structure exists.

### 3. Interactive vs Non-Interactive Mode

#### Non-Interactive Mode (`--no-interactive`)

Create a minimal plan bundle with:

- `version: "1.0"`
- Empty `idea` (None)
- Empty `business` (None)
- Empty `product` (themes: [], releases: [])
- Empty `features` ([])

Write to output path and exit.

#### Interactive Mode (default)

### 4. Choose Plan Creation Approach

**First**, ask the user which approach they want:

```text
Plan Creation Approach:
1. Greenfield - Start from scratch (manual plan creation)
2. Brownfield - Import from existing codebase (scan repository first)

Choose option (1 or 2): _
```

**If user chooses option 2 (Brownfield)**:

1. **Run brownfield analysis first**:

   ```bash
   specfact import from-code --repo . --name my-project --confidence 0.7
   ```

   - This analyzes the codebase and generates an auto-derived plan bundle
   - Plan is saved to: `.specfact/plans/<name>-<timestamp>.bundle.yaml` (where `<name>` is the sanitized plan name)

2. **Load the auto-derived plan**:
   - Read the generated plan bundle from brownfield analysis
   - Extract features, themes, and structure from the auto-derived plan

3. **Proceed with interactive refinement**:
   - Use the auto-derived plan as the starting point
   - Guide user through Sections 1-4 to refine/add:
     - Idea section (title, narrative, target users, metrics)
     - Business context (if needed)
     - Product themes (confirm/add to auto-derived themes)
     - Features (confirm/refine auto-derived features, add stories if missing)

4. **Merge and finalize**:
   - Merge refined idea/business sections with auto-derived features
   - Write final plan bundle to output path

**If user chooses option 1 (Greenfield)**:

- Proceed directly to Section 1 (Idea) with empty/scratch plan
- Use standard interactive prompts as defined in CLI command

### 5. Section 1: Idea

**For Brownfield approach**: Pre-fill with values from auto-derived plan if available (extract from plan bundle's `idea` section or from README/pyproject.toml analysis).

Prompt for:

- **Project title** (required) - If brownfield, suggest from auto-derived plan or extract from README/pyproject.toml
- **Project narrative** (required) - Brief description - If brownfield, suggest from auto-derived plan or README
- **Optional details**:
  - Target users (list) - If brownfield, suggest from auto-derived plan
  - Value hypothesis (text) - If brownfield, suggest from README value proposition
  - Success metrics (dict: `{"metric_name": "target_value"}`) - Suggest based on project type

### 6. Section 2: Business Context (Optional)

Ask if user wants to add business context:

- **Market segments** (list)
- **Problems you're solving** (list)
- **Your solutions** (list)
- **How you differentiate** (list)
- **Business risks** (list)

### 7. Section 3: Product - Themes and Releases

**For Brownfield approach**: Pre-fill themes from auto-derived plan (extract from plan bundle's `product.themes`).

Prompt for:

- **Product themes** (list, e.g., "AI/ML", "Security", "Performance") - If brownfield, pre-fill with themes from auto-derived plan
- **Releases** (optional, interactive loop):
  - Release name (e.g., "v1.0 - MVP")
  - Release objectives (list)
  - Feature keys in scope (list, e.g., `["FEATURE-001", "FEATURE-002"]`) - If brownfield, suggest feature keys from auto-derived plan
  - Release risks (list)
  - Ask if user wants to add another release

### 8. Section 4: Features

**For Brownfield approach**: Pre-fill with features from auto-derived plan. For each feature:

- Show auto-derived feature details (key, title, outcomes, acceptance criteria)
- Ask user to confirm, refine, or add stories
- If features have no stories, prompt to add them interactively

Interactive loop to add features:

- **Feature key** (required, e.g., "FEATURE-001")
- **Feature title** (required)
- **Expected outcomes** (list)
- **Acceptance criteria** (list)
- **Optional details**:
  - Constraints (list)
  - Confidence (0.0-1.0, float)
  - Draft flag (boolean)
- **Stories** (optional, interactive loop):
  - Story key (required, e.g., "STORY-001")
  - Story title (required)
  - Acceptance criteria (list)
  - Optional details:
    - Tags (list, e.g., `["critical", "backend"]`)
    - Confidence (0.0-1.0, float)
    - Draft flag (boolean)

### 9. Sensitive Information Disclosure Gate

**BEFORE generating the final plan bundle**, perform a disclosure gate check to identify potentially sensitive information that should not be published publicly:

1. **Review Business Section** (if provided):
   - **Risks**: Check for internal business concerns (e.g., "Market competition", "Open source sustainability", "Proprietary competition") - **Remove these** as they contain internal strategy
   - **Segments**: Check for specific targeting strategies - **Generalize if needed** (e.g., "GitHub Spec-Kit community" → "Open source developers")
   - **Differentiation**: Check for competitive positioning details - **Keep public differentiators only** (remove strategic positioning)
   - **Problems/Solutions**: Keep only information already published in public docs (README, public guides)

2. **Review Idea Section**:
   - **Metrics**: Check for internal KPIs - **Keep only public success metrics**
   - **Value Hypothesis**: Keep only public value proposition

3. **Review Features Section**:
   - **Features**: Technical implementation details are generally safe to publish (already in codebase)
   - **Stories**: Implementation details are safe

4. **Display Disclosure Warning**:

   ```text
   ⚠️  Disclosure Gate Check
   ============================================================
   
   Potentially Sensitive Information Detected:
   - Business risks: [list of risks]
   - Market segments: [list of segments]
   - Competitive differentiation: [list of differentiators]
   
   This information may contain internal strategy that should not
   be published publicly. Consider:
   1. Removing business section entirely (it's optional)
   2. Sanitizing business section (remove risks, generalize segments)
   3. Keeping as-is if already published in public docs
   
   Proceed with sanitized plan? (y/n)
   ```

5. **If user confirms sanitization**, remove or generalize sensitive information before proceeding.

6. **If user chooses to keep sensitive info**, warn them that it will be included in the plan bundle.

**Note**: For brownfield plans, business context may have been extracted from internal docs. Always review before finalizing.

### 10. Generate Plan Bundle

Create structured plan bundle (YAML) with:

- `version: "1.0"`
- `idea`: Idea object (or None if not provided) - Use refined idea from Sections 1-2
- `business`: Business object (or None if not provided) - Use sanitized business from Section 2 (after disclosure gate)
- `product`: Product object with themes and releases - Use refined themes/releases from Section 3
- `features`: List of Feature objects with stories - Use confirmed/refined features from Section 4 (for brownfield: merge with auto-derived features)

**For Brownfield approach**: Merge the auto-derived plan's features with the refined idea/business/product sections from interactive prompts.

### 11. Validate Plan Bundle

Validate the generated plan bundle:

- Schema validation (Pydantic models)
- Required fields check
- Data type validation
- Report validation results

### 12. Write Plan Bundle

Write plan bundle to output path:

- Create parent directories if needed
- Write YAML with proper formatting
- Report success with file path

**Final Disclosure Reminder**: Before committing or publishing, verify that the plan bundle does not contain sensitive internal strategy (business risks, specific competitive positioning, internal targets).

### 13. Display Summary

Show plan summary:

- Title
- Themes count
- Features count
- Releases count
- Business context included (yes/no) - warn if sensitive info detected

**Note**: Plans created with this command can later be exported to Spec-Kit format using `specfact sync spec-kit --bidirectional`. The export will generate fully compatible Spec-Kit artifacts (spec.md, plan.md, tasks.md) with all required fields including INVSEST criteria, Scenarios, Constitution Check, and Phase organization.

## Output Format

### Plan Bundle Structure

```yaml
version: "1.0"
idea:
  title: "My Awesome Project"
  narrative: "A project that does amazing things"
  target_users: ["Developers", "Data Scientists"]
  value_hypothesis: "Users will save 50% of their time"
  metrics:
    user_satisfaction: "> 4.5/5"
    time_saved: "50%"
business:
  segments: ["Enterprise", "SMB"]
  problems: ["Complex workflows", "Time-consuming tasks"]
  solutions: ["Automation", "AI assistance"]
  differentiation: ["Better UX", "Lower cost"]
  # Note: 'risks' field removed - contains internal strategy, not suitable for public disclosure
product:
  themes: ["AI/ML", "Security"]
  releases:
    - name: "v1.0 - MVP"
      objectives: ["Core features", "Basic security"]
      scope: ["FEATURE-001", "FEATURE-002"]
      risks: ["Scope creep", "Timeline delays"]
features:
  - key: "FEATURE-001"
    title: "User Authentication"
    outcomes: ["Secure login", "Session management"]
    acceptance: ["Users can log in", "Sessions persist"]
    constraints: ["Must use OAuth2"]
    confidence: 1.0
    draft: false
    stories:
      - key: "STORY-001"
        title: "Login API"
        acceptance: ["API returns JWT token"]
        tags: ["critical", "backend"]
        confidence: 1.0
        draft: false
```

## Guidelines

### Feature Keys

- Use format: `FEATURE-###` (e.g., `FEATURE-001`, `FEATURE-002`)
- Keys should be unique within a plan
- Sequential numbering recommended

### Story Keys

- Use format: `STORY-###` (e.g., `STORY-001`, `STORY-002`)
- Keys should be unique within a feature
- Sequential numbering recommended

### Confidence Scores

- Range: 0.0-1.0
- Default: 1.0 for manually created plans
- Lower confidence indicates uncertainty or draft status

### Validation

- All required fields must be present
- Data types must match schema
- Feature keys must be unique
- Story keys must be unique within their feature

## Summary

**Key Decision Point**: Always ask the user first whether they want:

1. **Greenfield** - Start from scratch with interactive prompts (standard CLI behavior)
2. **Brownfield** - Import existing codebase structure using `specfact analyze code2spec`, then refine interactively

**For Brownfield**:

- Run `specfact analyze code2spec --repo . --confidence 0.7` first
- Load auto-derived plan from `.specfact/reports/brownfield/auto-derived-<timestamp>.bundle.yaml`
- Use auto-derived features, themes, and structure as pre-filled suggestions in interactive prompts
- User can confirm, refine, or add to auto-derived content
- Merge refined idea/business sections with auto-derived features
- **Always perform disclosure gate check** before finalizing (business context may contain internal strategy)

**For Greenfield**:

- Proceed directly with interactive prompts (no pre-filling)
- Standard CLI command behavior

**Disclosure Gate** (Section 9):

- **Always perform disclosure gate check** before generating final plan bundle
- Review business section for sensitive information (risks, competitive positioning, targeting strategy)
- Sanitize or remove internal strategy information before publishing
- Warn user if sensitive information is detected
- Get user confirmation before including sensitive information in plan bundle

## Context

{ARGS}
