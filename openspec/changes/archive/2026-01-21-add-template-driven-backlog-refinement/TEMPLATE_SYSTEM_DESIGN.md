# Template System Design: Personas, Frameworks, and Iteration/Sprint Support

## Overview

This document outlines the design for extending the backlog template system to support:

1. **Persona-specific templates** (product-owner, architect, developer)
2. **Framework-specific templates** (Agile, Scrum, SAFe)
3. **Iteration/Sprint filtering** (common in ADO, DevOps, Jira, Linear)
4. **Extensibility** for future providers (Jira, Linear, SAFe, etc.)

## Current State

### Existing Components

1. **BacklogTemplate Model**: Basic template with `template_id`, `name`, `scope`, `required_sections`, etc.
2. **TemplateRegistry**: Manages templates with corporate/team/user scoping
3. **BacklogItem Model**: Has `iteration` field but no filtering support
4. **PersonaTemplate Model**: Used for project bundle exports, separate from backlog templates

### Current Limitations

1. Templates don't support persona-specific variations
2. No framework-specific templates (Agile vs Scrum vs SAFe)
3. No iteration/sprint filtering in `backlog refine` command
4. No provider-specific template variations (ADO vs GitHub vs Jira)

## Design Goals

1. **Persona Support**: Templates can be persona-specific (product-owner sees different sections than developer)
2. **Framework Support**: Templates can be framework-specific (Scrum user stories vs SAFe features)
3. **Iteration/Sprint Filtering**: Filter backlog items by iteration/sprint path
4. **Provider Extensibility**: Easy to add provider-specific templates and filters
5. **Backward Compatibility**: Existing templates continue to work

## Proposed Architecture

### 1. Extended BacklogTemplate Model

```python
class BacklogTemplate(BaseModel):
    # Existing fields
    template_id: str
    name: str
    description: str
    scope: str  # corporate, team, user
    team_id: str | None
    
    # New fields for persona/framework support
    personas: list[str] = Field(
        default_factory=list,
        description="Personas this template applies to (product-owner, architect, developer). Empty = all personas"
    )
    framework: str | None = Field(
        default=None,
        description="Framework this template is for (agile, scrum, safe, kanban). None = framework-agnostic"
    )
    provider: str | None = Field(
        default=None,
        description="Provider this template is optimized for (github, ado, jira, linear). None = provider-agnostic"
    )
    
    # Existing fields
    required_sections: list[str]
    optional_sections: list[str]
    body_patterns: dict[str, str]
    title_patterns: list[str]
    schema_ref: str | None
```

### 2. Template Organization Structure

**Built-in templates** (included with SpecFact CLI package):

```bash
resources/templates/backlog/
├── defaults/                    # Framework-agnostic templates
│   ├── user_story_v1.yaml
│   ├── defect_v1.yaml
│   ├── spike_v1.yaml
│   └── enabler_v1.yaml
├── frameworks/                  # Framework-specific templates
│   ├── scrum/
│   │   ├── user_story_v1.yaml  # Scrum-specific user story
│   │   └── sprint_backlog_v1.yaml
│   ├── safe/
│   │   ├── feature_v1.yaml     # SAFe feature template
│   │   └── epic_v1.yaml
│   └── kanban/
│       └── work_item_v1.yaml
├── personas/                    # Persona-specific templates
│   ├── product-owner/
│   │   └── user_story_v1.yaml  # PO-focused user story
│   ├── architect/
│   │   └── technical_spec_v1.yaml
│   └── developer/
│       └── task_v1.yaml
└── providers/                   # Provider-specific templates
    ├── ado/
    │   └── work_item_v1.yaml    # ADO-optimized template
    ├── jira/
    │   └── story_v1.yaml
    └── linear/
        └── issue_v1.yaml
```

**Custom templates** (project-specific, overrides built-in):

```bash
.specfact/templates/backlog/
├── defaults/                    # Override built-in defaults
├── frameworks/                  # Override or extend framework templates
├── personas/                    # Override or extend persona templates
└── providers/                   # Override or extend provider templates
```

**Note**: The Python code for template registry (`TemplateRegistry` class) remains in `src/specfact_cli/templates/registry.py`. Only the YAML template files are located in `resources/templates/backlog/`.

### 3. Template Resolution Logic

When selecting a template, the system should:

1. **Match by priority**:
   - Provider-specific + Framework + Persona (highest priority)
   - Provider-specific + Framework
   - Provider-specific + Persona
   - Framework + Persona
   - Framework-specific
   - Persona-specific
   - Provider-specific
   - Default (lowest priority)

2. **Fallback chain**:

   ```
   provider+framework+persona → provider+framework → framework+persona → 
   framework → provider+persona → persona → provider → default
   ```

### 4. Iteration/Sprint Filtering

Extend `BacklogItem` and filtering:

```python
class BacklogItem(BaseModel):
    # Existing fields...
    iteration: str | None = Field(
        default=None,
        description="Iteration/sprint identifier (e.g., 'Sprint 2024-01', 'Iteration\\Sprint 1')"
    )
    sprint: str | None = Field(
        default=None,
        description="Sprint identifier (provider-specific, e.g., 'Sprint 1' for ADO)"
    )
    release: str | None = Field(
        default=None,
        description="Release identifier (e.g., 'Release 1.0', 'R1')"
    )
```

Filter options in `backlog refine`:

```python
def refine(
    adapter: str,
    # Common filters (BacklogItem already has these fields populated)
    labels: list[str] | None = None,   # Filter by labels/tags (BacklogItem.tags)
    state: str | None = None,          # Filter by state (BacklogItem.state)
    assignee: str | None = None,       # Filter by assignee (BacklogItem.assignees)
    # Iteration/sprint filters
    iteration: str | None = None,      # Filter by iteration path (BacklogItem.iteration)
    sprint: str | None = None,        # Filter by sprint (BacklogItem.sprint)
    release: str | None = None,        # Filter by release (BacklogItem.release)
    # Template filters
    persona: str | None = None,        # Filter templates by persona
    framework: str | None = None,      # Filter templates by framework
    # Generic search (provider-specific syntax, e.g., GitHub search, ADO query)
    search: str | None = None,         # Generic search query (existing)
    # ... existing options
)
```

**Note**: Common filters (labels, state, assignees) can use post-fetch filtering since `BacklogItem` already has these fields populated. Iteration/sprint filters may require provider API support or post-fetch filtering depending on provider capabilities.

### 5. Provider-Specific Iteration Handling

Different providers use different iteration/sprint formats:

- **Azure DevOps**: `System.IterationPath` (e.g., "Project\\Sprint 1", "Project\\Release 1\\Sprint 1")
- **GitHub**: Milestones (e.g., "Sprint 1", "Q1 2024")
- **Jira**: Sprints (e.g., "Sprint 1", "Board 1 Sprint 1")
- **Linear**: Cycles (e.g., "Cycle 1", "Q1 2024")

Converter functions should normalize these to `BacklogItem.iteration` and `BacklogItem.sprint`.

## Implementation Plan

### Phase 1: Extend BacklogTemplate Model

1. Add `personas`, `framework`, `provider` fields to `BacklogTemplate`
2. Update template YAML files with new fields
3. Update `TemplateRegistry` to support persona/framework/provider filtering
4. Add template resolution logic with fallback chain

### Phase 2: Add Iteration/Sprint Filtering

1. Add `sprint` and `release` fields to `BacklogItem`
2. Update converters to extract sprint/release from provider data
3. Add filtering options to `backlog refine` command
4. Update `_fetch_backlog_items` to support iteration/sprint filters

### Phase 3: Create Framework-Specific Templates

1. Create `frameworks/` directory structure
2. Create Scrum-specific templates (sprint backlog, etc.)
3. Create SAFe-specific templates (feature, epic, etc.)
4. Update template registry to load from frameworks directory

### Phase 4: Create Persona-Specific Templates

1. Create `personas/` directory structure
2. Create persona-specific template variations
3. Update template resolution to consider persona

### Phase 5: Provider-Specific Templates

1. Create `providers/` directory structure
2. Create provider-optimized templates (ADO, Jira, Linear)
3. Update converters to use provider-specific templates when available

## Example Template YAML

### Framework-Specific Template (Scrum)

```yaml
template_id: scrum_user_story_v1
name: Scrum User Story
description: User story template optimized for Scrum framework
scope: corporate
framework: scrum
personas: [product-owner, developer]
provider: null  # Works with all providers

required_sections:
  - "## As a"
  - "## I want"
  - "## So that"
  - "## Acceptance Criteria"
  - "## Sprint"

optional_sections:
  - "## Story Points"
  - "## Dependencies"
  - "## Notes"

body_patterns:
  as_a: "As a [^,]+"
  i_want: "I want [^,]+"
  so_that: "So that [^,]+"
  sprint: "Sprint [0-9]+"

title_patterns:
  - "^User Story:"
  - "^US-"
```

### Persona-Specific Template (Product Owner)

```yaml
template_id: po_user_story_v1
name: Product Owner User Story
description: User story template focused on business value for Product Owners
scope: corporate
personas: [product-owner]
framework: null
provider: null

required_sections:
  - "## Business Value"
  - "## As a"
  - "## I want"
  - "## So that"
  - "## Acceptance Criteria"
  - "## Priority"

optional_sections:
  - "## Business Metrics"
  - "## User Research"
```

### Provider-Specific Template (ADO)

```yaml
template_id: ado_work_item_v1
name: Azure DevOps Work Item
description: Work item template optimized for Azure DevOps
scope: corporate
provider: ado
framework: null
personas: []

required_sections:
  - "## Description"
  - "## Acceptance Criteria"
  - "## Iteration Path"

optional_sections:
  - "## Area Path"
  - "## Tags"
  - "## Related Work Items"
```

## Usage Examples

### Filter by Sprint

```bash
# Refine items in specific sprint
specfact backlog refine ado \
  --sprint "Sprint 1" \
  --iteration "Project\\Sprint 1"

# Refine items in current iteration
specfact backlog refine ado \
  --iteration "Project\\Current Sprint"
```

### Use Framework-Specific Template

```bash
# Use Scrum-specific template
specfact backlog refine github \
  --framework scrum \
  --template scrum_user_story_v1

# Use SAFe-specific template
specfact backlog refine ado \
  --framework safe \
  --template safe_feature_v1
```

### Use Persona-Specific Template

```bash
# Use Product Owner template
specfact backlog refine github \
  --persona product-owner \
  --template po_user_story_v1

# Use Developer template
specfact backlog refine ado \
  --persona developer \
  --template dev_task_v1
```

### Combined Filters

```bash
# Refine Scrum user stories for Product Owner in Sprint 1
specfact backlog refine ado \
  --framework scrum \
  --persona product-owner \
  --sprint "Sprint 1" \
  --template scrum_user_story_v1
```

## Extensibility for New Providers

### Adding Jira Support

1. **Create Jira converter**:

   ```python
   def convert_jira_issue_to_backlog_item(issue_data: dict) -> BacklogItem:
       # Extract sprint from Jira fields
       sprint = issue_data.get("fields", {}).get("customfield_10020", [])
       # Extract iteration from Jira board
       iteration = issue_data.get("fields", {}).get("customfield_10021")
       # ...
   ```

2. **Create Jira-specific template:

   ```yaml
   template_id: jira_story_v1
   provider: jira
   # ...
   ```

3. **Add Jira iteration/sprint extraction**:

   ```python
   # Jira uses custom fields for sprints
   sprint = fields.get("customfield_10020", [{}])[0].get("name", "")
   ```

### Adding Linear Support

1. **Create Linear converter**:

   ```python
   def convert_linear_issue_to_backlog_item(issue_data: dict) -> BacklogItem:
       # Extract cycle from Linear
       cycle = issue_data.get("cycle", {}).get("name", "")
       # Extract team from Linear
       team = issue_data.get("team", {}).get("name", "")
       # ...
   ```

2. **Create Linear-specific template**:

   ```yaml
   template_id: linear_issue_v1
   provider: linear
   # ...
   ```

## Migration Path

1. **Backward Compatibility**: Existing templates without `personas`, `framework`, `provider` fields continue to work (treated as framework-agnostic, persona-agnostic, provider-agnostic)

2. **Gradual Migration**: Teams can gradually adopt framework/persona-specific templates

3. **Default Behavior**: If no persona/framework specified, system uses default templates

## Testing Strategy

1. **Template Resolution Tests**: Verify fallback chain works correctly
2. **Filter Tests**: Verify iteration/sprint filtering works for each provider
3. **Converter Tests**: Verify sprint/iteration extraction from provider data
4. **Integration Tests**: End-to-end tests with real provider data

## Documentation Updates

1. Update backlog refinement guide with persona/framework filtering
2. Add template customization guide
3. Add provider extension guide
4. Update command reference with new filter options
