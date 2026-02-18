---
layout: default
title: SpecFact CLI Documentation
description: The swiss knife CLI that keeps backlog, specs, tests, and code in sync. Works for new and long-lived projects.
permalink: /
---

# SpecFact CLI Documentation

**The "swiss knife" CLI that turns any codebase into a clear, safe, and shippable workflow**  
Keep backlog, specs, tests, and code in sync so AI-assisted changes don’t break production.

**Built for both worlds**

- **Vibe coders and new builders** who want to ship fast with guardrails and confidence.
- **Legacy professionals** who want AI speed without lowering standards, plus end-to-end spec -> backlog -> code sync.

**Core promise**: Works for new and long-lived projects with contract enforcement and validation.

---

## The Missing Link (Coder + DevOps Bridge)

Most tools help **either** coders **or** agile teams. SpecFact does both:

- **Backlog sync that is actually strong**: round-trip sync + refinement with GitHub, Azure DevOps, Jira, Linear.
- **Ceremony support teams can run**: standup, refinement, sprint planning, flow metrics (Scrum/Kanban/SAFe).
- **Policy + validation**: DoR/DoD/flow checks plus contract enforcement for production-grade stability.

Recommended command entrypoints:
- `specfact backlog ceremony standup ...`
- `specfact backlog ceremony refinement ...`

**Try it now**

- **Coders**: [AI IDE Workflow](guides/ai-ide-workflow.md)
- **Agile teams**: [Agile/Scrum Workflows](guides/agile-scrum-workflows.md)

---

## 🚀 Quick Start

### New to SpecFact CLI?

**Primary Use Case**: Understanding and improving existing codebases (and new projects)

1. **[Installation](getting-started/installation.md)** - Get started in 60 seconds
2. **[First Steps](getting-started/first-steps.md)** - Run your first command
3. **[Tutorial: Backlog Refine with AI IDE](getting-started/tutorial-backlog-refine-ai-ide.md)** - Integrate backlog refinement with your AI IDE (agile DevOps)
4. **[Tutorial: Daily Standup and Sprint Review](getting-started/tutorial-daily-standup-sprint-review.md)** - Daily standup view, post comments, and Copilot export (GitHub/ADO)
5. **[Working With Existing Code](guides/brownfield-engineer.md)** ⭐ **PRIMARY** - Legacy-first guide
6. **[The Existing Code Journey](guides/brownfield-journey.md)** ⭐ - Complete modernization workflow

### Using GitHub Spec-Kit or OpenSpec?

**Secondary Use Case**: Add automated enforcement to your Spec-Kit or OpenSpec projects

- **[From Spec-Kit to SpecFact](guides/speckit-journey.md)** - Add enforcement to Spec-Kit projects
- **[Spec-Kit Comparison](guides/speckit-comparison.md)** - Understand when to use each tool
- **[From OpenSpec to SpecFact](guides/openspec-journey.md)** - Add enforcement to OpenSpec projects

## Module System Foundation

SpecFact now uses a module-first architecture to reduce hard-wired command coupling.

- Core runtime handles lifecycle, registry, contracts, and orchestration.
- Feature behavior lives in module-local command implementations.
- Legacy command-path shims remain for compatibility during migration windows.

Implementation layout:

- Primary module commands: `src/specfact_cli/modules/<module>/src/commands.py`
- Legacy compatibility shims: `src/specfact_cli/commands/*.py` (only `app` re-export is guaranteed)

Why this matters:

- Modules can evolve at different speeds without repeatedly changing CLI core wiring.
- Interfaces and contracts keep feature development isolated and safer to iterate.
- Pending OpenSpec-driven module changes can land incrementally with lower migration risk.

**Module security and extensions:**

- **[Using Module Security and Extensions](guides/using-module-security-and-extensions.md)** - How to use verified modules (arch-06) and schema extensions (arch-07) from the CLI and as a module author
- **[Extending ProjectBundle](guides/extending-projectbundle.md)** - Declare and use namespaced extension fields on Feature/ProjectBundle
- **[Module Security](reference/module-security.md)** - Publisher, integrity (checksum/signature), and versioned dependencies

## 📚 Documentation

### Guides

- **[Command Chains](guides/command-chains.md)** ⭐ **NEW** - Complete workflows from start to finish
- **[Agile/Scrum Workflows](guides/agile-scrum-workflows.md)** - Persona-based collaboration for teams
- **[Policy Engine Commands](guides/policy-engine-commands.md)** - Scaffold policy config templates and run `policy init|validate|suggest`
- **[DevOps Backlog Integration](guides/devops-adapter-integration.md)** 🆕 **NEW FEATURE** - Integrate SpecFact into agile DevOps workflows with bidirectional backlog sync
- **[Backlog Refinement](guides/backlog-refinement.md)** 🆕 **NEW FEATURE** - AI-assisted template-driven backlog refinement for standardizing work items
- **[Backlog Dependency Analysis](guides/backlog-dependency-analysis.md)** - Analyze critical path, cycles, orphans, and dependency impact from backlog graph data
- **[Backlog Delta Commands](guides/backlog-delta-commands.md)** - Track backlog graph changes under `specfact backlog delta`
- **[Project DevOps Flow](guides/project-devops-flow.md)** - Run plan/develop/review/release/monitor stage actions from one command surface
- **[Extending ProjectBundle](guides/extending-projectbundle.md)** - Add namespaced custom fields to Feature/ProjectBundle (arch-07)
- **[Using Module Security and Extensions](guides/using-module-security-and-extensions.md)** - Use arch-06 (module security) and arch-07 (schema extensions) from CLI and as a module author
- **[Sidecar Validation](guides/sidecar-validation.md)** 🆕 - Validate external codebases without modifying source
- **[Thorough Codebase Validation](reference/thorough-codebase-validation.md)** - Quick check, contract-full, sidecar, dogfooding
- **[UX Features](guides/ux-features.md)** - Progressive disclosure, context detection, intelligent suggestions
- **[Use Cases](guides/use-cases.md)** - Real-world scenarios and workflows
- **[IDE Integration](guides/ide-integration.md)** - Set up slash commands in your IDE
- **[CoPilot Mode](guides/copilot-mode.md)** - Using `--mode copilot` on CLI
- **[Template Customization](guides/template-customization.md)** 🆕 **NEW** - Create and customize backlog templates for your team
- **[Troubleshooting](guides/troubleshooting.md)** - Common issues and solutions
- **[Competitive Analysis](guides/competitive-analysis.md)** - How SpecFact compares

### DevOps & Backlog Sync 🚀

**For Developers & DevOps Teams**: Keep your backlogs in sync with feature branches, code changes, and validations.

- **[DevOps Integration Guide](guides/devops-adapter-integration.md)** ⭐ - Complete guide for GitHub Issues and Azure DevOps integration
  - **Cross-Adapter Sync**: Lossless round-trip migration between backlog tools (GitHub ↔ ADO)
  - **Bidirectional Sync**: Import backlog items as proposals, export proposals as backlog items
  - **Code Change Tracking**: Automatically detect commits and add progress comments
  - **Status Synchronization**: Keep OpenSpec and backlog status in sync

- **[Backlog Refinement Guide](guides/backlog-refinement.md)** 🆕 **NEW** - AI-assisted template-driven refinement for standardizing work items
  - **[Tutorial: Backlog Refine with AI IDE](getting-started/tutorial-backlog-refine-ai-ide.md)** - End-to-end tutorial for agile DevOps teams (slash prompt, DoR, split stories, underspec/overspec)
  - **[Tutorial: Daily Standup and Sprint Review](getting-started/tutorial-daily-standup-sprint-review.md)** - Daily standup view, post yesterday/today/blockers, interactive mode, Copilot export (GitHub/ADO)
  - **Template Detection**: Automatically detect which template matches a backlog item with priority-based resolution
  - **AI-Assisted Refinement**: Generate prompts for IDE AI copilots to refine unstructured input
  - **Confidence Scoring**: Validate refined content and provide confidence scores
  - **Lossless Preservation**: Preserve original backlog data for round-trip synchronization
  - **Agile Filtering** 🆕: Filter by sprint, release, iteration, labels, state, assignee for agile workflows
  - **Persona/Framework Support** 🆕: Filter templates by persona (product-owner, architect, developer) and framework (scrum, safe, kanban)
  - **Definition of Ready (DoR)** 🆕: Validate sprint readiness with repo-level DoR configuration
  - **Preview/Write Safety** 🆕: Preview mode by default, explicit `--write` flag for writeback
  - **OpenSpec Integration** 🆕: Add OpenSpec reference comments with `--openspec-comment` flag (preserves original body)
  - **Template Customization** 🆕: Create custom templates for your team - see [Template Customization Guide](guides/template-customization.md)

- **[Authentication](reference/authentication.md)** - Device code auth for GitHub and Azure DevOps
- **[GitHub Adapter](adapters/github.md)** - GitHub Issues adapter reference
- **[Azure DevOps Adapter](adapters/azuredevops.md)** - Azure DevOps work items adapter reference
- **[Backlog Adapter Patterns](adapters/backlog-adapter-patterns.md)** - Patterns for implementing backlog adapters

**Quick Start for DevOps Teams:**

```bash
# Export OpenSpec proposals to GitHub Issues
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org --repo-name your-repo

# Export to Azure DevOps work items
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org --ado-project your-project

# Cross-adapter sync: GitHub -> ADO (lossless round-trip)
specfact sync bridge --adapter github --mode bidirectional \
  --bundle main --backlog-ids 123
specfact sync bridge --adapter ado --mode export-only \
  --bundle main --change-ids <change-id>
```

### Reference

- **[Reference Documentation](reference/)** - Complete technical reference index
- **[Command Reference](reference/commands.md)** - Complete command documentation
- **[Authentication](reference/authentication.md)** - Device code auth flows and token storage
- **[Architecture](reference/architecture.md)** - Technical design and principles
- **[Bridge Registry](reference/bridge-registry.md)** 🆕 - Module-declared bridge converters and lifecycle registration
- **[Operational Modes](reference/modes.md)** - CI/CD vs CoPilot modes
- **[Directory Structure](reference/directory-structure.md)** - Project structure

### Module Protocol Reporting

- Lifecycle protocol compliance reporting now classifies modules using the effective runtime interface and
  emits a single aggregate summary line for full/partial/legacy status.

### Examples

- **[Brownfield Examples](examples/)** - Real-world modernization examples
- **[Quick Examples](examples/quick-examples.md)** - Code snippets and patterns

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

See [CONTRIBUTING.md](https://github.com/nold-ai/specfact-cli/blob/main/CONTRIBUTING.md) for guidelines.

---

**Happy building!** 🚀

---

Copyright © 2025 Nold AI (Owner: Dominikus Nold)

**Trademarks**: All product names, logos, and brands mentioned in this documentation are the property of their respective owners. NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). See [TRADEMARKS.md](../TRADEMARKS.md) for more information.

**License**: See [LICENSE](../LICENSE) for licensing information.
