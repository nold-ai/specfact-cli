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

### **Love GitHub Spec-Kit? SpecFact Adds What's Missing**

**Use both together:** Keep using Spec-Kit for new features, add SpecFact for legacy code modernization.

**If you've tried GitHub Spec-Kit**, you know it's great for documenting new features. SpecFact adds what's missing for legacy code modernization:

- ✅ **Runtime contract enforcement** → Spec-Kit generates docs; SpecFact prevents regressions with executable contracts
- ✅ **Brownfield-first** → Spec-Kit excels at new features; SpecFact understands existing code
- ✅ **Formal verification** → Spec-Kit uses LLM suggestions; SpecFact uses mathematical proof (CrossHair)
- ✅ **Team collaboration** → Spec-Kit is single-user focused; SpecFact supports persona-based workflows for agile teams
- ✅ **GitHub Actions integration** → Works seamlessly with your existing GitHub workflows

**Perfect together:**

- ✅ **Spec-Kit** for new features → Fast spec generation with Copilot
- ✅ **SpecFact** for legacy code → Runtime enforcement prevents regressions
- ✅ **Bidirectional sync** → Keep both tools in sync automatically
- ✅ **Team workflows** → SpecFact adds persona-based collaboration for agile/scrum teams

**Bottom line:** Use Spec-Kit for documenting new features. Use SpecFact for modernizing legacy code safely and enabling team collaboration. Use both together for the best of both worlds.

👉 **[See detailed comparison](guides/speckit-comparison.md)** | **[Journey from Spec-Kit](guides/speckit-journey.md)**

---

## 🎯 Find Your Path

### New to SpecFact?

**Primary Goal**: Modernize legacy Python codebases in < 5 minutes

1. **[Getting Started](getting-started/README.md)** - Install and run your first command
2. **[Modernizing Legacy Code?](guides/brownfield-engineer.md)** ⭐ **PRIMARY** - Brownfield-first guide
3. **[The Brownfield Journey](guides/brownfield-journey.md)** ⭐ - Complete modernization workflow
4. **[See It In Action](examples/dogfooding-specfact-cli.md)** - Real example (< 10 seconds)
5. **[Use Cases](guides/use-cases.md)** - Common scenarios

**Time**: < 10 minutes | **Result**: Running your first brownfield analysis

---

### Working with an Agile/Scrum Team?

**Primary Goal**: Enable team collaboration with role-based workflows

1. **[Agile/Scrum Workflows](guides/agile-scrum-workflows.md)** ⭐ **START HERE** - Persona-based team collaboration
2. **[Command Reference - Project Commands](reference/commands.md#project---project-bundle-management)** - `project export` and `project import` commands
3. **[Persona Workflows](guides/agile-scrum-workflows.md#persona-based-workflows)** - How Product Owners, Architects, and Developers work together
4. **[Definition of Ready](guides/agile-scrum-workflows.md#definition-of-ready-dor)** - DoR validation and sprint planning

**Time**: 15-30 minutes | **Result**: Understanding how your team can collaborate with SpecFact

---

### Love GitHub Spec-Kit?

**Why SpecFact?** Keep using Spec-Kit for new features, add SpecFact for legacy code modernization.

**Use both together:**

- ✅ **Spec-Kit** for new features → Fast spec generation with Copilot
- ✅ **SpecFact** for legacy code → Runtime enforcement prevents regressions
- ✅ **Bidirectional sync** → Keep both tools in sync automatically
- ✅ **GitHub Actions** → SpecFact integrates with your existing GitHub workflows

1. **[How SpecFact Compares to Spec-Kit](guides/speckit-comparison.md)** ⭐ **START HERE** - See what SpecFact adds
2. **[The Journey: From Spec-Kit to SpecFact](guides/speckit-journey.md)** - Add enforcement to Spec-Kit projects
3. **[Migration Use Case](guides/use-cases.md#use-case-2-github-spec-kit-migration)** - Step-by-step
4. **[Bidirectional Sync](guides/use-cases.md#use-case-2-github-spec-kit-migration)** - Keep both tools in sync

**Time**: 15-30 minutes | **Result**: Understand how SpecFact complements Spec-Kit for legacy code modernization

---

### Using SpecFact Daily?

**Goal**: Use SpecFact effectively in your workflow

1. **[Command Reference](reference/commands.md)** - All commands with examples
2. **[Use Cases](guides/use-cases.md)** - Real-world scenarios
3. **[IDE Integration](guides/ide-integration.md)** - Set up slash commands
4. **[CoPilot Mode](guides/copilot-mode.md)** - Enhanced prompts

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

#### Secondary Use Case: Spec-Kit Integration

- [Spec-Kit Journey](guides/speckit-journey.md) - Add enforcement to Spec-Kit projects
- [Spec-Kit Comparison](guides/speckit-comparison.md) - Understand when to use each tool

#### Team Collaboration & Agile/Scrum

- [Agile/Scrum Workflows](guides/agile-scrum-workflows.md) ⭐ **NEW** - Persona-based team collaboration with Product Owners, Architects, and Developers
- [Persona Workflows](guides/agile-scrum-workflows.md#persona-based-workflows) - Role-based workflows for agile teams
- [Definition of Ready](guides/agile-scrum-workflows.md#definition-of-ready-dor) - DoR validation and sprint planning
- [Dependency Management](guides/agile-scrum-workflows.md#dependency-management) - Track story and feature dependencies

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

Copyright © 2025 Nold AI (Owner: Dominikus Nold)

**Trademarks**: All product names, logos, and brands mentioned in this documentation are the property of their respective owners. NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). See [TRADEMARKS.md](../TRADEMARKS.md) for more information.
