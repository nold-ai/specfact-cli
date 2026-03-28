---
layout: default
title: IDE Integration with SpecFact CLI
permalink: /guides/ide-integration/
---

# IDE Integration with SpecFact CLI

**Status**: ✅ **AVAILABLE** (v0.4.2+)  
**Last Updated**: 2025-11-09

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow. Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE. No platform to learn, no vendor lock-in.

**Important**: SpecFact CLI does **not** provide built-in AI. IDE integration means SpecFact installs prompt templates and slash commands that your chosen IDE copilot can use to run SpecFact as part of a guided command chain.

**Terminal Output**: The CLI automatically detects embedded terminals (Cursor, VS Code) and CI/CD environments, adapts formatting automatically, and falls back to ASCII-safe rendering when the active terminal encoding cannot display UTF-8 symbols. See [Troubleshooting](troubleshooting.md#terminal-output-issues) for details.

---

## Overview

SpecFact CLI supports IDE integration through **prompt templates** that work with various AI-assisted IDEs. These templates are copied to IDE-specific locations and automatically registered by the IDE as slash commands. The AI stays in your IDE; SpecFact remains the deterministic CLI the prompts call.

**See real examples**: [Integration Showcases](../examples/integration-showcases/) - 5 complete examples showing bugs fixed via IDE integrations

**Supported IDEs:**

- ✅ **Cursor** - `.cursor/commands/`
- ✅ **VS Code / GitHub Copilot** - `.github/prompts/` + `.vscode/settings.json`
- ✅ **Claude Code** - `.claude/commands/`
- ✅ **Gemini CLI** - `.gemini/commands/`
- ✅ **Qwen Code** - `.qwen/commands/`
- ✅ **opencode** - `.opencode/command/`
- ✅ **Windsurf** - `.windsurf/workflows/`
- ✅ **Kilo Code** - `.kilocode/workflows/`
- ✅ **Auggie** - `.augment/commands/`
- ✅ **Roo Code** - `.roo/commands/`
- ✅ **CodeBuddy** - `.codebuddy/commands/`
- ✅ **Amp** - `.agents/commands/`
- ✅ **Amazon Q Developer** - `.amazonq/prompts/`

---

## Quick Start

### Step 1: Initialize IDE Integration

Run the `specfact init` command in your repository:

```bash
# Auto-detect IDE
specfact init

# Or specify IDE explicitly
specfact init ide --ide cursor
specfact init ide --ide vscode
specfact init ide --ide copilot

# Install required packages for contract enhancement
specfact init --install-deps

# Initialize for specific IDE and install dependencies
specfact init ide --ide cursor --install-deps
```

**What it does:**

1. Detects your IDE (or uses `--ide` flag)
2. Discovers prompt templates from installed workflow modules first, then copies them to the IDE-specific location
3. Creates/updates VS Code settings if needed
4. Makes slash commands available in your IDE
5. Optionally installs required packages for contract enhancement (if `--install-deps` is provided):
   - `beartype>=0.22.4` - Runtime type checking
   - `icontract>=2.7.1` - Design-by-contract decorators
   - `crosshair-tool>=0.0.97` - Contract exploration
   - `pytest>=8.4.2` - Testing framework

### Step 2: Use Slash Commands in Your IDE

Once initialized, you can use slash commands directly in your IDE's AI chat:

**In Cursor / VS Code / Copilot:**

```bash
# Core workflow commands (numbered for natural progression)
/specfact.01-import legacy-api --repo .
/specfact.02-plan init legacy-api
/specfact.02-plan add-feature --bundle legacy-api --key FEATURE-001 --title "User Auth"
/specfact.03-review legacy-api
/specfact.04-sdd legacy-api
/specfact.05-enforce legacy-api
/specfact.06-sync --adapter speckit --repo . --bidirectional
/specfact.07-contracts legacy-api --apply all-contracts  # Analyze, generate prompts, apply contracts sequentially

# Advanced commands
/specfact.compare --bundle legacy-api
/specfact.validate --repo .
```

The IDE automatically recognizes these commands and exposes the corresponding prompt templates. Those prompts then guide your AI copilot to call SpecFact commands.

---

## How It Works

### Prompt Templates

Slash commands are **markdown prompt templates** (not executable CLI commands). They:

1. **Are owned by installed workflow modules** - Bundle-specific prompts ship with their corresponding module packages
2. **Get copied to IDE locations** - `specfact init ide` discovers installed module resources and copies them to IDE-specific directories
3. **Registered automatically** - The IDE reads these files and makes them available as slash commands
4. **Fall back safely during transition** - If no installed module prompt payloads are present yet, SpecFact can still use packaged core fallback resources
5. **Provide enhanced prompts** - Templates include detailed instructions for the AI assistant

### Template Format

Each template follows this structure:

```markdown
---
description: Command description for IDE display
---

## User Input

```text
$ARGUMENTS
```

## Goal

Detailed instructions for the AI assistant...

## Execution Steps

1. Parse arguments...

2. Execute command...

3. Generate output...

```text

### IDE Registration

**How IDEs discover slash commands:**

- **VS Code / Copilot**: Reads `.github/prompts/*.prompt.md` files listed in `.vscode/settings.json` under `chat.promptFilesRecommendations`
- **Cursor**: Automatically discovers `.cursor/commands/*.md` files
- **Other IDEs**: Follow their respective discovery mechanisms

---

## Available Slash Commands

**Complete Reference**: [Prompts README](../prompts/README.md) - Full slash commands reference with examples

**Workflow Guide**: [AI IDE Workflow Guide](ai-ide-workflow.md) - Complete workflow from setup to validation

## Available Slash Commands

**Core Workflow Commands** (numbered for workflow ordering):

| Command | Description | CLI Equivalent |
|---------|-------------|----------------|
| `/specfact.01-import` | Import codebase into plan bundle | `specfact code import <bundle-name>` |
| `/specfact.02-plan` | Plan management (init, add-feature, add-story, update-idea, update-feature, update-story) | `specfact project snapshot --bundle <bundle-name>` |
| `/specfact.03-review` | Review plan and promote through stages | `specfact project devops-flow --stage develop --bundle <bundle-name>`, `specfact project health-check` |
| `/specfact.04-sdd` | Create SDD manifest from plan | `specfact project snapshot <bundle-name>` |
| `/specfact.05-enforce` | Validate SDD and contracts | `specfact govern enforce sdd <bundle-name>` |
| `/specfact.06-sync` | Sync with external tools or repository | `specfact project sync bridge --adapter <adapter>` |
| `/specfact.07-contracts` | Contract enhancement workflow: analyze → generate prompts → apply sequentially | `specfact code analyze contracts` (use your AI IDE skill `/specfact.07-contracts` for contract enhancement workflows) |

**Advanced Commands** (no numbering):

| Command | Description | CLI Equivalent |
|---------|-------------|----------------|
| `/specfact.compare` | Compare manual vs auto plans | `specfact project regenerate` |
| `/specfact.validate` | Run validation suite | `specfact code repro` |
| `/specfact.generate-contracts-prompt` | Generate AI IDE prompt for adding contracts | Use your AI IDE skill (`/specfact.07-contracts`) for contract enhancement workflows |

---

## Examples

### Example 1: Initialize for Cursor

```bash
# Run init in your repository
cd /path/to/my-project
specfact init ide --ide cursor

# Output:
# ✓ Initialization Complete
# Copied 5 template(s) to .cursor/commands/
#
# You can now use SpecFact slash commands in Cursor!
# Example: /specfact.01-import legacy-api --repo .
```

**Now in Cursor:**

1. Open Cursor AI chat
2. Type `/specfact.01-import legacy-api --repo .`
3. Cursor recognizes the command and provides enhanced prompts

### Example 2: Initialize for VS Code / Copilot

```bash
# Run init in your repository
specfact init ide --ide vscode

# Output:
# ✓ Initialization Complete
# Copied 5 template(s) to .github/prompts/
# Updated VS Code settings: .vscode/settings.json

```

**VS Code settings.json:**

```json
{
  "chat": {
    "promptFilesRecommendations": [
      ".github/prompts/specfact.01-import.prompt.md",
      ".github/prompts/specfact.02-plan.prompt.md",
      ".github/prompts/specfact.03-review.prompt.md",
      ".github/prompts/specfact.04-sdd.prompt.md",
      ".github/prompts/specfact.05-enforce.prompt.md",
      ".github/prompts/specfact.06-sync.prompt.md",
      ".github/prompts/specfact.07-contracts.prompt.md",
      ".github/prompts/specfact.compare.prompt.md",
      ".github/prompts/specfact.validate.prompt.md"
    ]
  }
}
```

### Example 3: Update Templates

If you update SpecFact CLI, run `init` again to update templates:

```bash
# Re-run init to update templates (use --force to overwrite)
specfact init ide --ide cursor --force
```

---

## Advanced Usage

### Custom Template Locations

By default, templates are copied from SpecFact CLI's package resources. To use custom templates:

1. Create your own templates in a custom location
2. Modify `specfact init` to use custom path (future feature)

### IDE-Specific Customization

Different IDEs may require different template formats:

- **Markdown** (Cursor, Claude, etc.): Direct `.md` files
- **TOML** (Gemini, Qwen): Converted to TOML format automatically
- **VS Code**: `.prompt.md` files with settings.json integration

The `specfact init` command handles all conversions automatically.

---

## Troubleshooting

### Slash Commands Not Showing in IDE

**Issue**: Commands don't appear in IDE autocomplete

**Solutions:**

1. **Verify files exist:**

   ```bash
   ls .cursor/commands/specfact-*.md  # For Cursor
   ls .github/prompts/specfact-*.prompt.md  # For VS Code

   ```

2. **Re-run init:**

   ```bash
   specfact init ide --ide cursor --force
   ```

3. **Restart IDE**: Some IDEs require restart to discover new commands

### VS Code Settings Not Updated

**Issue**: VS Code settings.json not created or updated

**Solutions:**

1. **Check permissions:**

   ```bash
   ls -la .vscode/settings.json

   ```

2. **Manually verify settings.json:**

   ```json
   {
     "chat": {
       "promptFilesRecommendations": [...]
     }
   }

   ```

3. **Re-run init:**

   ```bash
   specfact init ide --ide vscode --force
   ```

---

## Related Documentation

- [Command Reference](../reference/commands.md) - All CLI commands
- [CoPilot Mode Guide](copilot-mode.md) - Using `--mode copilot` on CLI
- [Getting Started](../getting-started/installation.md) - Installation and setup
- [Troubleshooting](troubleshooting.md#terminal-output-issues) - Terminal output auto-detection in embedded terminals

---

## Next Steps

- ⭐ **[Integration Showcases](../examples/integration-showcases/)** - See real bugs fixed via VS Code, Cursor, GitHub Actions integrations
- ✅ Initialize IDE integration with `specfact init`
- ✅ Use slash commands in your IDE
- 📖 Read [CoPilot Mode Guide](copilot-mode.md) for CLI usage
- 📖 Read [Command Reference](../reference/commands.md) for all commands

---

**Trademarks**: All product names, logos, and brands mentioned in this guide are the property of their respective owners. NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). See [TRADEMARKS.md](/TRADEMARKS/) for more information.
