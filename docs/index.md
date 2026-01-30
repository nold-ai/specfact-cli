---
layout: default
title: SpecFact CLI Documentation
description: Brownfield-first CLI for reverse engineering legacy Python code into specs with runtime contract enforcement
permalink: /
---

# SpecFact CLI Documentation

**Brownfield-first CLI: Reverse engineer legacy Python → specs → enforced contracts**

SpecFact CLI helps you modernize legacy codebases by automatically extracting specifications from existing code and enforcing them at runtime to prevent regressions.

---

## 🚀 Quick Start

### New to SpecFact CLI?

**Primary Use Case**: Modernizing legacy Python codebases

1. **[Installation](getting-started/installation.md)** - Get started in 60 seconds
2. **[First Steps](getting-started/first-steps.md)** - Run your first command
3. **[Tutorial: Backlog Refine with AI IDE](getting-started/tutorial-backlog-refine-ai-ide.md)** - Integrate backlog refinement with your AI IDE (agile DevOps)
4. **[Modernizing Legacy Code](guides/brownfield-engineer.md)** ⭐ **PRIMARY** - Brownfield-first guide
5. **[The Brownfield Journey](guides/brownfield-journey.md)** ⭐ - Complete modernization workflow

### Using GitHub Spec-Kit?

**Secondary Use Case**: Add automated enforcement to your Spec-Kit projects

- **[From Spec-Kit to SpecFact](guides/speckit-journey.md)** - Add enforcement to Spec-Kit projects
- **[Spec-Kit Comparison](guides/speckit-comparison.md)** - Understand when to use each tool

## 📚 Documentation

### Guides

- **[Command Chains](guides/command-chains.md)** ⭐ **NEW** - Complete workflows from start to finish
- **[Agile/Scrum Workflows](guides/agile-scrum-workflows.md)** - Persona-based collaboration for teams
- **[DevOps Backlog Integration](guides/devops-adapter-integration.md)** 🆕 **NEW FEATURE** - Integrate SpecFact into agile DevOps workflows with bidirectional backlog sync
- **[Backlog Refinement](guides/backlog-refinement.md)** 🆕 **NEW FEATURE** - AI-assisted template-driven backlog refinement for standardizing work items
- **[Sidecar Validation](guides/sidecar-validation.md)** 🆕 - Validate external codebases without modifying source
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

# Cross-adapter sync: GitHub → ADO (lossless round-trip)
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
- **[Operational Modes](reference/modes.md)** - CI/CD vs CoPilot modes
- **[Directory Structure](reference/directory-structure.md)** - Project structure

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

**License**: See [LICENSE.md](../LICENSE.md) for licensing information.
