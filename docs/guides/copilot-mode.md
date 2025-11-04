# Using CoPilot Mode

**Status**: ✅ **AVAILABLE** (v0.2.2)  
**Last Updated**: 2025-11-02

---

## Overview

SpecFact CLI supports two operational modes:

- **CI/CD Mode** (Default): Fast, deterministic execution for automation
- **CoPilot Mode**: Interactive assistance with enhanced prompts for IDEs

Mode is auto-detected based on environment, or you can explicitly set it with `--mode cicd` or `--mode copilot`.

---

## Quick Start

### Quick Start Using CoPilot Mode

```bash
# Explicitly enable CoPilot mode
specfact --mode copilot import from-code --repo . --confidence 0.7

# Mode is auto-detected based on environment (IDE integration, CoPilot API availability)
specfact import from-code --repo . --confidence 0.7  # Auto-detects CoPilot if available
```

### What You Get with CoPilot Mode

- ✅ **Enhanced prompts** with context injection (current file, selection, workspace)
- ✅ **Agent routing** for better analysis and planning
- ✅ **Context-aware execution** optimized for interactive use
- ✅ **Better AI steering** with detailed instructions

---

## How It Works

### Mode Detection

SpecFact CLI automatically detects the operational mode:

1. **Explicit flag** - `--mode cicd` or `--mode copilot` (highest priority)
2. **Environment detection** - Checks for CoPilot API availability, IDE integration
3. **Default** - Falls back to CI/CD mode if no CoPilot environment detected

### Agent Routing

In CoPilot mode, commands are routed through specialized agents:

| Command | Agent | Purpose |
|---------|-------|---------|
| `import from-code` | `AnalyzeAgent` | AI-first brownfield analysis with semantic understanding (multi-language support) |
| `plan init` | `PlanAgent` | Plan management with business logic understanding |
| `plan compare` | `PlanAgent` | Plan comparison with deviation analysis |
| `sync spec-kit` | `SyncAgent` | Bidirectional sync with conflict resolution |

### Context Injection

CoPilot mode automatically injects relevant context:

- **Current file**: Active file in IDE
- **Selection**: Selected text/code
- **Workspace**: Repository root path
- **Git context**: Current branch, recent commits
- **Codebase context**: Directory structure, files, dependencies

This context is used to generate enhanced prompts that instruct the AI IDE to:

- Understand the codebase semantically
- Call the SpecFact CLI with appropriate arguments
- Enhance CLI results with semantic understanding

### Pragmatic Integration Benefits

- ✅ **No separate LLM setup** - Uses AI IDE's existing LLM (Cursor, CoPilot, etc.)
- ✅ **No additional API costs** - Leverages existing IDE infrastructure
- ✅ **Simpler architecture** - No langchain, API keys, or complex integration
- ✅ **Better developer experience** - Native IDE integration via slash commands
- ✅ **Streamlined workflow** - AI understands codebase, CLI handles structured work

---

## Examples

### Example 1: Brownfield Analysis

```bash
# CI/CD mode (fast, deterministic, Python-only)
specfact --mode cicd import from-code --repo . --confidence 0.7

# CoPilot mode (AI-first, semantic understanding, multi-language)
specfact --mode copilot import from-code --repo . --confidence 0.7

# Output (CoPilot mode):
# Mode: CoPilot (AI-first analysis)
# 🤖 AI-powered analysis (semantic understanding)...
# ✓ AI analysis complete
# ✓ Found X features
# ✓ Detected themes: ...
```

**Key Differences**:

- **CoPilot Mode**: Uses LLM for semantic understanding, supports all languages, generates high-quality Spec-Kit artifacts
- **CI/CD Mode**: Uses Python AST for fast analysis, Python-only, generates generic content (hardcoded fallbacks)

### Example 2: Plan Initialization

```bash
# CI/CD mode (minimal prompts)
specfact --mode cicd plan init --no-interactive

# CoPilot mode (enhanced interactive prompts)
specfact --mode copilot plan init --interactive

# Output:
# Mode: CoPilot (agent routing)
# Agent prompt generated (XXX chars)
# [enhanced interactive prompts]
```

### Example 3: Plan Comparison

```bash
# CoPilot mode with enhanced deviation analysis
specfact --mode copilot plan compare \
  --manual .specfact/plans/main.bundle.yaml \
  --auto .specfact/plans/my-project-*.bundle.yaml

# Output:
# Mode: CoPilot (agent routing)
# Agent prompt generated (XXX chars)
# [enhanced deviation analysis with context]
```

---

## Mode Differences

| Feature | CI/CD Mode | CoPilot Mode |
|---------|-----------|--------------|
| **Speed** | Fast, deterministic | Slightly slower, context-aware |
| **Output** | Structured, minimal | Enhanced, detailed |
| **Prompts** | Standard | Enhanced with context |
| **Context** | Minimal | Full context injection |
| **Agent Routing** | Direct execution | Agent-based routing |
| **Use Case** | Automation, CI/CD | Interactive development, IDE |

---

## When to Use Each Mode

### Use CI/CD Mode When

- ✅ Running in CI/CD pipelines
- ✅ Automating workflows
- ✅ Need fast, deterministic execution
- ✅ Don't need enhanced prompts

### Use CoPilot Mode When

- ✅ Working in IDE with AI assistance
- ✅ Need enhanced prompts for better AI steering
- ✅ Want context-aware execution
- ✅ Interactive development workflows

---

## IDE Integration

For IDE integration with slash commands, see:

- **[IDE Integration Guide](ide-integration.md)** - Set up slash commands in your IDE

---

## Related Documentation

- [IDE Integration Guide](ide-integration.md) - Set up IDE slash commands
- [Command Reference](../reference/commands.md) - All CLI commands
- [Architecture](../reference/architecture.md) - Technical details

---

## Next Steps

- ✅ Use `--mode copilot` on CLI commands for enhanced prompts
- 📖 Read [IDE Integration Guide](ide-integration.md) for slash commands
- 📖 Read [Command Reference](../reference/commands.md) for all commands
