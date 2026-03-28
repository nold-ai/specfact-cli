## 1. Expand ToolCapabilities dataclass

- [x] 1.1 Add optional fields to `ToolCapabilities` in `src/specfact_cli/models/capabilities.py`: `extensions: list[str] | None`, `extension_commands: dict[str, list[str]] | None`, `presets: list[str] | None`, `hook_events: list[str] | None`, `detected_version_source: str | None`
- [x] 1.2 Add unit tests for `ToolCapabilities` construction with new fields and verify backward compatibility (all new fields default to `None`)
- [x] 1.3 Add `@beartype` and `@ensure` contracts on any new methods that consume the expanded fields

## 2. Extension catalog detection in SpecKitScanner

- [x] 2.1 Add `scan_extensions(self) -> list[dict]` method to `SpecKitScanner` in `src/specfact_cli/importers/speckit_scanner.py` — parse `extensions/catalog.community.json` and `extensions/catalog.core.json`
- [x] 2.2 Add `.extensionignore` parsing — read ignore file and filter excluded extensions from scan results
- [x] 2.3 Add defensive JSON parsing with warning logging for malformed catalogs
- [x] 2.4 Add unit tests for `scan_extensions()`: catalog present, no catalog, malformed JSON, extensionignore filtering

## 3. Version detection in SpecKitAdapter

- [x] 3.1 Add `_detect_version_from_cli(repo_path: Path) -> str | None` method to `SpecKitAdapter` — run `specify --version` with 5-second timeout, parse version string
- [x] 3.2 Add `_detect_version_from_heuristics(repo_path: Path) -> str | None` method — check for `presets/` (>=0.3.0), `extensions/` (>=0.2.0), `.specify/` (>=0.1.0)
- [x] 3.3 Integrate version detection into `get_capabilities()`: try CLI first, fall back to heuristics, populate `version` and `detected_version_source`
- [x] 3.4 Add unit tests for both detection methods and the integration flow (CLI available, CLI missing, heuristic fallback, timeout)

## 4. Preset detection in SpecKitScanner

- [x] 4.1 Add `scan_presets(self) -> list[str]` method to `SpecKitScanner` — scan `presets/` directory for preset catalog files
- [x] 4.2 Add unit tests for preset detection: presets present, no presets directory

## 5. Hook event detection

- [x] 5.1 Add `scan_hook_events(self) -> list[str]` method to `SpecKitScanner` — detect before/after hook wiring in `.specify/prompts/` template files
- [x] 5.2 Add unit tests for hook event detection

## 6. Expand BridgeConfig command mappings

- [x] 6.1 Update `preset_speckit_classic()` in `src/specfact_cli/models/bridge.py` to include all 7 slash commands: specify, plan, tasks, implement, constitution, clarify, analyze
- [x] 6.2 Update `preset_speckit_specify()` with the same 7 command mappings
- [x] 6.3 Update `preset_speckit_modern()` with the same 7 command mappings
- [x] 6.4 Add unit tests verifying all 3 presets contain the full 7-command set

## 7. Integrate extensions/presets/hooks into SpecKitAdapter.get_capabilities()

- [x] 7.1 Update `get_capabilities()` in `src/specfact_cli/adapters/speckit.py` to call scanner methods and populate new `ToolCapabilities` fields
- [x] 7.2 Ensure cross-repo scenarios (`external_base_path`) use filesystem-only detection (skip CLI probe)
- [x] 7.3 Add integration tests for full `get_capabilities()` flow with v0.4.x repo structure
- [x] 7.4 Add integration test for legacy repo structure (verify backward compat — all new fields are `None`)

## 8. Documentation updates

- [x] 8.1 Update `docs/guides/speckit-comparison.md` feature matrix with new detection capabilities
- [x] 8.2 Update `docs/guides/speckit-journey.md` workflow steps to reference extension and preset awareness
- [x] 8.3 Review and update any adapter reference docs that mention spec-kit capabilities

## 9. Contract and quality gates

- [x] 9.1 Ensure all new public methods have `@icontract` (`@require`/`@ensure`) and `@beartype` decorators
- [x] 9.2 Run `hatch run format && hatch run type-check && hatch run contract-test && hatch test --cover -v`
- [x] 9.3 Record TDD evidence in `TDD_EVIDENCE.md`
