---
layout: default
title: 5-Minute Quickstart
permalink: /getting-started/quickstart/
redirect_from:
  - /getting-started/first-steps/
description: Get SpecFact CLI running in under 5 minutes — uvx first, then optional pip install for IDE workflows and deeper analysis.
keywords: [quickstart, first-run, bootstrap, analysis, uvx]
audience: [solo, team]
expertise_level: [beginner]
doc_owner: specfact-cli
tracks:
  - src/specfact_cli/**
  - openspec/**
last_reviewed: 2026-05-21
exempt: false
exempt_reason: ""
---

<!-- markdownlint-disable-next-line MD025 -->
# 5-Minute Quickstart

Get from zero to a **scored code review** in a few commands. This path is aimed at developers who want one command and one clear result before reading about modules, profiles, or architecture.

## Prerequisites

- Python 3.11+ (`python3 --version`)
- A Git repository to analyze (or create a test project)

## Step 1: Bootstrap with uvx (no pip install)

From your repo root:

```bash
uvx specfact-cli init --profile solo-developer
```

This installs the workflow bundles for the solo-developer profile (including the code-review module). See [specfact init](/core-cli/init/) for other profiles.

## Step 2: Run a scored code review

```bash
uvx specfact-cli code review run --path . --scope full
```

You should see a **Verdict**, **Score**, and findings. That is the fastest “aha” path on a real codebase.

If the Code Review bundle reports `category=ai_bloat`, treat those entries as cleanup candidates, not proof of AI authorship. They are `severity=info`, advisory-only, and score-neutral. Write the JSON report, then use `/specfact.08-simplify` from your IDE prompts to review each proposed simplification:

```bash
uvx specfact-cli code review run --json --out .specfact/code-review.json --path . --scope full
```

For the focused walkthrough, see the [AI bloat quickstart](https://modules.specfact.io/quickstart-ai-bloat/) on the modules docs site.

## Step 3: Install SpecFact locally (optional)

When you want a stable `specfact` command and IDE integration, install with pip:

```bash
pip install specfact-cli
cd /path/to/your/project
specfact init --profile solo-developer
```

## Step 4: Set Up IDE (Optional)

```bash
specfact init ide --ide cursor --install-deps
```

This creates `.specfact/` directory structure and IDE-specific prompt templates.

## Step 5: Analyze Your Codebase and Check Health

```bash
specfact code import my-project --repo .
specfact project health-check
```

`code import` analyzes your code and extracts features, user stories, and dependency graphs into a project bundle at `.specfact/projects/my-project/`. `project health-check` summarizes what SpecFact discovered.

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
