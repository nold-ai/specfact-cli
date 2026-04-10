# Change: Bundle Mapper — Intelligent Spec-to-Bundle Mapping Strategy

## Why

Teams need intelligent spec-to-bundle assignment with confidence scoring and user confirmation to prevent mis-bundled specs. Currently, bundle assignment is manual or based on simple heuristics, leading to specs landing in wrong bundles and making conflict detection unreliable.

This change establishes the **`bundle-mapper` module** — providing confident, history-aware spec-to-bundle assignment with interactive review for ambiguous mappings. Per the SpecFact Backlog & OpenSpec Implementation Roadmap (2026-01-18), this implements Plan C with three confidence signals.

## Module Package Structure

```
modules/bundle-mapper/
  module-package.yaml          # name: bundle-mapper; enhances backlog refine/import --auto-bundle
  src/bundle_mapper/
    __init__.py
    mapper/
      engine.py                # BundleMapper — confidence-based mapping with three signals
      history.py               # Mapping history persistence (.specfact/config.yaml)
    models/
      bundle_mapping.py        # BundleMapping (bundle_id, confidence, candidates, explanation)
    commands/
      refine_hook.py           # --auto-bundle flag integration for backlog refine
      import_hook.py           # --auto-bundle flag integration for backlog import
    ui/
      interactive.py           # User prompts with confidence visualization (Rich)
```

**`module-package.yaml` declares:**

- `name: bundle-mapper`
- `version: 0.1.0`
- `commands: []` (no top-level commands; enhances existing `backlog refine/import` via hooks)
- `schema_extensions:` — see arch-07 section below
- `dependencies: []`
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## Module Package Structure

```
modules/bundle-mapper/
  module-package.yaml          # name: bundle-mapper; enhances backlog refine/import --auto-bundle
  src/bundle_mapper/
    __init__.py
    mapper/
      engine.py                # BundleMapper — confidence-based mapping with three signals
      history.py               # Mapping history persistence (.specfact/config.yaml)
    models/
      bundle_mapping.py        # BundleMapping (bundle_id, confidence, candidates, explanation)
    commands/
      refine_hook.py           # --auto-bundle flag integration for backlog refine
      import_hook.py           # --auto-bundle flag integration for backlog import
    ui/
      interactive.py           # User prompts with confidence visualization (Rich)
```

**`module-package.yaml` declares:**

- `name: bundle-mapper`
- `version: 0.1.0`
- `commands: []` (no top-level commands; enhances existing `backlog refine/import` via hooks)
- `schema_extensions:` — see arch-07 section below
- `dependencies: []`
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## What Changes

- **NEW**: `BundleMapper` engine in `modules/bundle-mapper/src/bundle_mapper/mapper/engine.py` — confidence-based mapping with three signals: explicit labels, historical patterns, content similarity.
- **NEW**: `BundleMapping` model in `modules/bundle-mapper/src/bundle_mapper/models/bundle_mapping.py` — result model with `bundle_id`, `confidence`, `candidates`, `explanation`.
- **NEW**: Mapping history persistence in `modules/bundle-mapper/src/bundle_mapper/mapper/history.py` — auto-learned rules from user confirmations stored in `.specfact/config.yaml`.
- **NEW**: Interactive mapping UI in `modules/bundle-mapper/src/bundle_mapper/ui/interactive.py` — user prompts with confidence visualization using Rich.
- **EXTEND**: `--auto-bundle` flag for `backlog refine` and `backlog import` commands — when `bundle-mapper` module is loaded, these flags activate bundle mapping. No changes to core commands; added via command extension hooks declared in `module-package.yaml`.
- **EXTEND** (arch-07 schema extensions): Register `bundle_mapper.mapping_metadata` extension on `SourceTracking` model via `module-package.yaml`:
  - `bundle_mapper.bundle_id` — assigned bundle
  - `bundle_mapper.mapping_confidence` — confidence score (0.0 - 1.0)
  - `bundle_mapper.mapping_method` — method used (label/history/similarity)
  - `bundle_mapper.mapping_timestamp` — when mapping was made
  - Access via `source_tracking.get_extension("bundle_mapper", "mapping_confidence")` — **no direct modification of `SourceTracking` Pydantic model**.
- **EXTEND**: OpenSpec generation pipeline accepts `BundleMapping` parameter and records mapping decisions via schema extension.

## Capabilities

- **bundle-mapper**: `BundleMapper` with three confidence signals (labels, history, similarity); `BundleMapping` result model; mapping history persistence (auto-learned rules); interactive UI with confidence visualization; `--auto-bundle` flag for `backlog refine/import`; arch-07 SourceTracking extensions for mapping metadata.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #121
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/121>
- **Last Synced Status**: proposed
- **Sanitized**: false
