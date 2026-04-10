---
layout: default
title: Doc-sync frontmatter reference
permalink: /contributing/frontmatter-schema/
description: Required ownership fields, validation rules, and cross-site documentation contracts for core docs.
keywords: [documentation, frontmatter, schema, validation]
audience: [solo, team, enterprise]
expertise_level: [intermediate, advanced]
doc_owner: specfact-cli
tracks:
  - scripts/check_doc_frontmatter.py
  - docs/contributing/**
last_reviewed: 2026-03-29
exempt: false
exempt_reason: ""
---

# Doc-sync frontmatter reference

This page is the **authoritative schema** for the ownership and tracking fields consumed by `scripts/check_doc_frontmatter.py`. Jekyll fields (`layout`, `title`, `permalink`, etc.) stay unchanged; the rows below are **additional** keys for doc-sync.

## Required fields

| Field | Type | Rules |
| --- | --- | --- |
| `doc_owner` | string | Repo-relative path that exists, or a token from `VALID_OWNER_TOKENS` in the script (`specfact-cli`, `nold-ai`, `openspec`). |
| `tracks` | list of strings | Non-empty; each entry is a [fnmatch](https://docs.python.org/3/library/fnmatch.html)-style glob. Brackets and braces must balance; patterns must compile as fnmatch regex (see `validate_glob_patterns` in the script). |
| `last_reviewed` | `YYYY-MM-DD` | ISO date; YAML may load as a string or date. |
| `exempt` | boolean | `true` only for pages that intentionally skip sync rules. |
| `exempt_reason` | string | Empty when `exempt` is `false`; non-empty when `exempt` is `true`. |

Runtime validation uses a Pydantic model (`DocFrontmatter` in `scripts/check_doc_frontmatter.py`): missing keys, wrong types, bad globs, unresolved `doc_owner`, and invalid exempt/reason pairs fail the check.

## Additional fields for `docs/agent-rules/`

Files under `docs/agent-rules/` carry extra governance metadata on top of the standard doc-sync fields so bootstrap loaders can make deterministic decisions without reading every rule file in full.

| Field | Type | Rules |
| --- | --- | --- |
| `id` | string | Stable rule identifier used by references and dependencies. |
| `always_load` | boolean | `true` when the rule must be loaded during every applicable bootstrap. |
| `applies_when` | list of strings | Non-empty task signals such as `session-bootstrap`, `implementation`, or `github-public-work`. |
| `priority` | integer | Non-negative ordering value used for deterministic rule loading. |
| `blocking` | boolean | Whether the rule can stop progress when its conditions are unmet. |
| `user_interaction_required` | boolean | Whether unmet conditions require user clarification before implementation continues. |
| `stop_conditions` | list of strings | Non-empty human-readable blocking conditions enforced by the rule. |
| `depends_on` | list of strings | Other rule ids that must load first. Empty list is allowed. |

## Cross-repo notes

- **Core vs modules:** Canonical user-facing docs for bundles and marketplace content live on [modules.specfact.io](https://modules.specfact.io/). Linking and URL rules are described in [Documentation URL contract](../reference/documentation-url-contract.md).
- **Bundled modules:** When CLI or module surface changes, update both this repo’s docs (as tracked by `tracks`) and the sibling **specfact-cli-modules** documentation where applicable; CodeRabbit linked-repo analysis can flag cross-repo drift.

## Commands

```bash
hatch run doc-frontmatter-check
hatch run doc-frontmatter-check -- --all-docs
```

Rollout scope is controlled by `docs/.doc-frontmatter-enforced`. See [Documentation ownership and frontmatter](/contributing/docs-sync/) for workflow.
