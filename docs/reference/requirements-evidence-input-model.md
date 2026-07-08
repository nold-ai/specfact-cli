---
layout: default
title: Requirements Evidence Input Model
permalink: /reference/requirements-evidence-input-model/
description: Normalized requirement input records used by SpecFact validation evidence.
keywords: [requirements, validation, evidence, projectbundle, schema-extension]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - src/specfact_cli/models/requirements.py
  - tests/unit/models/test_requirements.py
last_reviewed: 2026-07-07
exempt: false
exempt_reason: ""
---

# Requirements Evidence Input Model

SpecFact can store normalized requirement input records for validation evidence.
These records point back to upstream sources such as issues, documents,
OpenSpec changes, Spec Kit artifacts, or local files. SpecFact does not become
the requirement authoring system or product-management source of truth.

## Model Surface

Use `RequirementInput` when an adapter or validation step needs a compact
requirement record:

- `requirement_id`: stable requirement identifier
- `schema_version`: requirement input schema version
- `title`: short requirement title
- `sources`: one or more upstream source references
- `business_rules`: optional Given/When/Then rules imported from the source
- `constraints`: optional performance, security, integration, compliance, UX, or operational constraints
- `evidence_links`: optional architecture, spec, code, test, validation, or requirement evidence targets
- `completeness_findings`: advisory profile-aware findings

## ProjectBundle Extension

Requirement inputs are carried through the existing `ProjectBundle.extensions`
field under `requirements.inputs`. This keeps bundles backward compatible:

```python
from specfact_cli.models.requirements import (
    RequirementInput,
    RequirementSourceReference,
    requirements_input_extension_payload,
)

requirement = RequirementInput(
    requirement_id="REQ-123",
    schema_version="1",
    title="Checkout preserves selected currency",
    sources=[
        RequirementSourceReference(
            source_type="issue",
            locator="https://github.com/example/repo/issues/123",
        )
    ],
)

bundle.set_extension(
    "requirements",
    "inputs",
    requirements_input_extension_payload([requirement]),
)
```

## Compatibility Notes

- Missing `schema_version` is invalid for a requirement input record.
- At least one source reference is required so evidence can explain where the
  requirement came from.
- Profile completeness findings are advisory evidence. They can affect
  validation severity without blocking model construction by themselves.
- No requirement authoring commands or backlog write-back behavior are provided
  by this model.
