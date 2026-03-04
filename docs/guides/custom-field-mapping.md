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

## Discovering Available ADO Fields

Before creating custom field mappings, you need to know which fields are available in your Azure DevOps project. There are two ways to discover available fields:

### Method 1: Using Interactive Mapping Command (Recommended)

The easiest way to discover and map ADO fields is using the interactive mapping command:

```bash
specfact backlog map-fields --ado-org myorg --ado-project myproject
```

This command will:

1. Fetch all available fields from your Azure DevOps project
2. Filter out system-only fields automatically
3. Pre-populate default mappings from `AdoFieldMapper.DEFAULT_FIELD_MAPPINGS`
4. Prefer `Microsoft.VSTS.Common.*` fields over `System.*` fields for better compatibility
5. Use regex/fuzzy matching to suggest potential matches when no default exists
6. Display an interactive menu with arrow-key navigation (↑↓ to navigate, Enter to select)
7. Pre-select the best match (existing custom > default > fuzzy match > "<no mapping>")
8. Guide you through mapping ADO fields to canonical field names
9. Validate the mapping before saving
10. Save the mapping to `.specfact/templates/backlog/field_mappings/ado_custom.yaml`

**Interactive Menu Navigation:**

- Use **↑** (Up arrow) and **↓** (Down arrow) to navigate through available ADO fields
- Press **Enter** to select a field
- The menu shows all available ADO fields in a scrollable list
- Default mappings are pre-selected automatically
- Fuzzy matching suggests relevant fields when no default mapping exists

**Example Output:**

```bash
Fetching fields from Azure DevOps...
✓ Loaded existing mapping from .specfact/templates/backlog/field_mappings/ado_custom.yaml

Interactive Field Mapping
Map ADO fields to canonical field names.

Description (canonical: description)
  Current mapping: System.Description

  Available ADO fields:
  > System.Description (Description)                    [default - pre-selected]
    Microsoft.VSTS.Common.AcceptanceCriteria (Acceptance Criteria)
    Microsoft.VSTS.Common.StoryPoints (Story Points)
    Microsoft.VSTS.Scheduling.StoryPoints (Story Points)
    ...
    <no mapping>
```

### Method 2: Using ADO REST API

You can also discover available fields directly from the Azure DevOps REST API:

**Step 1: Get your Azure DevOps PAT (Personal Access Token)**

- Go to: `https://dev.azure.com/{org}/_usersSettings/tokens`
- Create a new token with "Work Items (Read)" permission

**Step 2: Fetch fields using curl or HTTP client**

```bash
# Replace {org}, {project}, and {token} with your values
curl -u ":{token}" \
  "https://dev.azure.com/{org}/{project}/_apis/wit/fields?api-version=7.1" \
  | jq '.value[] | {referenceName: .referenceName, name: .name}'
```

**Step 3: Identify field names from API response**

The API returns a JSON array with field information:

```json
{
  "value": [
    {
      "referenceName": "System.Description",
      "name": "Description",
      "type": "html"
    },
    {
      "referenceName": "Microsoft.VSTS.Common.AcceptanceCriteria",
      "name": "Acceptance Criteria",
      "type": "html"
    }
  ]
}
```

**Common ADO Field Names by Process Template:**

- **Scrum**: `Microsoft.VSTS.Scheduling.StoryPoints`, `System.AcceptanceCriteria`
- **Agile**: `Microsoft.VSTS.Common.StoryPoints`, `System.AcceptanceCriteria`
- **SAFe**: `Microsoft.VSTS.Scheduling.StoryPoints`, `Microsoft.VSTS.Common.AcceptanceCriteria`
- **Custom Templates**: May use `Custom.*` prefix (e.g., `Custom.StoryPoints`, `Custom.AcceptanceCriteria`)

**Note**: The field `Microsoft.VSTS.Common.AcceptanceCriteria` is commonly used in many ADO process templates, while `System.AcceptanceCriteria` is less common. SpecFact CLI supports both by default and **prefers `Microsoft.VSTS.Common.*` fields over `System.*` fields** when multiple alternatives exist for better compatibility across different ADO process templates.

## Using Custom Field Mappings

### Method 1: Interactive Mapping Command (Recommended)

Use the interactive mapping command to create and update field mappings:

```bash
specfact backlog map-fields --ado-org myorg --ado-project myproject
```

This command:

- Fetches available fields from your ADO project
- Shows current mappings (if they exist)
- Guides you through mapping each canonical field
- Validates the mapping before saving
- Saves to `.specfact/templates/backlog/field_mappings/ado_custom.yaml`

**Options:**

- `--ado-org`: Azure DevOps organization (required)
- `--ado-project`: Azure DevOps project (required)
- `--ado-token`: Azure DevOps PAT (optional, uses token resolution priority: explicit > env var > stored token)
- `--reset`: Reset custom field mapping to defaults (deletes `ado_custom.yaml` and restores default mappings)
- `--ado-base-url`: Azure DevOps base URL (defaults to `https://dev.azure.com`)

**Token Resolution:**

The command automatically uses stored tokens from `specfact backlog auth azure-devops` if available. Token resolution priority:

1. Explicit `--ado-token` parameter
2. `AZURE_DEVOPS_TOKEN` environment variable
3. Stored token via `specfact backlog auth azure-devops`
4. Expired stored token (with warning and options to refresh)

**Examples:**

```bash
# Uses stored token automatically (recommended)
specfact backlog map-fields --ado-org myorg --ado-project myproject

# Override with explicit token
specfact backlog map-fields --ado-org myorg --ado-project myproject --ado-token your_token_here

# Reset to default mappings
specfact backlog map-fields --ado-org myorg --ado-project myproject --reset
```

**Automatic Usage:**

After creating a custom mapping, it is **automatically used** by all subsequent backlog operations in that directory. No restart or additional configuration needed. The `AdoFieldMapper` automatically detects and loads `.specfact/templates/backlog/field_mappings/ado_custom.yaml` if it exists.

### Method 2: CLI Parameter

Use the `--custom-field-mapping` option when running the refine command:

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

```bash
.specfact/templates/backlog/field_mappings/ado_custom.yaml
```

SpecFact CLI will automatically detect and use this file if no `--custom-field-mapping` parameter is provided.

### Method 3: Manually Creating Field Mapping Files

You can also create field mapping files manually by editing YAML files directly.

**Step 1: Create the directory structure**

```bash
mkdir -p .specfact/templates/backlog/field_mappings
```

**Step 2: Create `ado_custom.yaml` file**

Create a new file `.specfact/templates/backlog/field_mappings/ado_custom.yaml` with the following structure:

```yaml
# Framework identifier (scrum, safe, kanban, agile, default)
framework: default

# Field mappings: ADO field name -> canonical field name
field_mappings:
  System.Description: description
  Microsoft.VSTS.Common.AcceptanceCriteria: acceptance_criteria
  Microsoft.VSTS.Scheduling.StoryPoints: story_points
  Microsoft.VSTS.Common.BusinessValue: business_value
  Microsoft.VSTS.Common.Priority: priority
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

**Step 3: Validate the YAML file**

Use a YAML validator or test with SpecFact CLI:

```bash
# The refine command will validate the file automatically
specfact backlog refine ado --ado-org myorg --ado-project myproject --state Active
```

**YAML Schema Reference:**

- **`framework`** (string, optional): Framework identifier (`scrum`, `safe`, `kanban`, `agile`, `default`)
- **`field_mappings`** (dict, required): Mapping from ADO field names to canonical field names
  - Keys: ADO field reference names (e.g., `System.Description`, `Microsoft.VSTS.Common.AcceptanceCriteria`)
  - Values: Canonical field names (`description`, `acceptance_criteria`, `story_points`, `business_value`, `priority`, `work_item_type`)
- **`work_item_type_mappings`** (dict, optional): Mapping from ADO work item types to canonical work item types
  - Keys: ADO work item type names (e.g., `Product Backlog Item`, `User Story`)
  - Values: Canonical work item type names (e.g., `User Story`, `Feature`, `Epic`)

**Examples for Different ADO Process Templates:**

**Scrum Template:**

```yaml
framework: scrum
field_mappings:
  System.Description: description
  System.AcceptanceCriteria: acceptance_criteria
  Microsoft.VSTS.Common.AcceptanceCriteria: acceptance_criteria  # Alternative
  Microsoft.VSTS.Scheduling.StoryPoints: story_points
  Microsoft.VSTS.Common.BusinessValue: business_value
  Microsoft.VSTS.Common.Priority: priority
  System.WorkItemType: work_item_type
```

**Agile Template:**

```yaml
framework: agile
field_mappings:
  System.Description: description
  Microsoft.VSTS.Common.AcceptanceCriteria: acceptance_criteria
  Microsoft.VSTS.Scheduling.StoryPoints: story_points
  Microsoft.VSTS.Common.BusinessValue: business_value
  Microsoft.VSTS.Common.Priority: priority
  System.WorkItemType: work_item_type
```

**SAFe Template:**

```yaml
framework: safe
field_mappings:
  System.Description: description
  Microsoft.VSTS.Common.AcceptanceCriteria: acceptance_criteria
  Microsoft.VSTS.Scheduling.StoryPoints: story_points
  Microsoft.VSTS.Common.BusinessValue: business_value
  Microsoft.VSTS.Common.Priority: priority
  System.WorkItemType: work_item_type
  Microsoft.VSTS.Common.ValueArea: value_points
```

**Custom Template:**

```yaml
framework: default
field_mappings:
  System.Description: description
  Custom.AcceptanceCriteria: acceptance_criteria
  Custom.StoryPoints: story_points
  Custom.BusinessValue: business_value
  Custom.Priority: priority
  System.WorkItemType: work_item_type
```

### Method 4: Environment Variable

Set the `SPECFACT_ADO_CUSTOM_MAPPING` environment variable:

```bash
export SPECFACT_ADO_CUSTOM_MAPPING=/path/to/ado_custom.yaml
specfact backlog refine ado --ado-org my-org --ado-project my-project
```

**Priority Order**:

1. CLI parameter (`--custom-field-mapping`) - highest priority
2. Environment variable (`SPECFACT_ADO_CUSTOM_MAPPING`)
3. Auto-detection from `.specfact/templates/backlog/field_mappings/ado_custom.yaml` (created by `specfact init` or `specfact backlog map-fields`)

## Default Field Mappings

If no custom mapping is provided, SpecFact CLI uses default mappings that work with most standard ADO process templates:

- `System.Description` → `description`
- `System.AcceptanceCriteria` → `acceptance_criteria`
- `Microsoft.VSTS.Common.AcceptanceCriteria` → `acceptance_criteria` (alternative, commonly used)
- `Microsoft.VSTS.Common.StoryPoints` → `story_points`
- `Microsoft.VSTS.Scheduling.StoryPoints` → `story_points` (alternative)
- `Microsoft.VSTS.Common.BusinessValue` → `business_value`
- `Microsoft.VSTS.Common.Priority` → `priority`
- `System.WorkItemType` → `work_item_type`

**Multiple Field Alternatives**: SpecFact CLI supports multiple ADO field names mapping to the same canonical field. For example, both `System.AcceptanceCriteria` and `Microsoft.VSTS.Common.AcceptanceCriteria` can map to `acceptance_criteria`. The mapper will check all alternatives and use the first found value.

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

```bash
Error: Custom field mapping file not found: /path/to/file.yaml
```

**Invalid YAML**:

```bash
Error: Invalid custom field mapping file: YAML parsing error
```

**Invalid Schema**:

```bash
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
   - Use `specfact backlog map-fields` to discover the exact field names in your project
   - Or use the ADO REST API to fetch available fields
2. **Check Work Item Type**: Some fields may only exist for certain work item types
   - Test with different work item types (User Story, Feature, Epic)
3. **Check Multiple Alternatives**: Some fields have multiple names (e.g., `System.AcceptanceCriteria` vs `Microsoft.VSTS.Common.AcceptanceCriteria`)
   - Add both alternatives to your mapping if needed
   - SpecFact CLI checks all alternatives and uses the first found value
4. **Test with Defaults**: Try without custom mapping to see if defaults work
5. **Check Logs**: Enable verbose logging to see field extraction details
6. **Verify API Response**: Check the raw ADO API response to see which fields are actually present

### Mapping Not Applied

If your custom mapping is not being applied:

1. **Check File Location**: Ensure the mapping file is in the correct location:
   - `.specfact/templates/backlog/field_mappings/ado_custom.yaml` (auto-detection)
   - Or use `--custom-field-mapping` to specify a custom path
2. **Validate YAML Syntax**: Use a YAML validator to check syntax
   - Common issues: incorrect indentation, missing colons, invalid characters
3. **Check File Permissions**: Ensure the file is readable
4. **Verify Schema**: Ensure the file matches the `FieldMappingConfig` schema
   - Required: `field_mappings` (dict)
   - Optional: `framework` (string), `work_item_type_mappings` (dict)

### Interactive Mapping Fails

If the interactive mapping command (`specfact backlog map-fields`) fails:

1. **Check Token Resolution**: The command uses token resolution priority:
   - First: Explicit `--ado-token` parameter
   - Second: `AZURE_DEVOPS_TOKEN` environment variable
   - Third: Stored token via `specfact backlog auth azure-devops`
   - Fourth: Expired stored token (shows warning with options)

   **Solutions:**
   - Use `--ado-token` to provide token explicitly
   - Set `AZURE_DEVOPS_TOKEN` environment variable
   - Store token: `specfact backlog auth azure-devops --pat your_pat_token`
   - Re-authenticate: `specfact backlog auth azure-devops`

2. **Check ADO Connection**: Verify you can connect to Azure DevOps
   - Test with: `curl -u ":{token}" "https://dev.azure.com/{org}/{project}/_apis/wit/fields?api-version=7.1"`

3. **Verify Permissions**: Ensure your PAT has "Work Items (Read)" permission

4. **Check Token Expiration**: OAuth tokens expire after ~1 hour
   - Use PAT token for longer expiration (up to 1 year): `specfact backlog auth azure-devops --pat your_pat_token`

5. **Verify Organization/Project**: Ensure the org and project names are correct
   - Check for typos in organization or project names

6. **Check Base URL**: For Azure DevOps Server (on-premise), use `--ado-base-url` option

7. **Reset to Defaults**: If mappings are corrupted, use `--reset` to restore defaults:

   ```bash
   specfact backlog map-fields --ado-org myorg --ado-project myproject --reset
   ```

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
