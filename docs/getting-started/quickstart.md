---
layout: default
title: 5-Minute Quickstart
permalink: /getting-started/quickstart/
redirect_from:
  - /getting-started/first-steps/
description: Get SpecFact CLI running in under 5 minutes for AI-bloat defense, cleanup forecasts, and deterministic code review.
keywords: [quickstart, first-run, bootstrap, analysis, uvx, ai-bloat, cleanup forecast]
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

Get from zero to **AI-bloat defense** and a scored code review in a few commands. This path is aimed at developers who want one command, one clear result, and a JSON handoff for AI IDE cleanup before reading about modules, profiles, or architecture.

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

If the Code Review bundle reports `category=ai_bloat`, treat those entries as cleanup candidates, not proof of AI authorship. They are `severity=info`, advisory-only, and score-neutral.

## Step 3: Run the JSON-first cleanup loop

Run simplify-focused review with JSON output:

```bash
uvx specfact-cli code review run --scope changed --enforcement shadow --focus simplify --preview-fixes --json --out .specfact/code-review.json
```

Then work the report in this order:

1. Inspect `cleanup_forecast` and the AI-bloat index.
2. Hand remediation packets to your AI IDE.
3. Accept only safe or approved changes.
4. Re-run review for proof.

This is AI-bloat defense, not AI-authorship detection. For exact simplify flags, invalid combinations, and report fields, see the [AI bloat quickstart](https://modules.specfact.io/quickstart-ai-bloat/) and [Code Review run guide](https://modules.specfact.io/bundles/code-review/run/) on the modules docs site.

## Step 4: Install SpecFact locally (optional)

When you want a stable `specfact` command and IDE integration, install with pip:

```bash
pip install specfact-cli
cd /path/to/your/project
specfact init --profile solo-developer
```

## Step 5: Set Up IDE (Optional)

```bash
specfact init ide --ide cursor --install-deps
```

This creates `.specfact/` directory structure and IDE-specific prompt templates.

## Step 6: Analyze Your Codebase and Check Health

```bash
specfact code import --repo . my-project
specfact project health-check
```

`code import` analyzes your code and extracts features, user stories, and dependency graphs into a project bundle at `.specfact/projects/my-project/`. `project health-check` summarizes what SpecFact discovered.

## Step 7: Validate

```bash
specfact code repro --verbose
```

Runs the full validation suite: linting, type checking, contracts, and tests.

## What's Next

- **[specfact init](/core-cli/init/)** - Profiles and IDE setup options
- **[specfact module](/core-cli/module/)** - Install additional workflow bundles
- **[Command Reference](/reference/commands/)** - Full command surface
- **Module workflows** - Visit [modules.specfact.io](https://modules.specfact.io/) for backlog, governance, and adapter guides
