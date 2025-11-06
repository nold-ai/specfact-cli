# IDE Integration with SpecFact CLI

**Status**: ✅ **AVAILABLE** (v0.2.2)  
**Last Updated**: 2025-11-02

---

## Overview

SpecFact CLI supports IDE integration through **prompt templates** that work with various AI-assisted IDEs. These templates are copied to IDE-specific locations and automatically registered by the IDE as slash commands.

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
```

**What it does:**

1. Detects your IDE (or uses `--ide` flag)
2. Copies prompt templates from `resources/prompts/` to IDE-specific location
3. Creates/updates VS Code settings if needed
4. Makes slash commands available in your IDE

### Step 2: Use Slash Commands in Your IDE

Once initialized, you can use slash commands directly in your IDE's AI chat:

**In Cursor / VS Code / Copilot:**

```bash
/specfact-import-from-code --repo . --confidence 0.7
/specfact-plan-init --idea idea.yaml
/specfact-plan-compare --manual main.bundle.yaml --auto auto.bundle.yaml
/specfact-sync --repo . --bidirectional
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

```

### IDE Registration

**How IDEs discover slash commands:**

- **VS Code / Copilot**: Reads `.github/prompts/*.prompt.md` files listed in `.vscode/settings.json` under `chat.promptFilesRecommendations`
- **Cursor**: Automatically discovers `.cursor/commands/*.md` files
- **Other IDEs**: Follow their respective discovery mechanisms

---

## Available Slash Commands

| Command | Description | CLI Equivalent |
|---------|-------------|----------------|
| `/specfact-import-from-code` | Reverse-engineer plan from brownfield code | `specfact import from-code` |
| `/specfact-plan-init` | Initialize new development plan | `specfact plan init` |
| `/specfact-plan-promote` | Promote plan through stages | `specfact plan promote` |
| `/specfact-plan-compare` | Compare manual vs auto plans | `specfact plan compare` |
| `/specfact-sync` | Sync with Spec-Kit or repository | `specfact sync spec-kit` |

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
# Example: /specfact-import-from-code --repo . --confidence 0.7
```

**Now in Cursor:**

1. Open Cursor AI chat
2. Type `/specfact-import-from-code --repo . --confidence 0.7`
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
      ".github/prompts/specfact-import-from-code.prompt.md",
      ".github/prompts/specfact-plan-init.prompt.md",
      ".github/prompts/specfact-plan-compare.prompt.md",
      ".github/prompts/specfact-plan-promote.prompt.md",
      ".github/prompts/specfact-sync.prompt.md"
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

- ✅ Initialize IDE integration with `specfact init`
- ✅ Use slash commands in your IDE
- 📖 Read [CoPilot Mode Guide](copilot-mode.md) for CLI usage
- 📖 Read [Command Reference](../reference/commands.md) for all commands

---

**Trademarks**: All product names, logos, and brands mentioned in this guide are the property of their respective owners. NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). See [TRADEMARKS.md](../../TRADEMARKS.md) for more information.
