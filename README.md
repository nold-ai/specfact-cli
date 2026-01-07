# SpecFact CLI

> **Brownfield-first legacy code modernization with runtime contract enforcement.**  
> Analyze existing Python code → Extract specs → Find gaps → Enforce contracts → Prevent regressions

**No API keys required. Works offline. Zero vendor lock-in.**

[![PyPI version](https://img.shields.io/pypi/v/specfact-cli.svg)](https://pypi.org/project/specfact-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/specfact-cli.svg)](https://pypi.org/project/specfact-cli/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/nold-ai/specfact-cli)

<div align="center">

**[🌐 specfact.com](https://specfact.com)** • **[📚 specfact.io](https://specfact.io)** • **[👨‍💻 specfact.dev](https://specfact.dev)** • **[📖 Documentation](https://docs.specfact.io/)** • **[💬 Support](mailto:hello@noldai.com)**

</div>

## 🌐 SpecFact Domains

- **[specfact.com](https://specfact.com)** - Commercial landing page (marketing, pricing, enterprise)
- **[specfact.io](https://specfact.io)** - Product ecosystem hub (CLI reference, integrations, changelog, product docs)
- **[specfact.dev](https://specfact.dev)** - Developer community (tutorials, guides, blog, community content) ⭐ **For developers**
- **[docs.specfact.io](https://docs.specfact.io/)** - Complete online documentation

---

## What is SpecFact?

**SpecFact CLI analyzes your existing Python code** to automatically extract specifications, find missing tests and contracts, and enforce them to prevent bugs during modernization.

**Perfect for:** Teams modernizing legacy Python systems who can't afford production bugs during migration.

### Why SpecFact?

AI coding assistants are powerful but unpredictable when requirements live in chat history. SpecFact adds a **brownfield-first analysis workflow** that understands existing code, extracts specs automatically, and enforces them as runtime contracts, giving you deterministic, reviewable outputs.

**Key outcomes:**

- **Understand legacy code** in minutes, not weeks (automatic spec extraction)
- **Find gaps** in tests, contracts, and documentation automatically
- **Prevent regressions** with runtime contract enforcement during modernization
- **Works with the tools you already use**: VS Code, Cursor, GitHub Actions, pre-commit hooks
- **No API keys required** - Works completely offline

---

## 🚀 Quick Start

### Step 1: Install SpecFact CLI

```bash
# Zero-install (recommended - no setup needed)
uvx specfact-cli@latest

# Or install globally
pip install -U specfact-cli
```

### Step 2: Initialize IDE Integration

**Set up slash commands in your IDE (Cursor, VS Code, Copilot, etc.):**

```bash
# Auto-detect IDE and initialize
specfact init

# Or specify IDE explicitly
specfact init --ide cursor
specfact init --ide vscode

# Install required packages for contract enhancement
specfact init --ide cursor --install-deps
```

**What this does:**

- Copies prompt templates to your IDE
- Makes slash commands available in your IDE's AI chat
- Optionally installs required packages (`beartype`, `icontract`, `crosshair-tool`, `pytest`)

### Step 3: Run Your First Analysis

**In your IDE's AI chat, use the slash command:**

```bash
# In IDE chat (Cursor, VS Code, Copilot, etc.)
/specfact.01-import my-project --repo .
```

**Or use the CLI directly:**

```bash
# Analyze legacy codebase (most common use case)
specfact import from-code my-project --repo .
```

**⏱️ Timing:** Analysis typically takes **10-15 minutes** for typical repositories (e.g., `specfact-cli` itself with several hundred features & contracts). Smaller codebases may complete in 2-5 minutes. Large codebases (3000+ features) may take 15-30 minutes, but progress reporting shows real-time status. The analysis performs AST parsing, Semgrep pattern detection, and Specmatic integration.

**💾 Checkpointing:** Features are saved immediately after initial analysis, so you can safely interrupt and resume the import process without losing progress.

**⚡ Performance:** Optimized for large codebases with pre-computed AST parsing and file hashes (5-15x faster than previous versions).

**That's it!** SpecFact will extract features and stories from your code, find missing tests and contracts, and generate a plan bundle you can enforce.

👉 **[Getting Started Guide](docs/getting-started/README.md)** - Complete walkthrough with examples  
👉 **[AI IDE Workflow Guide](docs/guides/ai-ide-workflow.md)** ⭐ - Complete AI-assisted development workflow

---

## 🎯 Find Your Path

### New to SpecFact?

**Primary Goal**: Analyze legacy Python → find gaps → enforce contracts

1. **[Getting Started](docs/getting-started/README.md)** - Install and run your first command
2. **[Command Chains Reference](docs/guides/command-chains.md)** ⭐ **NEW** - Complete workflows from start to finish
3. **[Common Tasks Quick Reference](docs/guides/common-tasks.md)** ⭐ **NEW** - Quick answers to "How do I X?"
4. **[Modernizing Legacy Code?](docs/guides/brownfield-engineer.md)** ⭐ - Brownfield-first guide
5. **[The Brownfield Journey](docs/guides/brownfield-journey.md)** ⭐ - Complete modernization workflow

**Time**: < 10 minutes | **Result**: Running your first brownfield analysis

### Using AI IDEs? (Cursor, Copilot, Claude)

**Primary Goal**: Let SpecFact find gaps, use your AI IDE to fix them

👉 **[AI IDE Workflow Guide](docs/guides/ai-ide-workflow.md)** ⭐ **NEW** - Complete AI-assisted development workflow

### Working with a Team?

**Primary Goal**: Enable team collaboration with role-based workflows

👉 **[Agile/Scrum Workflows](docs/guides/agile-scrum-workflows.md)** ⭐ - Persona-based team collaboration

### Need Integrations?

**Primary Goal**: Integrate with Spec-Kit, OpenSpec, Specmatic, or DevOps tools

👉 **[Integrations Overview](docs/guides/integrations-overview.md)** ⭐ **NEW** - Complete guide to all integrations

---

## Key Features

### 🔍 Code Analysis

- **Reverse engineer** legacy code into documented specs
- **Find gaps** in tests, contracts, and documentation
- **Works with** any Python project (no special setup required)

👉 **[Command Chains](docs/guides/command-chains.md)** - See complete workflows

### 🛡️ Contract Enforcement

- **Prevent regressions** with runtime contract validation
- **CI/CD integration** - Block bad code from merging
- **Works offline** - No cloud required

👉 **[Command Reference](docs/reference/commands.md)** - All enforcement commands

### 👥 Team Collaboration

- **Role-based workflows** - Product Owners, Architects, Developers work in parallel
- **Markdown-based** - No YAML editing required
- **Agile/scrum ready** - DoR checklists, story points, dependencies

👉 **[Agile/Scrum Workflows](docs/guides/agile-scrum-workflows.md)** - Team collaboration guide

### 🔌 Integrations

- **VS Code, Cursor** - Catch bugs before you commit
- **GitHub Actions** - Automated quality gates
- **AI IDEs** - Generate prompts for fixing gaps
- **DevOps tools** - Sync with GitHub Issues, Linear, Jira
- **Spec-Kit, OpenSpec, Specmatic** - Works with your existing tools

👉 **[Integrations Overview](docs/guides/integrations-overview.md)** - All integration options

---

## Common Use Cases

### 1. Modernizing Legacy Code ⭐ **Most Common**

**Problem:** Existing codebase with no specs or outdated documentation

👉 **[Brownfield Modernization Guide](docs/guides/brownfield-engineer.md)** - Complete walkthrough

### 2. Working with a Team

**Problem:** Need team collaboration with role-based workflows

👉 **[Agile/Scrum Workflows Guide](docs/guides/agile-scrum-workflows.md)** - Team collaboration guide

### 3. Using AI IDEs (Cursor, Copilot, Claude)

**Problem:** Want AI to fix gaps, but need validation

👉 **[AI IDE Workflow Guide](docs/guides/ai-ide-workflow.md)** - Complete AI-assisted workflow

### 4. Integrating with Other Tools

**Problem:** Want to use SpecFact with Spec-Kit, OpenSpec, or Specmatic

👉 **[Integrations Overview](docs/guides/integrations-overview.md)** - Choose the right integration

---

## Documentation

### Quick References

- **[Command Chains](docs/guides/command-chains.md)** ⭐ **NEW** - Complete workflows from start to finish
- **[Common Tasks](docs/guides/common-tasks.md)** ⭐ **NEW** - Quick answers to "How do I X?"
- **[Command Reference](docs/reference/commands.md)** - All commands documented

### Getting Started

- **[Getting Started Guide](docs/getting-started/README.md)** - Install and first commands
- **[Modernizing Legacy Code?](docs/guides/brownfield-engineer.md)** ⭐ - Brownfield-first guide
- **[The Brownfield Journey](docs/guides/brownfield-journey.md)** ⭐ - Complete modernization workflow

### Guides

- **[AI IDE Workflow](docs/guides/ai-ide-workflow.md)** ⭐ **NEW** - AI-assisted development
- **[Agile/Scrum Workflows](docs/guides/agile-scrum-workflows.md)** ⭐ - Team collaboration
- **[Integrations Overview](docs/guides/integrations-overview.md)** ⭐ **NEW** - All integrations
- **[Use Cases](docs/guides/use-cases.md)** - Common scenarios

### Integration Guides

- **[Spec-Kit Journey](docs/guides/speckit-journey.md)** - From Spec-Kit to SpecFact
- **[OpenSpec Journey](docs/guides/openspec-journey.md)** - OpenSpec integration
- **[Specmatic Integration](docs/guides/specmatic-integration.md)** - API contract testing
- **[DevOps Adapter Integration](docs/guides/devops-adapter-integration.md)** - GitHub Issues, Linear, Jira

👉 **[Full Documentation Index](docs/README.md)** - Browse all documentation  
👉 **[Online Documentation](https://docs.specfact.io/)** - Complete documentation site

---

## How SpecFact Compares

**New to spec-driven development?** Here's how SpecFact compares to other tools:

| Tool | Best For | SpecFact's Focus |
|------|----------|------------------|
| **GitHub Spec-Kit** | Greenfield specs, multi-language, interactive authoring | **Brownfield analysis**, runtime enforcement, formal verification |
| **OpenSpec** | Specification anchoring, change tracking, cross-repo workflows | **Code analysis**, contract enforcement, DevOps integration |
| **Traditional Testing** | Manual test writing, code review | **Automated gap detection**, contract-first validation, CI/CD gates |

**Key Differentiators:**

- ✅ **Brownfield-first** - Reverse engineers existing code (primary use case)
- ✅ **Runtime enforcement** - Contracts prevent regressions automatically
- ✅ **Formal verification** - CrossHair symbolic execution (not just LLM suggestions)
- ✅ **Team collaboration** - Role-based workflows for agile/scrum teams
- ✅ **Works offline** - No API keys, no cloud, zero vendor lock-in

👉 **[See detailed comparison guide](docs/guides/speckit-comparison.md)** - Understand when to use SpecFact, Spec-Kit, OpenSpec, or all together

---

## Benefits

### Works with Your Existing Tools

- ✅ **No new platform** - Pure CLI, works offline
- ✅ **No account required** - Fully local, zero vendor lock-in
- ✅ **Integrates everywhere** - VS Code, Cursor, GitHub Actions, pre-commit hooks

### Built for Real Teams

- ✅ **Role-based workflows** - Product Owners, Architects, Developers work in parallel
- ✅ **Markdown-based** - No YAML editing, human-readable conflicts
- ✅ **Agile/scrum ready** - DoR checklists, story points, sprint planning

### Proven Results

- ✅ **Catches real bugs** - See [Integration Showcases](docs/examples/integration-showcases/)
- ✅ **Prevents regressions** - Runtime contract enforcement
- ✅ **Works on legacy code** - Analyzed itself successfully

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/nold-ai/specfact-cli.git
cd specfact-cli
pip install -e ".[dev]"
hatch run contract-test-full
```

---

## License

**Apache License 2.0** - Open source and enterprise-friendly

- ✅ Free to use for any purpose (commercial or non-commercial)
- ✅ Modify and distribute as needed
- ✅ Enterprise-friendly with explicit patent grant

[Full license](LICENSE.md)

---

## Support

- 💬 **Questions?** [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 **Found a bug?** [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 **Need help?** [hello@noldai.com](mailto:hello@noldai.com)
- 🌐 **Learn more:** [specfact.com](https://specfact.com) • [specfact.io](https://specfact.io) • [specfact.dev](https://specfact.dev)

---

<div align="center">

**Built with ❤️ by [NOLD AI](https://noldai.com)**

Copyright © 2025-2026 Nold AI (Owner: Dominikus Nold)

**Trademarks**: NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). All other trademarks mentioned in this project are the property of their respective owners. See [TRADEMARKS.md](TRADEMARKS.md) for more information.

</div>
