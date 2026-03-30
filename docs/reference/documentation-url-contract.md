---
layout: default
title: Documentation URL contract (core and modules)
permalink: /reference/documentation-url-contract/
description: Rules for linking between docs.specfact.io and modules.specfact.io; canonical ownership of paths.
keywords: [docs contract, handoff, core vs modules]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - src/specfact_cli/**
  - openspec/**
last_reviewed: 2026-03-29
exempt: false
exempt_reason: ""
---

# Documentation URL contract (core and modules)

The **authoritative** URL and ownership rules for **both** documentation sites are maintained in the **modules** repository so bundle paths, `redirect_from` history, and permalink policy stay in one place.

## Canonical reference

- **[Core and modules docs URL contract](https://modules.specfact.io/reference/documentation-url-contract/)** (`specfact-cli-modules`) — read this before changing cross-site links or permalinks.

## Quick rules for core contributors

1. **Do not assume** a modules guide lives at ``/guides/<name>/`` just because core uses
   ``/guides/<name>/``. Modules uses ``/guides/.../``, ``/bundles/.../``,
   ``/integrations/.../``, and root paths such as ``/brownfield-engineer/`` depending on the
   page—**always** verify the target file’s `permalink` in `specfact-cli-modules`.
2. **Handoff pages** (see OpenSpec `docs-07-core-handoff-conversion`) must point to the **modules canonical URL** for each topic, with a short summary and prerequisites on core.
3. **Internal core links** must continue to resolve on `docs.specfact.io` per published `permalink` (docs review gate / parity tests).

## Repositories

| Concern | Repository |
| --- | --- |
| Core CLI docs source | `nold-ai/specfact-cli` → `docs/` |
| Modules docs source | `nold-ai/specfact-cli-modules` → `docs/` |
