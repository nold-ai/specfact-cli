# Change: Generic Backlog Format & Adapter Extensibility

## Why

Teams need support for arbitrary backlog formats (GitHub, ADO, JIRA, GitLab, local YAML, etc.) while maintaining lossless round-trip sync and template matching. Currently, backlog adapters are tightly coupled to specific providers, making it difficult to add new backlog sources without modifying core logic.

This change implements Plan B from the SpecFact Backlog & OpenSpec Implementation Roadmap (2026-01-18), introducing a generic adapter interface and format abstraction that enables extensible backlog support.

## What Changes

- **NEW**: `BacklogAdapter` abstract base interface (`src/specfact_cli/backlog/adapters/base.py`) - Standard contract for all backlog sources
- **NEW**: `BacklogFormat` abstraction (`src/specfact_cli/backlog/formats/base.py`) - Serialization abstraction for Markdown, YAML, JSON
- **NEW**: `MarkdownFormat` (`src/specfact_cli/backlog/formats/markdown_format.py`) - Markdown serialization implementation
- **NEW**: `StructuredFormat` (`src/specfact_cli/backlog/formats/structured_format.py`) - YAML/JSON serialization implementation
- **NEW**: `FormatDetector` (`src/specfact_cli/backlog/format_detector.py`) - Heuristic format detection
- **NEW**: `LocalYAMLBacklogAdapter` (`src/specfact_cli/backlog/adapters/local_yaml_adapter.py`) - Example new adapter proving extensibility
- **REFACTOR**: GitHub adapter (`src/specfact_cli/backlog/adapters/github_adapter.py`) - Inherit from `BacklogAdapter`, behavior unchanged
- **REFACTOR**: ADO adapter (`src/specfact_cli/backlog/adapters/ado_adapter.py`) - Inherit from `BacklogAdapter`, behavior unchanged
- **NEW**: `BacklogFilters` dataclass - Standardized filtering interface (used by `add-template-driven-backlog-refinement` for filter options)

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #123
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/123>
- **Last Synced Status**: proposed
- **Sanitized**: true
