---
layout: default
title: Custom Field Mapping Guide
permalink: /guides/custom-field-mapping/
---

# Custom Field Mapping Guide

> **Customize ADO field mappings** for your specific Azure DevOps process templates and agile frameworks.

This guide explains how to create and use custom field mapping configurations to adapt SpecFact CLI to your organization's specific Azure DevOps field names and work item types.

## Overview

SpecFact CLI uses **field mappers** to normalize provider-specific field structures (GitHub markdown, ADO fields) into canonical field names that work across all providers. For Azure DevOps, you can customize these mappings to match your specific process template.

### Why Custom Field Mappings?

Different Azure DevOps organizations use different process templates (Scrum, SAFe, Kanban, Basic, or custom templates) with varying field names:

- **Scrum**: Uses `Microsoft.VSTS.Scheduling.StoryPoints`
- **Agile**: Uses `Microsoft.VSTS.Common.StoryPoints`
- **Custom Templates**: May use completely different field names like `Custom.StoryPoints` or `MyCompany.Effort`

Custom field mappings allow you to:

- Map your organization's custom ADO fields to canonical field names
- Support multiple agile frameworks (Scrum, SAFe, Kanban)
- Normalize work item type names across different process templates
- Maintain compatibility with SpecFact CLI's backlog refinement features

## Field Mapping Template Format

Field mapping files are YAML configuration files that define how ADO field names map to canonical field names.

### Basic Structure

```yaml
# Framework identifier (scrum, safe, kanban, agile, default)
framework: scrum

# Field mappings: ADO field name -> canonical field name
field_mappings:
  System.Description: description
  System.AcceptanceCriteria: acceptance_criteria
  Custom.StoryPoints: story_points
  Custom.BusinessValue: business_value
  Custom.Priority: priority
  System.WorkItemType: work_item_type

# Work item type mappings: ADO work item type -> canonical work item type
work_item_type_mappings:
  Product Backlog Item: User Story
  User Story: User Story
  Feature: Feature
  Epic: Epic
  Task: Task
  Bug: Bug
```

### Canonical Field Names

All field mappings must map to these canonical field names:

- **`description`**: Main description/content of the backlog item
- **`acceptance_criteria`**: Acceptance criteria for the item
- **`story_points`**: Story points estimate (0-100 range, Scrum/SAFe)
- **`business_value`**: Business value estimate (0-100 range, Scrum/SAFe)
- **`priority`**: Priority level (1-4 range, 1=highest, all frameworks)
- **`value_points`**: Value points (SAFe-specific, calculated from business_value / story_points)
- **`work_item_type`**: Work item type (Epic, Feature, User Story, Task, Bug, etc., framework-aware)

### Field Validation Rules

- **Story Points**: Must be in range 0-100 (automatically clamped)
- **Business Value**: Must be in range 0-100 (automatically clamped)
- **Priority**: Must be in range 1-4, where 1=highest (automatically clamped)
- **Value Points**: Automatically calculated as `business_value / story_points` if both are present

## Framework-Specific Examples

### Scrum Process Template

```yaml
framework: scrum

field_mappings:
  System.Description: description
  System.AcceptanceCriteria: acceptance_criteria
  Microsoft.VSTS.Scheduling.StoryPoints: story_points
  Microsoft.VSTS.Common.BusinessValue: business_value
  Microsoft.VSTS.Common.Priority: priority
  System.WorkItemType: work_item_type
  System.IterationPath: iteration
  System.AreaPath: area

work_item_type_mappings:
  Product Backlog Item: User Story
  Bug: Bug
  Task: Task
  Epic: Epic
```

### SAFe Process Template

```yaml
framework: safe

field_mappings:
  System.Description: description
  System.AcceptanceCriteria: acceptance_criteria
  Microsoft.VSTS.Scheduling.StoryPoints: story_points
  Microsoft.VSTS.Common.BusinessValue: business_value
  Microsoft.VSTS.Common.Priority: priority
  System.WorkItemType: work_item_type
  # SAFe-specific fields
  Microsoft.VSTS.Common.ValueArea: value_points

work_item_type_mappings:
  Epic: Epic
  Feature: Feature
  User Story: User Story
  Task: Task
  Bug: Bug
```

### Kanban Process Template

```yaml
framework: kanban

field_mappings:
  System.Description: description
  System.AcceptanceCriteria: acceptance_criteria
  Microsoft.VSTS.Common.Priority: priority
  System.WorkItemType: work_item_type
  System.State: state
  # Kanban doesn't require story points, but may have them
  Microsoft.VSTS.Scheduling.StoryPoints: story_points

work_item_type_mappings:
  User Story: User Story
  Task: Task
  Bug: Bug
  Feature: Feature
  Epic: Epic
```

### Custom Process Template

```yaml
framework: default

field_mappings:
  System.Description: description
  Custom.AcceptanceCriteria: acceptance_criteria
  Custom.StoryPoints: story_points
  Custom.BusinessValue: business_value
  Custom.Priority: priority
  System.WorkItemType: work_item_type

work_item_type_mappings:
  Product Backlog Item: User Story
  Requirement: User Story
  Issue: Bug
```

## Using Custom Field Mappings

### Method 1: CLI Parameter (Recommended)

Use the `--custom-field-mapping` option when running the refine command:

```bash
specfact backlog refine ado \
  --ado-org my-org \
  --ado-project my-project \
  --custom-field-mapping /path/to/ado_custom.yaml \
  --state Active
```

The CLI will:
1. Validate the file exists and is readable
2. Validate the YAML format and schema
3. Set it as an environment variable for the converter to use
4. Display a success message if validation passes

### Method 2: Auto-Detection

Place your custom mapping file at:

```
.specfact/templates/backlog/field_mappings/ado_custom.yaml
```

SpecFact CLI will automatically detect and use this file if no `--custom-field-mapping` parameter is provided.

### Method 3: Environment Variable

Set the `SPECFACT_ADO_CUSTOM_MAPPING` environment variable:

```bash
export SPECFACT_ADO_CUSTOM_MAPPING=/path/to/ado_custom.yaml
specfact backlog refine ado --ado-org my-org --ado-project my-project
```

**Priority Order**:
1. CLI parameter (`--custom-field-mapping`) - highest priority
2. Environment variable (`SPECFACT_ADO_CUSTOM_MAPPING`)
3. Auto-detection from `.specfact/templates/backlog/field_mappings/ado_custom.yaml`

## Default Field Mappings

If no custom mapping is provided, SpecFact CLI uses default mappings that work with most standard ADO process templates:

- `System.Description` → `description`
- `System.AcceptanceCriteria` → `acceptance_criteria`
- `Microsoft.VSTS.Common.StoryPoints` → `story_points`
- `Microsoft.VSTS.Scheduling.StoryPoints` → `story_points` (alternative)
- `Microsoft.VSTS.Common.BusinessValue` → `business_value`
- `Microsoft.VSTS.Common.Priority` → `priority`
- `System.WorkItemType` → `work_item_type`

Custom mappings **override** defaults. If a field is mapped in your custom file, it will be used instead of the default.

## Built-in Template Files

SpecFact CLI includes built-in field mapping templates for common frameworks:

- **`ado_default.yaml`**: Generic mappings for most ADO templates
- **`ado_scrum.yaml`**: Scrum-specific mappings
- **`ado_agile.yaml`**: Agile-specific mappings
- **`ado_safe.yaml`**: SAFe-specific mappings
- **`ado_kanban.yaml`**: Kanban-specific mappings

These are located in `resources/templates/backlog/field_mappings/` and can be used as reference when creating your custom mappings.

## Validation and Error Handling

### File Validation

The CLI validates custom mapping files before use:

- **File Existence**: File must exist and be readable
- **YAML Format**: File must be valid YAML
- **Schema Validation**: File must match `FieldMappingConfig` schema (Pydantic validation)

### Common Errors

**File Not Found**:
```
Error: Custom field mapping file not found: /path/to/file.yaml
```

**Invalid YAML**:
```
Error: Invalid custom field mapping file: YAML parsing error
```

**Invalid Schema**:
```
Error: Invalid custom field mapping file: Field 'field_mappings' must be a dict
```

## Best Practices

1. **Start with Defaults**: Use the built-in template files as a starting point
2. **Test Incrementally**: Add custom mappings one at a time and test
3. **Version Control**: Store custom mapping files in your repository
4. **Document Custom Fields**: Document any custom ADO fields your organization uses
5. **Framework Alignment**: Set the `framework` field to match your agile framework
6. **Work Item Type Mapping**: Map your organization's work item types to canonical types

## Integration with Backlog Refinement

Custom field mappings work seamlessly with backlog refinement:

1. **Field Extraction**: Custom mappings are used when extracting fields from ADO work items
2. **Field Display**: Extracted fields (story_points, business_value, priority) are displayed in refinement output
3. **Field Validation**: Fields are validated according to canonical field rules (0-100 for story_points, 1-4 for priority)
4. **Writeback**: Fields are mapped back to ADO format using the same custom mappings

## Troubleshooting

### Fields Not Extracted

If fields are not being extracted:

1. **Check Field Names**: Verify the ADO field names in your mapping match exactly (case-sensitive)
2. **Check Work Item Type**: Some fields may only exist for certain work item types
3. **Test with Defaults**: Try without custom mapping to see if defaults work
4. **Check Logs**: Enable verbose logging to see field extraction details

### Validation Errors

If you see validation errors:

1. **Check YAML Syntax**: Use a YAML validator to check syntax
2. **Check Schema**: Ensure all required fields are present
3. **Check Field Types**: Ensure field values match expected types (strings, integers)

### Work Item Type Not Mapped

If work item types are not being normalized:

1. **Add to `work_item_type_mappings`**: Add your work item type to the mappings section
2. **Check Case Sensitivity**: Work item type names are case-sensitive
3. **Use Default**: If not mapped, the original work item type is used

## Related Documentation

- [Backlog Refinement Guide](./backlog-refinement.md) - Complete guide to backlog refinement
- [ADO Adapter Documentation](../adapters/backlog-adapter-patterns.md) - ADO adapter patterns
- [Field Mapper API Reference](../reference/architecture.md) - Technical architecture details
