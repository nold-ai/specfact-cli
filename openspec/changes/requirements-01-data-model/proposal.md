# Change: Requirements Evidence Input Model

## Why

SpecFact needs a normalized way to reference upstream requirement context during
validation. It does not need to become the primary requirement-authoring tool.
Spec Kit, OpenSpec, backlog systems, docs, and issue trackers remain the source
of planning intent; SpecFact stores the minimum local records needed to explain
validation evidence and drift.

## What Changes

- **NEW**: Pydantic models in `src/specfact_cli/models/requirements.py` for
  normalized requirement inputs, business rules, constraints, source references,
  completeness findings, and validation evidence links.
- **NEW**: Schema versioning for forward-compatible adapters.
- **NEW**: Profile-aware completeness checks that affect validation severity, not
  planning workflow ownership.
- **EXTEND**: `ProjectBundle` can carry requirement input records through the
  existing `requirements.inputs` schema-extension namespace.

## Out of Scope

- Interactive requirement authoring as a flagship workflow.
- Treating `.specfact/requirements/` as the system of record for product
  management.
- Bidirectional backlog sync or ceremony automation.

## Capabilities

### New Capabilities

- `requirements-evidence-input-model`: Normalized requirement input records and
  source references used by validation evidence and drift detection.

### Modified Capabilities

- `data-models`: ProjectBundle extended with an optional requirements-input
  namespace.

## Impact

- **Affected specs**: `requirements-evidence-input-model`, `data-models`
- **Affected code**:
  - `src/specfact_cli/models/requirements.py`
  - `src/specfact_cli/models/__init__.py`
  - `src/specfact_cli/models/project.py` extension usage remains backward compatible
- **Affected tests**:
  - `tests/unit/models/test_requirements.py`
  - `tests/unit/models/test_schema_extensions.py`
- **Affected docs**:
  - `docs/reference/requirements-evidence-input-model.md`
  - `CHANGELOG.md`
- **Integration points**: downstream import adapters and validation evidence graph
  changes consume these records; this change does not introduce backlog write-back
  or requirement-authoring commands.
- **Rollback plan**: remove the new requirements model module, exports, docs page,
  and extension tests; existing ProjectBundle serialization remains compatible
  because the namespace lives in optional extension data.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #238
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/238>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: in_review
- **Sanitized**: false
<!-- content_hash: 1dad52a86e44c9f9 -->
