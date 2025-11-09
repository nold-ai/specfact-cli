# SpecFact CLI

> **Stop "vibe coding", start shipping quality code with contracts**

[![License](https://img.shields.io/badge/license-Sustainable%20Use-blue.svg)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/nold-ai/specfact-cli)

---

## What is SpecFact CLI?

A command-line tool that helps you write better code by enforcing **contracts** - rules that catch bugs before they reach production.

Think of it as a **quality gate** for your development workflow that:

- ✅ Catches async bugs automatically
- ✅ Validates your code matches your specs
- ✅ Blocks bad code from merging
- ✅ Works offline, no cloud required

**Perfect for:** Teams who want to ship faster without breaking things.

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
# Starting a new project?
specfact plan init --interactive

# Have existing code?
specfact import from-code --repo . --name my-project

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

**Using Spec-Kit?** See [The Journey: From Spec-Kit to SpecFact](docs/guides/speckit-journey.md)

**Need help?** Browse the [Documentation Hub](docs/README.md)

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

**Sustainable Use License** - Free for internal business use

### ✅ You Can

- Use it for your business (internal tools, automation)
- Modify it for your own needs
- Provide consulting services using SpecFact CLI

### ❌ You Cannot

- Sell it as a SaaS product
- White-label and resell
- Create competing products

For commercial licensing, contact [hello@noldai.com](mailto:hello@noldai.com)

**Full license**: [LICENSE.md](LICENSE.md) | **FAQ**: [USAGE-FAQ.md](USAGE-FAQ.md)

---

## Support

- 💬 **Questions?** [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 **Found a bug?** [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 **Need help?** [hello@noldai.com](mailto:hello@noldai.com)

---

> **Built with ❤️ by [NOLD AI](https://noldai.com)**

Copyright © 2025 Nold AI (Owner: Dominikus Nold)

**Trademarks**: NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). All other trademarks mentioned in this project are the property of their respective owners. See [TRADEMARKS.md](TRADEMARKS.md) for more information.
