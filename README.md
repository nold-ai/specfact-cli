# SpecFact CLI

> **The "swiss knife" CLI that turns any codebase into a clear, safe, and shippable workflow.**
> Keep backlog, specs, tests, and code in sync so AI-assisted changes do not break production.
> Works for brand-new projects and long-lived codebases - even if you are new to coding.

**No API keys required. Works offline. Zero vendor lock-in.**

[![PyPI version](https://img.shields.io/pypi/v/specfact-cli.svg?color=22c55e)](https://pypi.org/project/specfact-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/specfact-cli.svg)](https://pypi.org/project/specfact-cli/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)
[![Status](https://img.shields.io/badge/status-beta-F59E0B.svg)](https://github.com/nold-ai/specfact-cli)

<div align="center">

**[specfact.com](https://specfact.com)** • **[specfact.io](https://specfact.io)** • **[specfact.dev](https://specfact.dev)** • **[Documentation](https://docs.specfact.io/)** • **[Support](mailto:hello@noldai.com)**

</div>

---

## Start Here (60 seconds)

### Install

```bash
# Zero-install (recommended)
uvx specfact-cli@latest

# Or install globally
pip install -U specfact-cli
```

### Bootstrap and IDE Setup

```bash
# Bootstrap module registry and local config (~/.specfact)
specfact init

# Configure IDE prompts/templates (interactive selector by default)
specfact init ide
specfact init ide --ide cursor
specfact init ide --ide vscode
```

### Run Your First Flow

```bash
# Analyze an existing codebase
specfact import from-code my-project --repo .

# Validate external code without modifying source
specfact validate sidecar init my-project /path/to/repo
specfact validate sidecar run my-project /path/to/repo
```

**AI IDE quick start**

```bash
# In your IDE chat (Cursor, VS Code, Copilot, etc.)
/specfact.01-import my-project --repo .
```

**Next steps**

- **[Getting Started](docs/getting-started/README.md)**
- **[AI IDE Workflow](docs/guides/ai-ide-workflow.md)**
- **[Command Chains](docs/guides/command-chains.md)**

---

## Proof and Expectations

- **Typical runtime**: 2-15 minutes depending on repo size and complexity.
- **Checkpointing**: Progress is saved during analysis so you can resume safely.
- **Performance**: Optimized for large codebases with cached parsing and file hashes.

---

## Why It Matters (Plain Language)

- **Clarity**: Turn messy code into clear specs your team can trust.
- **Safety**: Catch risky changes early with validation and contract checks.
- **Sync**: Keep backlog items, specs, tests, and code aligned end to end.
- **Adoption**: Simple CLI, no platform lock-in, works offline.

---

## Who It Is For

- **Vibe coders and new builders** who want to ship fast with guardrails and confidence.
- **Legacy professionals** who want AI speed without lowering standards.
- **DevOps and engineering leaders** who need evidence and repeatable workflows.

---

## How It Works (High Level)

1. **Analyze**: Read code and extract specs, gaps, and risks.
2. **Sync**: Connect specs, backlog items, and plans in one workflow.
3. **Validate**: Enforce contracts and block regressions before production.

---

## The Missing Link (Coder + DevOps Bridge)

Most tools help **either** coders **or** agile teams. SpecFact does both:

- **Backlog sync that is actually strong**: round-trip sync + refinement with GitHub, Azure DevOps, Jira, Linear.
- **Ceremony support teams can run**: standup, refinement, sprint planning, flow metrics (Scrum/Kanban/SAFe).
- **Policy + validation**: DoR/DoD/flow checks plus contract enforcement for production-grade stability.

**Try it now**

- **Coders**: [AI IDE Workflow](docs/guides/ai-ide-workflow.md)
- **Agile teams**: [Agile/Scrum Workflows](docs/guides/agile-scrum-workflows.md)

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

### Module Lifecycle Baseline

SpecFact now has a lifecycle-managed module system:

- `specfact init` is bootstrap-first: initializes local CLI state, discovers installed modules, and reports prompt status.
- `specfact init ide` handles IDE prompt/template sync and IDE settings updates.
- `specfact init --list-modules` shows effective enabled/disabled state.
- `specfact init --enable-module` / `--disable-module` support:
  - interactive selection in interactive terminals when no module id is provided
  - explicit ids in non-interactive mode (for automation)
  - dependency-aware safety checks with `--force` cascading enable/disable behavior
- Module manifests support dependency and core-version compatibility enforcement at registration time.

This lifecycle model is the baseline for future granular module updates and enhancements. Module installation from third-party or open-source community providers is planned, but not implemented yet.

Contract-first module architecture highlights:

- `ModuleIOContract` formalizes module IO operations (`import`, `export`, `sync`, `validate`) on `ProjectBundle`.
- Core-module isolation is enforced by static analysis (`core` never imports `specfact_cli.modules.*` directly).
- Registration tracks protocol operation coverage and schema compatibility metadata.

---

## Developer Note: Command Layout

- Primary command implementations live in `src/specfact_cli/modules/<module>/src/commands.py`.
- Legacy imports from `src/specfact_cli/commands/*.py` are compatibility shims and only guarantee `app` re-exports.
- Preferred imports for module code:
  - `from specfact_cli.modules.<module>.src.commands import app`
  - `from specfact_cli.modules.<module>.src.commands import <symbol>`
- Shim deprecation timeline:
  - Legacy shim usage is deprecated for non-`app` symbols now.
  - Shim removal is planned no earlier than `v0.30` (or the next major migration window).

---

## Developer Note: Command Layout

- Primary command implementations live in `src/specfact_cli/modules/<module>/src/commands.py`.
- Legacy imports from `src/specfact_cli/commands/*.py` are compatibility shims and only guarantee `app` re-exports.
- Preferred imports for module code:
  - `from specfact_cli.modules.<module>.src.commands import app`
  - `from specfact_cli.modules.<module>.src.commands import <symbol>`
- Shim deprecation timeline:
  - Legacy shim usage is deprecated for non-`app` symbols now.
  - Shim removal is planned no earlier than `v0.30` (or the next major migration window).

---

## Developer Note: Command Layout

- Primary command implementations live in `src/specfact_cli/modules/<module>/src/commands.py`.
- Legacy imports from `src/specfact_cli/commands/*.py` are compatibility shims and only guarantee `app` re-exports.
- Preferred imports for module code:
  - `from specfact_cli.modules.<module>.src.commands import app`
  - `from specfact_cli.modules.<module>.src.commands import <symbol>`
- Shim deprecation timeline:
  - Legacy shim usage is deprecated for non-`app` symbols now.
  - Shim removal is planned no earlier than `v0.30` (or the next major migration window).

---

## Where SpecFact Fits

SpecFact complements your stack rather than replacing it.

- **Spec-Kit/OpenSpec** for authoring and change tracking
- **Backlog tools** for planning and delivery
- **CI/CD** for enforcement and regression prevention

**SpecFact connects them** with adapters, policy checks, and deterministic validation.

**Integrations snapshot**: GitHub, Azure DevOps, Jira, Linear, Spec-Kit, OpenSpec, Specmatic.

- **[Integrations Overview](docs/guides/integrations-overview.md)**
- **[DevOps Adapter Integration](docs/guides/devops-adapter-integration.md)**

---

## Recommended Paths

- **I want a quick win**: [Getting Started](docs/getting-started/README.md)
- **I use an AI IDE**: [AI IDE Workflow](docs/guides/ai-ide-workflow.md)
- **We have a team backlog**: [Agile/Scrum Workflows](docs/guides/agile-scrum-workflows.md)
- **We have a long-lived codebase**: [Working With Existing Code](docs/guides/brownfield-engineer.md)

---

## Documentation Map

- **[Documentation Index](docs/README.md)**
- **[Command Reference](docs/reference/commands.md)**
- **[Backlog Refinement](docs/guides/backlog-refinement.md)**
- **[Sidecar Validation](docs/guides/sidecar-validation.md)**
- **[OpenSpec Journey](docs/guides/openspec-journey.md)**

---

## Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
git clone https://github.com/nold-ai/specfact-cli.git
cd specfact-cli
pip install -e ".[dev]"
hatch run contract-test-full
```

---

## License

**Apache License 2.0** - Open source and enterprise-friendly.

[Full license](LICENSE.md)

---

## Support

- **GitHub Discussions**: https://github.com/nold-ai/specfact-cli/discussions
- **GitHub Issues**: https://github.com/nold-ai/specfact-cli/issues
- **Email**: hello@noldai.com
- **Debug logs**: Run with `--debug` and check `~/.specfact/logs/specfact-debug.log`.

---

<div align="center">

**Built by [NOLD AI](https://noldai.com)**

Copyright © 2025-2026 Nold AI (Owner: Dominikus Nold)

**Trademarks**: NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). All other trademarks mentioned in this project are the property of their respective owners. See [TRADEMARKS.md](TRADEMARKS.md) for more information.

</div>
