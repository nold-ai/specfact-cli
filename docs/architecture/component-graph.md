# SpecFact CLI Component Graph

## High-Level System Architecture

```mermaid
graph TD
    A[CLI Entry Point] --> B[Command Registry]
    B --> C[Module Discovery]
    C --> D[Lazy Loading]
    D --> E[Module Execution]
    
    A --> F[Mode Detection]
    F --> G[CI/CD Mode]
    F --> H[CoPilot Mode]
    
    E --> I[Adapters]
    I --> J[Bridge Adapters]
    I --> K[Backlog Adapters]
    I --> L[DevOps Adapters]
    
    E --> M[Analyzers]
    M --> N[Code Analyzer]
    M --> O[Graph Analyzer]
    M --> P[Contract Extractor]
    
    E --> Q[Generators]
    Q --> R[Plan Generator]
    Q --> S[Protocol Generator]
    Q --> T[Report Generator]
    
    E --> U[Validators]
    U --> V[Contract Validator]
    U --> W[FSM Validator]
    U --> X[Schema Validator]
```

## Core Component Relationships

### Main CLI Flow

```mermaid
graph LR
    cli[cli.py] --> registry[CommandRegistry]
    registry --> bootstrap[Bootstrap]
    bootstrap --> modules[Module Packages]
    modules --> commands[Command Implementations]
    commands --> adapters[Adapters]
    commands --> analyzers[Analyzers]
    commands --> generators[Generators]
    commands --> validators[Validators]
```

### Module System Architecture

```mermaid
graph TD
    Registry[CommandRegistry] -->|register| Modules[Module Packages]
    Modules -->|module-package.yaml| Manifest[Module Manifest]
    Modules -->|src/app.py| Entry[Module Entry Point]
    Entry -->|import| Commands[Command Implementations]
    
    Registry -->|lazy load| Loaders[Module Loaders]
    Loaders -->|on demand| Commands
    
    State[Module State] -->|~/.specfact/registry/modules.json| Registry
    State -->|enabled/disabled| Modules
```

### Adapter System Architecture

```mermaid
graph TD
    AdapterRegistry[AdapterRegistry] -->|register| BaseAdapter[BridgeAdapter]
    BaseAdapter -->|implement| OpenSpecAdapter[OpenSpecAdapter]
    BaseAdapter -->|implement| SpecKitAdapter[SpecKitAdapter]
    BaseAdapter -->|implement| GitHubAdapter[GitHubAdapter]
    BaseAdapter -->|implement| ADOAdapter[ADOAdapter]
    
    Commands -->|get_adapter| AdapterRegistry
    AdapterRegistry -->|return| SpecificAdapter[Concrete Adapter]
    SpecificAdapter -->|import/export| ExternalTools[External Tools]
```

## Data Flow Architecture

### Plan Bundle Processing Flow

```mermaid
graph LR
    Input[YAML/Markdown Files] --> Parser[Bundle Parser]
    Parser --> Models[Pydantic Models]
    Models --> Validator[Schema Validator]
    Validator --> Analyzer[Code Analyzer]
    Analyzer --> Generator[Plan Generator]
    Generator --> Output[Generated Artifacts]
```

### Contract Validation Flow

```mermaid
graph TD
    Code[Source Code] --> Extractor[Contract Extractor]
    Extractor --> Contracts[Runtime Contracts]
    Contracts --> Explorer[CrossHair Explorer]
    Explorer --> Counterexamples[Counterexamples]
    
    Code --> Static[Static Analyzer]
    Static --> Issues[Code Issues]
    
    Contracts --> Sentinel[Runtime Sentinel]
    Sentinel --> Gate[No-Escape Gate]
    Gate --> Result[PR Approved/Blocked]
```

## Interface Boundaries

### Core-Module Isolation

```mermaid
graph LR
    Core[Core Runtime] -->|CommandRegistry| Modules[Feature Modules]
    Core -->|no direct imports| Modules
    Modules -->|explicit interfaces| Core
    
    Core --> cli[cli.py]
    Core --> registry[registry/]
    Core --> models[models/]
    Core --> utils[utils/]
    Core --> contracts[contracts/]
    
    Modules --> commands[commands/]
    Modules --> adapters[adapters/]
    Modules --> analyzers[analyzers/]
```

### Adapter Interface Boundary

```mermaid
graph TD
    Commands -->|BridgeAdapter interface| Adapters
    Adapters -->|detect| Boolean
    Adapters -->|import_artifact| ProjectBundle
    Adapters -->|export_artifact| ToolFormat
    Adapters -->|load_change_tracking| ChangeTracking
    Adapters -->|save_change_tracking| None
    
    Adapters -->|External Tools| SpecKit
    Adapters -->|External Tools| OpenSpec
    Adapters -->|External Tools| GitHub
    Adapters -->|External Tools| AzureDevOps
```

## Physical Architecture

### File System Layout

```mermaid
graph TD
    Root[specfact-cli/] --> Src[src/specfact_cli/]
    Src --> CLI[cli.py]
    Src --> Registry[registry/]
    Src --> Modules[modules/]
    Src --> Commands[commands/]
    Src --> Adapters[adapters/]
    Src --> Models[models/]
    
    Root --> Docs[docs/]
    Root --> Tests[tests/]
    Root --> OpenSpec[openspec/]
    Root --> Resources[resources/]
```

### Module Package Structure

```mermaid
graph TD
    Module[modules/<name>/] --> Manifest[module-package.yaml]
    Module --> Src[src/]
    Src --> App[app.py]
    Src --> Commands[commands.py]
    
    Manifest -->|metadata| Registry
    App -->|Typer app| Commands
    Commands -->|implementation| ModuleLogic
```

## Key Interfaces and Contracts

### CommandRegistry Interface

- `register_command(name: str, loader: Callable, metadata: CommandMetadata)`
- `get_typer_app(name: str) -> typer.Typer`
- `list_commands() -> list[CommandMetadata]`

### BridgeAdapter Interface

- `detect(repo_path: Path) -> bool`
- `import_artifact(artifact_key: str, artifact_path: Path, project_bundle: Any) -> None`
- `export_artifact(artifact_key: str, artifact_data: Any) -> Path | dict`
- `load_change_tracking(bundle_dir: Path) -> ChangeTracking | None`
- `save_change_tracking(bundle_dir: Path, change_tracking: ChangeTracking) -> None`

### Module Package Contract

- `name: str` - Module identifier
- `version: str` - Semantic version
- `commands: list[str]` - Command names provided
- `pip_dependencies: list[str]` - Optional Python dependencies
- `module_dependencies: list[str]` - Module dependencies

## Architecture Decision Records

### ADR-001: Modular Command Registry

**Status**: Implemented in v0.27
**Decision**: Replace hard-wired command imports with lazy-loaded module registry
**Rationale**: Faster startup, independent module delivery, better test isolation

### ADR-002: Contract-First Development

**Status**: Core principle since v0.1
**Decision**: All public APIs must have @icontract and @beartype decorators
**Rationale**: Runtime validation, better error messages, contract exploration

### ADR-003: Dual-Mode Operation

**Status**: Implemented in v0.21
**Decision**: Support both CI/CD (fast, automated) and CoPilot (interactive) modes
**Rationale**: Serve different user needs without compromising either experience

### ADR-004: Bridge Adapter Pattern

**Status**: Implemented in v0.21.1
**Decision**: Use plugin-based adapter registry for tool integrations
**Rationale**: Extensible architecture, no hard-coded adapter checks in core
