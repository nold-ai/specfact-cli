# SpecFact CLI

> **Stop vibe coding. Start shipping quality code with contracts.**  
> Analyze legacy Python code → Find gaps → Enforce contracts → Prevent regressions

[![PyPI version](https://img.shields.io/pypi/v/specfact-cli.svg)](https://pypi.org/project/specfact-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/specfact-cli.svg)](https://pypi.org/project/specfact-cli/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/nold-ai/specfact-cli)

<div align="center">

**[🌐 Website](https://noldai.com)** • **[📚 Documentation](https://nold-ai.github.io/specfact-cli)** • **[💬 Support](mailto:hello@noldai.com)**

</div>

---

<<<<<<< HEAD
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
=======
## What is SpecFact?

**SpecFact CLI analyzes your existing Python code** to automatically extract specifications, find missing tests and contracts, and enforce them to prevent bugs during modernization.

**Perfect for:** Teams modernizing legacy Python systems who can't afford production bugs during migration.

### The Problem It Solves
>>>>>>> origin/main

- ❌ **Legacy code** with no documentation or outdated specs
- ❌ **Missing tests** and contracts that should exist
- ❌ **Regressions** introduced during refactoring/modernization
- ❌ **No safety net** to catch bugs before production

### The Solution

SpecFact CLI:

1. **Analyzes** your existing code → Extracts specs automatically
2. **Finds gaps** → Missing tests, contracts, documentation
3. **Enforces contracts** → Prevents regressions with runtime validation
4. **Integrates** → Works with VS Code, Cursor, GitHub Actions, pre-commit hooks

**Works offline. No account required. Zero vendor lock-in.**

### How It Works

```mermaid
graph TB
    subgraph "Your Legacy Code"
        LC[Legacy Python Code<br/>No docs, no tests]
    end
    
    subgraph "SpecFact Analysis"
        A1[import from-code<br/>Extract specs]
        A2[Find Gaps<br/>Missing tests & contracts]
        A3[Generate Plan Bundle<br/>Features & Stories]
    end
    
    subgraph "Contract Enforcement"
        E1[Add Contracts<br/>Runtime validation]
        E2[Enforce SDD<br/>Quality gates]
        E3[CI/CD Integration<br/>Block bad code]
    end
    
    subgraph "Team Collaboration"
        T1[Export by Role<br/>PO, Architect, Dev]
        T2[Markdown Workflows<br/>No YAML editing]
        T3[Sync to DevOps<br/>GitHub, Linear, Jira]
    end
    
    subgraph "Safety Net"
        S1[Prevent Regressions<br/>Catch bugs early]
        S2[Modernize Safely<br/>Refactor with confidence]
    end
    
    LC -->|Step 1| A1
    A1 --> A2
    A2 --> A3
    A3 -->|Step 2| E1
    E1 --> E2
    E2 --> E3
    E3 -->|Step 3| S1
    S1 --> S2
    
    A3 -->|Optional| T1
    T1 --> T2
    T2 --> T3
    
    style LC fill:#ef4444,stroke:#dc2626,stroke-width:2px,color:#fff
    style A1 fill:#f97316,stroke:#c2410c,stroke-width:2px,color:#fff
    style A2 fill:#f97316,stroke:#c2410c,stroke-width:2px,color:#fff
    style A3 fill:#f97316,stroke:#c2410c,stroke-width:2px,color:#fff
    style E1 fill:#3b82f6,stroke:#1e40af,stroke-width:2px,color:#fff
    style E2 fill:#3b82f6,stroke:#1e40af,stroke-width:2px,color:#fff
    style E3 fill:#3b82f6,stroke:#1e40af,stroke-width:2px,color:#fff
    style T1 fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    style T2 fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    style T3 fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    style S1 fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff
    style S2 fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff
```

### Typical Workflow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant SF as SpecFact CLI
    participant Code as Legacy Code
    participant CI as CI/CD
    
    Note over Dev,CI: Step 1: Analyze Legacy Code
    Dev->>SF: specfact import from-code my-project
    SF->>Code: Analyze Python files
    Code-->>SF: Extract features & stories
    SF-->>Dev: Plan bundle created
    
    Note over Dev,CI: Step 2: Find & Fix Gaps
    Dev->>SF: specfact analyze gaps my-project
    SF-->>Dev: Missing tests & contracts found
    Dev->>Dev: Add tests & contracts
    
    Note over Dev,CI: Step 3: Enforce Contracts
    Dev->>SF: specfact enforce sdd my-project
    SF->>SF: Validate contracts
    SF-->>Dev: Quality gates configured
    
    Note over Dev,CI: Step 4: Modernize Safely
    Dev->>Code: Refactor code
    Code->>CI: Push changes
    CI->>SF: Run contract validation
    SF-->>CI: ✅ Pass or ❌ Block
    
    alt Contracts Pass
        CI-->>Dev: ✅ Merge allowed
    else Contracts Fail
        CI-->>Dev: ❌ Merge blocked
        Dev->>Code: Fix violations
    end
```

---

## 🚀 Quick Start

### Install (10 seconds)

```bash
# Zero-install (recommended - no setup needed)
uvx specfact-cli@latest

# Or install globally
pip install -U specfact-cli
```

### Your First Command (< 60 seconds)

**Analyze your existing code:**

```bash
# Analyze legacy codebase (most common use case)
specfact import from-code my-project --repo .

# Or start a new project
specfact plan init my-project --interactive
```

**That's it!** SpecFact will:

- Extract features and stories from your code
- Find missing tests and contracts
- Generate a plan bundle you can enforce

👉 **[Getting Started Guide](docs/getting-started/README.md)** - Complete walkthrough with examples

---

## Key Features

### 🔍 Code Analysis

- **Reverse engineer** legacy code into documented specs
- **Find gaps** in tests, contracts, and documentation
- **Works with** any Python project (no special setup required)

### 🛡️ Contract Enforcement

- **Prevent regressions** with runtime contract validation
- **CI/CD integration** - Block bad code from merging
- **Works offline** - No cloud required

### 👥 Team Collaboration

- **Role-based workflows** - Product Owners, Architects, Developers work in parallel
- **Markdown-based** - No YAML editing required
- **Agile/scrum ready** - DoR checklists, story points, dependencies

### 🔌 Integrations

- **VS Code, Cursor** - Catch bugs before you commit
- **GitHub Actions** - Automated quality gates
- **AI IDEs** - Generate prompts for fixing gaps
- **DevOps tools** - Sync with GitHub Issues, Linear, Jira

---

## Common Use Cases

<<<<<<< HEAD
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
=======
### 1. Modernizing Legacy Code ⭐ **Most Common**

**Problem:** Existing codebase with no specs or outdated documentation
>>>>>>> origin/main

```bash
# Step 1: Analyze your code
specfact import from-code my-project --repo .

# Step 2: Review what was found
specfact plan review my-project

# Step 3: Enforce contracts to prevent regressions
specfact enforce sdd my-project
```

👉 **[Brownfield Modernization Guide](docs/guides/brownfield-engineer.md)** - Complete walkthrough

### 2. Working with a Team

**Problem:** Need team collaboration with role-based workflows

```bash
# Product Owner: Export backlog
specfact project export --bundle my-project --persona product-owner

# Architect: Export technical design
specfact project export --bundle my-project --persona architect

# Developer: Export implementation tasks
specfact project export --bundle my-project --persona developer
```

👉 **[Agile/Scrum Workflows Guide](docs/guides/agile-scrum-workflows.md)** - Team collaboration guide

### 3. Using AI IDEs (Cursor, Copilot, Claude)

<<<<<<< HEAD
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
=======
**Problem:** Want AI to fix gaps, but need validation
>>>>>>> origin/main

```bash
# Step 1: Find gaps
specfact analyze gaps --bundle my-project

# Step 2: Generate AI prompt
specfact generate fix-prompt GAP-001 --bundle my-project

# Step 3: Copy to AI IDE → AI fixes → Validate
specfact enforce sdd --bundle my-project
```

👉 **[AI IDE Integration](docs/guides/ide-integration.md)** - Setup guide

---

## See It In Action

We ran SpecFact CLI **on itself** to prove it works:

- ⚡ Analyzed 32 legacy Python files → Found **32 features** and **81 stories** in **3 seconds**
- 🚫 Set enforcement → **Blocked 2 HIGH violations** automatically
- 📊 Compared plans → Found **24 deviations** in **5 seconds**

**Total time**: < 10 seconds | **Result**: Found real bugs and inconsistencies

👉 **[Read the complete example](docs/examples/dogfooding-specfact-cli.md)** - See actual commands and outputs

---

## Documentation

### 🎯 Find Your Path

**New to SpecFact?**

1. **[Getting Started](docs/getting-started/README.md)** - Install and first commands
2. **[Modernizing Legacy Code?](docs/guides/brownfield-engineer.md)** ⭐ - Complete guide
3. **[Use Cases](docs/guides/use-cases.md)** - Common scenarios
4. **[Command Reference](docs/reference/commands.md)** - All commands

**Working with a Team?**

- **[Agile/Scrum Workflows](docs/guides/agile-scrum-workflows.md)** ⭐ - Persona-based collaboration
- **[Project Commands](docs/reference/commands.md#project---project-bundle-management)** - Export/import workflows

**Want Integrations?**

- **[IDE Integration](docs/guides/ide-integration.md)** - VS Code, Cursor setup
- **[Integration Showcases](docs/examples/integration-showcases/)** - Real bugs fixed
- **[GitHub Actions](docs/guides/use-cases.md#use-case-4-cicd-integration)** - CI/CD setup

**Advanced Topics**

- **[Architecture](docs/reference/architecture.md)** - How it works
- **[Schema Versioning](docs/reference/schema-versioning.md)** - Bundle schemas
- **[Testing Guide](docs/technical/testing.md)** - Development setup

👉 **[Full Documentation Index](docs/README.md)** - Browse all documentation

---

## Version 0.21.1

**Latest release** introduces change tracking data models (v1.1 schema) and code change tracking with progress comments.

**What's New:**

- ✅ Change tracking data models for delta spec tracking
- ✅ Code change tracking with GitHub issue progress comments
- ✅ DevOps backlog tracking integration (GitHub Issues, ADO, Linear, Jira)
- ✅ OpenSpec bridge adapter support

👉 **[Changelog](CHANGELOG.md)** - Complete release history

---

## Why SpecFact?

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
- 🌐 **Learn more:** [noldai.com](https://noldai.com)

---

<div align="center">

**Built with ❤️ by [NOLD AI](https://noldai.com)**

Copyright © 2025 Nold AI (Owner: Dominikus Nold)

**Trademarks**: NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). All other trademarks mentioned in this project are the property of their respective owners. See [TRADEMARKS.md](TRADEMARKS.md) for more information.

</div>
