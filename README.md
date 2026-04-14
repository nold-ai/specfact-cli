# SpecFact CLI

> Review AI-assisted code against your own contracts.
> Catch drift before it reaches PR or main.

[![PyPI version](https://img.shields.io/pypi/v/specfact-cli.svg?color=22c55e)](https://pypi.org/project/specfact-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/specfact-cli.svg)](https://pypi.org/project/specfact-cli/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-F59E0B.svg)](https://github.com/nold-ai/specfact-cli)

**No API keys required. Works offline. Zero vendor lock-in.**

<div align="center">

**[Documentation](https://docs.specfact.io/)** • **[Modules](https://modules.specfact.io/)** • **[Support](mailto:hello@noldai.com)**

</div>

## Try it in 60 seconds

```bash
# Zero-install, no API key, works offline
uvx specfact-cli init --profile solo-developer
uvx specfact-cli code review run --path . --scope full
```

**Sample output:**

```text
SpecFact CLI - v0.46.1

Running Ruff checks...
Running Radon complexity checks...
Running Semgrep rules...
Running AST clean-code checks...
Running basedpyright type checks...
Running pylint checks...
Running contract checks...
Running targeted tests and coverage...

Verdict: FAIL | CI exit: 1 | Score: 0 | Reward delta: -80

Findings:
  - specfact_demo/enforcement.py:96   Cyclomatic complexity for run_enforcement is 16.
  - specfact_demo/main.py:81          Avoid print() in source files; use structured logging instead.
  - examples/buggy_math.py:4          Public function divide is missing @require/@ensure decorators.

Evidence bundle: docs/_support/readme-first-contact/sample-output/
```

⭐ **Star this repo if the output is useful.** Open an issue if you want the workflow adapted for your stack.

**Already installed the CLI?** Use:

```bash
specfact init --profile solo-developer
specfact code review run --path . --scope full
```

The sample output comes from a pinned capture against `nold-ai/specfact-demo-repo`. Reproduce it with `docs/_support/readme-first-contact/capture-readme-output.sh`; capture metadata lives alongside the raw logs in `docs/_support/readme-first-contact/sample-output/`.

## What SpecFact does

- **Reviews AI-assisted changes deterministically** — compare code against contracts, clean-code rules, and policy gates
- **Extracts structure from existing code** — reverse-engineer brownfield repos before you change them
- **Blocks drift before merge** — use the same checks locally, in pre-commit, and in CI
- **Links backlog intent to code reality** — connect backlog, specs, validation, and implementation
- **Stays local-first** — no cloud account, no vendor lock-in, no built-in model dependency

## What is SpecFact?

SpecFact is a local CLI for catching backlog/spec/code drift before it becomes expensive. It gives solo developers, legacy maintainers, and teams a validation layer around AI-assisted delivery, brownfield reverse engineering, and contract-first reviews.

It exists because delivery drifts in predictable ways:

- AI-assisted code lands faster than validation catches up
- brownfield systems rarely have trustworthy up-to-date specs
- backlog intent gets reinterpreted before it reaches code
- teams need the same review rules across IDEs, CI, and pull requests

## Add SpecFact to your workflow

### Pre-commit hook

This repository uses a **modular** local hook layout (parity with `specfact-cli-modules`: `fail_fast`,
separate verify / format / YAML / Markdown / workflow / lint / Block 2 hooks). Copy
[`.pre-commit-config.yaml`](.pre-commit-config.yaml) from this repo and run `pre-commit install`.

For a **single-hook** setup in downstream repos, keep using the stable id and script shim:

```yaml
- repo: https://github.com/nold-ai/specfact-cli
  rev: v0.46.1
  hooks:
    - id: specfact-smart-checks
```

The shim runs `scripts/pre-commit-quality-checks.sh all` (full pipeline including module verify).

### GitHub Actions

```yaml
- name: SpecFact Gate
  run: uvx specfact-cli@latest govern enforce stage --preset minimal
```

## How SpecFact is built

SpecFact uses the same discipline it asks you to trust:

1. Outside-in research on the workflow or drift problem
2. Public **OpenSpec** proposal and spec deltas
3. TDD evidence before implementation
4. Dogfooding with `specfact code review`
5. Format, type-check, contract-test, and docs quality gates
6. PR review with evidence artifacts
7. Release through the same reproducible CLI paths

## For teams and organizations

SpecFact still scales beyond the solo-developer entry path:

- **Backlog + ceremony workflows** for GitHub, Azure DevOps, Jira, and Linear
- **DoR/DoD and policy enforcement** for teams that need repeatable gates
- **Evidence-backed PR review** with the same checks used locally
- **CI/CD adoption path** that keeps validation deterministic instead of model-driven

Start with:

- `specfact backlog ceremony standup ...`
- `specfact backlog ceremony refinement ...`
- `specfact backlog verify-readiness --bundle <bundle-name>`
- `specfact govern ...`

## Module system

Official workflow behavior ships from `nold-ai/specfact-cli-modules`. The core CLI owns bootstrap, runtime contracts, trust checks, logging, and the grouped command surface. Installed modules add families such as `project`, `backlog`, `code`, `spec`, and `govern`.

Install examples:

```bash
specfact module install nold-ai/specfact-project
specfact module install nold-ai/specfact-backlog
specfact module install nold-ai/specfact-codebase
specfact module install nold-ai/specfact-code-review
specfact module install nold-ai/specfact-govern
```

If startup warns that modules are missing or outdated, run:

```bash
specfact module init --scope project
specfact module init
```

## Documentation topology

`docs.specfact.io` is the canonical starting point for SpecFact.

- Core CLI/runtime/platform documentation remains owned by `specfact-cli`
- Module-specific deep docs are canonically owned by `specfact-cli-modules`
- The live modules docs site is published at `https://modules.specfact.io/`

Use this repository's docs for the product story, runtime lifecycle, command topology, trust model, and getting-started flow. Use the modules docs site when you want deeper workflow, adapter, and module-authoring guidance.

## How do I get started if I want more?

Next steps:

- **[Core CLI docs](docs/index.md)** for the core runtime, bootstrap, and validation flow
- **[Installation guide](https://docs.specfact.io/getting-started/installation/)** for uvx-first and persistent CLI setup
- **[Quickstart](https://docs.specfact.io/getting-started/quickstart/)** for the first repo review path
- **[Reference: command topology](docs/reference/commands.md)** for grouped command surfaces
- **[Canonical modules docs site](https://modules.specfact.io/)** for bundle-deep workflows
