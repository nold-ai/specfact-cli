# Change: Wave 1 Delta Closure for Verification Gaps

## Why

Wave 1 changes were merged into `dev` for release `v0.34.0`, but post-merge verification identified implementation-to-spec and docs-to-reality gaps that affect trust and adoption:

- `bundle-mapper-01` engine code exists, but `--auto-bundle` flow is not wired end-to-end in backlog refine/import runtime paths.
- `patch-mode-01` command surface exists, but local/apply and upstream/write paths are still lightweight stubs rather than operational patch pipeline behavior.
- release documentation is out of sync with runtime: duplicate `0.34.0` changelog entries and missing `specfact patch` reference coverage.

This delta closes those gaps so shipped behavior, OpenSpec requirements, and user-facing documentation are aligned.

## What Changes

- **EXTEND** `bundle-mapper` integration so `--auto-bundle` activates real mapping flow in backlog refine/import paths (confidence routing, interactive fallback, persistence of learned mappings).
- **EXTEND** `patch-mode` apply/write pipeline so `specfact patch apply <patchfile>` performs effective local patch application and `--write` performs explicit, confirmed upstream write orchestration with idempotency safeguards.
- **EXTEND** documentation and changelog governance so command/reference docs and `CHANGELOG.md` reflect shipped command surfaces and release entries without duplication.
- **EXTEND** verification evidence for this delta with strict OpenSpec validation and dependency impact analysis report.

## Capabilities

- **bundle-mapping**: Runtime hook completion for `--auto-bundle` in backlog refine/import with confidence-based routing and mapping persistence.
- **patch-mode**: Operational local apply and explicit upstream write behavior (confirmed + idempotent) aligned with patch-mode acceptance scenarios.
- **cli-output**: Release/changelog/documentation parity for shipped command surfaces (including patch command and corrected release sectioning).

## Impact

- **Affected specs**:
  - `bundle-mapping` (modified)
  - `patch-mode` (modified)
  - `cli-output` (modified)
- **Affected code**:
  - `modules/bundle-mapper/src/bundle_mapper/*`
  - `src/specfact_cli/modules/backlog/src/commands.py`
  - `src/specfact_cli/modules/patch_mode/src/patch_mode/*`
  - `docs/reference/commands.md`
  - `docs/guides/backlog-refinement.md`
  - `CHANGELOG.md`
- **Integration points**:
  - Backlog ceremony/refine/import flows
  - Patch-mode command pipeline
  - OpenSpec/doc release reporting and command reference parity

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #276
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/276>
- **Last Synced Status**: proposed
- **Sanitized**: false
