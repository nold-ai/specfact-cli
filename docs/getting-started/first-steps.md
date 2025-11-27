# Your First Steps with SpecFact CLI

This guide walks you through your first commands with SpecFact CLI, with step-by-step explanations.

## Before You Start

- [Install SpecFact CLI](installation.md) (if not already installed)
- **Python 3.11+ required**: Check with `python3 --version`
- Choose your scenario below

**Installation Options**:

- **Quick start (CLI-only)**: `uvx specfact-cli@latest --help` (no installation needed)
- **Better results (Interactive)**: `pip install specfact-cli` + `specfact init` (recommended for legacy code)

---

## Scenario 1: Modernizing Legacy Code ⭐ PRIMARY

**Goal**: Reverse engineer existing code into documented specs

**Time**: < 5 minutes

### Step 1: Analyze Your Legacy Codebase

**Option A: CLI-only Mode** (Quick start, works with uvx):

```bash
uvx specfact-cli@latest import from-code my-project --repo .
```

**Option B: Interactive AI Assistant Mode** (Recommended for better results):

```bash
# Step 1: Install SpecFact CLI
pip install specfact-cli

# Step 2: Navigate to your project
cd /path/to/your/project

# Step 3: Initialize IDE integration (one-time)
specfact init

# Step 4: Use slash command in IDE chat
/specfact-import-from-code
# The AI assistant will prompt you for bundle name
```

**What happens**:

- Analyzes all Python files in your repository
- Extracts features, user stories, and business logic from code
- Generates dependency graphs
- Creates plan bundle with extracted specs

**Example output** (Interactive mode - better results):

```bash
✅ Analyzed 47 Python files
✅ Extracted 23 features
✅ Generated 112 user stories
⏱️  Completed in 8.2 seconds
```

**Example output** (CLI-only mode - may show 0 features for simple cases):

```bash
✅ Analyzed 3 Python files
✅ Extracted 0 features  # ⚠️ AST-based analysis may miss features in simple code
✅ Generated 0 user stories
⏱️  Completed in 2.1 seconds
```

**Note**: CLI-only mode uses AST-based analysis which may show 0 features for simple test cases. Interactive AI Assistant mode provides better semantic understanding and feature detection.

### Step 2: Review Extracted Specs

```bash
# Review the extracted bundle using CLI commands
specfact plan review my-project

# Or get structured findings for analysis
specfact plan review my-project --list-findings --findings-format json
```

Review the auto-generated plan to understand what SpecFact discovered about your codebase.

**Note**: Use CLI commands to interact with bundles. The bundle structure is managed by SpecFact CLI - use commands like `plan review`, `plan add-feature`, `plan update-feature` to work with bundles, not direct file editing.

**💡 Tip**: If you plan to sync with Spec-Kit later, the import command will suggest generating a bootstrap constitution. You can also run it manually:

```bash
specfact bridge constitution bootstrap --repo .
```

### Step 3: Add Contracts to Critical Functions

```bash
# Start in shadow mode (observe only)
specfact enforce stage --preset minimal
```

See [Brownfield Engineer Guide](../guides/brownfield-engineer.md) for complete workflow.

---

## Scenario 2: Starting a New Project (Alternative)

**Goal**: Create a plan before writing code

**Time**: 5-10 minutes

### Step 1: Initialize a Plan

```bash
specfact plan init my-project --interactive
```

**What happens**:

- Creates `.specfact/` directory structure
- Prompts you for project title and description
- Creates modular project bundle at `.specfact/projects/my-project/`

**Example output**:

```bash
📋 Initializing new development plan...

Enter project title: My Awesome Project
Enter project description: A project to demonstrate SpecFact CLI

✅ Plan initialized successfully!
📁 Project bundle: .specfact/projects/my-project/
```

### Step 2: Add Your First Feature

```bash
specfact plan add-feature \
  --bundle my-project \
  --key FEATURE-001 \
  --title "User Authentication" \
  --outcomes "Users can login securely"
```

**What happens**:

- Adds a new feature to your project bundle
- Creates a feature with key `FEATURE-001`
- Sets the title and outcomes

### Step 3: Add Stories to the Feature

```bash
specfact plan add-story \
  --bundle my-project \
  --feature FEATURE-001 \
  --title "As a user, I can login with email and password" \
  --acceptance "Login form validates input" \
  --acceptance "User is redirected after successful login"
```

**What happens**:

- Adds a user story to the feature
- Defines acceptance criteria
- Links the story to the feature

### Step 4: Validate the Plan

```bash
specfact repro
```

**What happens**:

- Validates the plan bundle structure
- Checks for required fields
- Reports any issues

**Expected output**:

```bash
✅ Plan validation passed
📊 Features: 1
📊 Stories: 1
```

### Next Steps

- [Use Cases](../guides/use-cases.md) - See real-world examples
- [Command Reference](../reference/commands.md) - Learn all commands
- [IDE Integration](../guides/ide-integration.md) - Set up slash commands

---

## Scenario 3: Migrating from Spec-Kit (Secondary)

**Goal**: Add automated enforcement to Spec-Kit project

**Time**: 15-30 minutes

### Step 1: Preview Migration

```bash
specfact import from-bridge \
  --repo ./my-speckit-project \
  --adapter speckit \
  --dry-run
```

**What happens**:

- Analyzes your Spec-Kit project structure
- Detects Spec-Kit artifacts (specs, plans, tasks, constitution)
- Shows what will be imported
- **Does not modify anything** (dry-run mode)

**Example output**:

```bash
🔍 Analyzing Spec-Kit project...
✅ Found .specify/ directory (modern format)
✅ Found specs/001-user-authentication/spec.md
✅ Found specs/001-user-authentication/plan.md
✅ Found specs/001-user-authentication/tasks.md
✅ Found .specify/memory/constitution.md

📊 Migration Preview:
  - Will create: .specfact/projects/<bundle-name>/ (modular project bundle)
  - Will create: .specfact/protocols/workflow.protocol.yaml (if FSM detected)
  - Will convert: Spec-Kit features → SpecFact Feature models
  - Will convert: Spec-Kit user stories → SpecFact Story models
  
🚀 Ready to migrate (use --write to execute)
```

### Step 2: Execute Migration

```bash
specfact import from-bridge \
  --repo ./my-speckit-project \
  --adapter speckit \
  --write
```

**What happens**:

- Imports Spec-Kit artifacts into SpecFact format using bridge architecture
- Creates `.specfact/` directory structure
- Converts Spec-Kit features and stories to SpecFact models
- Creates modular project bundle at `.specfact/projects/<bundle-name>/`
- Preserves all information

### Step 3: Review Generated Bundle

```bash
# Review the imported bundle
specfact plan review <bundle-name>

# Check bundle status
specfact plan select
```

**What was created**:

- Modular project bundle at `.specfact/projects/<bundle-name>/` with multiple aspect files
- `.specfact/protocols/workflow.protocol.yaml` - FSM definition (if protocol detected)
- `.specfact/gates/config.yaml` - Quality gates configuration

**Note**: Use CLI commands (`plan review`, `plan add-feature`, etc.) to interact with bundles. Do not edit `.specfact` files directly.

### Step 4: Set Up Bidirectional Sync (Optional)

Keep Spec-Kit and SpecFact synchronized:

```bash
# Generate constitution if missing (auto-suggested during sync)
specfact bridge constitution bootstrap --repo .

# One-time bidirectional sync
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional

# Continuous watch mode
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch --interval 5
```

**What happens**:

- **Constitution bootstrap**: Auto-generates constitution from repository analysis (if missing or minimal)
- Syncs changes between Spec-Kit and SpecFact
- Bidirectional: changes in either direction are synced
- Watch mode: continuously monitors for changes
- **Auto-generates all Spec-Kit fields**: When syncing from SpecFact to Spec-Kit, all required fields (frontmatter, INVSEST, Constitution Check, Phases, Technology Stack, Story mappings) are automatically generated - ready for `/speckit.analyze` without manual editing

### Step 5: Enable Enforcement

```bash
# Start in shadow mode (observe only)
specfact enforce stage --preset minimal

# After stabilization, enable warnings
specfact enforce stage --preset balanced

# For production, enable strict mode
specfact enforce stage --preset strict
```

**What happens**:

- Configures enforcement rules
- Sets severity levels (HIGH, MEDIUM, LOW)
- Defines actions (BLOCK, WARN, LOG)

### Next Steps for Scenario 3 (Secondary)

- [The Journey: From Spec-Kit to SpecFact](../guides/speckit-journey.md) - Complete migration guide
- [Use Cases - Spec-Kit Migration](../guides/use-cases.md#use-case-1-github-spec-kit-migration) - Detailed migration workflow
- [Workflows - Bidirectional Sync](../guides/workflows.md#bidirectional-sync) - Keep both tools in sync

---

## Common Questions

### What if I make a mistake?

All commands support `--dry-run` or `--shadow-only` flags to preview changes without modifying files.

### Can I undo changes?

Yes! SpecFact CLI creates backups and you can use Git to revert changes:

```bash
git status
git diff
git restore .specfact/
```

### How do I learn more?

- [Command Reference](../reference/commands.md) - All commands with examples
- [Use Cases](../guides/use-cases.md) - Real-world scenarios
- [Workflows](../guides/workflows.md) - Common daily workflows
- [Troubleshooting](../guides/troubleshooting.md) - Common issues and solutions

---

**Happy building!** 🚀
