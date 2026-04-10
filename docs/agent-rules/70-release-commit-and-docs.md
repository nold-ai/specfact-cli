---
layout: default
title: Agent release, commit, and docs rules
permalink: /contributing/agent-rules/release-commit-and-docs/
description: Versioning, changelog, documentation, README, and commit-signing rules preserved from the previous AGENTS.md.
keywords: [agents, versioning, changelog, docs, commits]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - CHANGELOG.md
  - README.md
  - docs/**
  - pyproject.toml
  - setup.py
  - src/specfact_cli/__init__.py
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
id: agent-rules-release-commit-and-docs
always_load: false
applies_when:
  - finalization
  - release
  - documentation-update
priority: 70
blocking: false
user_interaction_required: true
stop_conditions:
  - version bump requested without confirmation
depends_on:
  - agent-rules-index
  - agent-rules-quality-gates-and-review
---

# Agent release, commit, and docs rules

## Versioning

- Keep version updates in sync across `pyproject.toml`, `setup.py`, and `src/specfact_cli/__init__.py`.
- `feature/*` branches imply a minor bump, `bugfix/*` and `hotfix/*` imply a patch bump, and major bumps require explicit confirmation.

## Changelog

- Update `CHANGELOG.md` in the same commit as the version bump.
- Follow Keep a Changelog sections: `Added`, `Changed`, `Fixed`, `Removed`, `Security`.

## Commits

- Use Conventional Commits.
- If signed commits fail in a non-interactive shell, stage files and hand the exact `git commit -S -m "<message>"` command to the user instead of bypassing signing.

## Documentation and README

- Keep docs current with every user-facing behavior change.
- Preserve all Jekyll frontmatter on docs edits.
- Update navigation when adding or moving pages.
- Keep `README.md` and the docs landing page aligned with what SpecFact actually does.
