---
layout: default
title: Documentation ownership and frontmatter
permalink: /contributing/docs-sync/
description: YAML frontmatter schema for documentation ownership, tracking, and validation on docs.specfact.io.
keywords: [documentation, frontmatter, ownership, validation]
audience: [solo, team, enterprise]
expertise_level: [intermediate, advanced]
doc_owner: specfact-cli
tracks:
  - scripts/check_doc_frontmatter.py
  - docs/**
last_reviewed: 2026-03-29
exempt: false
exempt_reason: ""
---

# Documentation ownership and frontmatter

Core documentation uses **YAML frontmatter** for Jekyll (layout, title, permalink) and for **ownership** fields that drive the `scripts/check_doc_frontmatter.py` checker.

## Schema (ownership)

For field definitions, validation rules, and cross-repo notes, see **[Doc-sync frontmatter reference](frontmatter-schema.md)**.

Add these keys alongside existing Jekyll fields:

| Field | Required | Description |
| --- | --- | --- |
| `doc_owner` | yes | Repo path (e.g. `src/specfact_cli`) or a known token (`specfact-cli`, `nold-ai`, `openspec`). |
| `tracks` | yes | List of glob patterns for sources this page should stay aligned with. |
| `last_reviewed` | yes | `YYYY-MM-DD` date of last substantive review. |
| `exempt` | yes | `true` only for stable or legal pages that skip sync rules; use with `exempt_reason`. |
| `exempt_reason` | yes | Empty string when `exempt` is `false`; non-empty when `exempt` is `true`. |

## Validation

From the repository root:

```bash
hatch run doc-frontmatter-check
```

Use `--fix-hint` for suggested YAML blocks. During rollout, only paths listed in `docs/.doc-frontmatter-enforced` are checked unless you pass `--all-docs`.

## Troubleshooting

- **Missing `doc_owner`**: add the field and a sensible `tracks` list for the code or specs this page describes.
- **Owner does not resolve**: use a path that exists under the repo or one of the known tokens.
- **Invalid `tracks`**: ensure balanced `[]` and `{}` in glob patterns.
