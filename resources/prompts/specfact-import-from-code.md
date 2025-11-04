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

## Goal

Import an existing codebase (brownfield) into a plan bundle that represents the current system using **AI-first semantic understanding**. This command leverages the AI IDE's native LLM capabilities to understand codebase semantics and generate structured plan bundles directly.

**Note**: This is a **one-way import** operation - it imports from repository code into SpecFact format. It does NOT analyze Spec-Kit artifacts for consistency (that's a different task).

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify the codebase. Generate structured plan bundles (YAML) and optional import reports (Markdown) directly.

**Command**: `specfact import from-code`

## AI-First Approach (Recommended)

**Key Principle**: Use the AI IDE's native LLM to understand the codebase semantically, then generate the plan bundle directly as YAML. This avoids the need for separate LLM API setup, langchain, or additional API keys.

**Note**: This is a **one-way import** operation - it imports from repository code into SpecFact format. It does NOT analyze Spec-Kit artifacts for consistency (that's a different task). For Spec-Kit artifact consistency checking, see Spec-Kit's `/speckit.analyze` command.

### Workflow

1. **Semantic Understanding** (AI IDE's LLM):
   - Read and understand the codebase structure
   - Identify features from business logic (not just class structure)
   - Extract user stories from code intent (not just method patterns)
   - Infer priorities, constraints, unknowns from code context
   - Understand technology stack from dependencies

2. **Plan Bundle Generation** (AI IDE's LLM):
   - Generate a PlanBundle structure directly (as a Python dict matching the Pydantic model)
   - Convert to YAML format using proper YAML formatting
   - Write to `.specfact/plans/<name>-<timestamp>.bundle.yaml` (where `<name>` is the sanitized plan name)
   - If no name provided, ask user for a meaningful plan name before proceeding

3. **Result Presentation**:
   - Present the generated plan bundle to the user
   - Show feature/story counts with confidence scores
   - Highlight semantic insights and recommendations

### When to Use This Approach

- ✅ **AI IDE environment** (Cursor, VS Code with CoPilot, etc.)
- ✅ **Multi-language codebases** (Python, TypeScript, JavaScript, PowerShell, etc.)
- ✅ **Semantic understanding needed** (priorities, constraints, unknowns)
- ✅ **High-quality Spec-Kit artifacts** required

### When to Use CLI (CI/CD Mode)

- ✅ **CI/CD pipelines** (no LLM access)
- ✅ **Python-only codebases** (AST-based analysis sufficient)
- ✅ **Fast, deterministic results** needed
- ✅ **Offline analysis** required

## Execution Steps

### 1. Understand Codebase Semantically (AI IDE's LLM)

Use your AI capabilities to understand the codebase:

- **Read repository structure**: Identify modules, packages, and organization
- **Understand business logic**: Identify features from business intent, not just class structure
- **Extract semantic information**:
  - Priorities from code context (comments, docs, usage patterns)
  - Constraints from code/docs (technical limitations, requirements)
  - Unknowns from code analysis (missing information, unclear decisions)
  - Technology stack from dependencies and imports
- **Identify user stories**: Extract from code intent, not just method patterns
- **Generate scenarios**: Infer Primary, Alternate, Exception, Recovery scenarios from acceptance criteria

### 2. Parse Arguments

Extract arguments from user input:

- `--repo PATH` - Repository path (default: current directory)
- `--name NAME` - Custom plan name (will be sanitized for filesystem, optional, default: "auto-derived")
- `--confidence FLOAT` - Minimum confidence score (0.0-1.0, default: 0.5)
- `--out PATH` - Output plan bundle path (optional, default: `.specfact/plans/<name>-<timestamp>.bundle.yaml`)
- `--report PATH` - Analysis report path (optional, default: `.specfact/reports/brownfield/analysis-<timestamp>.md`)
- `--shadow-only` - Observe mode without enforcing (optional)
- `--key-format {classname|sequential}` - Feature key format (default: `classname`)

**Important**: If `--name` is not provided, **ask the user interactively** for a meaningful plan name. The name will be automatically sanitized (lowercased, spaces/special chars removed) for filesystem persistence.

For single quotes in args like "I'm Groot", use escape syntax: e.g `'I'\''m Groot'` (or double-quote if possible: `"I'm Groot"`).

### 3. Generate Plan Bundle Directly

**Generate a PlanBundle structure** directly using your semantic understanding:

1. **Create PlanBundle structure** (as a Python dict matching the Pydantic model):

**IMPORTANT**: Use the provided plan name (from `--name` argument) for `idea.title` instead of "Unknown Project". If no plan name is provided, use a meaningful title derived from the repository name or ask the user.

```python
plan_bundle = {
    "version": "1.0",
    "idea": {
        "title": "<plan_name or repo_name>",  # Use provided plan name, NOT "Unknown Project"
        "narrative": "Auto-derived plan from brownfield analysis of <plan_name or repo_name>",
        "target_users": [],
        "value_hypothesis": "",
        "constraints": []
    },
    "product": {
        "themes": [...],
        "releases": [...]
    },
    "features": [
        {
            "key": "FEATURE-001",
            "title": "Feature Title",
            "outcomes": [...],
            "acceptance": [...],
            "constraints": [...],
            "confidence": 0.85,
            "draft": False,
            "stories": [
                {
                    "key": "STORY-001",
                    "title": "Story Title",
                    "acceptance": [...],
                    "tags": [...],
                    "confidence": 0.90,
                    "draft": False
                }
            ]
        }
    ],
    "metadata": {
        "stage": "draft"
    }
}
```

2. **Convert to YAML** using proper YAML formatting (2-space indentation, no flow style):
   - Use standard YAML formatting (no JSON-style arrays)
   - Preserve string quotes where needed
   - Use proper list indentation (2 spaces for lists, 4 spaces for nested items)

3. **Write to file**: Create the output directory if needed and write the YAML file:
   - Default path: `.specfact/reports/brownfield/auto-derived-<timestamp>.yaml`
   - Use ISO 8601 timestamp format: `YYYY-MM-DDTHH-MM-SS`
   - Ensure directory exists: `.specfact/reports/brownfield/`

### 4. Generate Import Report (Optional)

If `--report` is provided, generate a Markdown import report:

- Repository path and timestamp
- Confidence threshold used
- Feature/story counts and average confidence
- Detailed feature descriptions
- Recommendations and insights

### 5. Present Results

**Present the generated plan bundle** to the user:

- **Plan bundle location**: Show where the YAML file was written
- **Feature summary**: List identified features with confidence scores
- **Story summary**: List identified stories per feature
- **Semantic insights**: Highlight key findings from your analysis
- **Recommendations**: Suggest improvements based on your analysis

**Example Output**:

```markdown
✓ Import complete!

Plan bundle written to: .specfact/plans/api-client-v2.2025-11-04T22-17-22.bundle.yaml

Found 19 features:
- User Authentication (Confidence: 0.85)
- Payment Processing (Confidence: 0.78)
- ...

Semantic Insights:
- Priority: "Critical for user onboarding" (from code comments)
- Constraint: "Must support OAuth 2.0" (from dependencies)
- Unknown: "Migration strategy for legacy auth" (from TODO comments)
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

### AI-First Semantic Understanding

Use your AI capabilities to:

1. **Understand business logic**: Identify features from business intent, not just class structure
2. **Extract semantic information**: Priorities, constraints, unknowns from code context
3. **Identify user stories**: Extract from code intent, not just method patterns
4. **Generate scenarios**: Infer Primary, Alternate, Exception, Recovery scenarios

**Then generate the plan bundle directly** as YAML using your semantic understanding.

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

## Context

{ARGS}
