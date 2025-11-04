---
description: Synchronize Spec-Kit artifacts with SpecFact plans bidirectionally.
---
# SpecFact Sync Command

## User Input

```text
$ARGUMENTS
```

## Action Required

**If arguments provided**: Execute `specfact sync spec-kit` immediately with provided arguments.

**If arguments missing**: Ask user interactively for:

1. **Sync direction**: "Unidirectional (Spec-Kit → SpecFact)" or "Bidirectional (both directions)"?
2. **Repository path**: "Which repository path? (default: current directory)"
3. **Confirmation**: Confirm before executing

**Only execute after** getting necessary information from user.

## Command

```bash
specfact sync spec-kit [--repo PATH] [--bidirectional] [--plan PATH] [--overwrite] [--watch] [--interval SECONDS]
```

## Quick Reference

**Arguments:**

- `--repo PATH` - Repository path (default: current directory)
- `--bidirectional` - Enable bidirectional sync (Spec-Kit ↔ SpecFact) - **ASK USER if not provided**
- `--plan PATH` - Path to SpecFact plan bundle for SpecFact → Spec-Kit conversion (default: main plan)
- `--overwrite` - Overwrite existing Spec-Kit artifacts (delete all existing before sync) - **ASK USER if intent is clear**
- `--watch` - Watch mode (not implemented - will exit with message)
- `--interval SECONDS` - Watch interval (default: 5, only with `--watch`)

**What it does:**

1. Detects Spec-Kit repository (exits with error if not found)
2. Auto-creates SpecFact structure if missing
3. Syncs Spec-Kit → SpecFact (unidirectional) or both directions (bidirectional)
4. Reports sync summary with features updated/added

**Spec-Kit Format Compatibility:**

When exporting to Spec-Kit (bidirectional sync), the generated artifacts are **fully compatible** with Spec-Kit commands (`/speckit.analyze`, `/speckit.implement`, `/speckit.checklist`). The export includes:

- **spec.md**: Frontmatter (Feature Branch, Created date, Status), INVSEST criteria, Scenarios (Primary, Alternate, Exception, Recovery), "Why this priority" text
- **plan.md**: Constitution Check section (Article VII, VIII, IX), Phases (Phase 0, Phase 1, Phase 2, Phase -1), Technology Stack, Constraints, Unknowns
- **tasks.md**: Phase organization (Phase 1: Setup, Phase 2: Foundational, Phase 3+: User Stories), Parallel markers [P], Story mappings

This ensures exported Spec-Kit artifacts work seamlessly with Spec-Kit slash commands.

## Interactive Flow

**Step 1**: Check if `--bidirectional` or sync direction is specified in user input.

- **If missing**: Ask user: "Sync direction? (1) Unidirectional: Spec-Kit → SpecFact, (2) Bidirectional: both directions"
- **If provided**: Use specified direction

**Step 2**: Check if `--repo` is specified.

- **If missing**: Ask user: "Repository path? (default: current directory '.')"
- **If provided**: Use specified path

**Step 3**: Check if intent is clear for SpecFact → Spec-Kit sync.

- **If bidirectional is enabled OR user input mentions "update spec-kit" or "sync to spec-kit"**: Ask about overwrite mode
  - Ask user: "How should SpecFact → Spec-Kit sync work? (1) Merge: Keep existing Spec-Kit artifacts and update/merge, (2) Overwrite: Delete all existing Spec-Kit artifacts and replace with SpecFact plan"
  - **If merge (default)**: Use without `--overwrite`
  - **If overwrite**: Add `--overwrite` flag
- **If intent is not clear**: Skip this step

**Step 4**: Check if `--plan` should be specified.

- **If user input mentions "auto-derived", "from code", "brownfield", or "code2spec"**: Suggest using auto-derived plan
  - Ask user: "Use auto-derived plan (from codebase) instead of main plan? (y/n)"
  - **If yes**: Find latest auto-derived plan in `.specfact/reports/brownfield/` and add `--plan PATH`
  - **If no**: Use default main plan

**Step 5**: Confirm execution.

- Show summary: "Will sync [DIRECTION] in [REPO_PATH] [with overwrite mode if enabled] [using PLAN_PATH if specified]. Continue? (y/n)"
- **If yes**: Execute command
- **If no**: Cancel or ask for changes

**Step 6**: Execute command with confirmed arguments.

## Expected Output

**Unidirectional sync:**

```bash
Syncing Spec-Kit artifacts from: /path/to/repo
✓ Detected Spec-Kit repository
✓ Detected SpecFact structure (or created automatically)
📦 Scanning Spec-Kit artifacts...
✓ Found 5 features in specs/
📝 Converting to SpecFact format...
  - Updated 2 features
  - Added 0 new features
✓ Sync complete!

Sync Summary (Unidirectional):
  - Updated: 2 features
  - Added: 0 new features
  - Direction: Spec-Kit → SpecFact
```

**Bidirectional sync** adds:

```bash
🔄 Converting SpecFact → Spec-Kit...
✓ Converted 2 features to Spec-Kit
✓ Generated Spec-Kit compatible artifacts:
  - spec.md with frontmatter, INVSEST criteria, scenarios
  - plan.md with Constitution Check, Phases, Technology Stack
  - tasks.md with phase organization and parallel markers
✓ No conflicts detected

Sync Summary (Bidirectional):
  - Spec-Kit → SpecFact: Updated 2, Added 0 features
  - SpecFact → Spec-Kit: 2 features converted to Spec-Kit markdown
  - Format Compatibility: ✅ Full (works with /speckit.analyze, /speckit.implement, /speckit.checklist)
  - Conflicts: None detected
```

**Bidirectional sync with overwrite** adds:

```bash
🔄 Converting SpecFact → Spec-Kit...
⚠ Overwrite mode: Removing existing Spec-Kit artifacts...
✓ Existing artifacts removed
✓ Converted 32 features to Spec-Kit
✓ Generated Spec-Kit compatible artifacts:
  - spec.md with frontmatter, INVSEST criteria, scenarios
  - plan.md with Constitution Check, Phases, Technology Stack
  - tasks.md with phase organization and parallel markers
✓ No conflicts detected

Sync Summary (Bidirectional):
  - Spec-Kit → SpecFact: Updated 2, Added 0 features
  - SpecFact → Spec-Kit: 32 features converted to Spec-Kit markdown (overwritten)
  - Format Compatibility: ✅ Full (works with /speckit.analyze, /speckit.implement, /speckit.checklist)
  - Conflicts: None detected
```

## Context

{ARGS}
