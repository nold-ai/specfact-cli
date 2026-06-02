---
layout: default
title: Getting Started
permalink: /getting-started/
---

# Getting Started with SpecFact CLI

SpecFact starts as AI-bloat defense for Python-first AI-assisted code: run deterministic review,
inspect the cleanup forecast, hand remediation packets to your AI IDE, and re-run for proof. The
same local CLI also supports contract/spec evidence, brownfield analysis, and team gates when you
need more depth.

`ai_bloat` findings are cleanup candidates, not AI-authorship detection. For exact simplify flags
and report fields, use the [AI bloat quickstart](https://modules.specfact.io/quickstart-ai-bloat/)
on the modules docs site.

## Start Here

- **[Where to Start](where-to-start.md)** - New-user overview: what SpecFact is for, what core owns, and what to do next

## Installation

- **[Installation Guide](installation.md)** - All installation options (uvx, pip, Docker, GitHub Actions)
- **[Enhanced Analysis Dependencies](../installation/enhanced-analysis-dependencies.md)** - Optional dependencies for graph-based analysis

## Quick Start

```bash
# Zero-install AI-bloat defense pass
uvx specfact-cli init --profile solo-developer
uvx specfact-cli code review run --path . --scope full
```

See the **[5-Minute Quickstart](quickstart.md)** for a complete walkthrough.

## Core Commands

| Command | Purpose |
|---------|---------|
| `specfact init` | Bootstrap and IDE setup ([reference](/core-cli/init/)) |
| `specfact module` | Module lifecycle management ([reference](/core-cli/module/)) |
| `specfact upgrade` | CLI updates ([reference](/core-cli/upgrade/)) |

## After Setup

- **[Bootstrap Checklist](/module-system/bootstrap-checklist/)** - Verify modules are installed
- **[Command Reference](/reference/commands/)** - Full command surface
- **[Brownfield Engineer Guide](../guides/brownfield-engineer.md)** - Modernizing legacy code

## Module Tutorials

Module-specific tutorials are hosted on the modules site:

- **[Backlog Quickstart Demo](https://modules.specfact.io/getting-started/tutorial-backlog-quickstart-demo/)** - End-to-end backlog workflow
- **[Backlog Refine with AI IDE](https://modules.specfact.io/getting-started/tutorial-backlog-refine-ai-ide/)** - Story quality and refinement
- **[Daily Standup and Sprint Review](https://modules.specfact.io/getting-started/tutorial-daily-standup-sprint-review/)** - Standup automation

## Need Help?

- [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- [hello@noldai.com](mailto:hello@noldai.com)
