# Change: Traceability Index & Orphan Detection

## Why




As the number of requirements, specs, and code modules grows, manually tracking traceability becomes impossible. Teams need a fast, queryable index that maps every artifact to its upstream/downstream counterparts — and actively detects orphans (artifacts with broken or missing links). This index is the backbone for the full-chain validation, coverage dashboards, and ceremony enrichment. Without it, traceability is a write-once artifact that decays the moment someone adds a new endpoint without linking it.

## Ownership Alignment (2026-04-08)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: shared traceability index contracts and artifact linkage semantics.
- Bundle-owned follow-up required: the flat `specfact trace ...` command family and `modules/trace/...` package structure below are not canonical in the grouped command model.
- Target modules-repo follow-up issue: [#170](https://github.com/nold-ai/specfact-cli-modules/issues/170) in `nold-ai/specfact-cli-modules`
- Implementation MUST NOT proceed from the legacy package layout below until the bundle-owned query/reporting surface is defined separately.

## Module Package Structure

```
modules/trace/
  module-package.yaml          # name: trace; commands: trace index, trace show, trace orphans, trace matrix
  src/trace/
    __init__.py
    main.py                    # typer.Typer app — trace command group
    engine/
      indexer.py               # Build/rebuild traceability index from all layers
      query.py                 # Query index by requirement, spec, code, or test ID
      orphan_detector.py       # Find artifacts with broken or missing upstream/downstream links
      matrix_generator.py      # Generate traceability matrix (markdown, CSV, JSON)
    models/
      trace_index.py           # TraceIndex, TraceEntry, OrphanReport models
    storage/
      index_store.py           # Read/write .specfact/trace/index.json (generated, not authored)
    commands/
      index.py                 # specfact trace index --rebuild
      show.py                  # specfact trace show <id>
      orphans.py               # specfact trace orphans
      matrix.py                # specfact trace matrix --format markdown|csv|json
```

**`module-package.yaml` declares:**
- `name: trace`
- `version: 0.1.0`
- `commands: [trace index, trace show, trace orphans, trace matrix]`
- `dependencies: [requirements-02-module-commands, architecture-01-solution-layer]`
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## Module Package Structure

```
modules/trace/
  module-package.yaml          # name: trace; commands: trace index, trace show, trace orphans, trace matrix
  src/trace/
    __init__.py
    main.py                    # typer.Typer app — trace command group
    engine/
      indexer.py               # Build/rebuild traceability index from all layers
      query.py                 # Query index by requirement, spec, code, or test ID
      orphan_detector.py       # Find artifacts with broken or missing upstream/downstream links
      matrix_generator.py      # Generate traceability matrix (markdown, CSV, JSON)
    models/
      trace_index.py           # TraceIndex, TraceEntry, OrphanReport models
    storage/
      index_store.py           # Read/write .specfact/trace/index.json (generated, not authored)
    commands/
      index.py                 # specfact trace index --rebuild
      show.py                  # specfact trace show <id>
      orphans.py               # specfact trace orphans
      matrix.py                # specfact trace matrix --format markdown|csv|json
```

**`module-package.yaml` declares:**
- `name: trace`
- `version: 0.1.0`
- `commands: [trace index, trace show, trace orphans, trace matrix]`
- `dependencies: [requirements-02-module-commands, architecture-01-solution-layer]`
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## What Changes




- **NEW**: Trace module in `modules/trace/` with auto-maintained traceability index
- **NEW**: `specfact trace index --rebuild` — scan all requirements, architecture, specs, code, and test artifacts to build a comprehensive traceability index stored at `.specfact/trace/index.json`
- **NEW**: `specfact trace show REQ-123` — query upstream/downstream links for any artifact (requirement, component, spec operation, code module, test)
- **NEW**: `specfact trace orphans` — detect orphaned artifacts: specs with no requirement, code with no spec, requirements with no architecture coverage, tests with no code reference
- **NEW**: `specfact trace matrix --format markdown|csv|json` — export traceability matrix showing the full chain for each requirement
- **NEW**: Incremental index updates — when a single file changes, update only affected trace entries (not full rebuild)
- **NEW**: TraceIndex model with bidirectional links: each entry stores both `upstream_refs` and `downstream_refs`

## Capabilities
### New Capabilities

- `traceability-index`: Auto-maintained bidirectional traceability index mapping requirements → architecture → specs → code → tests, with orphan detection, incremental updates, and matrix export in markdown/CSV/JSON.

### Modified Capabilities

(none)


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #242
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/242>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#170
- **Paired Modules Scope**: traceability runtime queries and orphan detection
- **Last Synced Status**: proposed
- **Sanitized**: false
