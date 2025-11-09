# Your First Steps with SpecFact CLI

This guide walks you through your first commands with SpecFact CLI, with step-by-step explanations.

## Before You Start

- [Install SpecFact CLI](installation.md) (if not already installed)
- Choose your scenario below

---

## Scenario 1: Starting a New Project

**Goal**: Create a plan before writing code

**Time**: 5-10 minutes

### Step 1: Initialize a Plan

```bash
specfact plan init --interactive
```

**What happens**:

- Creates `.specfact/` directory structure
- Prompts you for project title and description
- Creates initial plan bundle at `.specfact/plans/main.bundle.yaml`

**Example output**:

```bash
📋 Initializing new development plan...

Enter project title: My Awesome Project
Enter project description: A project to demonstrate SpecFact CLI

✅ Plan initialized successfully!
📁 Plan bundle: .specfact/plans/main.bundle.yaml
```

### Step 2: Add Your First Feature

```bash
specfact plan add-feature \
  --key FEATURE-001 \
  --title "User Authentication" \
  --outcomes "Users can login securely"
```

**What happens**:

- Adds a new feature to your plan bundle
- Creates a feature with key `FEATURE-001`
- Sets the title and outcomes

### Step 3: Add Stories to the Feature

```bash
specfact plan add-story \
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

## Scenario 2: Analyzing Existing Code

**Goal**: Understand what your code does

**Time**: 2-5 minutes

### Step 1: Import from Code

```bash
specfact import from-code \
  --repo . \
  --name my-project \
  --shadow-only
```

**What happens**:

- Analyzes your codebase (Python files by default)
- Extracts features from classes and modules
- Generates an auto-derived plan bundle
- Saves to `.specfact/reports/brownfield/auto-derived.*.yaml`

**Example output**:

```bash
🔍 Analyzing repository: .
✓ Found 15 features
✓ Detected themes: API, Database, Authentication
✓ Total stories: 42

✅ Analysis complete!
📁 Plan bundle: .specfact/reports/brownfield/auto-derived.2025-11-09T21-00-00.bundle.yaml
```

### Step 2: Review Generated Plan

```bash
cat .specfact/reports/brownfield/auto-derived.*.yaml | head -50
```

**What you'll see**:

- Features extracted from your codebase
- Stories inferred from commit messages and docstrings
- Confidence scores for each feature
- API surface detected from public methods

### Step 3: Compare with Manual Plan (if exists)

If you have a manual plan in `.specfact/plans/main.bundle.yaml`:

```bash
specfact plan compare --repo .
```

**What happens**:

- Compares manual plan vs auto-derived plan
- Detects deviations (missing features, extra features, differences)
- Generates comparison report

**Example output**:

```bash
📊 Comparing plans...
✓ Manual plan: .specfact/plans/main.bundle.yaml
✓ Auto-derived plan: .specfact/reports/brownfield/auto-derived.*.yaml

📈 Deviations found: 3
  - HIGH: Feature FEATURE-001 missing in auto plan
  - MEDIUM: Story STORY-002 differs in acceptance criteria
  - LOW: Extra feature FEATURE-999 in auto plan

📁 Report: .specfact/reports/comparison/report-*.md
```

### Step 4: Set Up Enforcement (Optional)

```bash
specfact enforce stage --preset balanced
```

**What happens**:

- Configures quality gates
- Sets enforcement rules (BLOCK, WARN, LOG)
- Creates enforcement configuration

### Next Steps for Scenario 2

- [Use Cases - Brownfield Analysis](../guides/use-cases.md#use-case-2-brownfield-code-hardening) - Detailed brownfield workflow
- [Command Reference](../reference/commands.md) - Learn all commands
- [Workflows](../guides/workflows.md) - Common daily workflows

---

## Scenario 3: Migrating from Spec-Kit

**Goal**: Add automated enforcement to Spec-Kit project

**Time**: 15-30 minutes

### Step 1: Preview Migration

```bash
specfact import from-spec-kit \
  --repo ./my-speckit-project \
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
  - Will create: .specfact/plans/main.bundle.yaml
  - Will create: .specfact/protocols/workflow.protocol.yaml (if FSM detected)
  - Will convert: Spec-Kit features → SpecFact Feature models
  - Will convert: Spec-Kit user stories → SpecFact Story models
  
🚀 Ready to migrate (use --write to execute)
```

### Step 2: Execute Migration

```bash
specfact import from-spec-kit \
  --repo ./my-speckit-project \
  --write
```

**What happens**:

- Imports Spec-Kit artifacts into SpecFact format
- Creates `.specfact/` directory structure
- Converts Spec-Kit features and stories to SpecFact models
- Preserves all information

### Step 3: Review Generated Contracts

```bash
ls -la .specfact/
```

**What you'll see**:

- `.specfact/plans/main.bundle.yaml` - Plan bundle (converted from Spec-Kit)
- `.specfact/protocols/workflow.protocol.yaml` - FSM definition (if protocol detected)
- `.specfact/enforcement/config.yaml` - Quality gates configuration

### Step 4: Set Up Bidirectional Sync (Optional)

Keep Spec-Kit and SpecFact synchronized:

```bash
# One-time bidirectional sync
specfact sync spec-kit --repo . --bidirectional

# Continuous watch mode
specfact sync spec-kit --repo . --bidirectional --watch --interval 5
```

**What happens**:

- Syncs changes between Spec-Kit and SpecFact
- Bidirectional: changes in either direction are synced
- Watch mode: continuously monitors for changes

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

### Next Steps for Scenario 3

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
