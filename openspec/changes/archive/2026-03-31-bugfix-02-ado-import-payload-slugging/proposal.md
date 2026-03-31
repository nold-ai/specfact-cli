# Change: Fix ADO selective bridge import payload contract and title-based change IDs

## Why

Issue [#425](https://github.com/nold-ai/specfact-cli/issues/425) confirms a real regression in the ADO selective import path used by `specfact project sync bridge --adapter ado --mode bidirectional --backlog-ids <id>`. The current bridge flow calls `fetch_backlog_item()` and then imports the returned artifact as an OpenSpec change proposal, but `AdoAdapter._get_work_item_data()` strips the provider payload down to summary fields and drops the native `fields` object that `AdoAdapter.import_artifact()` and `extract_change_proposal_data()` still expect. Valid ADO work items therefore fail import with `ADO work item must have fields`.

After a local hotfix restores the raw payload, the follow-up behavior is still wrong: when the ADO item does not already contain OpenSpec metadata in its description or comments, the generated change ID falls back to the numeric work item ID instead of a readable slug derived from the title. That makes imported OpenSpec changes hard to review, easy to collide, and inconsistent with the rest of the backlog import workflow.

This change fixes both defects together and explicitly audits adjacent import commands that rely on the same `fetch_backlog_item()` to `import_artifact()` contract so we do not repeat the same summary-vs-native payload mistake in nearby adapters or bridge entry points.

## What Changes

- **MODIFY** `AdoAdapter.fetch_backlog_item()` and its internal work-item fetch helpers so selective ADO import returns the native work item payload, including `fields`, while preserving convenience keys such as `title`, `state`, and `description` for existing callers.
- **MODIFY** the ADO change-proposal extraction path so imported proposals derive a kebab-case change ID from the work item title when no OpenSpec metadata is already embedded in the source artifact.
- **MODIFY** shared backlog import normalization so duplicate or numeric-only fallback IDs get a deterministic suffix that keeps the readable slug and reserves the provider numeric ID for source tracking metadata instead of primary naming.
- **ADD** regression coverage for selective `project sync bridge` / bridge import flows, including raw payload preservation, title-based slug generation, duplicate-slug collision handling, and cross-checks for similar adapter import commands.
- **REVIEW** adjacent bridge/adapters that call `fetch_backlog_item()`, `extract_change_proposal_data()`, or `import_backlog_item_as_proposal()` so similar commands either share the same helper or are covered by explicit contract tests.

## Capabilities

### Modified Capabilities

- `devops-sync`: selective ADO bridge imports must preserve the provider-native work item payload required for OpenSpec proposal import and must create readable change IDs when no prior metadata exists.
- `backlog-adapter`: adapter import contracts must preserve required native fields during single-item import and normalize imported proposal IDs title-first instead of defaulting to raw numeric source IDs.

## Impact

- **Affected code**: `src/specfact_cli/adapters/ado.py`, `src/specfact_cli/adapters/backlog_base.py`, and the selective import orchestration in `src/specfact_cli/sync/bridge_sync.py`; adjacent adapter call sites may need small defensive updates if the audit finds the same contract gap elsewhere.
- **Affected tests**: targeted unit/integration coverage under `tests/unit/adapters/`, `tests/unit/specfact_cli/adapters/`, `tests/unit/specfact_cli/sync/`, and any command-audit coverage that validates bridge command surfaces.
- **Documentation**: user-facing sync and ADO adapter docs in `docs/` plus any command reference examples that show selective bridge import should be reviewed so the fixed import behavior and change-ID expectations are documented.
- **Release impact**: patch release. No new command surface, but behavior changes are user-visible because valid ADO work items will import successfully and produce stable human-readable OpenSpec change IDs.
- **Sequencing**: no hard blocker in `openspec/CHANGE_ORDER.md`; the change should still be linked under backlog feature #357 and epic #186 and back to the originating bug issue.

## Related Issues

- Originating bug report: [#425](https://github.com/nold-ai/specfact-cli/issues/425)
- Parent feature: [#357](https://github.com/nold-ai/specfact-cli/issues/357)
- Parent epic: [#186](https://github.com/nold-ai/specfact-cli/issues/186)

## Source Tracking

- **GitHub Issue**: #427
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/427>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
