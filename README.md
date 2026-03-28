# SpecFact CLI

> **The "swiss knife" CLI that turns any codebase into a clear, safe, and shippable workflow.**
> Keep backlog, specs, tests, and code in sync so changes made by people or AI copilots do not break production.
> Works for brand-new projects and long-lived codebases - even if you are new to coding.

**No API keys required. Works offline. Zero vendor lock-in.**

SpecFact CLI does **not** include built-in AI. It is a deterministic local CLI
that can be paired with IDE slash-command prompts so your chosen AI copilot can
invoke SpecFact as part of a command chain.

[![PyPI version](https://img.shields.io/pypi/v/specfact-cli.svg?color=22c55e)](https://pypi.org/project/specfact-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/specfact-cli.svg)](https://pypi.org/project/specfact-cli/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-F59E0B.svg)](https://github.com/nold-ai/specfact-cli)

<div align="center">

**[specfact.com](https://specfact.com)** • **[specfact.io](https://specfact.io)** • **[specfact.dev](https://specfact.dev)** • **[Documentation](https://docs.specfact.io/)** • **[Support](mailto:hello@noldai.com)**

</div>

---

## Documentation Topology

`docs.specfact.io` is the canonical docs entry point for SpecFact.

- Core CLI/runtime/platform documentation remains owned by `specfact-cli`.
- Module-specific deep docs are canonically owned by `specfact-cli-modules`.
- The live modules docs site is currently published at `https://modules.specfact.io/`.

Use this repository's docs for the overall SpecFact workflow, CLI runtime lifecycle, module registry, trust model, and command-group topology.
Use the modules docs site for bundle-specific deep dives, adapter details, workflow tutorials, and module-authoring guidance.
In short, module-specific deep docs are canonically owned by `specfact-cli-modules`.

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
# First run: install official bundles
specfact init --profile solo-developer

# Alternative bundle selection
specfact init --install backlog,codebase
specfact init --install all

# IDE prompt/template setup
specfact init ide
specfact init ide --ide cursor
specfact init ide --ide vscode
```

`specfact init ide` discovers prompt resources from installed workflow modules and exports them to your IDE. If module prompt payloads are not installed yet, the CLI uses packaged fallback resources.

### Run Your First Flow

```bash
# Analyze an existing codebase
specfact code import my-project --repo .

# Snapshot current project state
specfact project snapshot --bundle my-project

# Validate external code without modifying source
specfact code validate sidecar init my-project /path/to/repo
specfact code validate sidecar run my-project /path/to/repo
```

### Migration Note (Flat Commands Removed)

As of `0.40.0`, flat root commands are removed. Use grouped commands:

- `specfact validate ...` -> `specfact code validate ...`
- `specfact plan ...` -> removed; use `specfact project devops-flow` or `specfact project snapshot`
- `specfact policy ...` -> removed; use `specfact backlog verify-readiness`

### Backlog Bridge (60 seconds)

SpecFact's USP is closing the drift gap between **backlog -> specs -> code**.
These commands require the backlog bundle to be installed first, for example via
`specfact init --profile backlog-team` or `specfact init --install backlog`.

```bash
# 1) Initialize backlog config + field mapping
specfact backlog init-config --force
specfact backlog map-fields --provider ado --ado-org <org> --ado-project "<project>"

# 2) Run ceremony workflows on real backlog scope
specfact backlog ceremony standup ado --ado-org <org> --ado-project "<project>" --state any --assignee any --limit 5
specfact backlog ceremony refinement ado --ado-org <org> --ado-project "<project>" --id <work-item-id> --preview

# 3) Keep backlog + spec intent aligned (avoid silent drift)
specfact backlog verify-readiness --bundle <bundle-name>
```

Compatibility note: `specfact backlog daily ...` and `specfact backlog refine ...` still exist, but the preferred entrypoints are `backlog ceremony standup` and `backlog ceremony refinement`.

For GitHub, replace adapter/org/project with:
`specfact backlog ceremony standup github --repo-owner <owner> --repo-name <repo> --state any --assignee any --limit 5`

**AI IDE quick start**

```bash
# In your IDE chat (Cursor, VS Code, Copilot, etc.)
/specfact.01-import my-project --repo .
```

**Next steps**

- **[Core CLI docs](docs/index.md)**
- **[Reference: command topology](docs/reference/commands.md)**
- **[Canonical modules docs site](https://modules.specfact.io/)**

---

## Who It Is For

- **Vibe coders and new builders** who want to ship fast with guardrails and confidence.
- **Legacy professionals** who want AI speed without lowering standards.
- **DevOps and engineering leaders** who need evidence and repeatable workflows.

---

## The Missing Link (Coder + DevOps Bridge)

Most tools help **either** coders **or** agile teams. SpecFact does both:

- **Backlog sync that is actually strong**: round-trip sync + refinement with GitHub, Azure DevOps, Jira, Linear.
- **Ceremony support teams can run**: standup, refinement, sprint planning, flow metrics (Scrum/Kanban/SAFe).
- **Policy + validation**: DoR/DoD/flow checks plus contract enforcement for production-grade stability.

Recommended command entrypoints:
- `specfact backlog ceremony standup ...`
- `specfact backlog ceremony refinement ...`
- `specfact backlog verify-readiness --bundle <bundle-name>`
- `specfact backlog analyze-deps --bundle <bundle-name>`

What the backlog readiness and ceremony commands do in practice:
- Turns team agreements (DoR, DoD, flow checks) into executable checks against your real backlog data.
- Shows exactly what is missing per item (for example missing acceptance criteria or definition of done).
- Runs structured ceremony workflows directly from the CLI.

Start with:
- `specfact backlog ceremony standup --help`
- `specfact backlog verify-readiness --bundle <bundle-name>`
- `specfact backlog refine --help`

---

## Core CLI Features

The `specfact-cli` repository owns the platform-level features that every workflow bundle depends on:

- `specfact init` for first-run bootstrap and IDE setup.
- `specfact module` for install/list/show/search/enable/disable/uninstall/upgrade lifecycle flows.
- `specfact upgrade` for CLI upgrades.
- Runtime contracts, registry bootstrapping, trust checks, logging, and shared orchestration.
- The grouped command surface that mounts installed bundle families under `project`, `backlog`, `code`, `spec`, and `govern`.

## Official Modules Integration

Official workflow behavior now ships from `nold-ai/specfact-cli-modules`.
The core CLI discovers those bundle packages, mounts their command groups, and enforces compatibility, trust, and lifecycle rules.

Installed official bundles expose the current grouped surfaces:

- `specfact project ...`
- `specfact backlog ...`
- `specfact code ...`
- `specfact spec ...`
- `specfact govern ...`

Install examples:

```bash
specfact module install nold-ai/specfact-project
specfact module install nold-ai/specfact-backlog
specfact module install nold-ai/specfact-codebase
specfact module install nold-ai/specfact-spec
specfact module install nold-ai/specfact-govern
```

If startup warns that bundled modules are missing or outdated, run:

```bash
specfact module init --scope project
specfact module init
```

Use this repo's docs for the current CLI/runtime release branch and the overall process of how official modules plug into the core platform.
Use `https://modules.specfact.io/` for the in-depth backlog, project, spec, govern, adapter, and module-authoring guides.

---

## How It Works (High Level)

1. **Bootstrap**: install the CLI and initialize the official bundles you need.
2. **Analyze or sync**: import code, connect backlog systems, or sync external artifacts into project bundles.
3. **Validate**: run spec, governance, and sidecar validation flows before implementation or release.
4. **Iterate safely**: use module-provided workflows while the core runtime keeps command mounting, trust, and lifecycle consistent.

## Where SpecFact Fits

SpecFact complements your stack rather than replacing it.

- **Spec-Kit/OpenSpec** for authoring and change tracking
- **Backlog tools** for planning and delivery
- **CI/CD** for enforcement and regression prevention
