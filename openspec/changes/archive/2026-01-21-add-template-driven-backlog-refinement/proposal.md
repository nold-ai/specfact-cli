# Change: Template-Driven Backlog Refinement

## Why

Teams need to enforce corporate backlog templates (user stories, defects, spikes, enablers) while maintaining lossless GitHub/ADO sync and preparing data structures for future conflict detection. Currently, backlog items lack template/schema enforcement, making it difficult to standardize work items and extract structured signals for conflict detection.

This change implements Plan A from the SpecFact Backlog & OpenSpec Implementation Roadmap (2026-01-18), providing AI-assisted backlog refinement with template detection and validation.

**Architecture Note**: SpecFact CLI follows a CLI-first architecture where:

- SpecFact CLI generates prompts/instructions for IDE AI copilots (Cursor, Claude Code, etc.)
- IDE AI copilots execute those instructions using their native LLM
- IDE AI copilots feed results back to SpecFact CLI
- SpecFact CLI validates and processes the results
- SpecFact CLI does NOT directly invoke LLM APIs (OpenAI, Anthropic, etc.)

## What Changes

- **NEW**: `BacklogItem` domain model (`src/specfact_cli/models/backlog_item.py`) - Unified internal representation for all backlog sources
- **NEW**: `TemplateRegistry` (`src/specfact_cli/templates/registry.py`) - Centralized template management with detection and matching (Python code)
- **NEW**: `TemplateDetector` (`src/specfact_cli/backlog/template_detector.py`) - Structural + pattern-based template matching with confidence scoring
- **NEW**: `BacklogAIRefiner` (`src/specfact_cli/backlog/ai_refiner.py`) - Prompt generator and validator for IDE AI copilot refinement (SpecFact CLI does NOT directly invoke LLM APIs)
- **NEW**: `specfact backlog refine` CLI command (`src/specfact_cli/commands/backlog_commands.py`) - Interactive refinement workflow with filtering
- **EXTEND**: `SourceTracking` model (`src/specfact_cli/models/source_tracking.py`) - Add refinement metadata fields (template_id, refinement_confidence, refinement_timestamp, refinement_ai_model)
- **EXTEND**: OpenSpec generation pipeline - Accept template_id and refinement_confidence parameters
- **NEW**: Pre-built templates (`resources/templates/backlog/defaults/`) - user_story_v1, defect_v1, spike_v1, enabler_v1 (YAML files)
- **EXTEND**: `BacklogTemplate` model - Add `personas`, `framework`, `provider` fields for persona/framework/provider-specific templates
- **EXTEND**: `BacklogItem` model - Add `sprint` and `release` fields for iteration/sprint filtering
- **EXTEND**: `specfact backlog refine` command - Add explicit filter options:
  - Common filters: `--labels`/`--tags`, `--state`, `--assignee` (BacklogItem already has these fields)
  - Iteration/sprint filters: `--iteration`, `--sprint`, `--release`
  - Template filters: `--persona`, `--framework`
- **EXTEND**: Template resolution logic - Priority-based template matching with fallback chain (provider+framework+persona → default)
- **NEW**: Template organization structure - Support for `frameworks/`, `personas/`, `providers/` subdirectories in `resources/templates/backlog/` (built-in) and `.specfact/templates/backlog/` (custom)
- **EXTEND**: Backlog converters - Extract and normalize sprint/release data from provider-specific formats (ADO, GitHub, Jira, Linear)

## Documentation Updates

- **NEW**: Guide `docs/guides/backlog-refinement.md` - Complete guide for template-driven backlog refinement workflow
- **UPDATE**: `docs/reference/commands.md` - Add `backlog refine` command documentation
- **UPDATE**: `docs/index.md` - Add backlog refinement guide to documentation index
- **UPDATE**: `docs/_layouts/default.html` - Add backlog refinement to sidebar navigation (if needed)
- **UPDATE**: `docs/guides/devops-adapter-integration.md` - Reference backlog refinement workflow

All documentation files include proper Jekyll frontmatter with `layout: default`, `title`, and `permalink` for permanent URLs.

## Dependencies and Conflicts Resolution

### Dependencies on Other Changes

This change **extends and reuses** components from other pending changes:

1. **`add-generic-backlog-abstraction`** (should be implemented first):
   - **Reuses**: `BacklogAdapter` abstract base interface for adapter methods
   - **Reuses**: `BacklogFilters` dataclass for standardized filtering
   - **Action**: Implement adapter search methods (`search_issues()`, `list_work_items()`) on the new `BacklogAdapter` interface

2. **`add-bundle-mapping-strategy`**:
   - **Reuses**: `BundleMapper` for `--auto-bundle` flag implementation
   - **Reuses**: Bundle mapping metadata in `SourceTracking`
   - **Action**: Use `BundleMapper` when implementing `--auto-bundle` in `backlog refine` command

3. **`add-backlog-dependency-analysis-and-commands`** (should be implemented after this):
   - **Coordinates**: Adapter method naming - uses `fetch_all_issues()` as base, `search_issues()` as wrapper
   - **Coordinates**: Model naming - this change's `BacklogItem` is the base model; graph model should extend it or be named `GraphBacklogItem`
   - **Action**: Ensure graph model extends this change's `BacklogItem` or uses different name

### Conflict Resolutions

1. **BacklogItem Model Naming**:
   - **Decision**: This change's `BacklogItem` (`src/specfact_cli/models/backlog_item.py`) is the **base domain model** for backlog refinement
   - **Resolution**: `add-backlog-dependency-analysis-and-commands` should either:
     - Extend this change's `BacklogItem` with graph-specific fields (recommended)
     - OR use a different name like `GraphBacklogItem` for the graph node model
   - **Action**: Document this decision in both change proposals

2. **Adapter Method Naming**:
   - **Decision**: Use `fetch_all_issues()` as the base method (from `add-backlog-dependency-analysis-and-commands`)
   - **Resolution**: This change's `search_issues()` and `list_work_items()` are wrapper methods that call `fetch_all_issues()` with filtering
   - **Action**: Implement wrapper methods that use `fetch_all_issues()` internally

3. **Filter Implementation**:
   - **Decision**: Use `BacklogFilters` dataclass from `add-generic-backlog-abstraction`
   - **Resolution**: This change's filter options (`--labels`, `--state`, etc.) map to `BacklogFilters` fields
   - **Action**: Use `BacklogFilters` dataclass when implementing filters

## Impact

- **Affected specs**: backlog-refinement, template-detection, ai-refinement
- **Affected code**:
  - `src/specfact_cli/models/backlog_item.py` - Extended with sprint/release fields (base domain model for backlog refinement)
  - `src/specfact_cli/templates/registry.py` - Extended with persona/framework/provider support (Python code)
  - `resources/templates/backlog/` - Template YAML files organized in defaults/, frameworks/, personas/, providers/ subdirectories
  - `src/specfact_cli/backlog/template_detector.py` - Enhanced with template resolution logic
  - `src/specfact_cli/commands/backlog_commands.py` - Extended with iteration/sprint/persona/framework filters
  - `src/specfact_cli/backlog/converter.py` - Enhanced to extract sprint/release from providers
- **Integration points**:
  - Persona workflows (product-owner, architect, developer) - Templates can be persona-specific
  - Agile/Scrum workflows - Framework-specific templates (Scrum, SAFe, Kanban)
  - DevOps adapter integration - Provider-specific templates and iteration/sprint filtering
  - OpenSpec generation - Template metadata preserved in source tracking
  - **Adapter abstraction** - Uses `BacklogAdapter` interface from `add-generic-backlog-abstraction`
  - **Bundle mapping** - Uses `BundleMapper` from `add-bundle-mapping-strategy`
  - **Graph analysis** - Base `BacklogItem` model can be extended for dependency graph analysis

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #122
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/122>
- **Last Synced Status**: proposed
- **Sanitized**: true
