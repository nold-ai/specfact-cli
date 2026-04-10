---
layout: default
title: Agent migrated guidance catalog
permalink: /contributing/agent-rules/migrated-guidance-catalog/
description: Preserved guidance moved out of the previous long AGENTS.md before further tailoring and decomposition.
keywords: [agents, migrated-guidance, code-conventions, ci, testing]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - docs/agent-rules/**
  - src/specfact_cli/**
  - tests/**
  - .github/workflows/**
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
id: agent-rules-migrated-guidance-catalog
always_load: false
applies_when:
  - detailed-reference
priority: 80
blocking: false
user_interaction_required: false
stop_conditions:
  - none
depends_on:
  - agent-rules-index
---

# Agent migrated guidance catalog

This file preserves current instructions that were previously inline in the long `AGENTS.md` but are not yet fully split into narrower docs. Nothing here was intentionally dropped during the compact-governance migration.

## Developing specfact-cli-modules

Bundle code in **specfact-cli-modules** imports from `specfact_cli`. For local IDE work in the modules repo, run `hatch env create` there, keep `specfact-cli` available at `../specfact-cli`, and select the modules repo `.venv` in the IDE.

## Code conventions

- Python 3.11+, line length 120, Google-style docstrings
- `snake_case` for files, modules, and functions
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- All data structures use Pydantic `BaseModel` with `Field(...)` and descriptions
- CLI commands use `typer.Typer()` and `rich.console.Console()`

## CLI command pattern

Use `@beartype`, `@require`, and `@ensure` on public command functions and keep command implementations typed and contract-bound.

## Backlog command topology

- `specfact backlog ceremony standup`
- `specfact backlog ceremony refinement`
- `specfact backlog analyze-deps`
- `specfact backlog delta status|impact|cost-estimate|rollback-analysis`
- `specfact backlog verify-readiness`
- `specfact project link-backlog`
- `specfact project health-check`
- `specfact project devops-flow --stage <plan|develop|review|release|monitor> --action <...>`
- `specfact project snapshot|regenerate|export-roadmap`

## Testing

Contract-first coverage remains the primary testing philosophy. Test structure mirrors source under `tests/unit/`, `tests/integration/`, and `tests/e2e/`. Guard environment-sensitive logic with `os.environ.get("TEST_MODE") == "true"`.

## CI/CD

Key workflows in `.github/workflows/` include `tests.yml`, `specfact.yml`, `pr-orchestrator.yml`, and `build-and-push.yml`.
