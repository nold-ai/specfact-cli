# SpecFact CLI Documentation

> **Everything you need to know about using SpecFact CLI**

---

## Why SpecFact?

### **Built for Real-World Agile Teams**

SpecFact isn't just a technical tool—it's designed for **real-world agile/scrum teams** with role-based workflows:

- 👤 **Product Owners** → Work with backlog, DoR checklists, prioritization, dependencies, and sprint planning
- 🏗️ **Architects** → Work with technical constraints, protocols, contracts, architectural decisions, and risk assessments
- 💻 **Developers** → Work with implementation tasks, code mappings, test scenarios, and Definition of Done criteria

**Each role works in their own Markdown files** (no YAML editing), and SpecFact syncs everything together automatically. Perfect for teams using agile/scrum practices with clear role separation.

👉 **[Agile/Scrum Workflows Guide](guides/agile-scrum-workflows.md)** ⭐ **START HERE** - Complete guide to persona-based team collaboration

---

### **Love GitHub Spec-Kit or OpenSpec? SpecFact Adds What's Missing**

**Use together:** Keep using Spec-Kit for new features, OpenSpec for change tracking, add SpecFact for legacy code modernization.

**If you've tried GitHub Spec-Kit or OpenSpec**, you know they're great for documenting new features and tracking changes. SpecFact adds what's missing for legacy code modernization:

👉 **[OpenSpec Journey Guide](guides/openspec-journey.md)** 🆕 ⭐ - Complete integration guide with DevOps export, visual workflows, and brownfield modernization examples

- ✅ **Runtime contract enforcement** → Spec-Kit/OpenSpec generate docs; SpecFact prevents regressions with executable contracts
- ✅ **Brownfield-first** → Spec-Kit/OpenSpec excel at new features; SpecFact understands existing code
- ✅ **Formal verification** → Spec-Kit/OpenSpec use LLM suggestions; SpecFact uses mathematical proof (CrossHair)
- ✅ **Team collaboration** → Spec-Kit is single-user focused; SpecFact supports persona-based workflows for agile teams
- ✅ **DevOps integration** → Bridge adapters sync change proposals to GitHub Issues, ADO, Linear, Jira
- ✅ **GitHub Actions integration** → Works seamlessly with your existing GitHub workflows

**Perfect together:**

- ✅ **Spec-Kit** for new features → Fast spec generation with Copilot
- ✅ **OpenSpec** for change tracking → Specification anchoring and delta tracking
- ✅ **SpecFact** for legacy code → Runtime enforcement prevents regressions
- ✅ **Bridge adapters** → Sync between all tools automatically
- ✅ **Team workflows** → SpecFact adds persona-based collaboration for agile/scrum teams

**Bottom line:** Use Spec-Kit for documenting new features. Use OpenSpec for change tracking. Use SpecFact for modernizing legacy code safely and enabling team collaboration. Use all three together for the best of all worlds.

👉 **[See detailed comparison](guides/speckit-comparison.md)** | **[Journey from Spec-Kit](guides/speckit-journey.md)** | **[OpenSpec Journey](guides/openspec-journey.md)** 🆕 | **[Integrations Overview](guides/integrations-overview.md)** 🆕 | **[Bridge Adapters](reference/commands.md#sync-bridge)**

---

## 🎯 Find Your Path

### New to SpecFact?

**Primary Goal**: Analyze legacy Python → find gaps → enforce contracts

1. **[Getting Started](getting-started/README.md)** - Install and run your first command
2. **[Modernizing Legacy Code?](guides/brownfield-engineer.md)** ⭐ **PRIMARY** - Brownfield-first guide
3. **[The Brownfield Journey](guides/brownfield-journey.md)** ⭐ - Complete modernization workflow
4. **[See It In Action](examples/dogfooding-specfact-cli.md)** - Real example (< 10 seconds)
5. **[Use Cases](guides/use-cases.md)** - Common scenarios

**Time**: < 10 minutes | **Result**: Running your first brownfield analysis

---

### Using AI IDEs? (Cursor, Copilot, Claude) 🆕

**Primary Goal**: Let SpecFact find gaps, use your AI IDE to fix them

```bash
# 1. Run brownfield analysis and validation
specfact import from-code my-project --repo .
specfact repro --verbose

# 2. Generate AI-ready prompt for a specific gap
specfact generate fix-prompt GAP-001 --bundle my-project

# 3. Copy to AI IDE → AI generates fix → Validate with SpecFact
specfact enforce sdd --bundle my-project
```

**Why this approach?**

- ✅ **You control the AI** - Use your preferred AI model
- ✅ **SpecFact validates** - Ensure AI-generated code meets contracts
- ✅ **No lock-in** - Works with any AI IDE

👉 **[Command Reference - Generate Commands](reference/commands.md#generate---generate-artifacts)** - `fix-prompt` and `test-prompt` commands

---

### Working with an Agile/Scrum Team?

**Primary Goal**: Enable team collaboration with role-based workflows

1. **[Agile/Scrum Workflows](guides/agile-scrum-workflows.md)** ⭐ **START HERE** - Persona-based team collaboration
2. **[Command Reference - Project Commands](reference/commands.md#project---project-bundle-management)** - `project export` and `project import` commands
3. **[Persona Workflows](guides/agile-scrum-workflows.md#persona-based-workflows)** - How Product Owners, Architects, and Developers work together
4. **[Definition of Ready](guides/agile-scrum-workflows.md#definition-of-ready-dor)** - DoR validation and sprint planning

**Time**: 15-30 minutes | **Result**: Understanding how your team can collaborate with SpecFact

---

### Love GitHub Spec-Kit or OpenSpec?

**Why SpecFact?** Keep using Spec-Kit for new features, OpenSpec for change tracking, add SpecFact for legacy code modernization.

**Use together:**

- ✅ **Spec-Kit** for new features → Fast spec generation with Copilot
- ✅ **OpenSpec** for change tracking → Specification anchoring and delta tracking
- ✅ **SpecFact** for legacy code → Runtime enforcement prevents regressions
- ✅ **Bridge adapters** → Sync between all tools automatically
- ✅ **GitHub Actions** → SpecFact integrates with your existing GitHub workflows

1. **[Tutorial: Using SpecFact with OpenSpec or Spec-Kit](getting-started/tutorial-openspec-speckit.md)** ⭐ **START HERE** - Complete beginner-friendly step-by-step tutorial
2. **[How SpecFact Compares to Spec-Kit](guides/speckit-comparison.md)** - See what SpecFact adds
3. **[The Journey: From Spec-Kit to SpecFact](guides/speckit-journey.md)** - Add enforcement to Spec-Kit projects
4. **[The Journey: OpenSpec + SpecFact Integration](guides/openspec-journey.md)** 🆕 - Complete OpenSpec integration guide with DevOps export (✅) and bridge adapter (✅)
5. **[DevOps Adapter Integration](guides/devops-adapter-integration.md)** - GitHub Issues and backlog tracking
6. **[Bridge Adapters](reference/commands.md#sync-bridge)** - OpenSpec and DevOps integration
7. **[Migration Use Case](guides/use-cases.md#use-case-2-github-spec-kit-migration)** - Step-by-step
8. **[Bidirectional Sync](guides/use-cases.md#use-case-2-github-spec-kit-migration)** - Keep both tools in sync

**Time**: 15-30 minutes | **Result**: Understand how SpecFact complements Spec-Kit and OpenSpec for legacy code modernization

---

### Using SpecFact Daily?

**Goal**: Use SpecFact effectively in your workflow

1. **[Command Chains Reference](guides/command-chains.md)** ⭐ **NEW** - Complete workflows and command sequences
2. **[Common Tasks Index](guides/common-tasks.md)** ⭐ **NEW** - Quick "How do I X?" reference
3. **[Command Reference](reference/commands.md)** - All commands with examples
4. **[Use Cases](guides/use-cases.md)** - Real-world scenarios
5. **[IDE Integration](guides/ide-integration.md)** - Set up slash commands
6. **[CoPilot Mode](guides/copilot-mode.md)** - Enhanced prompts

**Time**: 30-60 minutes | **Result**: Master daily workflows

---

### Contributing to SpecFact?

**Goal**: Understand internals and contribute

1. **[Architecture](reference/architecture.md)** - Technical design
2. **[Development Setup](getting-started/installation.md#development-setup)** - Local setup
3. **[Testing Procedures](technical/testing.md)** - How we test
4. **[Technical Deep Dives](technical/README.md)** - Implementation details

**Time**: 2-4 hours | **Result**: Ready to contribute

---

## 📚 Documentation Sections

### Getting Started

- [Installation](getting-started/installation.md) - All installation options
- [Enhanced Analysis Dependencies](installation/enhanced-analysis-dependencies.md) - Optional dependencies for graph-based analysis
- [First Steps](getting-started/first-steps.md) - Step-by-step first commands

### User Guides

#### Primary Use Case: Brownfield Modernization ⭐

- [Brownfield Engineer Guide](guides/brownfield-engineer.md) ⭐ **PRIMARY** - Complete modernization guide
- [The Brownfield Journey](guides/brownfield-journey.md) ⭐ **PRIMARY** - Step-by-step workflow
- [Brownfield ROI](guides/brownfield-roi.md) ⭐ - Calculate savings
- [Use Cases](guides/use-cases.md) ⭐ - Real-world scenarios (brownfield primary)

#### Secondary Use Case: Spec-Kit & OpenSpec Integration

- [Spec-Kit Journey](guides/speckit-journey.md) - Add enforcement to Spec-Kit projects
- [Spec-Kit Comparison](guides/speckit-comparison.md) - Understand when to use each tool
- [OpenSpec Journey](guides/openspec-journey.md) 🆕 - OpenSpec integration with SpecFact (DevOps export ✅, bridge adapter ⏳)
- [DevOps Adapter Integration](guides/devops-adapter-integration.md) - GitHub Issues, backlog tracking, and progress comments
- [Bridge Adapters](reference/commands.md#sync-bridge) - OpenSpec and DevOps integration

#### Team Collaboration & Agile/Scrum

- [Agile/Scrum Workflows](guides/agile-scrum-workflows.md) ⭐ **NEW** - Persona-based team collaboration with Product Owners, Architects, and Developers
- [Persona Workflows](guides/agile-scrum-workflows.md#persona-based-workflows) - Role-based workflows for agile teams
- [Definition of Ready](guides/agile-scrum-workflows.md#definition-of-ready-dor) - DoR validation and sprint planning
- [Dependency Management](guides/agile-scrum-workflows.md#dependency-management) - Track story and feature dependencies
- [Conflict Resolution](guides/agile-scrum-workflows.md#conflict-resolution) - Persona-aware merge conflict resolution

#### General Guides

- [UX Features](guides/ux-features.md) - Progressive disclosure, context detection, intelligent suggestions, templates
- [Workflows](guides/workflows.md) - Common daily workflows
- [IDE Integration](guides/ide-integration.md) - Slash commands
- [CoPilot Mode](guides/copilot-mode.md) - Enhanced prompts
- [Troubleshooting](guides/troubleshooting.md) - Common issues and solutions

### Reference

- [Commands](reference/commands.md) - Complete command reference
- [Architecture](reference/architecture.md) - Technical design
- [Operational Modes](reference/modes.md) - CI/CD vs CoPilot modes
- [Telemetry](reference/telemetry.md) - Privacy-first, opt-in analytics
- [Feature Keys](reference/feature-keys.md) - Key normalization
- [Directory Structure](reference/directory-structure.md) - Project layout

### Examples

- [Dogfooding Example](examples/dogfooding-specfact-cli.md) - Main example
- [Quick Examples](examples/quick-examples.md) - Code snippets

### Technical

- [Code2Spec Analysis](technical/code2spec-analysis-logic.md) - AI-first approach
- [Testing Procedures](technical/testing.md) - Testing guidelines

---

## 🆘 Getting Help

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 [hello@noldai.com](mailto:hello@noldai.com)

---

**Happy building!** 🚀

---

Copyright © 2025-2026 Nold AI (Owner: Dominikus Nold)

**Trademarks**: All product names, logos, and brands mentioned in this documentation are the property of their respective owners. NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). See [TRADEMARKS.md](../TRADEMARKS.md) for more information.
