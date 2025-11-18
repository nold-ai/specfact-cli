---
description: Synchronize Spec-Kit artifacts with SpecFact plans bidirectionally.
---
# SpecFact Sync Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly or implement functionality.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact sync spec-kit` before any sync operation - execute the CLI command before any other operations
2. **NEVER write code**: Do not implement sync logic - the CLI handles this
3. **NEVER create YAML/JSON directly**: All sync operations must be CLI-generated
4. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata - use it, don't bypass its validation
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate or recreate it - use the CLI output as the source of truth
6. **NEVER manipulate internal code**: Do NOT use Python code to directly modify PlanBundle objects, SpecKit artifacts, or any internal data structures. The CLI is THE interface - use it exclusively.
7. **No internal knowledge required**: You should NOT need to know about internal implementation details (PlanBundle model, SpecKit converter, etc.). All operations must be performed via CLI commands.

### What Happens If You Don't Follow This

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures
- ❌ Works only in Copilot mode, fails in CI/CD
- ❌ Breaks when CLI internals change
- ❌ Requires knowledge of internal code structure

## ⏸️ Wait States: User Input Required

**When user input is required, you MUST wait for the user's response.**

### Wait State Rules

1. **Never assume**: If input is missing, ask and wait
2. **Never continue**: Do not proceed until user responds
3. **Be explicit**: Clearly state what information you need
4. **Provide options**: Give examples or default suggestions

## Goal

Synchronize Spec-Kit artifacts with SpecFact plan bundles bidirectionally. This command enables seamless integration between Spec-Kit workflows and SpecFact contract-driven development, allowing teams to use either tooling while maintaining consistency.

**Note**: This is a **read-write operation** - it modifies both Spec-Kit and SpecFact artifacts to keep them in sync.

## Action Required

**If arguments provided**: Execute `specfact sync spec-kit` immediately with provided arguments.

**If arguments missing**: Ask user interactively for each missing argument and **WAIT for their response**:

1. **Sync direction**: "Sync direction? (1) Unidirectional: Spec-Kit → SpecFact, (2) Bidirectional: both directions"
   - **[WAIT FOR USER RESPONSE - DO NOT CONTINUE]**

2. **Repository path**: "Repository path? (default: current directory '.')"
   - **[WAIT FOR USER RESPONSE - DO NOT CONTINUE]**

3. **Confirmation**: Confirm before executing
   - **[WAIT FOR USER RESPONSE - DO NOT CONTINUE]**

**Only execute CLI after** getting necessary information from user.

## Operating Constraints

**STRICTLY READ-WRITE**: This command modifies Spec-Kit and SpecFact artifacts. All sync operations must be performed by the specfact CLI.

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag. Mode is detected from:

- Environment variables (`SPECFACT_MODE`)
- CoPilot API availability
- IDE integration (VS Code/Cursor with CoPilot)
- Defaults to CI/CD mode if none detected

## Command

```bash
specfact sync spec-kit [--repo PATH] [--bidirectional] [--plan PATH] [--overwrite] [--watch] [--interval SECONDS]
```

**Note**: Mode is auto-detected by the CLI. No need to specify `--mode` flag.

**CRITICAL**: Always execute this CLI command. Never perform sync operations directly.

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
2. **Validates prerequisites**:
   - Constitution (`.specify/memory/constitution.md`) must exist and be populated (not just template placeholders)
   - For unidirectional sync: At least one `spec.md` file must exist in `specs/` directories
3. Auto-creates SpecFact structure if missing
4. Syncs Spec-Kit → SpecFact (unidirectional) or both directions (bidirectional)
5. Reports sync summary with features updated/added

**Prerequisites:**

Before running sync, ensure you have:

1. **Constitution** (REQUIRED for all sync operations):
   - **Option 1 (Recommended for brownfield)**: Run `specfact constitution bootstrap --repo .` to auto-generate from repository analysis
     - This analyzes your repository (README.md, pyproject.toml, .cursor/rules/, docs/rules/) and generates a bootstrap constitution
     - Perfect for brownfield projects where you want to extract principles from existing codebase
   - **Option 2 (Manual)**: Run `/speckit.constitution` command in your AI assistant and fill in the template
     - Use this for greenfield projects or when you want full manual control
   - **Enrichment**: If you have a minimal constitution, run `specfact constitution enrich --repo .` to fill placeholders
   - **Validation**: Run `specfact constitution validate` to check completeness before sync
   - The constitution must be populated (not just template placeholders like `[PROJECT_NAME]`)

2. **Spec-Kit Features** (REQUIRED for unidirectional sync):
   - Run `/speckit.specify` command to create at least one feature specification
   - Creates `specs/[###-feature-name]/spec.md` files
   - Optional: Run `/speckit.plan` and `/speckit.tasks` for complete artifacts

3. **SpecFact Plan** (REQUIRED for bidirectional sync when syncing SpecFact → Spec-Kit):
   - Must have a valid plan bundle at `.specfact/plans/main.bundle.yaml` (or specify with `--plan`)

**Validation Errors:**

If prerequisites are missing, the CLI will exit with clear error messages:

- **Constitution missing or empty**: "Constitution required. Run 'specfact constitution bootstrap --repo .' to auto-generate, or '/speckit.constitution' command to create manually."
- **No features found (unidirectional sync)**: "No Spec-Kit features found. Run '/speckit.specify' command first."

**Spec-Kit Format Compatibility:**

When exporting to Spec-Kit (bidirectional sync), the generated artifacts are **fully compatible** with Spec-Kit commands (`/speckit.analyze`, `/speckit.implement`, `/speckit.checklist`). The export includes:

- **spec.md**: Frontmatter (Feature Branch, Created date, Status), INVSEST criteria, Scenarios (Primary, Alternate, Exception, Recovery), "Why this priority" text
- **plan.md**: Constitution Check section (Article VII, VIII, IX), Phases (Phase 0, Phase 1, Phase 2, Phase -1), Technology Stack, Constraints, Unknowns
- **tasks.md**: Phase organization (Phase 1: Setup, Phase 2: Foundational, Phase 3+: User Stories), Parallel markers [P], Story mappings

This ensures exported Spec-Kit artifacts work seamlessly with Spec-Kit slash commands.

**Workflow Integration:**

After running `specfact sync spec-kit --bidirectional`, you can immediately run `/speckit.analyze` to validate consistency across all artifacts. The sync command ensures all prerequisites for `/speckit.analyze` are met:

- ✅ Constitution (`.specify/memory/constitution.md`) - Validated before sync
- ✅ spec.md - Generated during sync
- ✅ plan.md - Generated during sync
- ✅ tasks.md - Generated during sync

**Note**: `/speckit.analyze` is a read-only analysis command that checks for inconsistencies, duplications, ambiguities, and constitution alignment across the three core artifacts. It does not modify files.

**⚠️ Spec-Kit Requirements Fulfillment:**

The CLI automatically generates all required Spec-Kit fields during sync. However, you may want to customize some fields for your project:

1. **Constitution Check Gates** (plan.md): Default gates are provided, but you may want to customize Article VII/VIII/IX checks for your project
2. **Phase Organization** (plan.md, tasks.md): Default phases are auto-generated, but you may want to reorganize tasks into different phases
3. **Feature Branch Name** (spec.md): Auto-generated from feature key, but you can customize if needed
4. **INVSEST Criteria** (spec.md): Auto-generated as "YES" for all criteria, but you may want to adjust based on story characteristics

**Optional Customization Workflow:**

If you want to customize Spec-Kit-specific fields, you can:

1. **After sync**: Edit the generated `spec.md`, `plan.md`, and `tasks.md` files directly
2. **Before sync**: Use `specfact plan review` to enrich plan bundle with additional context that will be reflected in Spec-Kit artifacts
3. **During sync** (if implemented): The CLI may prompt for customization options in interactive mode

**Note**: All Spec-Kit fields are auto-generated with sensible defaults, so manual customization is **optional** unless you have specific project requirements.

## Interactive Flow

**Step 1**: Check if `--bidirectional` or sync direction is specified in user input.

- **If missing**: Ask user and **WAIT**:

  ```text
  "Sync direction? (1) Unidirectional: Spec-Kit → SpecFact, (2) Bidirectional: both directions
  [WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
  ```

- **If provided**: Use specified direction

**Step 2**: Check if `--repo` is specified.

- **If missing**: Ask user and **WAIT**:

  ```text
  "Repository path? (default: current directory '.')
  [WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
  ```

- **If provided**: Use specified path

**Step 3**: Check if intent is clear for SpecFact → Spec-Kit sync.

- **If bidirectional is enabled OR user input mentions "update spec-kit" or "sync to spec-kit"**: Ask about overwrite mode and **WAIT**:

  ```text
  "How should SpecFact → Spec-Kit sync work? 
  (1) Merge: Keep existing Spec-Kit artifacts and update/merge, 
  (2) Overwrite: Delete all existing Spec-Kit artifacts and replace with SpecFact plan
  [WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
  ```

  - **If merge (default)**: Use without `--overwrite`
  - **If overwrite**: Add `--overwrite` flag
- **If intent is not clear**: Skip this step

**Step 4**: Check if `--plan` should be specified.

- **If user input mentions "auto-derived", "from code", "brownfield", or "code2spec"**: Suggest using auto-derived plan and **WAIT**:

  ```text
  "Use auto-derived plan (from codebase) instead of main plan? (y/n)
  [WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
  ```

  - **If yes**: Find latest auto-derived plan in `.specfact/plans/` and add `--plan PATH`
  - **If no**: Use default main plan

**Step 5**: Check if user wants to customize Spec-Kit-specific fields (OPTIONAL).

- **If bidirectional sync is enabled**: Ask user if they want to customize Spec-Kit fields and **WAIT**:

  ```text
  "The sync will generate complete Spec-Kit artifacts with all required fields (frontmatter, INVSEST, Constitution Check, Phases, etc.).
  
  Do you want to customize any Spec-Kit-specific fields? (y/n)
  - Constitution Check gates (Article VII/VIII/IX)
  - Phase organization
  - Feature branch names
  - INVSEST criteria adjustments
  
  [WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
  ```

  - **If yes**: Note that customization will be done after sync (edit generated files)
  - **If no**: Proceed with default auto-generated fields

- **If unidirectional sync**: Skip this step (no Spec-Kit artifacts generated)

**Step 6**: Confirm execution.

- Show summary and **WAIT**:

  ```text
  "Will sync [DIRECTION] in [REPO_PATH] [with overwrite mode if enabled] [using PLAN_PATH if specified] [with Spec-Kit customization if requested]. 
  Continue? (y/n)
  [WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
  ```

- **If yes**: Execute CLI command
- **If no**: Cancel or ask for changes

**Step 7**: Execute CLI command with confirmed arguments.

```bash
specfact sync spec-kit --repo <repo_path> [--bidirectional] [--plan <plan_path>] [--overwrite]
```

**Capture CLI output**:

- Sync summary (features updated/added)
- Spec-Kit artifacts created/updated (with all required fields auto-generated)
- SpecFact artifacts created/updated
- Any error messages or warnings

**Step 8**: After sync completes, guide user on next steps.

- **Always suggest validation**: After successful sync, remind user to run `/speckit.analyze`:

  ```text
  "Sync completed successfully! Run '/speckit.analyze' to validate artifact consistency and quality.
  This will check for ambiguities, duplications, and constitution alignment."
  ```

- **If bidirectional sync completed**: Remind user that all Spec-Kit fields are auto-generated and ready for `/speckit.analyze`
  - **Note**: `/speckit.analyze` requires `spec.md`, `plan.md`, and `tasks.md` to exist. The sync command generates all three files, so artifacts are ready for analysis.
  - **Constitution requirement**: `/speckit.analyze` also requires the constitution (`.specify/memory/constitution.md`) which is validated before sync, so this prerequisite is already met.
  - **Constitution Check status**: Generated `plan.md` files have Constitution Check gates set to "PENDING" - users should review and check gates based on their project's actual state

- **If customization was requested**: Guide user to edit generated files:
  - `specs/<feature-num>-<feature-name>/spec.md` - Customize frontmatter, INVSEST, scenarios
  - `specs/<feature-num>-<feature-name>/plan.md` - Customize Constitution Check, Phases, Technology Stack
  - `specs/<feature-num>-<feature-name>/tasks.md` - Customize phase organization, story mappings
  - **After customization**: User should run `/speckit.analyze` to validate consistency across all artifacts

## Expected Output

**Unidirectional sync:**

```bash
Syncing Spec-Kit artifacts from: /path/to/repo
✓ Detected Spec-Kit repository
✓ Constitution found and validated
📦 Scanning Spec-Kit artifacts...
✓ Found 5 features in specs/
✓ Detected SpecFact structure (or created automatically)
📝 Converting to SpecFact format...
  - Updated 2 features
  - Added 0 new features
✓ Sync complete!

Sync Summary (Unidirectional):
  - Updated: 2 features
  - Added: 0 new features
  - Direction: Spec-Kit → SpecFact

Next Steps:
  Run '/speckit.analyze' to validate artifact consistency and quality
  This will check for ambiguities, duplications, and constitution alignment

✓ Sync complete!
```

**Error example (missing constitution):**

```bash
Syncing Spec-Kit artifacts from: /path/to/repo
✓ Detected Spec-Kit repository
✗ Constitution required
Constitution file not found: .specify/memory/constitution.md
The constitution is required before syncing Spec-Kit artifacts.

Next Steps:
1. Run 'specfact constitution bootstrap --repo .' to auto-generate from repository analysis (recommended for brownfield)
   OR run '/speckit.constitution' command in your AI assistant to create manually (for greenfield)
2. Review and adjust the generated constitution as needed
3. Run 'specfact constitution validate' to check completeness
4. Then run 'specfact sync spec-kit' again
```

**Error example (minimal constitution detected):**

```bash
Syncing Spec-Kit artifacts from: /path/to/repo
✓ Detected Spec-Kit repository
⚠ Constitution is minimal (essentially empty)
Generate bootstrap constitution from repository analysis? (y/n): y
Generating bootstrap constitution...
✓ Bootstrap constitution generated
Review and adjust as needed before syncing

Next Steps:
1. Review the generated constitution at .specify/memory/constitution.md
2. Adjust principles and sections as needed
3. Run 'specfact constitution validate' to check completeness
4. Then run 'specfact sync spec-kit' again
```

**Error example (no features for unidirectional sync):**

```bash
Syncing Spec-Kit artifacts from: /path/to/repo
✓ Detected Spec-Kit repository
✓ Constitution found and validated
📦 Scanning Spec-Kit artifacts...
✓ Found 0 features in specs/
✗ No Spec-Kit features found
Unidirectional sync (Spec-Kit → SpecFact) requires at least one feature specification.

Next Steps:
1. Run '/speckit.specify' command in your AI assistant to create feature specifications
2. Optionally run '/speckit.plan' and '/speckit.tasks' to create complete artifacts
3. Then run 'specfact sync spec-kit' again

Note: For bidirectional sync, Spec-Kit artifacts are optional if syncing from SpecFact → Spec-Kit
```

**Bidirectional sync** adds:

```bash
Syncing Spec-Kit artifacts from: /path/to/repo
✓ Detected Spec-Kit repository
✓ Constitution found and validated
📦 Scanning Spec-Kit artifacts...
✓ Found 2 features in specs/
✓ Detected SpecFact structure
📝 Converting Spec-Kit → SpecFact...
  - Updated 2 features
  - Added 0 new features
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

⚠ Note: Constitution Check gates in plan.md are set to PENDING - review and check gates based on your project's actual state

Next Steps:
  Run '/speckit.analyze' to validate artifact consistency and quality
  This will check for ambiguities, duplications, and constitution alignment

✓ Sync complete!
```

**Bidirectional sync with overwrite** adds:

```bash
Syncing Spec-Kit artifacts from: /path/to/repo
✓ Detected Spec-Kit repository
✓ Constitution found and validated
📦 Scanning Spec-Kit artifacts...
✓ Found 2 features in specs/
✓ Detected SpecFact structure
📝 Converting Spec-Kit → SpecFact...
  - Updated 2 features
  - Added 0 new features
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

⚠ Note: Constitution Check gates in plan.md are set to PENDING - review and check gates based on your project's actual state

Next Steps:
  Run '/speckit.analyze' to validate artifact consistency and quality
  This will check for ambiguities, duplications, and constitution alignment

✓ Sync complete!
```

## Context

{ARGS}
