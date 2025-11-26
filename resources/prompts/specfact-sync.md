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
2. **ALWAYS use non-interactive mode for CI/CD**: When executing CLI commands, use appropriate flags to avoid interactive prompts that can cause timeouts in Copilot environments
3. **ALWAYS use tools for read/write**: Use file reading tools (e.g., `read_file`) to read artifacts for display purposes only. Use CLI commands for all write operations. Never use direct file manipulation.
4. **NEVER modify .specfact folder directly**: Do NOT create, modify, or delete any files in `.specfact/` or `.specify/` folders directly. All operations must go through the CLI or Spec-Kit commands.
5. **NEVER write code**: Do not implement sync logic - the CLI handles this
6. **NEVER create YAML/JSON directly**: All sync operations must be CLI-generated
7. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata - use it, don't bypass its validation
8. **Use CLI output as grounding**: Parse CLI output, don't regenerate or recreate it - use the CLI output as the source of truth
9. **NEVER manipulate internal code**: Do NOT use Python code to directly modify PlanBundle objects, SpecKit artifacts, or any internal data structures. The CLI is THE interface - use it exclusively.
10. **No internal knowledge required**: You should NOT need to know about internal implementation details (PlanBundle model, SpecKit converter, etc.). All operations must be performed via CLI commands.

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

Synchronize external tool artifacts (Spec-Kit, Linear, Jira, etc.) with SpecFact project bundles bidirectionally using bridge architecture. This command enables seamless integration between external tools and SpecFact contract-driven development, allowing teams to use either tooling while maintaining consistency.

**Note**: This is a **read-write operation** - it modifies both external tool artifacts and SpecFact project bundles to keep them in sync. Uses configurable bridge mappings (`.specfact/config/bridge.yaml`) to translate between tool-specific formats and SpecFact structure.

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
specfact sync bridge --adapter <adapter> --bundle <bundle-name> [--repo PATH] [--bidirectional] [--overwrite] [--watch] [--interval SECONDS]
```

**Adapters**: `speckit` (Spec-Kit), `generic-markdown` (generic markdown specs). Auto-detected if not specified.

**Note**: Mode is auto-detected by the CLI. No need to specify `--mode` flag.

**CRITICAL**: Always execute this CLI command. Never perform sync operations directly.

## Quick Reference

**Arguments:**

- `--adapter <adapter>` - Adapter type: `speckit`, `generic-markdown` (default: auto-detect)
- `--bundle <bundle-name>` - Project bundle name (required for SpecFact → tool sync)
- `--repo PATH` - Repository path (default: current directory)
- `--bidirectional` - Enable bidirectional sync (tool ↔ SpecFact) - **ASK USER if not provided**
- `--overwrite` - Overwrite existing tool artifacts (delete all existing before sync) - **ASK USER if intent is clear**
- `--watch` - Watch mode for continuous sync
- `--interval SECONDS` - Watch interval (default: 5, only with `--watch`)

**What it does:**

1. Auto-detects adapter type and tool repository structure (or uses `--adapter`)
2. Loads or generates bridge configuration (`.specfact/config/bridge.yaml`)
3. **Validates prerequisites**:
   - Bridge configuration must exist (auto-generated if missing)
   - For Spec-Kit adapter: Constitution (`.specify/memory/constitution.md`) must exist and be populated
   - For unidirectional sync: At least one tool artifact must exist (per bridge mapping)
4. Auto-creates SpecFact project bundle structure if missing
5. Syncs tool → SpecFact (unidirectional) or both directions (bidirectional) using bridge mappings
6. Reports sync summary with features updated/added

**Prerequisites:**

Before running sync, ensure you have:

1. **Bridge Configuration** (REQUIRED):
   - Auto-generated via `specfact bridge probe` (recommended)
   - Or manually create `.specfact/config/bridge.yaml` with adapter mappings
   - Bridge config maps SpecFact concepts to tool-specific paths

2. **Tool-Specific Prerequisites** (varies by adapter):
   - **Spec-Kit adapter**: Constitution (`.specify/memory/constitution.md`) must exist and be populated
     - Generate via `specfact constitution bootstrap --repo .` (brownfield) or `/speckit.constitution` (greenfield)
   - **Generic markdown**: Tool artifacts must exist per bridge mapping

3. **SpecFact Project Bundle** (REQUIRED for bidirectional sync when syncing SpecFact → tool):
   - Must have a valid project bundle at `.specfact/projects/<bundle-name>/` (specify with `--bundle`)

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

1. **Before sync**: Use `specfact plan review` to enrich plan bundle with additional context that will be reflected in Spec-Kit artifacts
2. **After sync**: Use Spec-Kit commands (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks`) to customize the generated Spec-Kit artifacts - **DO NOT edit files directly in .specify/ or .specfact/ folders**
3. **During sync** (if implemented): The CLI may prompt for customization options in interactive mode

**⚠️ CRITICAL**: Never edit `.specfact/` or `.specify/` artifacts directly. Always use CLI commands or Spec-Kit commands for modifications.

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

**Step 4**: Check if `--bundle` should be specified.

- **If bundle name is missing**: Ask user and **WAIT**:

  ```text
  "Which project bundle should be used? (e.g., 'legacy-api', 'auth-module')
  [WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
  ```

  - **If user provides bundle name**: Use `--bundle <name>`
  - **If user mentions "auto-derived" or "from code"**: Suggest using the bundle created from `specfact import from-code`

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
specfact sync bridge --adapter <adapter> --bundle <bundle-name> --repo <repo_path> [--bidirectional] [--overwrite]
```

**Capture CLI output**:

- Sync summary (features updated/added)
- **Deduplication summary**: "✓ Removed N duplicate features from plan bundle" (if duplicates were found)
- Tool artifacts created/updated (with all required fields auto-generated per bridge mapping)
- SpecFact project bundle created/updated at `.specfact/projects/<bundle-name>/`
- Any error messages or warnings

**Understanding Deduplication**:

The CLI automatically deduplicates features during sync using normalized key matching:

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
3. **Analyze code coverage**: If multiple features reference the same code files/modules, they might be the same feature
4. **Suggest consolidation**: When semantic duplicates are found:
   - Use `specfact plan update-feature` to merge information into one feature
   - Use `specfact plan add-feature` to create a consolidated feature if needed
   - Remove duplicate features using appropriate CLI commands

**Example Semantic Duplicate Detection**:

```text
After sync, review the plan bundle and identify:
- Features with similar titles but different keys
- Features covering the same code modules
- Features with overlapping user stories
- Features that represent the same functionality

If semantic duplicates are found, suggest consolidation:
"Found semantic duplicates: FEATURE-GITOPERATIONS and FEATURE-GITOPERATIONSHANDLER
both cover git operations. Should I consolidate these into a single feature?"
```

**Step 8**: After sync completes, guide user on next steps.

- **Always suggest validation**: After successful sync, remind user to run `/speckit.analyze`:

  ```text
  "Sync completed successfully! Run '/speckit.analyze' to validate artifact consistency and quality.
  This will check for ambiguities, duplications, and constitution alignment."
  ```

- **If bidirectional sync completed**: Remind user that all tool-specific fields are auto-generated per bridge mapping
  - **For Spec-Kit adapter**: Artifacts are ready for `/speckit.analyze` (requires `spec.md`, `plan.md`, `tasks.md`, and constitution)
  - **Constitution Check status**: Generated `plan.md` files have Constitution Check gates set to "PENDING" - users should review and check gates based on their project's actual state

- **If customization was requested**: Guide user to edit generated files:
  - `specs/<feature-num>-<feature-name>/spec.md` - Customize frontmatter, INVSEST, scenarios
  - `specs/<feature-num>-<feature-name>/plan.md` - Customize Constitution Check, Phases, Technology Stack
  - `specs/<feature-num>-<feature-name>/tasks.md` - Customize phase organization, story mappings
  - **After customization**: User should run `/speckit.analyze` to validate consistency across all artifacts

## Expected Output

**Unidirectional sync:**

```bash
Syncing speckit artifacts from: /path/to/repo
✓ Detected adapter: speckit
✓ Bridge configuration loaded
✓ Constitution found and validated
📦 Scanning tool artifacts...
✓ Found 5 features in specs/
✓ Detected SpecFact project bundle (or created automatically)
📝 Converting to SpecFact format...
  - Updated 2 features
  - Added 0 new features
✓ Sync complete!

Sync Summary (Unidirectional):
  - Updated: 2 features
  - Added: 0 new features
  - Direction: tool → SpecFact
  - Project bundle: .specfact/projects/legacy-api/

Next Steps:
  Run '/speckit.analyze' to validate artifact consistency and quality
  This will check for ambiguities, duplications, and constitution alignment

✓ Sync complete!
```

**Error example (missing bridge config):**

```bash
Syncing artifacts from: /path/to/repo
✗ Bridge configuration not found
Bridge config file not found: .specfact/config/bridge.yaml

Next Steps:
1. Run 'specfact bridge probe' to auto-detect and generate bridge configuration
   OR manually create .specfact/config/bridge.yaml with adapter mappings
2. Then run 'specfact sync bridge --adapter <adapter> --bundle <bundle-name>' again
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
Syncing artifacts from: /path/to/repo
✓ Detected adapter: speckit
✓ Bridge configuration loaded
✓ Constitution found and validated
📦 Scanning tool artifacts...
✓ Found 0 features in specs/
✗ No tool artifacts found
Unidirectional sync (tool → SpecFact) requires at least one tool artifact per bridge mapping.

Next Steps:
1. For Spec-Kit: Run '/speckit.specify' command to create feature specifications
2. For other adapters: Create artifacts per bridge configuration mapping
3. Then run 'specfact sync bridge --adapter <adapter> --bundle <bundle-name>' again

Note: For bidirectional sync, tool artifacts are optional if syncing from SpecFact → tool
```

**Bidirectional sync** adds:

```bash
Syncing artifacts from: /path/to/repo
✓ Detected adapter: speckit
✓ Bridge configuration loaded
✓ Constitution found and validated
📦 Scanning tool artifacts...
✓ Found 2 features in specs/
✓ Detected SpecFact project bundle: .specfact/projects/legacy-api/
📝 Converting tool → SpecFact...
  - Updated 2 features
  - Added 0 new features
🔄 Converting SpecFact → tool...
✓ Converted 2 features to tool format
✓ Generated tool-compatible artifacts (per bridge mapping):
  - spec.md with frontmatter, INVSEST criteria, scenarios
  - plan.md with Constitution Check, Phases, Technology Stack
  - tasks.md with phase organization and parallel markers
✓ No conflicts detected

Sync Summary (Bidirectional):
  - tool → SpecFact: Updated 2, Added 0 features
  - SpecFact → tool: 2 features converted to tool format
  - Project bundle: .specfact/projects/legacy-api/
  - Format Compatibility: ✅ Full (works with tool-specific commands)
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
