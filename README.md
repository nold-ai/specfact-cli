# SpecFact CLI

> **SpecFact is the validation and alignment layer for software delivery.**
> It adds the missing validation layer that keeps backlog intent, specifications, tests, and code
> from drifting apart across AI-assisted coding, brownfield systems, and governed delivery.
> Use it to move fast without losing rigor.

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

## What is SpecFact?

SpecFact is the validation and alignment layer for software delivery.

It is a local CLI that helps you keep the intent behind a change aligned from
backlog or idea through specifications, implementation, and checks. The “Swiss-knife CLI” metaphor
fits because SpecFact gives you a set of focused tools for specific delivery problems, not a vague
bag of features.

In practice, SpecFact helps you:
- add guardrails to AI-assisted and fast-moving greenfield work
- reverse-engineer large brownfield codebases into trustworthy structured understanding
- reduce the “I wanted X but got Y” drift between backlog, spec, and implementation
- move from local rigor toward team and enterprise policy enforcement

## Why does it exist?

Modern delivery drifts in predictable ways:
- AI-generated quick wins often lack the validation layer needed for mid- and long-term reliability
- brownfield systems often have missing or drifted specs, so teams need to reverse-engineer reality
- backlog intent gets reinterpreted into something else before it reaches code
- teams working with different skill levels, opinions, and AI IDE setups need consistent review and
  policy enforcement

SpecFact exists to reduce that drift. It helps teams understand what is really there, express what
should happen more accurately, and validate that the result still matches the original intent.

## Why should I use it?

Use SpecFact if you want one of these outcomes:
- ship AI-assisted changes faster without accepting fragile “looks fine to me” quality
- understand a legacy or unfamiliar codebase before changing it
- hand brownfield insight into OpenSpec, Spec-Kit, or other spec-first workflows
- keep backlog expectations, specifications, and implementation from silently diverging
- enforce shared rules consistently across developers and CI/CD

## What do I get?

With SpecFact, you get:
- a deterministic local CLI instead of another opaque SaaS dependency
- a validation layer around fast-moving implementation work
- codebase analysis and sidecar flows for brownfield understanding
- stronger backlog/spec/code alignment for real delivery workflows
- a path from individual rigor to organization-level policy enforcement

## How do I get started?

### Start Here (about 2 minutes): scored code review — no `pip install`

**Point SpecFact at your code.** From a **git repository** (any branch), run two commands:

```bash
uvx specfact-cli init --profile solo-developer
uvx specfact-cli code review run --path . --scope full
```

You should see a **Verdict** (PASS/FAIL), a **Score**, and categorized **findings** — the fastest way to see SpecFact on real code before you dive into backlog, specs, or CI.

- **Command 1** installs the `solo-developer` bundles (including `specfact-codebase` and `specfact-code-review`) into your user module store so `code review` and related commands are available on the next invocation.
- **Command 2** runs the clean-code review on the repo at `.`. Use **`--scope full`** on the first run so review does not depend on having local git changes.

**Already installed the CLI?** Use the same flow with `specfact` instead of `uvx specfact-cli`:

```bash
specfact init --profile solo-developer
specfact code review run --path . --scope full
```

**Read the canonical walkthrough:** **[Documentation — Quickstart](https://docs.specfact.io/getting-started/quickstart/)** · **[Installation](https://docs.specfact.io/getting-started/installation/)** (uvx-first, then persistent install).

### Install (persistent CLI for daily use)

```bash
pip install -U specfact-cli
```

You can still use **`uvx specfact-cli@latest ...`** anytime without installing; it always fetches the latest published CLI.

### After the wow path: deeper workflows

When you want analysis, snapshots, or sidecar validation on top of the review layer:

```bash
# Analyze a codebase you care about
specfact code import my-project --repo .

# Snapshot the project state for follow-up workflows
specfact project snapshot --bundle my-project

# Validate external code without modifying the target repo
specfact code validate sidecar init my-project /path/to/repo
specfact code validate sidecar run my-project /path/to/repo
```

### AI IDE setup

```bash
specfact init ide
specfact init ide --ide cursor
specfact init ide --ide vscode
```

`specfact init ide` discovers prompt resources from installed workflow modules and exports them to
your IDE. If module prompt payloads are not installed yet, the CLI uses packaged fallback resources.

## Choose Your Path

### Greenfield and AI-assisted delivery

Use SpecFact as the validation layer around fast-moving implementation work.

Start with:
- `uvx specfact-cli init --profile solo-developer` then `uvx specfact-cli code review run --path . --scope full` (see **Start Here** above)
- `specfact code validate sidecar init <bundle> /path/to/repo`
- `specfact code validate sidecar run <bundle> /path/to/repo`

### Brownfield and reverse engineering

Use SpecFact to understand an existing system before you change it, then hand that understanding
into spec-first tools such as OpenSpec or Spec-Kit.

Start with:
- `specfact code import my-project --repo .`
- `specfact project snapshot --bundle my-project`
- `specfact code validate sidecar init my-project /path/to/repo`
- `specfact code validate sidecar run my-project /path/to/repo`

### Backlog to code alignment

Use SpecFact when the problem is not only code quality, but drift between expectations and delivery.
Backlog commands require a backlog-enabled profile or installed backlog bundle before the workflow
commands are available.

Start with:
- `specfact init --profile backlog-team`
- `specfact backlog ceremony standup ...`
- `specfact backlog ceremony refinement ...`
- `specfact backlog verify-readiness --bundle <bundle-name>`

### Team and policy enforcement

Use SpecFact when multiple developers and AI IDEs need consistent checks and review behavior.

Start with:
- `specfact backlog verify-readiness --bundle <bundle-name>`
- `specfact govern ...`
- CI validation flows that keep the same rules active outside local development

## How do I get started if I want more?

**Next steps**

- **[Core CLI docs](docs/index.md)** for the core runtime, bootstrap, validation, and command topology
- **[Reference: command topology](docs/reference/commands.md)** for grouped command surfaces
- **[Canonical modules docs site](https://modules.specfact.io/)** for bundle-deep workflows

## Documentation Topology

`docs.specfact.io` is the canonical starting point for SpecFact.

- Core CLI/runtime/platform documentation remains owned by `specfact-cli`.
- Module-specific deep docs are canonically owned by `specfact-cli-modules`.
- The live modules docs site is published at `https://modules.specfact.io/`.

Use this repository's docs for the overall product story, runtime lifecycle, command topology,
trust model, and getting-started flow. Use the modules docs site when you want deeper workflow,
adapter, and module-authoring guidance.

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

1. **Bootstrap**: use **uvx** or **pip**, then `init --profile` to install the bundles you need (for example `solo-developer` for a scored **code review** first).
2. **Review or analyze**: run **`code review run`** on a repo, or import code and snapshot state for deeper workflows.
3. **Sync**: connect backlog systems or sync external artifacts into project bundles when you are ready.
4. **Validate**: run spec, governance, and sidecar validation flows before implementation or release.
5. **Iterate safely**: use module-provided workflows while the core runtime keeps command mounting, trust, and lifecycle consistent.

## Where SpecFact Fits

SpecFact complements your stack rather than replacing it.

- **Spec-Kit/OpenSpec** for authoring and change tracking
- **Backlog tools** for planning and delivery
- **CI/CD** for enforcement and regression prevention
