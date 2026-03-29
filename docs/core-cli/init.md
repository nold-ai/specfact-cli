---
layout: default
title: specfact init
permalink: /core-cli/init/
description: Reference for the specfact init command - bootstrap SpecFact in a repository with profiles, IDE setup, and dependency installation.
keywords: [init, bootstrap, ide, profiles]
audience: [solo, team, enterprise]
expertise_level: [beginner, intermediate]
doc_owner: specfact-cli
tracks:
  - src/specfact_cli/**
  - openspec/**
last_reviewed: 2026-03-29
exempt: false
exempt_reason: ""
---

# specfact init

Bootstrap SpecFact CLI in a repository. Use `init ide` for IDE-specific setup; module lifecycle is under `specfact module`.

## Usage

```bash
specfact init [OPTIONS]
specfact init ide [OPTIONS]
```

## Options

| Option | Type | Description |
|--------|------|-------------|
| `--repo` | DIRECTORY | Repository path (default: current directory) |
| `--profile` | TEXT | First-run profile preset (see below) |
| `--install` | TEXT | Comma-separated bundle names or `all` to install without prompting |
| `--install-deps` | | Install required packages for contract enhancement |

## Profiles

Profiles select a default set of bundles appropriate for your team setup:

| Profile | Description |
|---------|-------------|
| `solo-developer` | Minimal bundle set for individual projects |
| `backlog-team` | Backlog sync and ceremony bundles for agile teams |
| `api-first-team` | Spec validation and contract testing bundles |
| `enterprise-full-stack` | All official bundles including governance and adapters |

```bash
# Bootstrap with the solo-developer preset
specfact init --profile solo-developer

# Install specific bundles during init
specfact init --install backlog,code-review
```

## IDE Setup

The `init ide` subcommand discovers prompt templates from **core** (bundled `specfact_cli` resources or your repo checkout) and from **installed modules** under the effective module roots (builtin, project `.specfact/modules`, user `~/.specfact/modules`, marketplace, and `SPECFACT_MODULES_ROOTS`). It is a **re-sync** command: it only copies what is already installed; it does not download or extract modules. If prompts are missing, install or seed modules first (for example `specfact module init --scope project` or `specfact module install --scope user`).

```bash
# Initialize Cursor IDE integration (interactive: pick IDE, then prompt sources)
specfact init ide --ide cursor

# Non-interactive: export all discovered sources (default)
specfact init ide --ide cursor --repo .

# Non-interactive: only core, or a comma-separated list of module ids
specfact init ide --ide cursor --prompts core
specfact init ide --ide cursor --prompts all
specfact init ide --ide cursor --prompts "core,nold-ai/specfact-backlog"

# Initialize with dependency installation
specfact init ide --install-deps
```

Exported IDE files are placed under **per-source subfolders** (for example `.cursor/commands/core/`, `.cursor/commands/nold-ai__specfact-backlog/`) so names collide deterministically and provenance stays visible.

This creates or refreshes:

- `.specfact/` directory structure
- `.specfact/templates/backlog/field_mappings/` with default field mapping templates when available
- IDE-specific command files under the IDE export directory, namespaced by prompt source

## Dependency Installation

Use `--install-deps` to install optional packages required for contract enhancement (CrossHair, beartype, icontract):

```bash
specfact init --install-deps
```

Prefer `specfact init ide --install-deps` when setting up IDE integration at the same time.

## Typical First-Run Sequence

```bash
# 1. Install SpecFact CLI
pip install specfact-cli

# 2. Bootstrap with a profile
specfact init --profile solo-developer

# 3. Set up IDE integration
specfact init ide --ide cursor

# 4. Verify modules are installed
specfact module list
```
