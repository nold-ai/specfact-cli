# Change: Integrate Sidecar Validation into SpecFact CLI

## Why

The sidecar validation workflow is currently implemented as bash scripts in `resources/templates/sidecar/`. This creates several problems:

1. **Not Native**: Users must manually initialize sidecar workspaces using `sidecar-init.sh`, which is not discoverable or integrated with the CLI
2. **Script-Based**: All logic is in bash scripts (`run_sidecar.sh`), making it hard to maintain, test, and extend
3. **No Standardization**: Doesn't use SpecFact CLI's standard UI/UX patterns (Rich console, progress bars, error handling)
4. **Limited Integration**: Can't be easily integrated with other CLI commands (e.g., `specfact repro`, `specfact analyze`)
5. **No Plugin Architecture**: Framework-specific extractors (Django, FastAPI, DRF) are hardcoded in templates, not extensible

**Alignment with project.md**: This follows the brownfield-first principle by integrating existing sidecar validation logic into the CLI as a native command. It uses existing SpecFact CLI patterns (Typer commands, Rich console, Pydantic models) and maintains backward compatibility with template-based sidecar workspaces.

## What Changes

### New CLI Command: `specfact validate sidecar`

- **Command**: `specfact validate sidecar --bundle <name> [options]`
- **Purpose**: Run sidecar validation workflow natively within SpecFact CLI
- **Replaces**: Manual `run_sidecar.sh` script execution
- **Maintains**: Template-based sidecar workspaces for backward compatibility

### New Python Modules

- **NEW**: `src/specfact_cli/validators/sidecar/` (sidecar validation package)
  - `__init__.py` - Package initialization
  - `orchestrator.py` - Main sidecar validation orchestrator
  - `harness_generator.py` - Python port of `generate_harness.py`
  - `contract_populator.py` - Python port of `populate_contracts.py`
  - `framework_detector.py` - Framework detection logic
  - `crosshair_runner.py` - CrossHair execution wrapper
  - `specmatic_runner.py` - Specmatic execution wrapper
  - `models.py` - Pydantic models for sidecar configuration

- **NEW**: `src/specfact_cli/validators/sidecar/frameworks/` (framework-specific modules)
  - `__init__.py` - Framework registry
  - `base.py` - Base framework extractor interface
  - `django.py` - Django URL/form extractor (port from template)
  - `fastapi.py` - FastAPI route extractor (port from template)
  - `drf.py` - DRF serializer extractor (port from template)

- **EXTEND**: `src/specfact_cli/commands/validate.py` (new command group)
  - `validate sidecar` - Sidecar validation command
  - `validate sidecar init` - Initialize sidecar workspace (replaces `sidecar-init.sh`)
  - `validate sidecar run` - Run sidecar validation (replaces `run_sidecar.sh`)

### Integration Points

- **EXTEND**: `src/specfact_cli/utils/console.py`
  - Add sidecar-specific progress indicators
  - Add sidecar-specific status messages

- **EXTEND**: `src/specfact_cli/utils/env_manager.py`
  - Add framework detection utilities
  - Add Python environment detection for sidecar execution

- **EXTEND**: `src/specfact_cli/validators/repro_checker.py`
  - Integrate sidecar validation into `specfact repro` workflow
  - Add option to run sidecar validation as part of repro suite
  - Support unannotated code validation via sidecar harness (Phase 11)

- **NEW**: `src/specfact_cli/validators/sidecar/crosshair_summary.py` (Phase 9)
  - Parse CrossHair output for summary counts
  - Generate `crosshair-summary.json` file
  - Display summary in console

- **EXTEND**: `src/specfact_cli/validators/sidecar/specmatic_runner.py` (Phase 10)
  - Auto-detect missing service/client configuration
  - Auto-skip Specmatic with clear message when no service available
  - Support unannotated code validation via sidecar harness (Phase 11)

- **NEW**: `src/specfact_cli/validators/sidecar/crosshair_summary.py` (Phase 9)
  - Parse CrossHair output for summary counts
  - Generate `crosshair-summary.json` file
  - Display summary in console

- **EXTEND**: `src/specfact_cli/validators/sidecar/specmatic_runner.py` (Phase 10)
  - Auto-detect missing service/client configuration
  - Auto-skip Specmatic with clear message when no service available

### Configuration

- **NEW**: Sidecar configuration model (`SidecarConfig` in `models.py`)
  - Framework type (Django, FastAPI, DRF, pure-python)
  - Tool flags (RUN_CROSSHAIR, RUN_SPECMATIC, RUN_SEMGREP, etc.)
  - Timeout settings
  - Path configurations (contracts, harness, bindings)

- **EXTEND**: Project bundle structure
  - Add sidecar configuration to bundle metadata
  - Store sidecar execution results in bundle reports

## Impact

- **Affected specs**: New capability `sidecar-validation` (sidecar validation workflow)
- **Affected code**:
  - New command module: `src/specfact_cli/commands/validate.py`
  - New validator package: `src/specfact_cli/validators/sidecar/`
  - Extended utilities: `console.py`, `env_manager.py`
  - Extended repro checker: `repro_checker.py`
- **Integration points**:
  - Existing CLI command structure (Typer)
  - Existing console utilities (Rich)
  - Existing environment detection (`env_manager.py`)
  - Existing repro workflow (`repro_checker.py`)
  - Existing contract management (`contract_cmd.py`)

## Non-Goals

- **Not removing**: Template-based sidecar workspaces (backward compatibility)
- **Not changing**: Framework-specific extractor logic (Django, FastAPI, DRF)
- **Not implementing**: New framework extractors (only porting existing ones)
- **Not adding**: New validation tools (only integrating existing CrossHair/Specmatic)
- **Not breaking**: Existing sidecar template structure (templates remain for reference)

## Quality Standards

### Testing Requirements

- **Unit Tests**: All new modules must have unit tests with ≥80% coverage
- **Contract Tests**: All public APIs must have `@icontract` decorators and contract validation
- **Integration Tests**: Full sidecar workflow must be tested with test repositories
- **Backward Compatibility Tests**: Template-based sidecar workspaces must continue to work

### Code Quality Requirements

- **Linting**: `hatch run format` (black, isort, basedpyright, ruff, pylint)
- **Type Checking**: `hatch run type-check` (basedpyright strict mode)
- **Contract Validation**: `hatch run contract-test` (runtime contract validation)
- **Test Coverage**: `hatch run smart-test` (≥80% coverage required)

### Git Workflow Requirements

- **Branch Creation**: Work must be done in `feature/integrate-sidecar-validation` branch (not on main/dev)
- **Branch Protection**: `main` and `dev` branches are protected - no direct commits
- **Pull Request**: All changes must be merged via PR to `dev` branch
- **Branch Naming**: `<branch-type>/<change-id>` format

### Acceptance Criteria

- [ ] Git branch created before any code modifications
- [ ] All tests pass (unit, integration, backward compatibility)
- [ ] Contracts validated (all public APIs have `@icontract` decorators)
- [ ] Documentation updated (user guides, command reference)
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Pull Request created and ready for review

---

## Related Issues

This change proposal consolidates and implements several related sidecar validation features:

- **#54**: [Feature] Add sidecar init/run CLI wrappers (Phase B) - **CONSOLIDATED**: This proposal implements `specfact validate sidecar init` and `specfact validate sidecar run` commands
- **#55**: [Feature] Sidecar: emit CrossHair summary counts - **INCLUDED**: CrossHair output parsing and summary file generation (Phase 9)
- **#56**: [Feature] Sidecar: safe defaults when no client/app (skip Specmatic) - **INCLUDED**: Auto-detection of missing service configuration and auto-skip Specmatic (Phase 10)
- **#57**: [Feature] Repro: CrossHair via sidecar on unannotated code (no-edit) - **INCLUDED**: Integration with `specfact repro` workflow for unannotated code validation (Phase 11)

**Note**: This proposal implements the core CLI integration (#54) in Phases 0-8. Features from #55, #56, and #57 are included as Phases 9-11 in the implementation plan.

---

## Source Tracking

- **GitHub Issue**: #97
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/97>
- **Last Synced Status**: proposed
<!-- content_hash: af3a55cdd443d95a -->