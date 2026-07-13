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
  - src/specfact_cli/requirements/importers.py
  - tests/unit/requirements/test_context_adapter.py
  - tests/unit/requirements/test_upstream_evidence_imports.py
last_reviewed: 2026-07-13
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
- `import_openspec_change(...)` reads a native OpenSpec change folder and
  derives deterministic, source-attributed requirement records.
- `import_speckit_feature(...)` reads a native Spec Kit feature folder through
  the existing scanner and derives deterministic requirement records.
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

Both native import helpers are read-only. They derive stable IDs, preserve
Given/When/Then scenarios as business rules, and record the parsed artifact's
`sha256:` revision. Re-running unchanged input produces the same records.

## Source Compatibility Boundary

Imports are deliberately fail-closed. The core supports only fixture-backed
default Markdown profiles: OpenSpec `spec-driven` (or no declared schema) with
native `Requirement` and `Scenario` headings, and the default Spec Kit
`Feature Specification`/`FR-` template. A custom OpenSpec schema, a Spec Kit
template override/preset/extension root, or unknown required heading produces
an error `unsupported-source-schema` diagnostic and no records from that
source.

The adapter does not infer an upstream CLI version from Markdown or fetch a
live schema during import: native artifacts do not consistently carry a tool
version, and network-dependent parsing would make CI non-reproducible. To add
an upstream format, add a pinned representative fixture, extend the core
profile, and pass its compatibility test before release.

## Import Validation Gates

For OpenSpec and Spec Kit records, `validate_requirement_context(...)` emits
machine-readable findings for:

- `scenario-unverified`: a derived scenario has no test or validation link.
- `stale-import`: an artifact's current bytes no longer match its imported
  `sha256:` revision.
- `source-missing`: an imported artifact is no longer available.
- `ambiguous-mapping`: different imported sources claim the same derived ID.

An error-severity finding makes the paired `requirements validate` command
exit non-zero; the module runtime owns terminal formatting and command flags.
The core helper also preserves `missing-evidence` as a stable, machine-readable
finding code.

When no profile is passed, validation resolves the layered profile from the
organization, repository, and developer-local configuration. The adapter maps
only evidence-backed required fields: `id`, `title`, `acceptance`, and
`trace_links`. Other profile fields are surfaced as
`unsupported-profile-field` advisories rather than requiring OpenSpec or Spec
Kit authors to add SpecFact metadata.

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

After this core change ships, the paired module change will add
`requirements import --from-openspec` and `--from-speckit`; those flags will
delegate entirely to these core helpers.
`requirements import --from-file` remains the generic fallback for records
outside the supported native profiles.

The currently released requirements module does not expose those native-import
flags yet. It remains compatible because it uses only `--from-file`; the paired
module release for #168 will declare a `0.52.0` core compatibility floor before
exposing `--from-openspec` or `--from-speckit`.

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
