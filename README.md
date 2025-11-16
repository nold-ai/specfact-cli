# SpecFact CLI

> **Understand and Modernize Legacy Code with Confidence**  
> Automatically extract specs from existing Python code, then enforce them as contracts

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/nold-ai/specfact-cli)

---

## What is SpecFact CLI?

A brownfield-first CLI that **reverse engineers your legacy code** into documented specs, then prevents regressions with runtime contract enforcement.

**Stop guessing what your legacy code does.** SpecFact automatically extracts specs from existing code, then enforces them as you modernize.

**Perfect for:** Teams modernizing legacy Python systems, data pipelines, DevOps scripts

**For teams that can't afford production bugs during migration.**

---

## Why SpecFact?

### **Love GitHub Spec-Kit? SpecFact Adds What's Missing**

**Use both together:** Keep using Spec-Kit for new features, add SpecFact for legacy code modernization.

| What You Need | Spec-Kit | SpecFact CLI |
|---------------|----------|--------------|
| **Work with existing code** | ⚠️ Designed for new features | ✅ **Reverse-engineer legacy code** |
| **Prevent regressions** | ⚠️ Documentation only | ✅ **Runtime contract enforcement** |
| **Find hidden bugs** | ⚠️ LLM suggestions (may miss) | ✅ **Symbolic execution** (CrossHair) |
| **Automated safety net** | ⚠️ Manual code review | ✅ **CI/CD gates** (GitHub Actions) |

**Perfect together:**

- ✅ **Spec-Kit** for new features → Fast spec generation with Copilot
- ✅ **SpecFact** for legacy code → Runtime enforcement prevents regressions
- ✅ **Bidirectional sync** → Keep both tools in sync automatically
- ✅ **GitHub Actions** → SpecFact integrates with your existing GitHub workflows

**Bottom line:** Spec-Kit is great for documenting new features. SpecFact is essential for modernizing legacy code safely. Use both together for the best of both worlds.

---

## 💡 Key Capabilities

- ✅ **Reverse engineer legacy code** → Extract specs automatically from existing code
- ✅ **Runtime contract enforcement** → Prevent regressions during modernization
- ✅ **Symbolic execution** → Discover hidden edge cases with CrossHair
- ✅ **Works offline** → No cloud required, fully local

---

## Quick Start

### Install in 10 seconds

```bash
# Zero-install (just run it)
uvx --from specfact-cli specfact --help

# Or install with pip
pip install specfact-cli
```

### Your first command (< 60 seconds)

```bash
# Modernizing legacy code? (Recommended)
specfact import from-code --repo . --name my-project

# Starting a new project?
specfact plan init --interactive

# Using GitHub Spec-Kit?
specfact import from-spec-kit --repo ./my-project --dry-run
```

That's it! 🎉

---

## See It In Action

We ran SpecFact CLI **on itself** to prove it works:

- ⚡ Analyzed 32 Python files → Discovered **32 features** and **81 stories** in **3 seconds**
- 🚫 Set enforcement to "balanced" → **Blocked 2 HIGH violations** (as configured)
- 📊 Compared manual vs auto-derived plans → Found **24 deviations** in **5 seconds**

**Total time**: < 10 seconds | **Total value**: Found real naming inconsistencies and undocumented features

👉 **[Read the complete example](docs/examples/dogfooding-specfact-cli.md)** with actual commands and outputs

---

## Documentation

**New to SpecFact?** Start with the [Getting Started Guide](docs/getting-started/README.md)

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

---

> **Built with ❤️ by [NOLD AI](https://noldai.com)**

Copyright © 2025 Nold AI (Owner: Dominikus Nold)

**Trademarks**: NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). All other trademarks mentioned in this project are the property of their respective owners. See [TRADEMARKS.md](TRADEMARKS.md) for more information.
