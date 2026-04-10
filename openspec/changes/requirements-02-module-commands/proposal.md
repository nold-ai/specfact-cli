# Change: Requirements Module — Extract, Author, Validate Commands

## Why

Even with a formal data model (requirements-01), there are no CLI commands for working with business requirements. Teams need to extract structured requirements from existing backlog items (reverse-engineer from AC text), author new requirements with profile-aware templates, and validate requirements completeness — all from the terminal. This module is the primary user-facing entry point for the upstream traceability chain.

## Ownership Alignment (2026-04-08)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: shared requirements contracts, schemas, and adapter/interface deltas needed by downstream owners.
- Bundle-owned follow-up required: the user-facing command surface proposed below cannot remain a flat `specfact requirements ...` family and cannot be implemented in `specfact-cli` core as described.
- Target modules-repo follow-up issue: [#165](https://github.com/nold-ai/specfact-cli-modules/issues/165) in `nold-ai/specfact-cli-modules`
- Implementation MUST NOT proceed from the legacy `modules/requirements/...` package structure below until a paired bundle-owned follow-up change defines the canonical grouped command home.

## Module Package Structure

```
modules/requirements/
  module-package.yaml          # name: requirements; commands: requirements extract, author, validate, list
  src/requirements/
    __init__.py
    main.py                    # typer.Typer app — requirements command group
    engine/
      extractor.py             # Parse AC text from backlog items → structured BusinessRequirement
      author.py                # Interactive + template-based requirement authoring
      validator.py             # Validate requirements completeness per profile schema
      coverage.py              # Compute requirement coverage (arch/spec/code/test links)
    templates/
      story.yaml               # User story template (As_a, I_want, So_that + business rules)
      feature.yaml             # Feature template (outcome, rules, constraints, UX)
      spike.yaml               # Spike template (hypothesis, success criteria)
    commands/
      extract.py               # specfact requirements extract --from-backlog <adapter>
      author.py                # specfact requirements author --template <type>
      validate.py              # specfact requirements validate
      list.py                  # specfact requirements list --show-coverage
```

**`module-package.yaml` declares:**

- `name: requirements`
- `version: 0.1.0`
- `commands: [requirements extract, requirements author, requirements validate, requirements list]`
- `dependencies: [requirements-01-data-model, arch-07-schema-extension-system]` (needs requirements models and schema extensions)
- `schema_extensions:` — via arch-07
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## Module Package Structure

```
modules/requirements/
  module-package.yaml          # name: requirements; commands: requirements extract, author, validate, list
  src/requirements/
    __init__.py
    main.py                    # typer.Typer app — requirements command group
    engine/
      extractor.py             # Parse AC text from backlog items → structured BusinessRequirement
      author.py                # Interactive + template-based requirement authoring
      validator.py             # Validate requirements completeness per profile schema
      coverage.py              # Compute requirement coverage (arch/spec/code/test links)
    templates/
      story.yaml               # User story template (As_a, I_want, So_that + business rules)
      feature.yaml             # Feature template (outcome, rules, constraints, UX)
      spike.yaml               # Spike template (hypothesis, success criteria)
    commands/
      extract.py               # specfact requirements extract --from-backlog <adapter>
      author.py                # specfact requirements author --template <type>
      validate.py              # specfact requirements validate
      list.py                  # specfact requirements list --show-coverage
```

**`module-package.yaml` declares:**

- `name: requirements`
- `version: 0.1.0`
- `commands: [requirements extract, requirements author, requirements validate, requirements list]`
- `dependencies: [requirements-01-data-model, arch-07-schema-extension-system]` (needs requirements models and schema extensions)
- `schema_extensions:` — via arch-07
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## What Changes

- **NEW**: Requirements module in `modules/requirements/` implementing `ModuleIOContract`:
  - `import_to_bundle`: Extract requirements from backlog items into ProjectBundle
  - `export_from_bundle`: Generate requirements documents (YAML, Markdown) from bundle
  - `sync_with_bundle`: Bidirectional sync between requirements and backlog (read-only in v1)
  - `validate_bundle`: Check requirements completeness per profile schema
- **NEW**: `specfact requirements extract --from-backlog <adapter> --project <org/repo>` — parse acceptance criteria from existing backlog items, infer business rules, generate `.specfact/requirements/*.req.yaml` files
- **NEW**: `specfact requirements author --template story|feature|spike --story STORY-123` — interactive requirement authoring with profile-aware templates (solo gets 3 fields, enterprise gets full schema)
- **NEW**: `specfact requirements validate --requirements-dir .specfact/requirements/` — validate completeness against active profile's required fields
- **NEW**: `specfact requirements list --show-coverage` — list requirements with traceability coverage status (architecture %, spec %, code %, test %)
- **NEW**: Profile-aware templates: solo requires only As_a/I_want/So_that; startup adds Business_outcome + Business_rules; mid-size uses org-defined schema; enterprise adds Regulatory_reference + Risk_owner

## Capabilities

### New Capabilities

- `requirements-module`: CLI commands for extracting requirements from backlog items, authoring with profile-aware templates, validating completeness per profile schema, and listing with traceability coverage status. Implements ModuleIOContract for requirements lifecycle.

### Modified Capabilities

- `module-io-contract`: New implementation of ModuleIOContract for the requirements domain (import from backlog, export to YAML/Markdown, sync, validate)
- `backlog-adapter`: Extended with requirement extraction hooks — adapters provide raw AC text, extractor parses into structured BusinessRequirement models

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #239
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/239>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#165
- **Paired Modules Scope**: requirements runtime commands
- **Last Synced Status**: proposed
- **Sanitized**: false
