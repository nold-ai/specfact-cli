---
layout: default
title: Requirements Context Adapter
permalink: /reference/requirements-context-adapter/
description: Core helpers for importing, normalizing, validating, and inspecting upstream requirement context.
keywords: [requirements, validation, evidence, adapter, projectbundle]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - src/specfact_cli/requirements/context.py
  - tests/unit/requirements/test_context_adapter.py
last_reviewed: 2026-07-08
exempt: false
exempt_reason: ""
---

# Requirements Context Adapter

SpecFact core provides helpers that module runtimes can use to normalize
upstream requirement context into validation evidence. The helpers are designed
for import, validation, and inspection. They do not create a built-in
requirements authoring workflow.

## Core Surface

- `normalize_requirement_records(...)` converts source-attributed mappings or
  `RequirementInput` objects into normalized records and bounded diagnostics.
- `attach_requirements_to_bundle(...)` stores normalized records under the
  existing `requirements.inputs` `ProjectBundle` extension.
- `load_requirements_from_bundle(...)` reads that extension back into
  `RequirementInput` instances.
- `validate_requirement_context(...)` emits a `ValidationReport` for evidence
  usefulness by profile.
- `inspect_requirement_context_coverage(...)` returns machine-readable coverage
  counts for downstream command handlers.
- `analyze_requirement_traceability(...)` reads `requirements.inputs`; when
  callers supply `known_targets`, it also returns deterministic stale-link drift
  findings for evidence consumers.

```python
from specfact_cli.models.requirements import RequirementInput, RequirementSourceReference
from specfact_cli.requirements.context import (
    attach_requirements_to_bundle,
    inspect_requirement_context_coverage,
    normalize_requirement_records,
)

result = normalize_requirement_records(
    [
        {
            "schema_version": "1",
            "requirement_id": "REQ-239",
            "title": "Imported context keeps source attribution",
            "sources": [
                {
                    "source_type": "issue",
                    "locator": "https://github.com/nold-ai/specfact-cli/issues/239",
                }
            ],
        }
    ],
    source_locator="requirements.yaml",
)
```

## Runtime Command Ownership

The `requirements` command group is owned by the requirements module runtime.
Runtime commands should call the core helpers instead of parsing provider
payloads directly inside root CLI code.

## Compatibility Notes

- Requirement inputs must include `schema_version` and at least one source
  reference.
- Invalid imported records produce bounded diagnostics; valid records remain
  usable.
- Enterprise, strict, and enterprise_full_stack validation treat missing
  downstream evidence links as errors. Less strict profiles receive warnings.
- Backlog write-back and interactive requirement authoring remain outside this
  core surface.
- Evidence files, CI flags, terminal rendering, and query commands are owned by
  paired module runtimes rather than core.
