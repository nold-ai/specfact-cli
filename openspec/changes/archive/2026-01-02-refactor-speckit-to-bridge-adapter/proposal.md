# Change: Refactor Spec-Kit Integration to Bridge Adapter Pattern

## Why

The Spec-Kit integration currently uses hard-coded logic in multiple places (`sync.py`, `bridge_probe.py`, `bridge_sync.py`), violating the universal abstraction layer principle established for the bridge adapter architecture. This creates maintenance burden, prevents consistent adapter behavior, and makes it difficult to add new adapters.

The OpenSpec adapter implementation demonstrated the correct pattern: all adapter-specific logic should be encapsulated in a `SpecKitAdapter` class implementing the `BridgeAdapter` interface, with no hard-coded checks in core sync/probe logic.

## What Changes

- **Create `SpecKitAdapter`** implementing `BridgeAdapter` interface
  - Move Spec-Kit detection logic from `bridge_probe.py` to `SpecKitAdapter.detect()`
  - Move Spec-Kit sync logic from `sync.py` to `SpecKitAdapter.import_artifact()` and `export_artifact()`
  - Encapsulate `SpecKitScanner` and `SpecKitConverter` usage within adapter
  - **Preserve bidirectional sync logic**: Move change detection and conflict resolution methods from `SpecKitSync` to `SpecKitAdapter` as private helper methods (`_detect_speckit_changes()`, `_detect_specfact_changes()`, `_merge_changes()`, `_detect_conflicts()`, `_resolve_conflicts()`)
  - Implement `get_capabilities()`, `generate_bridge_config()`, and change tracking methods
  - **Constitution validation**: Move constitution validation to `SpecKitAdapter.get_capabilities()` (check for constitution file and set `has_custom_hooks` flag)

- **Refactor `sync.py` command** to use adapter registry
  - Remove hard-coded `if adapter_type == AdapterType.SPECKIT:` checks (lines 86, 102, 199, 471, 488)
  - Remove direct instantiation of `SpecKitSync`, `SpecKitConverter`, `SpecKitScanner`
  - Remove `_sync_speckit_to_specfact()` helper function
  - Remove direct calls to `sync.detect_speckit_changes()` and `sync.detect_conflicts()` (bidirectional sync logic moved to adapter)
  - Use `BridgeSync` and adapter registry for all adapters consistently
  - **Bidirectional sync**: Use `BridgeSync.sync_bidirectional()` which delegates to adapter's `import_artifact()` and `export_artifact()` methods (adapter handles change detection and conflict resolution internally)

- **Refactor `bridge_probe.py`** to remove Spec-Kit-specific validation
  - Remove hard-coded `if bridge_config.adapter == AdapterType.SPECKIT:` check in `validate_bridge()`
  - Move Spec-Kit-specific validation suggestions to `SpecKitAdapter` if needed

- **Refactor `bridge_sync.py`** to remove hard-coded adapter checks
  - Remove hard-coded `if self.bridge_config.adapter.value != "openspec":` check in `generate_alignment_report()`
  - Make alignment report generation adapter-agnostic or move to adapter-specific method

- **Refactor `import_cmd.py`** to remove hard-coded Spec-Kit logic
  - Remove hard-coded `if adapter_type == AdapterType.SPECKIT:` checks
  - Use adapter registry pattern for all adapters
  - Use `adapter.discover_features()` instead of direct scanner usage

- **Remove deprecated commands** (breaking change)
  - Remove `specfact implement` command (deprecated in v0.17.0, removed in v0.22.0)
  - Remove `specfact generate tasks` command (removed per SPECFACT_0x_TO_1x_BRIDGE_PLAN.md)
  - Delete `src/specfact_cli/commands/implement.py` file
  - Remove `generate_tasks` function from `generate.py`

- **Update `BridgeConfig` model** (if needed)
  - Use existing `preset_speckit_classic()` and `preset_speckit_modern()` methods in `SpecKitAdapter.generate_bridge_config()`
  - Adapter should auto-detect format (classic: `specs/` at root, modern: `docs/specs/`) and return appropriate preset

- **Remove `SpecKitSync` class and related deprecated code** (breaking change - beta phase allows minor version breaking changes)
  - Delete `src/specfact_cli/sync/speckit_sync.py` file completely
  - Remove `SpecKitSync` and `SyncResult` imports from `src/specfact_cli/sync/__init__.py`
  - Remove all references to `SpecKitSync` in codebase
  - Update `SyncResult` usage if needed (check if it's used elsewhere or adapter-specific)

- **Refactor `specfact bridge` command** (remove bridge command, move constitution to top-level)
  - Remove `specfact bridge` command completely (bridge adapters are internal connectors, no user-facing commands)
  - Move `constitution` subcommand to `specfact sdd constitution` (Spec-Kit is an SDD tool, constitution is SDD-specific)
  - Update all references from `specfact bridge constitution` to `specfact sdd constitution`
  - Update help text and documentation to reflect new command location

- **Remove deprecated commands** (breaking change per SPECFACT_0x_TO_1x_BRIDGE_PLAN.md)
  - Remove `specfact implement` command (deprecated in v0.17.0, removed in v0.22.0)
  - Remove `specfact generate tasks` command (removed per SPECFACT_0x_TO_1x_BRIDGE_PLAN.md positioning)
  - Delete `src/specfact_cli/commands/implement.py` file
  - Remove `generate_tasks` function and `_format_task_list_as_markdown` helper from `generate.py`
  - Remove imports and registrations from `cli.py` and `commands/__init__.py`
  - **Rationale**: SpecFact CLI does not create plan -> feature -> task (that's the job for spec-kit, openspec, etc.). We complement those SDD tools to enforce tests and quality.

- **Register `SpecKitAdapter`** in adapter registry
  - Add `SpecKitAdapter` to `src/specfact_cli/adapters/__init__.py`
  - Ensure adapter is available via `AdapterRegistry.get_adapter("speckit")`

- **Update tests** to verify adapter registry usage
  - Remove tests that verify hard-coded Spec-Kit checks
  - Remove tests for `SpecKitSync` class (file deleted)
  - Add tests verifying Spec-Kit adapter registration and usage via registry
  - Update integration tests to use adapter registry pattern
  - Update tests for constitution command location change

## Impact

- **Affected specs**: `bridge-adapter` capability
- **Affected code**:
  - `src/specfact_cli/adapters/` (new `speckit.py` adapter)
  - `src/specfact_cli/commands/sync.py` (remove hard-coded logic, use adapter registry, refactor mode detection)
  - `src/specfact_cli/commands/import_cmd.py` (remove hard-coded Spec-Kit logic, use adapter registry) - **NEW**
  - `src/specfact_cli/commands/bridge.py` (remove entire file - bridge command deleted)
  - `src/specfact_cli/commands/implement.py` (remove entire file - implement command deleted)
  - `src/specfact_cli/commands/generate.py` (remove `generate_tasks` function and helper)
  - `src/specfact_cli/commands/sdd.py` (add constitution subcommand moved from bridge)
  - `src/specfact_cli/sync/bridge_probe.py` (remove hard-coded validation)
  - `src/specfact_cli/sync/bridge_sync.py` (remove hard-coded alignment report check, remove GitHub kwargs check)
  - `src/specfact_cli/sync/speckit_sync.py` (delete entire file - class removed)
  - `src/specfact_cli/sync/__init__.py` (remove SpecKitSync and SyncResult exports)
  - `src/specfact_cli/models/bridge.py` (use existing `preset_speckit_classic()` and `preset_speckit_modern()` methods)
  - `src/specfact_cli/models/capabilities.py` (potentially extend ToolCapabilities with sync mode support)
  - `src/specfact_cli/cli.py` (remove bridge and implement command registrations, update sdd command)
  - `src/specfact_cli/commands/__init__.py` (remove implement import)
  - `tests/` (update tests to use adapter registry, remove SpecKitSync tests, add bidirectional sync tests, update constitution command tests, update import command tests)
- **Breaking changes**: 
  - **Command change**: `specfact bridge constitution` → `specfact sdd constitution` (breaking CLI change)
  - **Removed class**: `SpecKitSync` class removed (breaking API change for any code using it directly)
  - **Removed command**: `specfact bridge` command removed (breaking CLI change)
  - **Removed command**: `specfact implement` command removed (breaking CLI change - deprecated in v0.17.0)
  - **Removed command**: `specfact generate tasks` command removed (breaking CLI change - deprecated per SPECFACT_0x_TO_1x_BRIDGE_PLAN.md)
- **Migration**: 
  - Update scripts/tooling using `specfact bridge constitution` to use `specfact sdd constitution`
  - Any code directly using `SpecKitSync` must migrate to `SpecKitAdapter` via adapter registry
  - **For task generation**: Use Spec-Kit, OpenSpec, or other SDD tools (SpecFact CLI complements these tools for enforcement, not task creation)
  - **For code implementation**: Use `specfact generate fix-prompt` and AI IDE tools (SpecFact CLI provides prompts, not code generation in 0.x)



---

## Source Tracking

### Repository: nold-ai/specfact-cli

- **GitHub Issue**: #72
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/72>
- **Last Synced Status**: applied
- **Sanitized**: true
<!-- content_hash: cccd974ffc32c749 -->