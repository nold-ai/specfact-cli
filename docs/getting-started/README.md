# Getting Started with SpecFact CLI

Welcome to SpecFact CLI! This guide will help you get started in under 60 seconds.

## Installation

Choose your preferred installation method:

- **[Installation Guide](installation.md)** - All installation options (uvx, pip, Docker, GitHub Actions)
- **[Enhanced Analysis Dependencies](../installation/enhanced-analysis-dependencies.md)** - Optional dependencies for graph-based analysis (pyan3, syft, bearer, graphviz)

## Quick Start

### Module System Note

SpecFact runs on a lifecycle-managed module system.

- Core runtime manages lifecycle, registry, contracts, and orchestration.
- Feature behavior is implemented in module-local command implementations.
- This allows feature modules to evolve independently without repeatedly rewiring CLI core logic.

### Your First Command

**For Legacy Code Modernization** (Recommended):

```bash
# CLI-only mode (works with uvx, no installation needed)
uvx specfact-cli@latest import from-code my-project --repo .

# Interactive AI Assistant mode (requires pip install + specfact init)
# See First Steps guide for IDE integration setup
```

**For New Projects**:

```bash
# CLI-only mode (bundle name as positional argument)
uvx specfact-cli@latest plan init my-project --interactive

# Interactive AI Assistant mode (recommended for better results)
# Requires: pip install specfact-cli && specfact init
```

**Note**: Interactive AI Assistant mode provides better feature detection and semantic understanding, but requires `pip install specfact-cli` and IDE setup. CLI-only mode works immediately with `uvx` but may show 0 features for simple test cases.

### Modernizing Legacy Code?

**New to brownfield modernization?** See our **[Brownfield Engineer Guide](../guides/brownfield-engineer.md)** for a complete walkthrough of modernizing legacy Python code with SpecFact CLI.

## Next Steps

- 📖 **[Installation Guide](installation.md)** - Install SpecFact CLI
- 📖 **[First Steps](first-steps.md)** - Step-by-step first commands
- 📖 **[Module Bootstrap Checklist](module-bootstrap-checklist.md)** - Verify bundled modules are installed in user/project scope
- 📖 **[Tutorial: Using SpecFact with OpenSpec or Spec-Kit](tutorial-openspec-speckit.md)** ⭐ **NEW** - Complete beginner-friendly tutorial
- 📖 **[DevOps Backlog Integration](../guides/devops-adapter-integration.md)** 🆕 **NEW FEATURE** - Integrate SpecFact into agile DevOps workflows
- 📖 **[Backlog Refinement](../guides/backlog-refinement.md)** 🆕 **NEW FEATURE** - AI-assisted template-driven refinement for standardizing work items
- 📖 **[Tutorial: Backlog Refine with AI IDE](tutorial-backlog-refine-ai-ide.md)** 🆕 - End-to-end for agile DevOps teams: slash prompt, story quality, underspecification, splitting, DoR, custom templates
- 📖 **[Tutorial: Daily Standup and Sprint Review](tutorial-daily-standup-sprint-review.md)** 🆕 - End-to-end daily standup: auto-detect repo (GitHub/ADO), view standup table, post comment, interactive, Copilot export
- 📖 **[Use Cases](../guides/use-cases.md)** - See real-world examples
- 📖 **[Command Reference](../reference/commands.md)** - Learn all available commands

## Need Help?

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 [hello@noldai.com](mailto:hello@noldai.com)
