---
layout: default
title: Code Review Module
description: Install and use the official specfact-code-review module scaffold.
permalink: /modules/code-review/
---

# Code Review Module

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
