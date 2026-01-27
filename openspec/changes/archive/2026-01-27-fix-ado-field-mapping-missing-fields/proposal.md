# Change: Fix ADO field mapping missing fields and add interactive template mapping

## Why

When running `specfact backlog refine` with Azure DevOps adapter, the Acceptance Criteria and Assignee fields are missing in the output (GitHub issue #144). The root causes are:

1. **Incorrect field mapping**: The default ADO field mappings use `System.AcceptanceCriteria`, but the actual ADO field name is `Microsoft.VSTS.Common.AcceptanceCriteria` (as shown in the ADO API response). This causes acceptance criteria to not be extracted.

2. **Missing assignee display**: The assignee is extracted in the converter (`convert_ado_work_item_to_backlog_item()`) but is not displayed in the preview output (`backlog_commands.py` line 776).

3. **No interactive template mapping**: Teams with custom ADO process templates cannot easily map their custom fields to canonical field names. They must manually create YAML files without guidance on available fields.

4. **Templates not initialized**: The `specfact init` command doesn't copy backlog field mapping templates to `.specfact/templates/backlog/field_mappings/`, making it harder for users to customize mappings.

5. **Incomplete documentation**: The custom field mapping guide doesn't provide step-by-step instructions for discovering available ADO fields and creating mappings.

Without these fixes, teams cannot:

- See acceptance criteria in backlog refinement output (critical for DoD validation)
- Filter by assignee (important for workload management)
- Easily adapt to custom ADO templates (requires manual YAML creation)
- Understand which ADO fields are available for mapping

This change fixes the field mapping issues, adds interactive template mapping, updates initialization, and improves documentation to enable proper backlog refinement for all ADO process templates.

## What Changes

- **FIX**: Update `AdoFieldMapper.DEFAULT_FIELD_MAPPINGS` in `src/specfact_cli/backlog/mappers/ado_mapper.py` to include `Microsoft.VSTS.Common.AcceptanceCriteria` as an alternative mapping for `acceptance_criteria` (in addition to `System.AcceptanceCriteria` for backward compatibility).
- **FIX**: Add assignee display to preview output in `src/specfact_cli/commands/backlog_commands.py` (line 776) to show `item.assignees` after Provider field.
- **FIX**: Update default ADO field mapping templates (`resources/templates/backlog/field_mappings/ado_*.yaml`) to include `Microsoft.VSTS.Common.AcceptanceCriteria` as alternative mapping.
- **NEW**: Add interactive template mapping command `specfact backlog map-fields` (standalone command, not subcommand) that:
  - Requires ADO connection parameters (`--ado-org`, `--ado-project`, `--ado-token` optional - uses stored tokens via `specfact auth azure-devops`)
  - Fetches available fields from ADO API using `GET https://dev.azure.com/{org}/{project}/_apis/wit/fields` endpoint
  - Filters out system-only fields (e.g., `System.Id`, `System.Rev`, `System.ChangedDate`) to show only relevant fields
  - Displays interactive menu using `questionary` library with arrow key navigation (↑↓ to navigate, ⏎ to select, like `openspec archive`)
  - For each canonical field (description, acceptance_criteria, story_points, business_value, priority, work_item_type):
    - Pre-populates with default mappings from `AdoFieldMapper.DEFAULT_FIELD_MAPPINGS` (checks which defaults exist in fetched fields)
    - Prefers `Microsoft.VSTS.Common.*` fields over `System.*` fields for better compatibility
    - Uses regex/fuzzy matching to suggest potential matches when no default mapping exists
    - Shows current mapping (if exists from existing custom mapping) or default mapping or "<no mapping>"
    - Displays all available ADO fields in scrollable interactive menu
    - Allows selection of ADO field or "<no mapping>" option
    - Pre-selects the best match (existing > default > fuzzy match > "<no mapping>")
  - Includes `--reset` parameter to restore default mappings (deletes `ado_custom.yaml`)
  - Validates mapping before saving (checks for duplicate mappings, validates YAML schema)
  - Saves mapping to `.specfact/templates/backlog/field_mappings/ado_custom.yaml` (per-project configuration)
  - Displays success message with file path
- **EXTEND**: Update `specfact init` command in `src/specfact_cli/commands/init.py` to:
  - Create `.specfact/templates/backlog/field_mappings/` directory structure during initialization
  - Copy default ADO field mapping templates (`ado_default.yaml`, `ado_scrum.yaml`, `ado_agile.yaml`, `ado_safe.yaml`, `ado_kanban.yaml`) from `resources/templates/backlog/field_mappings/` to `.specfact/templates/backlog/field_mappings/`
  - Only copy if files don't exist (or use `--force` flag to overwrite existing files)
  - Display message: "Copied ADO field mapping templates to .specfact/templates/backlog/field_mappings/"
  - Allow users to review and modify templates directly in their project after initialization
- **ENHANCE**: Add progress indicators to `specfact backlog refine` command initialization:
  - Show progress during template loading, detector initialization, AI refiner setup, adapter initialization, DoR configuration loading, and validation
  - Provides user feedback during 5-10 second initialization delay (especially important in corporate environments with security scans/firewalls)
  - Uses Rich Progress with spinners and time elapsed columns for professional UX
- **EXTEND**: Update `AdoFieldMapper._extract_field()` to support multiple field name alternatives (e.g., both `System.AcceptanceCriteria` and `Microsoft.VSTS.Common.AcceptanceCriteria` map to `acceptance_criteria`). The method should check all alternatives and return the first found value (backward compatible - existing `System.AcceptanceCriteria` mapping continues to work).
- **EXTEND**: Update custom field mapping guide (`docs/guides/custom-field-mapping.md`) with:
  - Step-by-step instructions for discovering available ADO fields via API
  - Step-by-step instructions for using interactive template mapping command (including `--reset` parameter)
  - Step-by-step instructions for manually creating/editing field mapping YAML files
  - Troubleshooting section for common field mapping issues
  - Examples for different ADO process templates (Scrum, Agile, SAFe, Kanban, Custom)
  - Information about default mappings pre-population and fuzzy matching for suggestions
- **EXTEND**: Update backlog refinement guide (`docs/guides/backlog-refinement.md`) to mention assignee filtering and acceptance criteria display.

## Impact

- **Affected specs**: `backlog-refinement`, `format-abstraction`
- **Affected code**:
  - `src/specfact_cli/backlog/mappers/ado_mapper.py` (field mapping fixes)
  - `src/specfact_cli/commands/backlog_commands.py` (assignee display, interactive mapping command, progress indicators)
  - `src/specfact_cli/commands/init.py` (template initialization)
  - `src/specfact_cli/backlog/converter.py` (assignee extraction improvements)
  - `resources/templates/backlog/field_mappings/ado_*.yaml` (default template updates)
  - `docs/guides/custom-field-mapping.md` (documentation updates)
  - `docs/guides/backlog-refinement.md` (documentation updates)
  - `pyproject.toml` (added `questionary>=2.0.1` dependency for interactive prompts)
- **Integration points**:
  - ADO adapter field extraction (uses `AdoFieldMapper`)
  - Backlog refinement preview output (displays extracted fields)
  - Template initialization workflow (copies templates to `.specfact/`)
  - Interactive mapping workflow (creates per-project mappings)

## Quality Standards

- **Testing Requirements**: All changes must have unit tests, integration tests, and contract tests
- **Code Quality**: Must pass `hatch run format`, `hatch run type-check`, `hatch run contract-test`
- **Test Coverage**: Must maintain ≥80% test coverage
- **Documentation**: Must update guides with step-by-step instructions

## Git Workflow Requirements

- **Branch Creation**: Work must be done in `bugfix/fix-ado-field-mapping-missing-fields` branch (not on main/dev)
- **Branch Protection**: `main` and `dev` branches are protected - no direct commits
- **Pull Request**: All changes must be merged via PR to `dev` branch
- **Branch Naming**: `bugfix/fix-ado-field-mapping-missing-fields` format

## Acceptance Criteria

- Git branch created before any code modifications
- All tests pass (unit, integration, contract tests)
- Contracts validated (`@icontract`, `@beartype`)
- Documentation updated with step-by-step guides
- No linting errors
- Pull Request created and ready for review
- Issue #144 linked to PR and branch via Development section

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #144
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/144>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: true
