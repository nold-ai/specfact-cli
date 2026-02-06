# SpecFact CLI Documentation

> **The "swiss knife" CLI that turns any codebase into a clear, safe, and shippable workflow.**  
> Keep backlog, specs, tests, and code in sync so AI-assisted changes don’t break production.  
> Works for brand-new projects and long-lived codebases — even if you’re new to coding.

**Built for both worlds**

- **Vibe coders and new builders** who want to ship fast with guardrails and confidence.
- **Legacy professionals** who want AI speed without lowering standards, plus end-to-end spec -> backlog -> code sync.

---

## The Missing Link (Coder + DevOps Bridge)

Most tools help **either** coders **or** agile teams. SpecFact does both:

- **Backlog sync that is actually strong**: round-trip sync + refinement for GitHub, Azure DevOps, Jira, Linear.
- **Ceremony support teams can run**: standup, refinement, sprint planning, flow metrics (Scrum/Kanban/SAFe).
- **Policy + validation**: DoR/DoD/flow checks plus contract enforcement for production-grade safety.

**Try it now**

- **Coders**: [AI IDE Workflow](guides/ai-ide-workflow.md)
- **Agile teams**: [Agile/Scrum Workflows](guides/agile-scrum-workflows.md)

---

## Start Here (Pick Your Path)

**Pick your path**

- **Working with existing code**: [Getting Started](getting-started/README.md) and [Legacy Engineer Guide](guides/brownfield-engineer.md)
- **Agile team workflows**: [Agile/Scrum Workflows](guides/agile-scrum-workflows.md) and [Backlog Refinement](guides/backlog-refinement.md)
- **AI IDE workflow**: [AI IDE Workflow Guide](guides/ai-ide-workflow.md)
- **Integrations**: [Integrations Overview](guides/integrations-overview.md)

---

## Modules and Capabilities

**Core modules**

- **Analyze**: Extract specs and plans from existing code.
- **Validate**: Enforce contracts, run reproducible checks, and block regressions.
- **Report**: CI/CD summaries and evidence outputs.

**Agile DevOps modules**

- **Backlog**: Refinement, dependency analysis, sprint summaries, risk rollups.
- **Ceremony**: Standup, refinement, and planning entry points.
- **Policy**: DoR, DoD, flow, PI readiness checks.
- **Patch**: Preview, apply, and write changes safely.

**Adapters and bridges**

- **Specs**: Spec-Kit and OpenSpec
- **Backlogs**: GitHub Issues, Azure DevOps, Jira, Linear
- **Contracts**: Specmatic, OpenAPI

## Module Lifecycle System

SpecFact CLI uses a lifecycle-managed module system:

- `specfact init` bootstraps local state and manages module enable/disable lifecycle.
- `specfact init ide` handles IDE prompt/template installation and updates.
- `specfact init --list-modules` shows current enabled/disabled state.
- `--enable-module` and `--disable-module` support interactive selection in interactive terminals and explicit ids in non-interactive mode.
- Dependency and compatibility guards prevent invalid module states; `--force` enables dependency-aware cascades.

This is the baseline for future granular module updates and enhancements. Third-party/community module installation is planned, but not available yet.

---

## Documentation Sections

### Getting Started

- [Installation](getting-started/installation.md)
- [First Steps](getting-started/first-steps.md)
- [Enhanced Analysis Dependencies](installation/enhanced-analysis-dependencies.md)

### Guides

- [Agile/Scrum Workflows](guides/agile-scrum-workflows.md)
- [Backlog Refinement](guides/backlog-refinement.md)
- [DevOps Adapter Integration](guides/devops-adapter-integration.md)
- [AI IDE Workflow](guides/ai-ide-workflow.md)
- [Sidecar Validation](guides/sidecar-validation.md)
- [Use Cases](guides/use-cases.md)

### Integrations

- [Spec-Kit Journey](guides/speckit-journey.md)
- [OpenSpec Journey](guides/openspec-journey.md)
- [Specmatic Integration](guides/specmatic-integration.md)
- [Custom Field Mapping](guides/custom-field-mapping.md)

### Reference

- [Command Reference](reference/commands.md)
- [Architecture](reference/architecture.md)
- [Debug Logging](reference/debug-logging.md)

### Contributing

- [Development Setup](getting-started/installation.md#development-setup)
- [Testing Procedures](technical/testing.md)
- [Technical Deep Dives](technical/README.md)

---

## Helpful Shortcuts

- **Command Chains**: [guides/command-chains.md](guides/command-chains.md)
- **Common Tasks**: [guides/common-tasks.md](guides/common-tasks.md)
- **Online Docs**: https://docs.specfact.io/

---

## Need Help?

- **GitHub Discussions**: https://github.com/nold-ai/specfact-cli/discussions
- **GitHub Issues**: https://github.com/nold-ai/specfact-cli/issues
- **Email**: hello@noldai.com
