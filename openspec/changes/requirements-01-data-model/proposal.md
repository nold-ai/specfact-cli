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
  and validation evidence links.
- **NEW**: Optional storage convention under `.specfact/requirements/` for
  imported or normalized records used by validation runs.
- **NEW**: Schema versioning for forward-compatible adapters.
- **NEW**: Profile-aware completeness checks that affect validation severity, not
  planning workflow ownership.
- **EXTEND**: `ProjectBundle` receives an optional requirements-input namespace
  through the existing schema extension system.

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

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #238
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/238>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 1dad52a86e44c9f9 -->
