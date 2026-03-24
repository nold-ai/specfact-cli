---
layout: default
title: specfact init
permalink: /core-cli/init/
description: Reference for the specfact init command - bootstrap SpecFact in a repository with profiles, IDE setup, and dependency installation.
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

The `init ide` subcommand generates IDE-specific prompt templates and settings:

```bash
# Initialize Cursor IDE integration
specfact init ide --ide cursor

# Initialize with dependency installation
specfact init ide --install-deps
```

This creates:

- `.specfact/` directory structure
- `.specfact/templates/backlog/field_mappings/` with default field mapping templates
- IDE-specific command files for your AI assistant

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
