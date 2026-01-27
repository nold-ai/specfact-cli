# Design: Sidecar Validation Integration

## Architecture Overview

The sidecar validation integration follows SpecFact CLI's existing command architecture:

```
specfact validate sidecar
├── Command Layer (Typer)
│   └── validate.py (commands/validate.py)
├── Orchestration Layer
│   └── orchestrator.py (validators/sidecar/orchestrator.py)
├── Framework Layer
│   └── frameworks/ (validators/sidecar/frameworks/)
│       ├── base.py (BaseFrameworkExtractor)
│       ├── django.py (DjangoExtractor)
│       ├── fastapi.py (FastAPIExtractor)
│       └── drf.py (DRFExtractor)
├── Tool Execution Layer
│   ├── crosshair_runner.py
│   ├── specmatic_runner.py
│   └── harness_generator.py
└── Configuration Layer
    └── models.py (Pydantic models)
```

## Design Decisions

### 1. Command Structure

**Decision**: Use `specfact validate sidecar` instead of `specfact sidecar`

**Rationale**:

- Aligns with existing command structure (`specfact repro`, `specfact analyze`)
- "validate" is the primary purpose of sidecar workflow
- Allows future expansion: `specfact validate contracts`, `specfact validate tests`, etc.

**Alternative Considered**: `specfact sidecar` - Rejected because it's too generic and doesn't indicate purpose

### 2. Framework Extractor Pattern

**Decision**: Use plugin registry pattern with base interface

**Rationale**:

- Matches existing SpecFact CLI patterns (BridgeAdapter registry)
- Easy to extend with new frameworks
- Type-safe with Pydantic models
- Testable in isolation

**Implementation**:

```python
class BaseFrameworkExtractor(ABC):
    @abstractmethod
    def detect(self, repo_path: Path) -> bool:
        """Detect if this framework is used in the repository."""
    
    @abstractmethod
    def extract_routes(self, repo_path: Path) -> list[RouteInfo]:
        """Extract route information from framework-specific patterns."""
    
    @abstractmethod
    def extract_schemas(self, repo_path: Path, routes: list[RouteInfo]) -> dict[str, Any]:
        """Extract request/response schemas from framework-specific patterns."""
```

### 3. Backward Compatibility

**Decision**: Maintain template-based sidecar workspaces

**Rationale**:

- Existing validation repos use templates
- Templates serve as reference implementation
- Allows gradual migration
- Templates can be used for advanced customization

**Implementation**:

- CLI command can detect existing sidecar workspace
- If detected, uses existing workspace configuration
- If not detected, creates new workspace using CLI-native approach
- Templates remain in `resources/templates/sidecar/` for reference

### 4. Configuration Management

**Decision**: Use Pydantic models for configuration

**Rationale**:

- Type-safe configuration
- Validation at load time
- Consistent with existing SpecFact CLI patterns
- Easy to serialize/deserialize (YAML/JSON)

**Model Structure**:

```python
class SidecarConfig(BaseModel):
    bundle_name: str
    repo_path: Path
    framework_type: FrameworkType | None = None
    tools: ToolConfig
    paths: PathConfig
    timeouts: TimeoutConfig
```

### 5. Tool Execution

**Decision**: Wrap external tools (CrossHair, Specmatic) in Python runners

**Rationale**:

- Better error handling than bash scripts
- Progress reporting via Rich console
- Integration with CLI's operational mode (CI/CD vs interactive)
- Consistent timeout handling

**Implementation**:

- `CrossHairRunner`: Executes CrossHair with proper PYTHONPATH and environment
- `SpecmaticRunner`: Executes Specmatic with proper configuration
- Both use `subprocess` with Rich progress indicators

### 6. Progress Reporting

**Decision**: Use Rich console for all sidecar operations

**Rationale**:

- Consistent with existing CLI commands
- Terminal capability detection (from `cli-output` spec)
- Progress bars for long-running operations
- Status messages for each phase

**Phases**:

1. Framework detection
2. Contract population
3. Harness generation
4. CrossHair analysis (source code)
5. CrossHair analysis (harness)
6. Specmatic validation (if applicable)

### 7. CrossHair Summary Reporting (Phase 9)

**Decision**: Parse CrossHair output and generate summary file

**Rationale**:

- Provides quick visibility into validation results
- Enables tracking across multiple repositories
- Reduces manual log scanning

**Implementation**:

- Parse CrossHair stdout/stderr for confirmed/not confirmed/violations counts
- Generate `crosshair-summary.json` with structured data
- Display summary line in console
- Handle different CrossHair output formats (verbose/non-verbose)

**Files**:

- `src/specfact_cli/validators/sidecar/crosshair_summary.py` - Parser module
- `src/specfact_cli/validators/sidecar/orchestrator.py` - Integration point

### 8. Specmatic Auto-Skip (Phase 10)

**Decision**: Auto-detect missing service configuration and skip Specmatic automatically

**Rationale**:

- Reduces noise for validation runs focused on harness/CrossHair
- Users shouldn't need to remember `--no-run-specmatic` each time
- Clear messaging explains why Specmatic was skipped

**Implementation**:

- Check for `test_base_url`, `host`, `port` in SpecmaticConfig
- Check for application server configuration (cmd, port)
- Auto-set `config.tools.run_specmatic = False` when no service detected
- Display clear message: "Skipping Specmatic: No service configuration detected"
- Manual override still works via `--run-specmatic` flag

**Files**:

- `src/specfact_cli/validators/sidecar/specmatic_runner.py` - Detection logic
- `src/specfact_cli/validators/sidecar/orchestrator.py` - Auto-skip integration

### 9. Repro Integration (Phase 11)

**Decision**: Integrate sidecar validation into `specfact repro` workflow

**Rationale**:

- Enables CrossHair on unannotated code without modifying source
- Provides no-edit path for Phase B validation
- Unifies validation workflows

**Implementation**:

- Add `--sidecar` option to `specfact repro` command
- Detect unannotated code (no icontract/beartype decorators)
- Generate sidecar harness for unannotated code paths
- Load bindings.yaml to map OpenAPI operations to callables
- Run CrossHair against generated harness (not source code)
- Support deterministic inputs and safe defaults

**Files**:

- `src/specfact_cli/validators/repro_checker.py` - Repro integration
- `src/specfact_cli/commands/repro.py` - Command extension

## Integration Points

### With Existing Commands

1. **`specfact repro`**: Add `--sidecar` flag to include sidecar validation
2. **`specfact analyze`**: Add sidecar results to contract coverage analysis
3. **`specfact contract`**: Use sidecar for contract population/enrichment

### With Existing Utilities

1. **`console.py`**: Use existing Rich console utilities
2. **`env_manager.py`**: Use existing environment detection
3. **`structure.py`**: Use existing SpecFact directory structure

### With Existing Models

1. **Contract models**: Use existing OpenAPI contract models
2. **Bundle models**: Extend with sidecar configuration
3. **Report models**: Extend with sidecar execution results

## Migration Path

### Phase 1: CLI Command (This Proposal)

- Implement `specfact validate sidecar` command
- Port core logic from bash scripts
- Maintain template compatibility

### Phase 9: CrossHair Summary Reporting (Issue #55)

- Parse CrossHair output to extract summary statistics (confirmed/not confirmed/violations)
- Generate `crosshair-summary.json` file in reports directory
- Display summary in console after CrossHair execution

### Phase 10: Safe Defaults for Specmatic (Issue #56)

- Auto-detect missing service/client configuration
- Auto-skip Specmatic with clear message when no service available
- Make auto-skip the default behavior for libraries

### Phase 11: Repro Integration (Issue #57)

- Add `--sidecar` option to `specfact repro` command
- Support unannotated code validation via sidecar harness
- Add deterministic inputs and safe defaults for sidecar repro mode

### Phase 2: Integration (Future)

- Integrate with `specfact analyze`
- Add sidecar results to bundle reports

### Phase 3: Enhancement (Future)

- Add new framework extractors
- Improve schema extraction
- Add contract enrichment via AI

## Testing Strategy

1. **Unit Tests**: Framework extractors, harness generator, contract populator
2. **Integration Tests**: Full sidecar workflow with test repositories
3. **E2E Tests**: CLI command execution with real projects
4. **Backward Compatibility Tests**: Verify template-based workspaces still work

## Performance Considerations

- **Parallel Execution**: CrossHair analysis can run in parallel for multiple contracts
- **Caching**: Cache framework detection results
- **Incremental Updates**: Only regenerate harness when contracts change
- **Progress Reporting**: Show progress for long-running operations (CrossHair, Specmatic)
