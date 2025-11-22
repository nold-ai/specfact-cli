# Getting Started with SpecFact CLI

Welcome to SpecFact CLI! This guide will help you get started in under 60 seconds.

## Installation

Choose your preferred installation method:

- **[Installation Guide](installation.md)** - All installation options (uvx, pip, Docker, GitHub Actions)

## Quick Start

### Your First Command

**For Legacy Code Modernization** (Recommended):

```bash
# CLI-only mode (works with uvx, no installation needed)
uvx specfact-cli@latest import from-code --repo . --name my-project

# Interactive AI Assistant mode (requires pip install + specfact init)
# See First Steps guide for IDE integration setup
```

**For New Projects**:

```bash
# CLI-only mode
uvx specfact-cli@latest plan init --interactive

# Interactive AI Assistant mode (recommended for better results)
# Requires: pip install specfact-cli && specfact init
```

**Note**: Interactive AI Assistant mode provides better feature detection and semantic understanding, but requires `pip install specfact-cli` and IDE setup. CLI-only mode works immediately with `uvx` but may show 0 features for simple test cases.

### Modernizing Legacy Code?

**New to brownfield modernization?** See our **[Brownfield Engineer Guide](../guides/brownfield-engineer.md)** for a complete walkthrough of modernizing legacy Python code with SpecFact CLI.

## Next Steps

- 📖 **[Installation Guide](installation.md)** - Install SpecFact CLI
- 📖 **[First Steps](first-steps.md)** - Step-by-step first commands
- 📖 **[Use Cases](../guides/use-cases.md)** - See real-world examples
- 📖 **[Command Reference](../reference/commands.md)** - Learn all available commands

## Need Help?

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 [hello@noldai.com](mailto:hello@noldai.com)
