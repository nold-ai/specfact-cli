---
layout: default
title: Agent non-negotiable checklist
permalink: /contributing/agent-rules/non-negotiable-checklist/
description: Always-load SHALL gates that apply to every implementation session in the repository.
keywords: [agents, governance, checklist, tdd, worktree]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - docs/agent-rules/**
  - openspec/CHANGE_ORDER.md
  - openspec/config.yaml
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
id: agent-rules-non-negotiable-checklist
always_load: true
applies_when:
  - session-bootstrap
  - implementation
priority: 5
blocking: true
user_interaction_required: true
stop_conditions:
  - main checkout implementation attempted without override
  - no valid OpenSpec change covers requested modification
  - stale or ambiguous change requires refinement
  - failing-before evidence missing for behavior change
depends_on:
  - agent-rules-index
---

# Agent non-negotiable checklist

- SHALL work in a git worktree unless the user explicitly overrides that rule.
- SHALL not implement from the `dev` or `main` checkout by default.
- SHALL treat a provided OpenSpec change id as candidate scope, not automatic permission to proceed.
- SHALL verify selected change validity against current repository reality and dependency state before implementation.
- SHALL not auto-refine stale, superseded, or ambiguous changes without the user.
- SHALL consult `openspec/CHANGE_ORDER.md` before creating, implementing, or archiving a change.
- SHALL consult `.specfact/backlog/github_hierarchy_cache.md` before manual GitHub hierarchy lookup and SHALL refresh it when missing or stale.
- SHALL require public GitHub metadata completeness before implementation when linked issue workflow applies: parent, labels, project assignment, blockers, and blocked-by relationships.
- SHALL check whether a linked GitHub issue is already `in progress` and SHALL pause for clarification if concurrent work is possible.
- SHALL perform `spec -> tests -> failing evidence -> code -> passing evidence` in that order for behavior changes.
- SHALL run required verification and quality gates for the touched scope before finalization.
- SHALL fix SpecFact code review findings, including warnings, unless a rare and explicit exception is documented.
- SHALL enforce module signatures and version bumps when signed module assets or manifests are affected.
- SHALL preserve existing instructions by moving them to canonical rule files before shortening the bootstrap surfaces.
