---
description: Promote a plan bundle through development stages with quality gate validation.
---

# SpecFact Promote Plan Bundle Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Help the user promote their plan bundle through development stages (draft → review → approved → released) to track progress and ensure quality gates are met.

## What This Command Does

The `specfact plan promote` command helps move a plan bundle through its lifecycle:

- **draft**: Initial state - can be modified freely
- **review**: Plan is ready for review - should be stable
- **approved**: Plan approved for implementation
- **released**: Plan released and should be immutable

## AI-First Interaction (Primary Approach)

**Key Principle**: Interact directly with the user in the chat/AI IDE interface. Execute the promotion logic directly using Python imports, then present results in chat. Only mention CLI commands as an alternative for pro users who prefer terminal interaction.

### 1. Understand What They Want

**Parse user input** to extract:

- Target stage (draft, review, approved, or released) - infer from context if not explicit
- Plan file path - handle special cases like "last imported brownfield plan"
- Validation preference (default: yes)
- Force promotion (default: no)

**Special cases to handle**:

- **"last imported brownfield plan"** or **"last brownfield"**: Find the latest file in `.specfact/plans/auto-derived.*.bundle.yaml`
- **"main plan"** or **"default plan"**: Use `.specfact/plans/main.bundle.yaml`
- **Missing target stage**: Infer next logical stage (draft→review→approved→released)

**If information is unclear**, ask the user directly in chat (don't redirect to terminal).

### 2. Execute Promotion Directly (AI IDE Chat)

**Load and promote the plan bundle directly** using Python:

1. **Find the plan file** (handle special cases like "last imported brownfield plan")
2. **Load the plan bundle** using `specfact_cli.validators.schema.validate_plan_bundle()` and `specfact_cli.utils.yaml_utils.load_yaml()`
3. **Check current stage** from `bundle.metadata.stage` (defaults to "draft" if None)
4. **Validate promotion rules**:
   - Cannot promote backward (e.g., review → draft)
   - **draft → review**: All features must have at least one story
   - **review → approved**: All features and stories must have acceptance criteria
   - **approved → released**: Requires confirmation (implementation check not yet implemented)
5. **Run validation** (if enabled) using `validate_plan_bundle()`
6. **Update metadata**:
   - Set `bundle.metadata.stage = target_stage`
   - Set `bundle.metadata.promoted_at = datetime.now(UTC).isoformat()`
   - Set `bundle.metadata.promoted_by = os.environ.get("USER") or "unknown"`
7. **Save the plan** using `specfact_cli.generators.plan_generator.PlanGenerator().generate()`
8. **Present results** in chat with clear formatting

### 3. Present Results in Chat

**Show results directly in chat** (don't redirect to terminal):

**Execute the promotion directly** using Python imports:

```python
from pathlib import Path
from datetime import datetime, UTC
import os
from specfact_cli.validators.schema import validate_plan_bundle
from specfact_cli.utils.yaml_utils import load_yaml
from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.models.plan import Metadata
from specfact_cli.utils.structure import SpecFactStructure

# 1. Find plan file (handle special cases)
if "last imported brownfield plan" in user_input or "last brownfield" in user_input:
    plan_path = SpecFactStructure.get_latest_brownfield_report()
    if not plan_path:
        # Show error in chat
        return
elif "main plan" in user_input or "default plan" in user_input:
    plan_path = SpecFactStructure.get_default_plan_path()
else:
    # Parse explicit path from user input
    plan_path = Path(...)

# 2. Load plan bundle
is_valid, error, bundle = validate_plan_bundle(plan_path)

# 3. Check current stage
current_stage = bundle.metadata.stage if bundle.metadata else "draft"

# 4. Validate promotion rules
# ... (validation logic)

# 5. Update metadata
bundle.metadata.stage = target_stage
bundle.metadata.promoted_at = datetime.now(UTC).isoformat()
bundle.metadata.promoted_by = os.environ.get("USER") or "unknown"

# 6. Save plan
generator = PlanGenerator()
generator.generate(bundle, plan_path)

# 7. Present results in chat
```

### 4. Handle Common Scenarios

**If validation fails:**

- Show what's missing directly in chat (e.g., "2 features without stories")
- List the specific features/stories that need attention
- Suggest fixes or ask if they want to force promote anyway
- Don't proceed unless user confirms force promotion

**If already at target stage:**

- Inform the user in chat and show current stage
- Suggest next appropriate stage if relevant

**If trying to promote backward:**

- Explain why backward promotion isn't allowed (in chat)
- Show the current stage progression path
- Ask if they want to promote to a different forward stage

### 5. Present Results in Chat

**After successful promotion**, present results directly in chat:

**Format example:**

```markdown
✓ Plan Promotion Successful

**Plan**: `.specfact/plans/auto-derived-2025-11-04T23-00-41.bundle.yaml`
**Stage**: draft → review
**Promoted at**: 2025-11-04T22:02:43.478499+00:00
**Promoted by**: dom

**Validation**: ✓ Passed
- ✓ All features have at least one story (11 features, 22 stories)
- ✓ Plan structure is valid
- ✓ All required fields are present

**Next Steps**:
- Review the plan bundle for completeness
- Ensure all features have acceptance criteria
- When ready, promote to approved: `/specfact-cli/specfact-plan-promote approved`
```

**If there are issues**, present them in chat:

```markdown
⚠ Cannot Promote to Review

**Issue**: 2 features without stories
- FEATURE-001: User Authentication
- FEATURE-002: Payment Processing

**Fix**: Add at least one story to each feature
**Alternative**: If you're aware of these issues, I can force promote anyway
```

### 6. CLI Alternative (For Pro Users)

**Only mention CLI as alternative** if the user explicitly asks or prefers terminal interaction:

```markdown
💡 **Pro Tip**: If you prefer terminal interaction, you can also use:

```bash
specfact plan promote --stage review --plan .specfact/plans/auto-derived-2025-11-04T23-00-41.bundle.yaml
```

```

**Key Principle**: CLI commands are mentioned as an alternative, not the primary interaction method.

## Interaction Guidelines

### Primary: Chat-Based Interaction

- **Interact directly in chat**: Don't redirect to terminal unless explicitly requested
- **Execute promotion logic directly**: Use Python imports to load, validate, update, and save plans
- **Present results in chat**: Show validation results, promotion status, and next steps directly
- **Handle special cases**: Understand "last imported brownfield plan", "main plan", etc.

### Secondary: CLI Alternative

- **Only mention CLI when**: User explicitly asks or prefers terminal interaction
- **Pro users**: CLI commands are available for automation and scripting
- **Example**: `specfact plan promote --stage review --plan PATH`

## Tips for the User

- **Start at draft**: New plans begin at draft stage automatically
- **Review before approving**: Make sure all features have stories and acceptance criteria before promoting to approved
- **Use validation**: Validation is enabled by default to catch issues early
- **Stage progression**: You can only move forward (draft → review → approved → released), not backward
- **Natural language**: You can say "promote last imported brownfield plan" or "promote main plan to review"

## Context

{ARGS}
