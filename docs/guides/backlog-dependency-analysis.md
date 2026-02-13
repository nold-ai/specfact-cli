---
layout: default
title: Backlog Dependency Analysis
permalink: /guides/backlog-dependency-analysis/
---

# Backlog Dependency Analysis

Use SpecFact to build a provider-agnostic dependency graph from backlog tools and analyze execution risk before delivery.

## Commands

```bash
specfact backlog analyze-deps --project-id <id> --adapter <github|ado> --template <template>
specfact backlog trace-impact <item-id> --project-id <id> --adapter <github|ado>
specfact backlog verify-readiness --project-id <id> --adapter <github|ado>
specfact backlog export-roadmap --project-id <id> --adapter <github|ado>   # via project command: see devops flow guide
```

## Typical Flow

1. Run `analyze-deps` to compute typed coverage, orphans, cycles, and critical path.
2. Run `trace-impact` for candidate changes to estimate downstream blast radius.
3. Run `verify-readiness` before release for blocker and child-completion checks.

## Templates

- `github_projects`
- `ado_scrum`
- `ado_safe`
- `jira_kanban`

Use `--template` to align type/dependency rules with your backlog model.

## Outputs

- Rich terminal summary (coverage/cycle/orphan metrics).
- Optional graph JSON export from `analyze-deps` via `--json-export`.
- Optional markdown report from `analyze-deps` via `--output`.
