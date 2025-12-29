# SpecFact CLI

> **Stop vibe coding. Start shipping quality code with contracts.**  
> Brownfield-first CLI: Analyze legacy Python → find gaps → enforce contracts

[![PyPI version](https://img.shields.io/pypi/v/specfact-cli.svg)](https://pypi.org/project/specfact-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/specfact-cli.svg)](https://pypi.org/project/specfact-cli/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/nold-ai/specfact-cli)

<div align="center">

**[🌐 Learn More at noldai.com](https://noldai.com)** • **[📚 Documentation](https://nold-ai.github.io/specfact-cli)** • **[💬 Support](mailto:hello@noldai.com)**

</div>

---

## 📋 Current Version: 0.21.0

**🎉 v0.21.0** introduces DevOps backlog tracking integration and OpenSpec bridge adapter support, expanding SpecFact's capabilities for team collaboration and specification management.

**SpecFact 0.21.0 focuses on what it does best: analyzing legacy code, enforcing contracts, and integrating with modern DevOps workflows.** This release is production-ready and continues to receive regular updates.

| Capability | Status | Description |
|------------|--------|-------------|
| **Code Analysis** | ✅ Stable | Reverse engineer legacy code into documented specs |
| **Gap Detection** | ✅ Stable | Find missing tests, contracts, and documentation |
| **Contract Enforcement** | ✅ Stable | Prevent regressions with runtime validation |
| **API Contract Testing** | ✅ Stable | Validate OpenAPI specs with Specmatic |
| **AI IDE Bridge** | ✅ Stable | Generate prompts for Cursor, Copilot, Claude |
| **DevOps Backlog Tracking** | ✅ New | Export OpenSpec change proposals to GitHub Issues, ADO, Linear, Jira |
| **OpenSpec Integration** | ✅ New | Bridge adapter for OpenSpec change proposals and specifications |
| **Code Generation** | ⚠️ Deprecated | Coming in v1.0 with AI-assisted workflow |

**Need code generation?** Use the new bridge commands to get AI-ready prompts:

```bash
# Get AI prompt to fix a gap
specfact generate fix-prompt GAP-001 --bundle legacy-api

# Get AI prompt to generate tests
specfact generate test-prompt src/auth/login.py
```

These prompts work with any AI IDE (Cursor, Copilot, Claude Code, etc.) - you control the code generation, SpecFact validates the results.

---

## 🚀 Quick Start in 60 Seconds

### Install in 10 seconds

```bash
# Zero-install (recommended)
uvx specfact-cli

# Or install with pip (upgrade if already installed)
pip install -U specfact-cli
```

### Your first command (< 60 seconds)

```bash
# Modernizing legacy code? (Recommended)
specfact import from-code legacy-api --repo .

# Starting a new project?
specfact plan init legacy-api --interactive

# Using GitHub Spec-Kit or other tools?
specfact import from-bridge --repo . --adapter speckit --write
```

That's it! 🎉

> **Need machine-readable artifacts?** Use `specfact --output-format json …` (or the per-command `--output-format` flag) to emit plan bundles and reports as JSON instead of YAML.

---

## What is SpecFact CLI?

A brownfield-first CLI that **analyzes your legacy code** to find gaps, then **enforces contracts** to prevent regressions during modernization.

**Stop vibe coding. Start shipping quality code with contracts.** SpecFact automatically extracts specs from existing code, finds missing tests and contracts, then enforces them as you modernize—preventing bugs before they reach production.

**Perfect for:** Teams modernizing legacy Python systems, data pipelines, DevOps scripts

**For teams that can't afford production bugs during migration.**

### 🎯 Built for Real-World Agile Teams

SpecFact isn't just a technical tool—it's designed for **real-world agile/scrum teams** with role-based workflows:

- 👤 **Product Owners** → Export backlog with DoR checklists, prioritization, dependencies, and sprint planning
- 🏗️ **Architects** → Export technical constraints, protocols, contracts, architectural decisions, and risk assessments
- 💻 **Developers** → Export implementation tasks, code mappings, test scenarios, and Definition of Done criteria

**Each role works in their own Markdown files** (no YAML editing), and SpecFact syncs everything together automatically. Perfect for teams using agile/scrum practices with clear role separation.

---

## Why SpecFact?

### **Love GitHub Spec-Kit or OpenSpec? SpecFact Adds What's Missing**

**Use together:** Keep using Spec-Kit for new features, OpenSpec for change tracking, add SpecFact for legacy code modernization.

| What You Need | Spec-Kit / OpenSpec | SpecFact CLI |
|---------------|---------------------|--------------|
| **Work with existing code** | ⚠️ Designed for new features | ✅ **Reverse-engineer legacy code** |
| **Prevent regressions** | ⚠️ Documentation only | ✅ **Runtime contract enforcement** |
| **Find hidden bugs** | ⚠️ LLM suggestions (may miss) | ✅ **Symbolic execution** (CrossHair) |
| **Automated safety net** | ⚠️ Manual code review | ✅ **CI/CD gates** (GitHub Actions) |
| **DevOps integration** | ⚠️ Manual export | ✅ **Bridge adapters** (GitHub, ADO, Linear, Jira) |

**Perfect together:**

- ✅ **Spec-Kit** for new features → Fast spec generation with Copilot
- ✅ **OpenSpec** for change tracking → Specification anchoring and delta tracking
- ✅ **SpecFact** for legacy code → Runtime enforcement prevents regressions
- ✅ **Bridge adapters** → Sync between all tools automatically (New in 0.21.0)
- ✅ **GitHub Actions** → SpecFact integrates with your existing GitHub workflows

**Bottom line:** Spec-Kit is great for documenting new features. OpenSpec excels at change tracking. SpecFact is essential for modernizing legacy code safely. Use all three together for the best of all worlds.

---

## 💡 Key Capabilities

### Technical Capabilities

- ✅ **Reverse engineer legacy code** → Extract specs automatically from existing code
- ✅ **Runtime contract enforcement** → Prevent regressions during modernization
- ✅ **Symbolic execution** → Discover hidden edge cases with CrossHair
- ✅ **API contract testing** → Validate OpenAPI/AsyncAPI specs with Specmatic integration
- ✅ **Works offline** → No cloud required, fully local
- ✅ **CLI integrations** → Works seamlessly with VS Code, Cursor, GitHub Actions, and any agentic workflow

### Team Collaboration Capabilities

- ✅ **Persona-based workflows** → Product Owners, Architects, and Developers work in parallel on their own sections
- ✅ **Agile/scrum alignment** → Definition of Ready (DoR), story points, dependencies, prioritization, sprint planning
- ✅ **Role-specific exports** → Each persona gets a tailored Markdown view with only what they need
- ✅ **Git-native collaboration** → Conflicts resolved in human-readable Markdown, not brittle YAML
- ✅ **Real-world templates** → Templates designed by agile coaches to match actual team expectations

---

## 👥 Team Collaboration: Persona-Based Workflows

SpecFact enables **real-world agile/scrum teams** to work together seamlessly with role-based workflows:

```bash
# Product Owner: Export backlog for sprint planning
specfact project export --bundle legacy-api --persona product-owner
# → Exports: DoR checklists, prioritization, dependencies, business value, sprint planning

# Architect: Export technical design
specfact project export --bundle legacy-api --persona architect
# → Exports: Technical constraints, protocols, contracts, architectural decisions, NFRs

# Developer: Export implementation details
specfact project export --bundle legacy-api --persona developer
# → Exports: Tasks, code mappings, test scenarios, Definition of Done

# Each role edits their Markdown, then imports back
specfact project import --bundle legacy-api --persona product-owner --source backlog.md
```

**Why this matters:**

- ✅ **No YAML editing** → Everyone works in familiar Markdown
- ✅ **Parallel workflows** → Product Owners, Architects, and Developers work simultaneously
- ✅ **Git-native** → Conflicts resolved in Markdown (human-readable), not YAML
- ✅ **Agile/scrum ready** → Built-in DoR validation, dependency tracking, sprint planning
- ✅ **Real-world templates** → Designed by agile coaches to match actual team expectations

👉 **[Agile/Scrum Workflows Guide](docs/guides/agile-scrum-workflows.md)** - Complete guide to persona-based team collaboration

---

## 🔌 CLI Integrations

SpecFact CLI works with your existing tools—no new platform to learn. See real bugs that were caught and fixed through different integrations:

- ✅ **VS Code** - Catch async bugs before you commit
- ✅ **Cursor** - Prevent regressions during AI-assisted refactoring
- ✅ **GitHub Actions** - Block bad code from merging
- ✅ **Pre-commit Hooks** - Validate code locally before pushing
- ✅ **AI Assistants** - Find edge cases AI might miss

👉 **[Integration Showcases](docs/examples/integration-showcases/)** - Real examples of bugs fixed via CLI integrations

**Core USP**: Pure CLI-first approach—works offline, no account required, zero vendor lock-in. Regularly showcases successful integrations that fix bugs not detected by other tools.

### 🔗 Bridge Adapter Integrations (New in 0.21.0)

SpecFact now supports bridge adapters for seamless integration with external tools and specification frameworks:

- ✅ **OpenSpec Integration** - Sync OpenSpec change proposals and specifications
  - Export change proposals to DevOps tools (GitHub Issues, ADO, Linear, Jira)
  - Read OpenSpec specifications for validation and alignment
  - Bidirectional sync between OpenSpec and SpecFact project bundles
  - Content sanitization for public repositories
- ✅ **GitHub Spec-Kit** - Bidirectional sync with Spec-Kit projects
- ✅ **Generic Markdown** - Import/export from any markdown-based specification format

### Example: OpenSpec DevOps Backlog Tracking

```bash
# Export OpenSpec change proposals to GitHub Issues
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli \
  --sanitize --target-repo nold-ai/specfact-cli

# Sync OpenSpec specifications (read-only)
specfact sync bridge --adapter openspec --mode read-only --bundle legacy-api
```

👉 **[Command Reference - Sync Bridge](docs/reference/commands.md#sync-bridge)** - Complete bridge adapter documentation

### 🤖 AI IDE Bridge (New in 0.17)

SpecFact now generates prompts you can use with any AI IDE for code generation:

```bash
# 1. Analyze your code to find gaps
specfact analyze gaps --bundle legacy-api

# 2. Generate AI prompt to fix a specific gap
specfact generate fix-prompt GAP-001

# 3. Copy prompt to your AI IDE (Cursor, Copilot, Claude)
# 4. AI generates the fix
# 5. Validate with SpecFact
specfact enforce sdd --bundle legacy-api
```

**Why this approach?**

- ✅ **You control the AI** - Use your preferred AI IDE and model
- ✅ **SpecFact validates** - Ensure AI-generated code meets contracts
- ✅ **No lock-in** - Works with Cursor, Copilot, Claude Code, or any AI tool
- ✅ **Quality gates** - Prevent AI hallucinations from reaching production

---

## See It In Action

We ran SpecFact CLI **on itself** to prove it works with legacy code:

- ⚡ Analyzed 32 legacy Python files → Discovered **32 features** and **81 stories** in **3 seconds**
- 🚫 Set enforcement to "balanced" → **Blocked 2 HIGH violations** (as configured)
- 📊 Compared manual vs auto-derived plans → Found **24 deviations** in **5 seconds**

**Total time**: < 10 seconds | **Total value**: Found real naming inconsistencies and undocumented features in legacy codebase

👉 **[Read the complete example](docs/examples/dogfooding-specfact-cli.md)** with actual commands and outputs

---

## Documentation

**New to SpecFact?** Start with the [Getting Started Guide](docs/getting-started/README.md)

**Working with a team?** See [Agile/Scrum Workflows](docs/guides/agile-scrum-workflows.md) - Persona-based team collaboration with Product Owners, Architects, and Developers

**Want to see integrations?** Check out [Integration Showcases](docs/examples/integration-showcases/) - Real bugs fixed via VS Code, Cursor, GitHub Actions

**Tried Spec-Kit?** See [How SpecFact Compares to Spec-Kit](docs/guides/speckit-comparison.md) and [The Journey: From Spec-Kit to SpecFact](docs/guides/speckit-journey.md)

**Need help?** Browse the [Documentation Hub](docs/README.md)

---

## Optional Telemetry (Opt-In)

- Telemetry is **off by default** and only activates if you set `SPECFACT_TELEMETRY_OPT_IN=true` or create `~/.specfact/telemetry.opt-in`.
- When enabled, SpecFact records anonymized metrics (e.g., number of features detected, contract violations blocked) to help us publish aggregate stats such as “contracts prevented 70% of the bugs surfaced during modernization.”
- Data is stored locally in `~/.specfact/telemetry.log`, and you can route it to your own OpenTelemetry collector via `SPECFACT_TELEMETRY_ENDPOINT`.
- Learn more in [`docs/reference/telemetry.md`](docs/reference/telemetry.md).

---

## Project Documentation

### 📚 Online Documentation

**GitHub Pages**: Full documentation is available at `https://nold-ai.github.io/specfact-cli/`

The documentation includes:

- Getting Started guides
- Complete command reference
- IDE integration setup
- Use cases and examples
- Architecture overview
- Testing procedures

**Note**: The GitHub Pages workflow is configured and will automatically deploy when changes are pushed to the `main` branch. Enable GitHub Pages in your repository settings to activate the site.

### 📖 Local Documentation

All documentation is in the [`docs/`](docs/) directory:

- **[Documentation Index](docs/README.md)** - Complete documentation overview
- **[Getting Started](docs/getting-started/installation.md)** - Installation and setup
- **[Command Reference](docs/reference/commands.md)** - All available commands
- **[IDE Integration](docs/guides/ide-integration.md)** - Set up slash commands
- **[Use Cases](docs/guides/use-cases.md)** - Real-world scenarios

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/nold-ai/specfact-cli.git
cd specfact-cli
pip install -e ".[dev]"
hatch run contract-test-full
```

---

## License

**Apache License 2.0** - Open source and enterprise-friendly

SpecFact CLI is licensed under the Apache License 2.0, which means:

- ✅ **Free to use** for any purpose (commercial or non-commercial)
- ✅ **Modify and distribute** as needed
- ✅ **Enterprise-friendly** with explicit patent grant
- ✅ **Build commercial products** on top of SpecFact CLI

**Full license**: [LICENSE.md](LICENSE.md)

**Note**: The Apache 2.0 license is ideal for enterprise brownfield modernization projects, as it provides legal clarity and patent protection that many enterprises require.

---

## Support

- 💬 **Questions?** [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 **Found a bug?** [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 **Need help?** [hello@noldai.com](mailto:hello@noldai.com)
- 🌐 **Learn more:** [noldai.com](https://noldai.com)

---

<div align="center">

**Built with ❤️ by [NOLD AI](https://noldai.com)**

Copyright © 2025 Nold AI (Owner: Dominikus Nold)

**Trademarks**: NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). All other trademarks mentioned in this project are the property of their respective owners. See [TRADEMARKS.md](TRADEMARKS.md) for more information.

</div>
