---
layout: default
title: Template Customization Guide
permalink: /guides/template-customization/
---

# Template Customization Guide

This guide explains how to create and customize backlog templates for your team's specific needs.

## Template Structure

Templates are YAML files that define the structure and patterns for backlog items. They support:

- **Required sections**: Sections that must be present in refined items
- **Optional sections**: Sections that may be present
- **Pattern matching**: Regex patterns for detecting template matches
- **Framework/Persona/Provider filtering**: Templates can be filtered by framework (Scrum, SAFe), persona (Product Owner, Developer), or provider (GitHub, ADO)

## Template File Format

```yaml
template_id: my_template_v1
name: My Template
description: Description of what this template is for
scope: corporate  # or "team" or "project"
framework: scrum  # Optional: framework filter
personas:
  - product-owner  # Optional: persona filter
provider: github  # Optional: provider filter
required_sections:
  - Section Name 1
  - Section Name 2
optional_sections:
  - Optional Section 1
body_patterns:
  pattern_name: "regex pattern"
title_patterns:
  - "^pattern.*$"
schema_ref: openspec/templates/my_template_v1/
```

## Template Locations

Templates are loaded from the following directories (in priority order):

**Built-in templates** (included with SpecFact CLI):

- Location: `resources/templates/backlog/` (in the SpecFact CLI package)
- **Default templates**: `resources/templates/backlog/defaults/`
- **Framework templates**: `resources/templates/backlog/frameworks/<framework>/`
- **Persona templates**: `resources/templates/backlog/personas/<persona>/`
- **Provider templates**: `resources/templates/backlog/providers/<provider>/`

**Custom templates** (user/team/project-specific):

- Location: `.specfact/templates/backlog/` (in your project repository)
- Same subdirectory structure: `defaults/`, `frameworks/`, `personas/`, `providers/`

## Creating Custom Templates

### Step 1: Choose Template Location

Decide where your template should live in your project's `.specfact/templates/backlog/` directory:

- **Framework-specific**: `.specfact/templates/backlog/frameworks/scrum/`
- **Persona-specific**: `.specfact/templates/backlog/personas/product-owner/`
- **Provider-specific**: `.specfact/templates/backlog/providers/ado/`
- **Default**: `.specfact/templates/backlog/defaults/`

**Note**: Built-in templates are in `resources/templates/backlog/` (package location). Custom templates should be in `.specfact/templates/backlog/` (project location) to override or extend built-in templates.

### Step 2: Create Template File

Create the directory structure and YAML file:

```bash
# Create directory structure
mkdir -p .specfact/templates/backlog/frameworks/scrum

# Create template file
touch .specfact/templates/backlog/frameworks/scrum/my_custom_template_v1.yaml
```

### Step 3: Define Template Structure

Define required and optional sections:

```yaml
template_id: my_custom_template_v1
name: My Custom Template
description: Custom template for my team
scope: team
framework: scrum
required_sections:
  - As a
  - I want
  - So that
  - Acceptance Criteria
optional_sections:
  - Notes
  - Dependencies
body_patterns:
  as_a: "As a [^,]+ I want"
  so_that: "So that [^,]+"
title_patterns:
  - "^.*[Uu]ser [Ss]tory.*$"
```

### Step 4: Test Template

Test your template with the backlog refine command:

```bash
# Test with GitHub adapter (requires repo-owner and repo-name)
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --template my_custom_template_v1 --preview

# Or test with ADO adapter (requires ado-org and ado-project)
specfact backlog refine ado --ado-org "my-org" --ado-project "my-project" --template my_custom_template_v1 --preview
```

## Template Resolution Priority

When multiple templates match, SpecFact CLI uses priority-based resolution:

1. **Provider + Framework + Persona** (highest priority)
2. **Provider + Framework**
3. **Provider + Persona**
4. **Framework + Persona**
5. **Provider only**
6. **Framework only**
7. **Persona only**
8. **Default templates** (lowest priority)

## Best Practices

1. **Version your templates**: Use version suffixes (e.g., `_v1`, `_v2`)
2. **Use descriptive names**: Template IDs should clearly indicate purpose
3. **Test patterns**: Ensure regex patterns match your team's writing style
4. **Document sections**: Add comments explaining required sections
5. **Keep it simple**: Start with minimal required sections, add optional ones later

## Examples

### Scrum User Story Template

```yaml
template_id: scrum_user_story_v1
name: Scrum User Story
framework: scrum
required_sections:
  - As a
  - I want
  - So that
  - Acceptance Criteria
  - Story Points
body_patterns:
  story_points: "Story Points?:\\s*\\d+"
```

### Product Owner Template

```yaml
template_id: product_owner_user_story_v1
name: Product Owner User Story
personas:
  - product-owner
required_sections:
  - Business Value
  - Acceptance Criteria
body_patterns:
  business_value: "Business Value?:\\s*.+"
```

## Related Documentation

- [Backlog Refinement Guide](./backlog-refinement.md) - Using templates for refinement
- [Command Reference](../reference/commands.md) - CLI command options
