## Why

GitHub Spec-Kit has advanced from an early-stage CLI to v0.4.3 with 46 community extensions, a pluggable preset system, 7+ slash commands, hook events, and auto-registered AI skills. Our SpecKitAdapter was built against the initial spec-kit layout (3 static presets, 2 command triggers, no version detection) and no longer models the tool's actual capabilities. This creates silent drift: SpecFact cannot detect extensions that own sync/reconcile workflows, misses new slash commands, cannot gate features by spec-kit version, and ignores the preset catalog. Users report difficulty using spec-kit as a first-class sync candidate alongside OpenSpec.

## What Changes

- **Expand `CommandMapping` in `BridgeConfig` presets**: Add triggers for `/speckit.constitution`, `/speckit.clarify`, `/speckit.analyze`, `/speckit.tasks`, `/speckit.implement` (currently only `/speckit.specify` and `/speckit.plan` are mapped)
- **Add extension catalog awareness to `SpecKitAdapter`**: Detect `extensions/` directory, parse `catalog.community.json` and `catalog.core.json`, model extension-provided commands (reconcile, sync, iterate, verify, retrospective, checkpoint, archive)
- **Implement version detection in `ToolCapabilities`**: Detect spec-kit version from `specify --version` or `specify status --json` when CLI is available; fall back to heuristic detection from directory structure features (e.g., `presets/` presence implies >= 0.3.0)
- **Add preset system detection**: Scan `presets/` directory, parse pluggable preset catalogs, detect active preset configuration, adjust artifact mappings based on active preset
- **Model hook events**: Detect before/after hook event wiring in templates; expose hook metadata in `ToolCapabilities` for downstream sync coordination
- **Add `.extensionignore` support**: Respect extension exclusion rules when scanning
- **Update `SpecKitScanner`**: Detect new directory entries (`extensions/`, `presets/`, `.extensionignore`) and parse extension metadata
- **Expand `ToolCapabilities` dataclass**: Add fields for `extensions`, `presets`, `hooks`, `detected_version_source`

## Capabilities

### New Capabilities

- `speckit-extension-catalog`: Detection, parsing, and modeling of spec-kit extension catalogs (community and core) and their provided commands
- `speckit-version-detection`: Version detection strategies for spec-kit installations (CLI probe, directory heuristics, preset presence)

### Modified Capabilities

- `bridge-adapter`: Expanded SpecKitAdapter with extension awareness, preset detection, hook modeling, and version-gated feature flags
- `bridge-registry`: ToolCapabilities extended with extension/preset/hook metadata fields

## Impact

- **Code**: `src/specfact_cli/adapters/speckit.py`, `src/specfact_cli/models/capabilities.py`, `src/specfact_cli/models/bridge.py`, `src/specfact_cli/importers/speckit_scanner.py`
- **Tests**: `tests/unit/adapters/test_speckit.py`, `tests/unit/importers/test_speckit_scanner.py`, `tests/integration/importers/test_speckit_format_compatibility.py`
- **Docs**: `docs/guides/speckit-comparison.md` (update feature matrix), `docs/guides/speckit-journey.md` (update workflow steps)
- **Dependencies**: No new external dependencies. Spec-Kit CLI is optional (version detection degrades gracefully)
- **Downstream**: `sync-01-unified-kernel` can use extension metadata to coordinate with spec-kit's own sync/reconcile. `requirements-03-backlog-sync` can detect spec-kit backlog extensions to avoid duplicate issue creation.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #453
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/453>
- **Parent Feature**: #369 (Sync Engine)
- **Last Synced Status**: proposed
- **Sanitized**: false
