---
layout: default
title: Agent repository context
permalink: /contributing/agent-rules/repository-context/
description: Project overview, key commands, architecture, and logging guidance preserved from the previous AGENTS.md.
keywords: [agents, commands, architecture, logging, project-overview]
audience: [team, enterprise]
expertise_level: [intermediate, advanced]
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - docs/agent-rules/**
  - src/specfact_cli/**
  - pyproject.toml
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
id: agent-rules-repository-context
always_load: false
applies_when:
  - repository-orientation
  - command-lookup
priority: 20
blocking: false
user_interaction_required: false
stop_conditions:
  - none
depends_on:
  - agent-rules-index
---

# Agent repository context

## Project overview

SpecFact CLI is a Python CLI tool for agile DevOps teams. It keeps backlogs, specs, tests, and code in sync with contract-driven development, validation, and enforcement. It is built with Typer and Rich, uses Hatch as the build system, and targets Python 3.12 (supports Python 3.11+ at runtime).

## Essential commands

```bash
pip install -e ".[dev]"
hatch shell
hatch run format
hatch run type-check
hatch run contract-test
hatch test --cover -v
hatch run lint
hatch run yaml-lint
hatch run lint-workflows
hatch run scan-all
hatch run specfact code review run --json --out .specfact/code-review.json
```

## Architecture

- Modular command registry with lazy loading under `src/specfact_cli/modules/`
- Pydantic models in `models/`
- Parsers and analyzers in `parsers/` and `analyzers/`
- Jinja2-backed generation under `generators/`
- Validation logic under `validators/`
- Tool integrations through bridge adapters in `adapters/`
- Operational modes under `modes/`
- Templates, prompts, schemas, and mappings under `resources/`

## Logging

Use `from specfact_cli.common import get_bridge_logger` in production paths and avoid `print()` in `src/`. Debug logs go to `~/.specfact/logs/specfact-debug.log` when `--debug` is passed.
