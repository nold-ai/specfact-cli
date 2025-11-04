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
uvx specfact --help

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

## What Can You Do?

### 1. 🔄 Import from GitHub Spec-Kit

Already using Spec-Kit? **Level up to automated enforcement** in one command:

```bash
specfact import from-spec-kit --repo ./spec-kit-project --write
```

**Result**: Your Spec-Kit artifacts become production-ready contracts with automated quality gates.

### 2. 🔍 Analyze Your Existing Code

Turn brownfield code into a clean spec:

```bash
specfact import from-code --repo . --name my-project
```

**Result**: Auto-generated plan showing what your code actually does

### 3. 📋 Plan New Features

Start with a spec, not with code:

```bash
specfact plan init --interactive
specfact plan add-feature --key FEATURE-001 --title "User Login"
```

**Result**: Clear acceptance criteria before writing any code

### 4. 🛡️ Enforce Quality

Set rules that actually block bad code:

```bash
specfact enforce stage --preset balanced
```

**Modes:**

- `minimal` - Just observe, never block
- `balanced` - Block critical bugs, warn on others
- `strict` - Block everything suspicious

### 5. ✅ Validate Everything

One command to check it all:

```bash
specfact repro
```

**Checks:** Contracts, types, async patterns, state machines

---

## Documentation

For complete documentation, see **[docs/README.md](docs/README.md)**.

**Quick Links:**

- 📖 **[Getting Started](docs/getting-started/README.md)** - Installation and first steps
- 🎯 **[The Journey: From Spec-Kit to SpecFact](docs/guides/speckit-journey.md)** - Level up from interactive authoring to automated enforcement
- 📋 **[Command Reference](docs/reference/commands.md)** - All commands with examples
- 🤖 **[IDE Integration](docs/guides/ide-integration.md)** - Set up slash commands in your IDE
- 💡 **[Use Cases](docs/guides/use-cases.md)** - Real-world scenarios

---

## Installation Options

### 1. uvx (Easiest)

No installation needed:

```bash
uvx specfact plan init
```

### 2. pip

Install globally:

```bash
pip install specfact-cli
specfact --help
```

### 3. Docker

Run in a container:

```bash
docker run ghcr.io/nold-ai/specfact-cli:latest --help
```

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
