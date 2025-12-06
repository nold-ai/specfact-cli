# IDE Integration with SpecFact CLI

**Status**: ✅ **AVAILABLE** (v0.4.2+)  
**Last Updated**: 2025-11-09

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow. Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE. No platform to learn, no vendor lock-in.

---

## Overview

SpecFact CLI supports IDE integration through **prompt templates** that work with various AI-assisted IDEs. These templates are copied to IDE-specific locations and automatically registered by the IDE as slash commands.

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
specfact init --ide cursor
specfact init --ide vscode
specfact init --ide copilot

# Install required packages for contract enhancement
specfact init --install-deps

# Initialize for specific IDE and install dependencies
specfact init --ide cursor --install-deps
```

**What it does:**

1. Detects your IDE (or uses `--ide` flag)
2. Copies prompt templates from `resources/prompts/` to IDE-specific location
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

The IDE automatically recognizes these commands and provides enhanced prompts.

---

## How It Works

### Prompt Templates

Slash commands are **markdown prompt templates** (not executable CLI commands). They:

1. **Live in your repository** - Templates are stored in `resources/prompts/` (packaged with SpecFact CLI)
2. **Get copied to IDE locations** - `specfact init` copies them to IDE-specific directories
3. **Registered automatically** - The IDE reads these files and makes them available as slash commands
4. **Provide enhanced prompts** - Templates include detailed instructions for the AI assistant

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

**Core Workflow Commands** (numbered for workflow ordering):

| Command | Description | CLI Equivalent |
|---------|-------------|----------------|
| `/specfact.01-import` | Import codebase into plan bundle | `specfact import from-code <bundle-name>` |
| `/specfact.02-plan` | Plan management (init, add-feature, add-story, update-idea, update-feature, update-story) | `specfact plan <operation> <bundle-name>` |
| `/specfact.03-review` | Review plan and promote through stages | `specfact plan review <bundle-name>`, `specfact plan promote <bundle-name>` |
| `/specfact.04-sdd` | Create SDD manifest from plan | `specfact plan harden <bundle-name>` |
| `/specfact.05-enforce` | Validate SDD and contracts | `specfact enforce sdd <bundle-name>` |
| `/specfact.06-sync` | Sync with external tools or repository | `specfact sync bridge --adapter <adapter>` |
| `/specfact.07-contracts` | Contract enhancement workflow: analyze → generate prompts → apply sequentially | `specfact analyze contracts`, `specfact generate contracts-prompt`, `specfact generate contracts-apply` |

**Advanced Commands** (no numbering):

| Command | Description | CLI Equivalent |
|---------|-------------|----------------|
| `/specfact.compare` | Compare manual vs auto plans | `specfact plan compare` |
| `/specfact.validate` | Run validation suite | `specfact repro` |
| `/specfact.generate-contracts-prompt` | Generate AI IDE prompt for adding contracts | `specfact generate contracts-prompt <file> --apply <contracts>` |

---

## Examples

### Example 1: Initialize for Cursor

```bash
# Run init in your repository
cd /path/to/my-project
specfact init --ide cursor

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
specfact init --ide vscode

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
specfact init --ide cursor --force
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
   specfact init --ide cursor --force
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
   specfact init --ide vscode --force
   ```

---

## Related Documentation

- [Command Reference](../reference/commands.md) - All CLI commands
- [CoPilot Mode Guide](copilot-mode.md) - Using `--mode copilot` on CLI
- [Getting Started](../getting-started/installation.md) - Installation and setup

---

## Next Steps

- ⭐ **[Integration Showcases](../examples/integration-showcases/)** - See real bugs fixed via VS Code, Cursor, GitHub Actions integrations
- ✅ Initialize IDE integration with `specfact init`
- ✅ Use slash commands in your IDE
- 📖 Read [CoPilot Mode Guide](copilot-mode.md) for CLI usage
- 📖 Read [Command Reference](../reference/commands.md) for all commands

---

**Trademarks**: All product names, logos, and brands mentioned in this guide are the property of their respective owners. NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). See [TRADEMARKS.md](../../TRADEMARKS.md) for more information.
