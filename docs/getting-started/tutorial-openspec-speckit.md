# Tutorial: Using SpecFact with OpenSpec or Spec-Kit

> **Complete step-by-step guide for new users**  
> Learn how to use SpecFact CLI with OpenSpec or Spec-Kit for brownfield code modernization

**Time**: 15-30 minutes | **Prerequisites**: Python 3.11+, basic command-line knowledge

**Note**: This tutorial assumes you're using `specfact` command directly.

---

## 🎯 What You'll Learn

By the end of this tutorial, you'll know how to:

- ✅ Install and set up SpecFact CLI
- ✅ Use SpecFact with OpenSpec for change tracking and DevOps integration
- ✅ Use SpecFact with Spec-Kit for greenfield + brownfield workflows
- ✅ Sync between tools using bridge adapters
- ✅ Export change proposals to GitHub Issues
- ✅ Track implementation progress automatically

---

## 📋 Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed (`python3 --version`)
- **Git** installed (`git --version`)
- **Command-line access** (Terminal, PowerShell, or WSL)
- **A GitHub account** (for DevOps integration examples)

**Optional but recommended:**

- **OpenSpec CLI** installed (`npm install -g @fission-ai/openspec@latest`) - for OpenSpec workflows
- **VS Code or Cursor** - for IDE integration

---

## 🚀 Quick Start: Choose Your Path

### Path A: Using SpecFact with OpenSpec

**Best for**: Teams using OpenSpec for specification management and change tracking

**Use case**: You have OpenSpec change proposals and want to:

- Export them to GitHub Issues
- Track implementation progress
- Sync OpenSpec specs with code analysis

👉 **[Jump to OpenSpec Tutorial](#path-a-using-specfact-with-openspec)**

### Path B: Using SpecFact with Spec-Kit

**Best for**: Teams using GitHub Spec-Kit for interactive specification authoring

**Use case**: You have Spec-Kit specs and want to:

- Add runtime contract enforcement
- Enable team collaboration with shared plans
- Sync Spec-Kit artifacts with SpecFact bundles

👉 **[Jump to Spec-Kit Tutorial](#path-b-using-specfact-with-spec-kit)**

---

## Path A: Using SpecFact with OpenSpec

### Step 1: Install SpecFact CLI

**Option 1: Quick Start (CLI-only)**

```bash
# No installation needed - works immediately
uvx specfact-cli@latest --help
```

**Option 2: Full Installation (Recommended)**

```bash
# Install SpecFact CLI
pip install specfact-cli

# Verify installation
specfact --version
```

**Expected output**: `specfact-cli, version 0.22.0`

### Step 2: Set Up Your Project

**If you already have an OpenSpec project:**

```bash
# Navigate to your OpenSpec project
cd /path/to/your-openspec-project

# Verify OpenSpec structure exists
ls openspec/
# Should show: specs/, changes/, and config.yaml (OPSX); project.md and AGENTS.md are legacy (optional)
```

**If you don't have OpenSpec yet:**

```bash
# Install OpenSpec CLI
npm install -g @fission-ai/openspec@latest

# Initialize OpenSpec in your project
cd /path/to/your-project
openspec init

# This creates openspec/ directory structure
```

### Step 3: Analyze Your Legacy Code with SpecFact

**First, extract specs from your existing code:**

```bash
# Analyze legacy codebase
cd /path/to/your-openspec-project
specfact import from-code legacy-api --repo .

# Expected output:
# 🔍 Analyzing codebase...
# ✅ Analyzed X Python files
# ✅ Extracted Y features
# ✅ Generated Z user stories
# ⏱️  Completed in X seconds
# 📁 Project bundle: .specfact/projects/legacy-api/
# ✅ Import complete!
```

**What this does:**

- Analyzes your Python codebase
- Extracts features and user stories automatically
- Creates a SpecFact project bundle (`.specfact/projects/legacy-api/`)

**Note**: If using `hatch run specfact`, run from the specfact-cli directory:
```bash
cd /path/to/specfact-cli
hatch run specfact import from-code legacy-api --repo /path/to/your-openspec-project
```

### Step 4: Create an OpenSpec Change Proposal

**Create a change proposal in OpenSpec:**

```bash
# Create change proposal directory
mkdir -p openspec/changes/modernize-api

# Create proposal.md
cat > openspec/changes/modernize-api/proposal.md << 'EOF'
# Change: Modernize Legacy API

## Why
Legacy API needs modernization for better performance and maintainability.

## What Changes
- Refactor API endpoints
- Add contract validation
- Update database schema

## Impact
- Affected specs: api, database
- Affected code: src/api/, src/db/
EOF

# Create tasks.md
cat > openspec/changes/modernize-api/tasks.md << 'EOF'
## Implementation Tasks

- [ ] Refactor API endpoints
- [ ] Add contract validation
- [ ] Update database schema
- [ ] Add tests
EOF
```

### Step 5: Export OpenSpec Proposal to GitHub Issues

**Export your change proposal to GitHub Issues:**

```bash
# Export OpenSpec change proposal to GitHub Issues
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --repo /path/to/openspec-repo

# Expected output:
# ✅ Found change proposal: modernize-api
# ✅ Created GitHub Issue #123: Modernize Legacy API
# ✅ Updated proposal.md with issue tracking
```

**What this does:**

- Reads your OpenSpec change proposal
- Creates a GitHub Issue from the proposal
- Updates the proposal with issue tracking information
- Enables progress tracking

### Step 6: Track Implementation Progress

**As you implement changes, track progress automatically:**

```bash
# Make commits with change ID in commit message
cd /path/to/source-code-repo
git commit -m "feat: modernize-api - refactor endpoints [change:modernize-api]"

# Track progress (detects commits and adds comments to GitHub Issue)
cd /path/to/openspec-repo
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --track-code-changes \
  --repo . \
  --code-repo /path/to/source-code-repo

# Expected output:
# ✅ Detected commit: feat: modernize-api - refactor endpoints
# ✅ Added progress comment to Issue #123
```

**Note**: Use `--track-code-changes` flag to enable automatic code change detection. The `--code-repo` option specifies where the source code repository is located (if different from the OpenSpec repo).

### Step 7: Sync OpenSpec Change Proposals to SpecFact

**Import OpenSpec change proposals into SpecFact:**

```bash
# Sync OpenSpec change proposals to SpecFact (read-only)
cd /path/to/openspec-repo
specfact sync bridge --adapter openspec --mode read-only \
  --bundle legacy-api \
  --repo .

# Expected output:
# ✅ Syncing OpenSpec artifacts (read-only)
# ✅ Found 1 change proposal: modernize-api
# ✅ Synced to SpecFact bundle: legacy-api
# ✅ Change tracking updated
```

**What this does:**

- Reads OpenSpec change proposals from `openspec/changes/`
- Syncs them to SpecFact change tracking
- Enables alignment reports (planned feature)

**Note**: Currently, OpenSpec adapter sync may show an error about `discover_features` method. This is a known limitation in v0.22.0. The adapter successfully loads change proposals, but alignment report generation may fail. This will be fixed in a future release.

### Step 8: Add Runtime Contract Enforcement

**Add contracts to prevent regressions:**

```bash
# Configure enforcement (global setting, no --bundle or --repo needed)
cd /path/to/your-project
specfact enforce stage --preset balanced

# Expected output:
# Setting enforcement mode: balanced
# Enforcement Mode: BALANCED
# ┏━━━━━━━━━━┳━━━━━━━━┓
# ┃ Severity ┃ Action ┃
# ┡━━━━━━━━╇━━━━━━━━┩
# │ HIGH     │ BLOCK  │
# │ MEDIUM   │ WARN   │
# │ LOW      │ LOG    │
# ✅ Quality gates configured
```

**What this does:**

- Configures quality gates (global setting for the repository)
- Enables contract enforcement
- Prepares CI/CD integration

**Note**: `enforce stage` is a global setting and doesn't take `--bundle` or `--repo` options. It configures enforcement for the current repository.

### Step 9: Archive Completed Change

**When implementation is complete, archive the change:**

```bash
# Archive completed change in OpenSpec
openspec archive modernize-api --yes

# Expected output:
# ✅ Change archived successfully
# ✅ Specs updated in openspec/specs/
```

---

## Path B: Using SpecFact with Spec-Kit

### Step 1: Install SpecFact CLI

**Option 1: Quick Start (CLI-only)**

```bash
# No installation needed
uvx specfact-cli@latest --help
```

**Option 2: Full Installation (Recommended)**

```bash
# Install SpecFact CLI
pip install specfact-cli

# Verify installation
specfact --version
```

### Step 2: Set Up Your Spec-Kit Project

**If you already have a Spec-Kit project:**

```bash
# Navigate to your Spec-Kit project
cd /path/to/your-speckit-project

# Verify Spec-Kit structure exists
ls specs/
# Should show: [###-feature-name]/ directories with spec.md, plan.md, tasks.md
```

**If you don't have Spec-Kit yet:**

```bash
# Spec-Kit is integrated into GitHub Copilot
# Use slash commands in Copilot chat:
# /speckit.specify --feature "User Authentication"
# /speckit.plan --feature "User Authentication"
# /speckit.tasks --feature "User Authentication"
```

### Step 3: Preview Spec-Kit Import

**See what will be imported (safe - no changes):**

```bash
# Preview import
specfact import from-bridge --adapter speckit --repo ./my-speckit-project --dry-run

# Expected output:
# 🔍 Analyzing Spec-Kit project via bridge adapter...
# ✅ Found .specify/ directory (modern format)
# ✅ Found specs/001-user-authentication/spec.md
# ✅ Found specs/001-user-authentication/plan.md
# ✅ Found specs/001-user-authentication/tasks.md
# ✅ Found .specify/memory/constitution.md
# 
# 📊 Migration Preview:
#   - Will create: .specfact/projects/<bundle-name>/ (modular project bundle)
#   - Will create: .specfact/protocols/workflow.protocol.yaml (if FSM detected)
#   - Will create: .specfact/gates/config.yaml
#   - Will convert: Spec-Kit features → SpecFact Feature models
#   - Will convert: Spec-Kit user stories → SpecFact Story models
#   
# 🚀 Ready to migrate (use --write to execute)
```

### Step 4: Import Spec-Kit Project

**Import your Spec-Kit project to SpecFact:**

```bash
# Execute import
specfact import from-bridge \
  --adapter speckit \
  --repo ./my-speckit-project \
  --write

# Expected output:
# ✅ Parsed Spec-Kit artifacts
# ✅ Generated SpecFact bundle: .specfact/projects/<bundle-name>/
# ✅ Created quality gates config
# ✅ Preserved Spec-Kit artifacts (original files untouched)
```

**What this does:**

- Parses Spec-Kit artifacts (spec.md, plan.md, tasks.md, constitution.md)
- Generates SpecFact project bundle
- Creates quality gates configuration
- Preserves your original Spec-Kit files

### Step 5: Review Generated Bundle

**Review what was created:**

```bash
# Review plan bundle (bundle name is positional argument, not --bundle)
# IMPORTANT: Must be in the project directory where .specfact/ exists
cd /path/to/your-speckit-project
specfact plan review <bundle-name>

# Note: Bundle name is typically "main" for Spec-Kit imports
# Check actual bundle name: ls .specfact/projects/

# Expected output:
# ✅ Features: 5
# ✅ Stories: 23
# ✅ Plan bundle reviewed successfully
```

**Note**: 
- `plan review` takes the bundle name as a positional argument (not `--bundle`)
- It uses the current directory to find `.specfact/projects/` (no `--repo` option)
- You must be in the project directory where the bundle was created

### Step 6: Enable Bidirectional Sync

**Keep Spec-Kit and SpecFact in sync:**

```bash
# One-time sync (bundle name is typically "main" for Spec-Kit imports)
cd /path/to/my-speckit-project
specfact sync bridge --adapter speckit --bundle main --repo . --bidirectional

# Continuous watch mode (recommended for team collaboration)
specfact sync bridge --adapter speckit --bundle main --repo . --bidirectional --watch --interval 5

# Expected output:
# ✅ Detected speckit repository
# ✅ Constitution found and validated
# ✅ Detected SpecFact structure
# ✅ No conflicts detected
# Sync Summary (Bidirectional):
#   - speckit → SpecFact: Updated 0, Added 0 features
#   - SpecFact → speckit: No features to convert
```

**What this does:**

- **Spec-Kit → SpecFact**: New specs automatically imported
- **SpecFact → Spec-Kit**: Changes synced back to Spec-Kit format
- **Team collaboration**: Multiple developers can work together

**Note**: Replace `main` with your actual bundle name if different. Check with `ls .specfact/projects/` after import.

### Step 7: Continue Using Spec-Kit Interactively

**Keep using Spec-Kit slash commands - sync happens automatically:**

```bash
# In GitHub Copilot chat:
/speckit.specify --feature "Payment Processing"
/speckit.plan --feature "Payment Processing"
/speckit.tasks --feature "Payment Processing"

# SpecFact automatically syncs (if watch mode enabled)
# → Detects changes in specs/[###-feature-name]/
# → Imports new spec.md, plan.md, tasks.md
# → Updates .specfact/projects/<bundle-name>/ aspect files
```

### Step 8: Add Runtime Contract Enforcement

**Add contracts to prevent regressions:**

```bash
# Configure enforcement (global setting, no --bundle or --repo needed)
cd /path/to/my-speckit-project
specfact enforce stage --preset balanced

# Expected output:
# Setting enforcement mode: balanced
# Enforcement Mode: BALANCED
# ┏━━━━━━━━━━┳━━━━━━━━┓
# ┃ Severity ┃ Action ┃
# ┡━━━━━━━━━━╇━━━━━━━━┩
# │ HIGH     │ BLOCK  │
# │ MEDIUM   │ WARN   │
# │ LOW      │ LOG    │
# ✅ Quality gates configured
```

**Note**: `enforce stage` is a global setting and doesn't take `--bundle` or `--repo` options.

### Step 9: Detect Code vs Plan Drift

**Compare intended design vs actual implementation:**

```bash
# Compare code vs plan (use --bundle to specify bundle name)
# IMPORTANT: Must be in the project directory where .specfact/ exists
cd /path/to/my-speckit-project
specfact plan compare --code-vs-plan --bundle <bundle-name>

# Note: Bundle name is typically "main" for Spec-Kit imports
# Check actual bundle name: ls .specfact/projects/

# Expected output:
# ✅ Comparing intended design vs actual implementation
# ✅ Found 3 deviations
# ✅ Auto-derived plans from code analysis
```

**What this does:**

- Compares Spec-Kit plans (what you planned) vs code (what's implemented)
- Identifies deviations automatically
- Helps catch drift between design and code

**Note**: 
- `plan compare` takes `--bundle` as an option (not positional)
- It uses the current directory to find bundles (no `--repo` option)
- You must be in the project directory where the bundle was created

---

## 🎓 Key Concepts

### Bridge Adapters

**What are bridge adapters?**

Bridge adapters are plugin-based connectors that sync between SpecFact and external tools (OpenSpec, Spec-Kit, GitHub Issues, etc.).

**Available adapters:**

- `openspec` - OpenSpec integration (read-only sync, v0.22.0+)
- `speckit` - Spec-Kit integration (bidirectional sync)
- `github` - GitHub Issues integration (export-only)

**How to use:**

```bash
# View available adapters (shown in help text)
specfact sync bridge --help

# Use an adapter
specfact sync bridge --adapter <adapter-name> --mode <mode> --bundle <bundle-name> --repo .
```

**Note**: Adapters are listed in the help text. There's no `--list-adapters` option, but adapters are shown when you use `--help` or when an adapter is not found (error message shows available adapters).

### Sync Modes

**Available sync modes:**

- `read-only` - Import from external tool (no modifications)
- `export-only` - Export to external tool (no imports)
- `bidirectional` - Two-way sync (read and write)
- `unidirectional` - One-way sync (Spec-Kit → SpecFact only)

**Which mode to use:**

- **OpenSpec**: Use `read-only` (v0.22.0+) or `export-only` (GitHub Issues)
- **Spec-Kit**: Use `bidirectional` for team collaboration
- **GitHub Issues**: Use `export-only` for DevOps integration

---

## 🐛 Troubleshooting

### Issue: "Adapter not found"

**Solution:**

```bash
# View available adapters in help text
specfact sync bridge --help

# Or check error message when adapter is not found (shows available adapters)
# Should show: openspec, speckit, github, generic-markdown
```

### Issue: "No change proposals found"

**Solution:**

```bash
# Verify OpenSpec structure
ls openspec/changes/
# Should show change proposal directories

# Check proposal.md exists
cat openspec/changes/<change-name>/proposal.md
```

### Issue: "Spec-Kit artifacts not found"

**Solution:**

```bash
# Verify Spec-Kit structure
ls specs/
# Should show: [###-feature-name]/ directories

# Check spec.md exists
cat specs/001-user-authentication/spec.md
```

### Issue: "GitHub Issues export failed"

**Solution:**

```bash
# Verify GitHub token
export GITHUB_TOKEN=your-token

# Or use GitHub CLI
gh auth login

# Verify repository access
gh repo view your-org/your-repo
```

---

## 📚 Next Steps

### For OpenSpec Users

1. **[OpenSpec Journey Guide](../guides/openspec-journey.md)** - Complete integration guide
2. **[DevOps Adapter Integration](../guides/devops-adapter-integration.md)** - GitHub Issues and backlog tracking
3. **[Commands Reference](../reference/commands.md#sync-bridge)** - Complete `sync bridge` documentation

### For Spec-Kit Users

1. **[Spec-Kit Journey Guide](../guides/speckit-journey.md)** - Complete integration guide
2. **[Spec-Kit Comparison](../guides/speckit-comparison.md)** - Understand when to use each tool
3. **[Commands Reference](../reference/commands.md#sync-bridge)** - Complete `sync bridge` documentation

### General Resources

1. **[Getting Started Guide](README.md)** - Installation and first commands
2. **[Brownfield Engineer Guide](../guides/brownfield-engineer.md)** - Complete brownfield modernization workflow
3. **[Use Cases](../guides/use-cases.md)** - Real-world scenarios

---

## 💡 Tips & Best Practices

### For OpenSpec Integration

- ✅ **Separate repositories**: Keep OpenSpec specs in a separate repo from code
- ✅ **Change proposals**: Use OpenSpec for structured change proposals
- ✅ **DevOps export**: Export proposals to GitHub Issues for team visibility
- ✅ **Progress tracking**: Use `--track-code-changes` to auto-track implementation

### For Spec-Kit Integration

- ✅ **Bidirectional sync**: Use `--bidirectional --watch` for team collaboration
- ✅ **Interactive authoring**: Keep using Spec-Kit slash commands
- ✅ **Contract enforcement**: Add SpecFact contracts to critical paths
- ✅ **Drift detection**: Regularly run `plan compare` to catch deviations

### General Tips

- ✅ **Start small**: Begin with one feature or change proposal
- ✅ **Use watch mode**: Enable `--watch` for automatic synchronization
- ✅ **Review before sync**: Use `--dry-run` to preview changes
- ✅ **Version control**: Commit SpecFact bundles to version control

---

## 🆘 Need Help?

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 [hello@noldai.com](mailto:hello@noldai.com)
- 📖 [Full Documentation](../README.md)

---

**Happy building!** 🚀

---

Copyright © 2025-2026 Nold AI (Owner: Dominikus Nold)

**Trademarks**: All product names, logos, and brands mentioned in this documentation are the property of their respective owners. NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). See [TRADEMARKS.md](../../TRADEMARKS.md) for more information.
