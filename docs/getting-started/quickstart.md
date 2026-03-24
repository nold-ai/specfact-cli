---
layout: default
title: 5-Minute Quickstart
permalink: /getting-started/quickstart/
redirect_from:
  - /getting-started/first-steps/
description: Get SpecFact CLI running in under 5 minutes - install, bootstrap, and analyze your first codebase.
---

# 5-Minute Quickstart

Get from zero to your first SpecFact analysis in under 5 minutes.

## Prerequisites

- Python 3.11+ (`python3 --version`)
- A Git repository to analyze (or create a test project)

## Step 1: Install

```bash
pip install specfact-cli
```

Or try without installing: `uvx specfact-cli@latest --help`

## Step 2: Bootstrap

```bash
# Navigate to your project
cd /path/to/your/project

# Initialize with a profile
specfact init --profile solo-developer
```

This installs the default set of workflow bundles. See [specfact init](/core-cli/init/) for other profiles.

## Step 3: Set Up IDE (Optional)

```bash
specfact init ide --ide cursor --install-deps
```

This creates `.specfact/` directory structure and IDE-specific prompt templates.

## Step 4: Analyze Your Codebase

```bash
specfact code import my-project --repo .
```

SpecFact analyzes your code and extracts features, user stories, and dependency graphs into a project bundle at `.specfact/projects/my-project/`.

## Step 5: Check Project Health

```bash
specfact project health-check
```

Review what SpecFact discovered about your codebase.

## Step 6: Validate

```bash
specfact code repro --verbose
```

Runs the full validation suite: linting, type checking, contracts, and tests.

## What's Next

- **[specfact init](/core-cli/init/)** - Profiles and IDE setup options
- **[specfact module](/core-cli/module/)** - Install additional workflow bundles
- **[Command Reference](/reference/commands/)** - Full command surface
- **Module workflows** - Visit [modules.specfact.io](https://modules.specfact.io/) for backlog, governance, and adapter guides
