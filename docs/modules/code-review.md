---
layout: default
title: Code Review Module
description: Install and use the official specfact-code-review module scaffold.
permalink: /modules/code-review/
---

## Code Review Module

The `nold-ai/specfact-code-review` module extends `specfact code` with a governed `review` subgroup for structured review execution, scoring, and reporting.

## Install

```bash
specfact module install nold-ai/specfact-code-review
```

After installation, the grouped command surface becomes available under:

```bash
specfact code review --help
```

## Command Overview

The scaffold adds these review entrypoints:

- `specfact code review run`
- `specfact code review ledger`
- `specfact code review rules`

This change delivers the command scaffold and the review data model foundation. Runtime review execution and ledger/rules behavior can be layered on in later changes.

## Scoring Algorithm

The module computes review scores from structured findings.

```text
base_score = 100

deductions:
- blocking error: -15
- fixable error: -5
- warning: -2
- info: -1

bonuses:
- zero LOC violations: +5
- zero complexity violations: +5
- all APIs use icontract: +5
- coverage >= 90%: +5
- no new suppressions: +5

score = clamp(0, 120)
reward_delta = score - 80
```

Verdict mapping:

- `PASS` for scores `>= 70`
- `PASS_WITH_ADVISORY` for scores `>= 50` and `< 70`
- `FAIL` for scores `< 50`
- Any blocking error forces `FAIL` regardless of score

## JSON Output Schema

The scaffolded `ReviewReport` envelope carries these fields:

```json
{
  "schema_version": "1.0",
  "run_id": "run-001",
  "timestamp": "2026-03-11T21:50:05Z",
  "overall_verdict": "PASS",
  "ci_exit_code": 0,
  "score": 85,
  "reward_delta": 5,
  "findings": [
    {
      "category": "security",
      "severity": "warning",
      "tool": "ruff",
      "rule": "S101",
      "file": "src/example.py",
      "line": 12,
      "message": "Avoid assert in production code.",
      "fixable": false
    }
  ],
  "summary": "Warnings remain but no blocking findings.",
  "house_rules_updates": []
}
```

## Governance-01 Alignment

`ReviewReport` is scaffolded as a governance-01-compatible evidence envelope:

- `schema_version`, `run_id`, `timestamp`, `overall_verdict`, and `ci_exit_code` are always present.
- Review-specific fields (`score`, `reward_delta`, `findings`, `summary`, `house_rules_updates`) extend the standard evidence shape without replacing it.
- CI can treat `ci_exit_code` as the contract-bound gate result from the start.

## Pre-Commit Review Gate

This repository wires `specfact code review run` into **Block 2** of the modular pre-commit pipeline
(`scripts/pre-commit-quality-checks.sh block2`), configured in `.pre-commit-config.yaml` alongside
hooks that mirror `specfact-cli-modules` (module verify, format, staged YAML/Markdown/workflow checks,
`hatch run lint` when Python is staged, then code review + contract tests).

Downstream copies can either use the full modular config from this repo or a single hook
`specfact-smart-checks` pointing at `scripts/pre-commit-smart-checks.sh` (shim → `pre-commit-quality-checks.sh all`).

Block 2 calls `scripts/pre_commit_code_review.py` with staged paths under `src/`, `scripts/`,
`tools/`, `tests/`, and `openspec/changes/` (non-Python paths are filtered inside the helper),
after Block 1 gates (module signatures, formatter safety, Markdown/YAML/workflow checks, and full
`hatch run lint` when `.py` is staged). The review helper itself
then runs:

```bash
specfact code review run --json --out .specfact/code-review.json <staged-python-files>
```

The JSON report is written under ``.specfact/`` (ignored by git via ``.specfact/`` in ``.gitignore``) so local tools and Copilot can read structured findings. The pre-commit helper does **not** print the nested review CLI’s full stdout (tool banners and runner lines); it only prints the short summary and copy-paste lines on stderr after the run.

### Verdict line, report file, and Copilot

After each run, the helper prints a **one-line summary on stderr** (with ``verbose: true`` on the hook so it is visible even when the commit is allowed), for example:

```text
Code review summary: 3 finding(s) (errors=0, warnings=3, advisory=0); overall_verdict='PASS'.
```

Immediately after that line, the script prints the **report path** (repo-relative and absolute), then **ready-to-paste prompts** for Copilot or Cursor so you can copy them without opening this page.

The **authoritative machine-readable report** is always at the repository root:

```text
.specfact/code-review.json
```

Open that file to see ``overall_verdict``, ``score``, ``findings`` (with ``file``, ``line``, ``rule``, ``severity``, ``message``), and the text ``summary``. Regenerate it anytime with the same ``specfact code review run --json --out .specfact/...`` command (or by letting pre-commit run the gate again).

**Do not forget:** when you want help from GitHub Copilot or Cursor, point the assistant at the JSON file so it can remediate findings with full context. Example prompts you can reuse:

- *Read ``.specfact/code-review.json`` from the latest review run and fix every finding, starting with errors then warnings.*
- *Using the review report at ``.specfact/code-review.json``, apply fixes in the listed files at the given line numbers.*
- *@workspace Attach or open ``.specfact/code-review.json`` and address each ``findings[]`` entry.*

Commit behavior:

- `PASS` keeps the commit green
- `PASS_WITH_ADVISORY` keeps the commit green
- `FAIL` blocks the commit when the report includes at least one severity=`error` finding
- Warning-only `FAIL` (low score across many staged files, summary still “0 blocking”) does not block pre-commit; fix errors first, then use the JSON report for advisory cleanup

Repository gate taxonomy:

- Local smart-check wrapper: merge-blocking for its enforced local checks.
- `specfact code review run`: advisory unless it returns `FAIL`; `PASS_WITH_ADVISORY` stays commit-green.
- CodeRabbit review comments/status: advisory review assistance, not a merge-blocking branch-protection gate by themselves.

To install the repo-owned hook flow:

```bash
pre-commit install
scripts/setup-git-hooks.sh
```

## Add to Any Project

For another project, you can use the same gate without this repo's helper
script by adding a local pre-commit hook that runs `specfact` directly:

```yaml
repos:
  - repo: local
    hooks:
      - id: specfact-code-review
        name: specfact code review gate
        entry: specfact code review run --json --out .specfact/code-review.json
        language: system
        files: \.pyi?$
```

This makes code review part of commit validation before the commit is green.
Pre-commit passes the staged matching files as arguments to the command.

## Optional house_rules Workflow

If a project maintains `house_rules`, keep that guidance current with:

```bash
specfact code review rules update
specfact code review rules show
```

The pre-commit gate does not require a `house_rules` file, but projects can use
the generated guidance as part of their broader coding workflow.

## Ledger Storage

For most local and offline use cases, the reward ledger should be treated as a
JSON file stored at:

```text
~/.specfact/ledger.json
```

That local JSON path is the default assumption for day-to-day usage. Supabase
remains optional when a team explicitly configures remote persistence or wants a
shared backend-backed ledger.
