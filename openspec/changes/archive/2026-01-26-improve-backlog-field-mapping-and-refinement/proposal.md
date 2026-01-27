# Change: Improve backlog field mapping and refinement handling

## Why

The current backlog sync and refinement implementation doesn't properly handle the structural differences between GitHub issues (single body with markdown headings) and Azure DevOps work items (separate fields like Description, Acceptance Criteria, Story Points, Priority, Business Value). This causes incorrect field assignment, validation failures for ADO items, missing story points/business value/priority calculations, and inability to support custom ADO template field mappings. Without proper field mapping, teams cannot effectively refine backlog items, calculate complexity scores, detect stories that need splitting, or adapt to custom ADO templates. This change implements abstract field mapping, provider-specific validation, story point/business value/priority calculations, and custom template-based field mapping support to enable proper backlog refinement across all providers.

## What Changes

- **NEW**: Implement abstract field mapping layer (`FieldMapper` abstract base class) that defines canonical field names (description, acceptance_criteria, story_points, business_value, priority, value_points, work_item_type) and provides provider-specific mappers (GitHub, ADO, Jira, Linear) with full Kanban/Scrum/SAFe framework alignment.
- **NEW**: Add `GitHubFieldMapper` (`src/specfact_cli/backlog/mappers/github_mapper.py`) that extracts fields from markdown body using heading patterns (e.g., `## Acceptance Criteria`, `## Story Points`).
- **NEW**: Add `AdoFieldMapper` (`src/specfact_cli/backlog/mappers/ado_mapper.py`) that extracts fields from separate ADO fields (`System.Description`, `System.AcceptanceCriteria`, `Microsoft.VSTS.Common.StoryPoints`, `Microsoft.VSTS.Common.BusinessValue`, `Microsoft.VSTS.Common.Priority`) with custom template mapping support.
- **NEW**: Add template configuration schema (`src/specfact_cli/backlog/mappers/template_config.py`) for custom ADO field mappings with YAML configuration support.
- **NEW**: Add default ADO field mapping templates (`resources/templates/backlog/field_mappings/ado_default.yaml`, `ado_scrum.yaml`, `ado_agile.yaml`) with fallback to custom mappings in `.specfact/templates/backlog/field_mappings/ado_custom.yaml`.
- **EXTEND**: Add `story_points: int | None`, `business_value: int | None`, `priority: int | None`, `value_points: int | None` (SAFe), `acceptance_criteria: str | None`, and `work_item_type: str | None` (Epic, Feature, User Story, Task, Bug, etc.) fields to `BacklogItem` model (`src/specfact_cli/models/backlog_item.py`) for full agile framework support (Kanban, Scrum, SAFe).
- **EXTEND**: Update `convert_github_issue_to_backlog_item()` and `convert_ado_work_item_to_backlog_item()` in `src/specfact_cli/backlog/converter.py` to use field mappers instead of direct field access.
- **EXTEND**: Update `BacklogAIRefiner._validate_required_sections()` in `src/specfact_cli/backlog/ai_refiner.py` to be provider-aware (GitHub: check markdown headings in body, ADO: check separate fields).
- **EXTEND**: Add story splitting detection logic to `BacklogAIRefiner` that flags stories > 13 points (Scrum) or multi-sprint stories for splitting into multiple stories under the same feature, with SAFe-specific validation (Feature → Story hierarchy, Value Points calculation).
- **EXTEND**: Include story points, business value, and priority in refinement prompts and validation scoring.
- **EXTEND**: Update `AdoAdapter` in `src/specfact_cli/adapters/ado.py` to use field mapper for extraction and writeback, supporting custom field mappings.
- **EXTEND**: Update `GitHubAdapter` in `src/specfact_cli/adapters/github.py` to use field mapper for extraction.
- **EXTEND**: Add `--custom-field-mapping` option to `specfact backlog refine` command for specifying custom ADO field mapping file.
- **EXTEND**: Add story splitting suggestions to `specfact backlog refine` command output when complex stories are detected.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #139
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/139>
- **Last Synced Status**: proposed
- **Sanitized**: true
