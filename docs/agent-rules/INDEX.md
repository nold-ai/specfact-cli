---
layout: default
title: Agent rules index
permalink: /contributing/agent-rules/
description: Canonical deterministic loader for repository governance instructions used by AGENTS.md and other AI instruction surfaces.
keywords: [agents, governance, instructions, openspec, worktree]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - CLAUDE.md
  - .github/copilot-instructions.md
  - .cursor/rules/session_startup_instructions.mdc
  - docs/agent-rules/**
  - scripts/check_doc_frontmatter.py
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
id: agent-rules-index
always_load: true
applies_when:
  - session-bootstrap
priority: 0
blocking: true
user_interaction_required: false
stop_conditions:
  - canonical rule index missing
depends_on: []
---

# Agent rules index

This page is the canonical loader for repository governance instructions. `AGENTS.md` stays small and mandatory, but the detailed rules live here and in the linked rule files so new sessions do not have to absorb the full policy corpus up front.

## Bootstrap sequence

1. Read `AGENTS.md`.
2. Load this index.
3. Load [`05-non-negotiable-checklist.md`](./05-non-negotiable-checklist.md).
4. Load [`10-session-bootstrap.md`](./10-session-bootstrap.md) (always-load; deterministic startup orchestration before enforcement).
5. Detect repository, branch, and worktree state.
6. Reject implementation from the `dev` or `main` checkout unless the user explicitly overrides that rule.
7. If GitHub hierarchy metadata is needed and `.specfact/backlog/github_hierarchy_cache.md` is missing or stale, refresh it with `python scripts/sync_github_hierarchy_cache.py`.
8. Load additional rule files from the applicability matrix below before implementation (beyond the always-load set, which already includes this index, the checklist, and session bootstrap).

## Precedence

1. Direct system and developer instructions
2. Explicit user override where repository governance allows it
3. `AGENTS.md`
4. `docs/agent-rules/05-non-negotiable-checklist.md`
5. Other `docs/agent-rules/*.md` files selected through this index
6. Change-local OpenSpec artifacts and workflow notes

## Always-load rules

| Order | File | Purpose |
| --- | --- | --- |
| 0 | `INDEX.md` | Deterministic rule dispatch and precedence |
| 5 | `05-non-negotiable-checklist.md` | Invariant SHALL gates |
| 10 | `10-session-bootstrap.md` | Startup checks and stop conditions |

## Applicability matrix

| Task signal | Required rule files | Optional rule files |
| --- | --- | --- |
| Any implementation request | `10-session-bootstrap.md`, `40-openspec-and-tdd.md`, `50-quality-gates-and-review.md` | `20-repository-context.md` |
| Code or docs changes on a branch | `30-worktrees-and-branching.md` | `80-current-guidance-catalog.md` |
| Public GitHub issue work | `60-github-change-governance.md` | `30-worktrees-and-branching.md` |
| Release or finalization work | `70-release-commit-and-docs.md`, `50-quality-gates-and-review.md` | `80-current-guidance-catalog.md` |
| Repo orientation or command lookup | `20-repository-context.md` | `80-current-guidance-catalog.md` |

## Canonical rule files

- [`05-non-negotiable-checklist.md`](./05-non-negotiable-checklist.md): always-load SHALL gates
- [`10-session-bootstrap.md`](./10-session-bootstrap.md): startup checks, compact context loading, and stop/continue behavior
- [`20-repository-context.md`](./20-repository-context.md): project overview, commands, architecture, and logging
- [`30-worktrees-and-branching.md`](./30-worktrees-and-branching.md): branch protection, worktree policy, and conflict avoidance
- [`40-openspec-and-tdd.md`](./40-openspec-and-tdd.md): OpenSpec selection, change validity, and strict TDD order
- [`50-quality-gates-and-review.md`](./50-quality-gates-and-review.md): required gates, code review JSON, clean-code enforcement, module signatures
- [`60-github-change-governance.md`](./60-github-change-governance.md): cache-first GitHub metadata, dependency completeness, and `in progress` ambiguity handling
- [`70-release-commit-and-docs.md`](./70-release-commit-and-docs.md): versioning, changelog, docs, README, and commit signing
- [`80-current-guidance-catalog.md`](./80-current-guidance-catalog.md): preserved migrated guidance not yet split into narrower documents

## Preservation note

The prior long `AGENTS.md` content has been preserved by reference in these rule files. The goal of this migration is to reduce startup token cost without silently dropping repository instructions.
