# Design: Template System Extensions

## Context

The backlog refinement feature requires extensibility for:

1. **Persona-specific templates** - Different roles (product-owner, architect, developer) need different template views
2. **Framework-specific templates** - Different methodologies (Agile, Scrum, SAFe, Kanban) have different work item structures
3. **Iteration/Sprint filtering** - Common DevOps practice to filter by sprint/iteration (ADO, GitHub, Jira, Linear)
4. **Provider extensibility** - Easy addition of new backlog providers (Jira, Linear, SAFe tools)

This design extends the initial template-driven backlog refinement implementation to support these requirements while maintaining backward compatibility.

## Goals / Non-Goals

### Goals

- Support persona-specific template variations (product-owner vs developer views)
- Support framework-specific templates (Scrum vs SAFe vs Kanban)
- Enable iteration/sprint filtering in `backlog refine` command
- Provide extensible architecture for adding new providers (Jira, Linear, etc.)
- Maintain backward compatibility with existing templates
- Support provider-specific template optimizations (ADO vs GitHub vs Jira)

### Non-Goals

- Replacing existing PersonaTemplate system (used for project bundle exports)
- Direct LLM API integration (remains CLI-first, IDE AI copilot orchestration)
- Real-time template synchronization (templates are loaded at command start)
- Template versioning/migration (future enhancement)

## Decisions

### Decision 1: Extend BacklogTemplate Model

**What**: Add `personas`, `framework`, `provider` fields to `BacklogTemplate` model.

**Why**:

- Enables template matching based on persona, framework, and provider
- Maintains backward compatibility (fields are optional with defaults)
- Follows existing pattern (scope, team_id fields already exist)

**Alternatives considered**:

- Separate template types (PersonaTemplate, FrameworkTemplate) - Rejected: Too complex, creates fragmentation
- Template inheritance - Rejected: Over-engineering for current needs
- Template composition - Rejected: Adds unnecessary abstraction

**Implementation**:

```python
class BacklogTemplate(BaseModel):
    # Existing fields...
    personas: list[str] = Field(default_factory=list, ...)
    framework: str | None = Field(default=None, ...)
    provider: str | None = Field(default=None, ...)
```

### Decision 2: Priority-Based Template Resolution

**What**: Implement fallback chain for template matching: provider+framework+persona → provider+framework → framework+persona → framework → provider+persona → persona → provider → default.

**Why**:

- Provides predictable template selection behavior
- Allows fine-grained control (provider+framework+persona) with sensible defaults
- Matches user expectations (most specific match wins)

**Alternatives considered**:

- Single template per combination - Rejected: Too rigid, doesn't allow fallbacks
- User selection only - Rejected: Poor UX, too many choices
- First match wins - Rejected: Unpredictable, doesn't prioritize specificity

**Implementation**:

```python
def resolve_template(
    registry: TemplateRegistry,
    provider: str | None = None,
    framework: str | None = None,
    persona: str | None = None,
    template_id: str | None = None,
) -> BacklogTemplate | None:
    # Priority-based resolution with fallback chain
```

### Decision 3: Template Directory Organization

**What**: Organize template YAML files in `resources/templates/backlog/` with `defaults/`, `frameworks/`, `personas/`, `providers/` subdirectories. Python code (`TemplateRegistry`) remains in `src/specfact_cli/templates/registry.py`.

**Why**:

- Clear separation of concerns (resources vs source code)
- Easy to discover and maintain templates
- Supports extensibility (teams can add custom templates in `.specfact/templates/backlog/`)
- Follows project convention: resources (YAML, prompts, schemas) in `resources/`, code in `src/`

**Alternatives considered**:

- Flat structure with naming convention - Rejected: Hard to navigate, naming conflicts
- Single directory with metadata - Rejected: Less discoverable
- Database storage - Rejected: Over-engineering, YAML files are sufficient

**Structure**:

```bash
templates/
├── defaults/         # Framework-agnostic (current)
├── frameworks/       # Scrum, SAFe, Kanban
├── personas/         # product-owner, architect, developer
└── providers/        # ado, github, jira, linear
```

### Decision 4: Common Filter Support

**What**: Add explicit filter options for common backlog fields (labels/tags, state, assignees) and iteration/sprint fields to `backlog refine` command.

**Why**:

- `BacklogItem` already has `tags`, `assignees`, `state` fields populated from providers
- Current `--search` option is generic and requires provider-specific syntax (e.g., GitHub search syntax)
- Explicit filters provide better UX and cross-provider consistency
- Common DevOps practice (ADO, GitHub, Jira all support sprints/iterations)
- Enables focused refinement workflows (refine items in current sprint, by assignee, by label)

**Alternatives considered**:

- Provider-specific filter syntax only - Rejected: Inconsistent UX, harder to learn
- Single `iteration` field only - Rejected: Doesn't capture sprint vs release distinction
- Complex query language - Rejected: Over-engineering, simple filters sufficient
- Generic `--search` only - Rejected: Requires provider-specific syntax knowledge

**Implementation**:

```python
class BacklogItem(BaseModel):
    # Existing fields...
    tags: list[str]        # Existing - labels/tags
    assignees: list[str]   # Existing - assignees
    state: str            # Existing - state (open, closed, etc.)
    iteration: str | None # Existing - iteration path
    sprint: str | None    # New - sprint identifier
    release: str | None   # New - release identifier

def refine(
    adapter: str,
    # Common filters (BacklogItem already has these fields)
    labels: list[str] | None = None,      # Filter by labels/tags
    state: str | None = None,             # Filter by state (open, closed, etc.)
    assignee: str | None = None,         # Filter by assignee
    # Iteration/sprint filters
    iteration: str | None = None,         # Filter by iteration path
    sprint: str | None = None,            # Filter by sprint
    release: str | None = None,           # Filter by release
    # Template/persona/framework filters
    persona: str | None = None,
    framework: str | None = None,
    # Existing options
    search: str | None = None,            # Generic search (provider-specific syntax)
    # ...
)
```

### Decision 5: Provider-Specific Converter Extensions

**What**: Enhance converters to extract sprint/release from provider-specific formats and normalize to `BacklogItem` fields.

**Why**:

- Providers use different formats (ADO: `System.IterationPath`, GitHub: milestones, Jira: custom fields)
- Normalization enables consistent filtering across providers
- Preserves provider-specific data in `provider_fields` for lossless round-trip

**Alternatives considered**:

- Provider-specific filter implementations - Rejected: Code duplication, harder to maintain
- Generic query translation - Rejected: Too complex, provider APIs differ significantly
- No normalization - Rejected: Inconsistent UX, harder to use

**Implementation**:

```python
def convert_ado_work_item_to_backlog_item(item_data: dict) -> BacklogItem:
    # Extract from System.IterationPath: "Project\\Sprint 1"
    iteration_path = fields.get("System.IterationPath", "")
    sprint = _extract_sprint_from_iteration_path(iteration_path)
    release = _extract_release_from_iteration_path(iteration_path)
    # ...

def convert_github_issue_to_backlog_item(issue_data: dict) -> BacklogItem:
    # Extract from milestones
    milestone = issue_data.get("milestone", {})
    sprint = milestone.get("title", "") if "sprint" in milestone.get("title", "").lower() else None
    # ...
```

## Risks / Trade-offs

### Risk 1: Template Resolution Complexity

**Risk**: Priority-based resolution may be confusing for users.

**Mitigation**:

- Clear documentation with examples
- Log template selection decisions
- Provide `--template` override option

### Risk 2: Backward Compatibility

**Risk**: Existing templates without new fields may break.

**Mitigation**:

- All new fields are optional with defaults
- Existing templates continue to work (treated as framework-agnostic, persona-agnostic)
- Migration guide for updating templates

### Risk 3: Provider Format Variations

**Risk**: Different providers use vastly different sprint/iteration formats.

**Mitigation**:

- Normalize to common fields (`sprint`, `release`)
- Preserve original in `provider_fields` for round-trip
- Document provider-specific extraction patterns
- Converter tests for each provider format

### Risk 4: Template Proliferation

**Risk**: Too many templates may confuse users.

**Mitigation**:

- Start with essential templates (Scrum, SAFe basics)
- Clear naming conventions
- Template discovery/listing commands
- Default templates for common scenarios

## Migration Plan

### Phase 1: Extend Models (Backward Compatible)

1. Add optional fields to `BacklogTemplate` (`personas`, `framework`, `provider`)
2. Add optional fields to `BacklogItem` (`sprint`, `release`)
3. Update existing templates to include new fields (optional, defaults work)
4. **No breaking changes** - Existing code continues to work

### Phase 2: Template Resolution

1. Implement priority-based template resolution logic
2. Update `TemplateRegistry` to support persona/framework/provider filtering
3. Add template resolution tests
4. **Backward compatible** - Default behavior unchanged

### Phase 3: Filtering Support

1. Add common filter options to `backlog refine` command:
   - `--labels` / `--tags` - Filter by labels/tags (BacklogItem.tags already populated)
   - `--state` - Filter by state (BacklogItem.state already populated)
   - `--assignee` - Filter by assignee (BacklogItem.assignees already populated)
   - `--iteration` - Filter by iteration path (BacklogItem.iteration already populated)
   - `--sprint` - Filter by sprint (new field)
   - `--release` - Filter by release (new field)
2. Update converters to extract sprint/release from provider data
3. Update `_fetch_backlog_items` to support all filters (post-fetch filtering for common fields, provider API for iteration/sprint)
4. **Backward compatible** - All filters are optional, `--search` still works

### Phase 4: Framework/Persona Templates

1. Create framework-specific templates (Scrum, SAFe)
2. Create persona-specific templates (product-owner, developer)
3. Update template loading to scan new directories
4. **Additive** - New templates, existing ones unchanged

### Phase 5: Provider Templates

1. Create provider-specific templates (ADO, Jira, Linear)
2. Update converters to use provider templates when available
3. **Additive** - New templates, existing ones unchanged

## Dependencies and Conflicts Resolution

### Dependencies on Other Changes

This change **extends and reuses** components from other pending changes:

1. **`add-generic-backlog-abstraction`** (should be implemented first):
   - **Reuses**: `BacklogAdapter` abstract base interface
   - **Reuses**: `BacklogFilters` dataclass for standardized filtering
   - **Implementation**: Adapter search methods (`search_issues()`, `list_work_items()`) are implemented on `BacklogAdapter` interface

2. **`add-bundle-mapping-strategy`**:
   - **Reuses**: `BundleMapper` for `--auto-bundle` flag
   - **Reuses**: Bundle mapping metadata in `SourceTracking`
   - **Implementation**: Use `BundleMapper.map_bundle()` when `--auto-bundle` is specified

3. **`add-backlog-dependency-analysis-and-commands`** (should be implemented after this):
   - **Coordinates**: Adapter method naming - `search_issues()` wraps `fetch_all_issues()` with filtering
   - **Coordinates**: Model naming - this change's `BacklogItem` is base; graph model should extend it

### Conflict Resolutions

1. **BacklogItem Model Naming**:
   - **Decision**: This change's `BacklogItem` (`src/specfact_cli/models/backlog_item.py`) is the **base domain model**
   - **Purpose**: Unified representation for backlog refinement (title, body, state, metadata, refinement state)
   - **Resolution**: Graph analysis change should extend this model or use `GraphBacklogItem` name
   - **Recommended**: Extend `BacklogItem` with graph-specific fields (parent_id, dependencies, etc.)

2. **Adapter Method Implementation**:
   - **Base Method**: `fetch_all_issues()` (from dependency analysis change)
   - **Wrapper Methods**: `search_issues(query, filters)` and `list_work_items(query, filters)` call `fetch_all_issues()` with filtering
   - **Implementation Pattern**:

     ```python
     def search_issues(self, query: str, filters: BacklogFilters) -> list[BacklogItem]:
         all_items = self.fetch_all_issues()
         return self._apply_filters(all_items, filters)
     ```

3. **Filter Implementation**:
   - **Use**: `BacklogFilters` dataclass from `add-generic-backlog-abstraction`
   - **Mapping**: CLI options (`--labels`, `--state`, etc.) map to `BacklogFilters` fields
   - **Implementation**: Convert CLI options to `BacklogFilters` instance, pass to adapter methods

## Open Questions

1. **Template versioning**: Should templates support versioning (e.g., `user_story_v1` vs `user_story_v2`)? → **Deferred**: Not needed for initial implementation
2. **Template inheritance**: Should templates be able to extend other templates? → **Deferred**: YAGNI, can add later if needed
3. **Dynamic template loading**: Should templates be reloaded during command execution? → **No**: Load at start, simpler and sufficient
4. **Template validation**: Should templates be validated against schema? → **Future**: Add validation in Phase 2 if needed

## Related Documentation

- **TEMPLATE_SYSTEM_DESIGN.md** - Detailed technical design with examples
- **proposal.md** - Change proposal and rationale
- **tasks.md** - Implementation checklist
- **CHANGE_VALIDATION.md** - Conflict analysis and resolution strategies
