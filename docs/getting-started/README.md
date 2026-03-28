---
layout: default
title: Getting Started
permalink: /getting-started/
---

# Getting Started with SpecFact CLI

## Start Here

- **[Where to Start](where-to-start.md)** - New-user overview: what SpecFact is for, what core owns, and what to do next

## Installation

- **[Installation Guide](installation.md)** - All installation options (uvx, pip, Docker, GitHub Actions)
- **[Enhanced Analysis Dependencies](../installation/enhanced-analysis-dependencies.md)** - Optional dependencies for graph-based analysis

## Quick Start

```bash
# Install
pip install specfact-cli

# Bootstrap with a profile
specfact init --profile solo-developer

# Analyze your codebase
specfact code import my-project --repo .
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
