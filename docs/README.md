# SpecFact CLI Documentation

> **Everything you need to know about using SpecFact CLI**

---

## 📚 Documentation

### New to SpecFact CLI?

Start here:

1. **[Getting Started](getting-started/README.md)** - Install and run your first command
2. **[Use Cases](guides/use-cases.md)** - See real-world examples
3. **[Command Reference](reference/commands.md)** - Learn all available commands

### Using GitHub Spec-Kit?

**🎯 Level Up**: SpecFact CLI is **the add-on** to level up from Spec-Kit's interactive authoring to automated enforcement:

- **[The Journey: From Spec-Kit to SpecFact](guides/speckit-journey.md)** - Complete guide to leveling up from interactive slash commands to automated CI/CD enforcement

### Guides

- **[IDE Integration](guides/ide-integration.md)** - Set up slash commands in your IDE
- **[CoPilot Mode](guides/copilot-mode.md)** - Using `--mode copilot` on CLI
- **[Use Cases](guides/use-cases.md)** - Real-world scenarios
- **[Competitive Analysis](guides/competitive-analysis.md)** - How SpecFact compares

### Reference Documentation

- **[Command Reference](reference/commands.md)** - Complete command documentation
- **[Architecture](reference/architecture.md)** - Technical design and principles
- **[Testing](reference/testing.md)** - Testing procedures
- **[Directory Structure](reference/directory-structure.md)** - Project structure

---

## 🚀 Quick Links

### Common Tasks

- **[Install SpecFact CLI](getting-started/installation.md)**
- **[Level up from GitHub Spec-Kit](guides/speckit-journey.md)** - **The add-on** to level up from interactive authoring to automated enforcement
- **[Set Up IDE Integration](guides/ide-integration.md)** - Initialize slash commands in your IDE
- **[Migrate from GitHub Spec-Kit](guides/use-cases.md#use-case-1-github-spec-kit-migration)**
- **[Analyze existing code](guides/use-cases.md#use-case-2-brownfield-code-hardening)**
- **[Start a new project](guides/use-cases.md#use-case-3-greenfield-spec-first-development)**

### By Role

**Developers:**

- [Getting Started Guide](getting-started/README.md)
- [Command Reference](reference/commands.md)
- [Use Cases & Examples](guides/use-cases.md)
- [IDE Integration](guides/ide-integration.md)

**Team Leads:**

- [Use Cases](guides/use-cases.md)
- [Competitive Analysis](guides/competitive-analysis.md)
- [Architecture Overview](reference/architecture.md)
- [Operational Modes](reference/architecture.md#operational-modes)

**Contributors:**

- [Contributing Guidelines](../CONTRIBUTING.md)
- [Architecture Documentation](reference/architecture.md)
- [Development Setup](getting-started/installation.md#development-setup)

---

## 💡 Learn by Example

### Example 1: Your First Command

```bash
# Install (no setup required)
uvx specfact plan init --interactive

# Or use CoPilot mode (if available)
/specfact-plan-init --idea idea.yaml
```

**Takes:** 60 seconds | **Learn:** Basic workflow

### Example 2: Analyze Existing Code

```bash
# CI/CD mode (fast, deterministic)
specfact import from-code --repo . --shadow-only

# CoPilot mode (enhanced prompts)
specfact --mode copilot import from-code --repo . --confidence 0.7

# Or use slash command in IDE (after running specfact init)
/specfact-import-from-code --repo . --confidence 0.7
```

**Takes:** 2-5 minutes | **Learn:** Brownfield analysis

### Example 3: Enforce Quality

```bash
specfact enforce stage --preset balanced
specfact repro
```

**Takes:** 2 minutes | **Learn:** Quality gates

### Example 4: Bidirectional Sync

```bash
# Sync Spec-Kit artifacts
specfact sync spec-kit --repo . --bidirectional --watch

# Sync repository changes
specfact sync repository --repo . --watch
```

**Takes:** < 1 minute | **Learn:** Continuous change management

---

## 🆘 Getting Help

### Documentation

You're here! Browse the guides above.

### Community

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions) - Ask questions
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues) - Report bugs

### Direct Support

- 📧 Email: [hello@noldai.com](mailto:hello@noldai.com)

---

## 🤝 Contributing

Found an error or want to improve the docs?

1. Fork the repository
2. Edit the markdown files in `docs/`
3. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

**Happy building!** 🚀

Copyright © 2025 Nold AI (Owner: Dominikus Nold)
