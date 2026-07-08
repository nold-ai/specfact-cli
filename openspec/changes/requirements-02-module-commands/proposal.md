# Change: Requirements Import and Validation Commands

## Why

SpecFact needs user-facing commands that can import, normalize, validate, and
inspect upstream requirement context for evidence. It should not position itself
as the authoring stack for requirements, since teams may already use Spec Kit,
OpenSpec, Jira, GitHub Issues, Azure DevOps, Linear, documents, or another
planning source.

## Ownership Alignment (2026-06-06)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: shared requirements input contracts, schemas,
  adapter semantics, and validation result boundaries.
- Bundle-owned follow-up required: runtime commands belong to the canonical
  grouped module command model.
- Target modules-repo follow-up issue: [#165](https://github.com/nold-ai/specfact-cli-modules/issues/165)
- Implementation MUST NOT ship requirement authoring as the critical path.

## What Changes

- **NEW**: Core import and normalization helpers for source-attributed
  requirement records supplied by upstream adapters, including backlog-derived
  snippets and OpenSpec-derived snippets that already conform to the normalized
  requirement input contract.
- **NEW**: Profile-aware validation boundaries that check source attribution and
  downstream evidence usefulness.
- **NEW**: Coverage inspection over normalized inputs, architecture, code, test,
  and validation evidence links.
- **NEW**: Adapter protocol hooks that return bounded, source-attributed records
  rather than free-form planning prose.
- **REMOVED FROM CRITICAL PATH**: Interactive authoring templates and broad
  requirement lifecycle management.

## Out of Scope

- Implementing the runtime `specfact requirements ...` command group in this
  core repository.
- Implementing concrete ingestion adapters for Spec Kit feature folders, local
  markdown files, or YAML requirement records.
- Interactive requirement authoring as a flagship workflow.
- Treating `.specfact/requirements/` as the system of record for product
  management.
- Bidirectional backlog sync or ceremony automation.

## Capabilities

### New Capabilities

- `requirements-context-adapter`: Core helpers for importing, normalizing,
  validating, and inspecting upstream requirement context as validation evidence.

### Modified Capabilities

- `module-io-contract`: Requirements implementations expose import,
  normalization, and validation hooks for evidence, not full lifecycle sync.
- `backlog-adapter`: Backlog adapters can provide source-attributed requirement
  snippets for validation.

## Impact

- **Affected specs**: `requirements-context-adapter`, `module-io-contract`,
  `backlog-adapter`
- **Affected code**:
  - `src/specfact_cli/requirements/context.py`
  - `src/specfact_cli/requirements/__init__.py`
  - `src/specfact_cli/registry/module_grouping.py`
- **Affected tests**:
  - `tests/unit/requirements/test_context_adapter.py`
  - `tests/unit/registry/test_module_grouping.py`
- **Affected docs**:
  - `docs/_data/nav.yml`
  - `docs/index.md`
  - `docs/reference/README.md`
  - `docs/reference/module-categories.md`
  - `docs/reference/requirements-context-adapter.md`
  - `docs/reference/requirements-evidence-input-model.md`
  - `CHANGELOG.md`
- **Integration points**: The paired modules runtime change
  `nold-ai/specfact-cli-modules#165` consumes these helpers for grouped
  commands. Core recognizes the `requirements` module category and group command
  so the paired runtime can mount without shipping root CLI handlers here. This
  core change does not ship backlog write-back or requirement authoring
  commands.
- **Rollback plan**: remove the requirements adapter package, tests, reference
  page, docs navigation/index updates, requirements evidence model cross-link,
  OpenSpec change artifacts, and version/changelog entry. Existing
  `requirements.inputs` bundle data remains compatible because it is still
  defined by `requirements-01-data-model`.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #239
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/239>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#165
- **Paired Modules Scope**: requirements runtime commands
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: in_progress
- **Sanitized**: false
<!-- content_hash: local-sync-2026-07-08-implementation -->
