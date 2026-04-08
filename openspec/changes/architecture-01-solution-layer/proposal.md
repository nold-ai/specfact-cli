# Change: Solution Architecture Layer — Derive, Store, Validate

## Why




Architectural decisions live in separate ADRs or Confluence pages with zero programmatic links to requirements or code. This is the layer where the costliest misalignments occur — a wrong architectural choice invalidates entire implementation efforts regardless of code quality. No tool today systematically connects business requirements → architectural decisions → implementation. A solution architecture module that derives, stores, and validates architecture with explicit traceability to requirements closes the biggest blind spot in the end-to-end chain.

## Ownership Alignment (2026-04-08)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: shared architecture schema, namespace extension ownership, and cross-change contracts.
- Bundle-owned follow-up required: the flat `specfact architecture ...` command family and `modules/architecture/...` package structure below are not canonical in the grouped command model.
- Target modules-repo follow-up issue: [#164](https://github.com/nold-ai/specfact-cli-modules/issues/164) in `nold-ai/specfact-cli-modules`
- Implementation MUST NOT proceed from the legacy package layout below until a bundle-owned follow-up defines the correct command surface.

## Module Package Structure

```
modules/architecture/
  module-package.yaml          # name: architecture; commands: architecture derive, validate-coverage, trace
  src/architecture/
    __init__.py
    main.py                    # typer.Typer app — architecture command group
    engine/
      deriver.py               # Derive architecture from requirements (template + AI-assisted)
      coverage_validator.py    # Validate architecture covers all requirements
      trace_builder.py         # Build architecture ↔ requirements traceability links
    models/
      solution_architecture.py # SolutionArchitecture, ComponentSpec, DataFlow, ADR models
    templates/
      microservice.yaml        # Microservice architecture template
      monolith.yaml            # Modular monolith template
      event_driven.yaml        # Event-driven architecture template
    commands/
      derive.py                # specfact architecture derive
      validate_coverage.py     # specfact architecture validate-coverage
      trace.py                 # specfact architecture trace
    storage/
      architecture_store.py    # Read/write .specfact/architecture/*.arch.yaml
```

**`module-package.yaml` declares:**
- `name: architecture`
- `version: 0.1.0`
- `commands: [architecture derive, architecture validate-coverage, architecture trace]`
- `dependencies: [requirements-01-data-model, requirements-02-module-commands]`
- `schema_extensions:` — via arch-07
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## Module Package Structure

```
modules/architecture/
  module-package.yaml          # name: architecture; commands: architecture derive, validate-coverage, trace
  src/architecture/
    __init__.py
    main.py                    # typer.Typer app — architecture command group
    engine/
      deriver.py               # Derive architecture from requirements (template + AI-assisted)
      coverage_validator.py    # Validate architecture covers all requirements
      trace_builder.py         # Build architecture ↔ requirements traceability links
    models/
      solution_architecture.py # SolutionArchitecture, ComponentSpec, DataFlow, ADR models
    templates/
      microservice.yaml        # Microservice architecture template
      monolith.yaml            # Modular monolith template
      event_driven.yaml        # Event-driven architecture template
    commands/
      derive.py                # specfact architecture derive
      validate_coverage.py     # specfact architecture validate-coverage
      trace.py                 # specfact architecture trace
    storage/
      architecture_store.py    # Read/write .specfact/architecture/*.arch.yaml
```

**`module-package.yaml` declares:**
- `name: architecture`
- `version: 0.1.0`
- `commands: [architecture derive, architecture validate-coverage, architecture trace]`
- `dependencies: [requirements-01-data-model, requirements-02-module-commands]`
- `schema_extensions:` — via arch-07
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## What Changes




- **NEW**: Pydantic domain models in `modules/architecture/src/architecture/models/`:
  - `SolutionArchitecture` — architecture ID, requirement IDs (traceability links), components, data flows, ADRs
  - `ComponentSpec` — name, responsibility, business rule IDs (from requirements), integrations
  - `DataFlow` — source, target, data type, protocol
  - `ADR` — ADR ID, decision, rationale (links to architectural constraints from requirements), alternatives considered, tradeoff
- **NEW**: `specfact architecture derive --requirements .specfact/requirements/ --suggest-components --interactive` — derive architecture from requirements using templates and optional AI assistance
- **NEW**: `specfact architecture validate-coverage` — verify every business rule maps to a component, every architectural constraint has an ADR, every component has spec coverage
- **NEW**: `specfact architecture trace --format table|json|markdown` — show traceability matrix: requirements ↔ components ↔ ADRs ↔ specs
- **NEW**: Storage convention: `.specfact/architecture/{architecture_id}.arch.yaml`
- **NEW**: Architecture templates for common patterns (microservice, monolith, event-driven) — profile-aware complexity
- **EXTEND**: `ProjectBundle` extended with optional `architecture` field via arch-07 schema extensions (namespace: `architecture.solution_architecture`)

## Capabilities
### New Capabilities

- `solution-architecture`: Derive, store, and validate solution architecture with explicit traceability to business requirements. Includes component specs, data flows, ADRs, and coverage validation.

### Modified Capabilities

- `data-models`: ProjectBundle extended with architecture field via arch-07 schema extensions


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #240
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/240>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#164
- **Paired Modules Scope**: architecture runtime delivery
- **Last Synced Status**: proposed
- **Sanitized**: false
