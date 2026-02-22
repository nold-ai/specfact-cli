# SpecFact CLI Module System Architecture

## Module Registry Architecture

### Overview

The SpecFact CLI uses a **modular command registry** introduced in v0.27 that enables:

- **Lazy Loading**: Modules are loaded only when their commands are invoked
- **Fast Startup**: No need to import all modules at startup
- **Independent Delivery**: Modules can be developed and delivered independently
- **Explicit Interfaces**: Clear boundaries between core and modules

### Core Components

```mermaid
classDiagram
    class CommandRegistry {
        +register_command(name, loader, metadata)
        +get_typer_app(name)
        +list_commands()
        +get_command_help(name)
    }
    
    class ModulePackage {
        +name: str
        +version: str
        +commands: list[str]
        +manifest: ModuleManifest
        +entry_point: str
    }
    
    class ModuleManifest {
        +name: str
        +version: str
        +commands: list[str]
        +pip_dependencies: list[str]
        +module_dependencies: list[str]
        +tier: str
        +addon_id: str
    }
    
    class ModuleLoader {
        +load()
    }
    
    CommandRegistry "1" *-- "0..*" ModulePackage : registers
    ModulePackage "1" *-- "1" ModuleManifest : contains
    ModulePackage "1" *-- "1" ModuleLoader : uses
```

## Module Discovery and Registration

### Discovery Process

```mermaid
sequenceDiagram
    participant CLI as cli.py
    participant Bootstrap as bootstrap.py
    participant Registry as CommandRegistry
    participant Discovery as module_packages.py
    participant Modules as Module Packages
    
    CLI->>Bootstrap: register_builtin_commands()
    Bootstrap->>Discovery: discover_module_packages()
    Discovery->>Modules: Scan modules/ directory
    Modules-->>Discovery: Return module manifests
    Discovery->>Discovery: Parse module-package.yaml
    Discovery->>Discovery: Validate manifests
    
    loop For each valid module
        Discovery->>Registry: register_command()
        Registry->>Registry: Store loader & metadata
    end
    
    Registry-->>Bootstrap: Registration complete
    Bootstrap-->>CLI: Ready for commands
```

### Registration Flow

```mermaid
graph TD
    A[Scan modules/ directory] --> B[Find module-package.yaml files]
    B --> C[Parse YAML manifest]
    C --> D[Validate manifest schema]
    D --> E[Check module dependencies]
    E --> F[Create module loader]
    F --> G[Register with CommandRegistry]
    G --> H[Store in registry]
```

## Lazy Loading Mechanism

### Load-on-Demand Pattern

```mermaid
sequenceDiagram
    participant User
    participant CLI as cli.py
    participant Registry as CommandRegistry
    participant Loader as ModuleLoader
    participant Module as Module Code
    
    User->>CLI: specfact sync bridge --adapter speckit
    CLI->>Registry: get_typer_app("sync")
    Registry->>Loader: load() - first time only
    Loader->>Module: import specfact_cli.modules.sync
    Module-->>Loader: Return Typer app
    Loader-->>Registry: Return app
    Registry-->>CLI: Return app
    CLI->>Module: Execute command
```

### Loading States

```mermaid
stateDiagram-v2
    [*] --> NotLoaded
    NotLoaded --> Loading: Command invoked
    Loading --> Loaded: Import successful
    Loading --> Failed: Import failed
    
    Loaded --> Executing: Command executes
    Executing --> [*]: Command complete
    
    Failed --> Fallback: Try fallback
    Fallback --> Loaded: Fallback successful
    Fallback --> [*]: Exit with error
```

## Module Package Structure

### Standard Module Layout

```bash
modules/<module-name>/
├── module-package.yaml      # Module manifest
├── src/
│   ├── __init__.py         # Python package init
│   ├── app.py              # Typer app entry point
│   └── commands.py         # Command implementations
└── tests/                  # Module-specific tests (optional)
```

### Module Manifest Example

```yaml
# module-package.yaml
name: sync
version: "1.0.0"
commands:
  - sync
  - bridge
command_help:
  sync: "Synchronize SpecFact artifacts with external tools"
  bridge: "Bridge-based bidirectional synchronization"
pip_dependencies:
  - "ruamel.yaml>=0.18.0"
module_dependencies:
  - core
  - registry
core_compatibility: "^0.27.0"
tier: community
addon_id: specfact.sync
```

## Module Entry Point Pattern

### Standard app.py Structure

```python
# modules/<name>/src/app.py
from typer import Typer
from . import commands

# Create Typer app for this module
app = Typer(
    name="sync",
    help="Synchronize SpecFact artifacts with external tools",
    rich_markup_mode="rich",
)

# Import commands (this triggers registration)
from .commands import bridge, repository

# Add command groups
app.add_typer(bridge.app, name="bridge")
app.add_typer(repository.app, name="repository")
```

### Command Implementation Pattern

```python
# modules/<name>/src/commands.py
from typer import Typer
from beartype import beartype
from icontract import require, ensure

app = Typer(name="bridge", help="Bridge-based synchronization")

@app.command()
@require(lambda adapter: adapter in ["speckit", "openspec", "github"])
@beartype
def sync(
    adapter: str,
    bundle: str,
    bidirectional: bool = False,
) -> None:
    """Synchronize using bridge adapter."""
    # Implementation here
```

## Module State Management

### State File Structure

```json
{
  "modules": [
    {
      "id": "sync",
      "version": "1.0.0",
      "enabled": true,
      "dependencies": ["core", "registry"]
    },
    {
      "id": "analyze",
      "version": "1.2.0",
      "enabled": false
    }
  ]
}
```

### State Management Flow

```mermaid
graph TD
    A[Load ~/.specfact/registry/modules.json] --> B[Parse module states]
    B --> C[Check enabled/disabled status]
    C --> D[Apply to CommandRegistry]
    D --> E[Command execution]
    E --> F[State changed?]
    F -->|Yes| G[Update modules.json]
    F -->|No| H[No change]
    G --> H
    H --> I[*] 
```

## Module Dependency Management

### Dependency Graph

```mermaid
graph TD
    sync --> core
    sync --> registry
    analyze --> core
    analyze --> code_analyzer
    plan --> core
    plan --> generators
    backlog --> core
    backlog --> adapters
```

### Dependency Resolution

```mermaid
flowchart TD
    A[Enable module X] --> B[Check dependencies]
    B --> C{All dependencies available?}
    C -->|Yes| D[Enable module X]
    C -->|No| E[Enable missing dependencies]
    E --> F{Dependencies enabled?}
    F -->|Yes| D
    F -->|No| G[Error: Circular dependency]
```

## Core-Module Isolation Principle

### Architecture Boundary

```mermaid
graph LR
    Core[Core Runtime] -->|CommandRegistry| Modules[Feature Modules]
    Core -->|No direct imports| Modules
    Modules -->|Explicit interfaces| Core
    
    subgraph Core
        cli.py
        registry/
        models/
        contracts/
        utils/
    end
    
    subgraph Modules
        modules/sync/
        modules/analyze/
        modules/plan/
        modules/backlog/
    end
```

### Isolation Enforcement

1. **No direct imports**: Core never imports from `specfact_cli.modules.*`
2. **Interface-based**: All communication through `CommandRegistry`
3. **Contract validation**: Module interfaces validated at registration
4. **Static checks**: CI tests enforce isolation boundaries

## Module Lifecycle Commands

### Command Reference

```bash
# List available modules
specfact module list

# Enable a module
specfact module enable sync

# Disable a module
specfact module disable analyze

# Install a marketplace module
specfact module install specfact/backlog

# Uninstall a module
specfact module uninstall backlog

# Show module info
specfact module info sync
```

### Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Installed
    Installed --> Enabled: specfact module enable
    Installed --> Uninstalled: specfact module uninstall
    
    Enabled --> Disabled: specfact module disable
    Disabled --> Enabled: specfact module enable
    
    Enabled --> Updated: specfact module upgrade
    Updated --> Enabled: Update complete
    
    Uninstalled --> [*]
```

## Module Development Workflow

### Development Process

```mermaid
graph TD
    A[Define module scope] --> B[Create module-package.yaml]
    B --> C[Implement commands]
    C --> D[Add contracts @icontract, @beartype]
    D --> E[Write tests]
    E --> F[Register with CommandRegistry]
    F --> G[Test lazy loading]
    G --> H[Validate isolation]
    H --> I[Document module]
```

### Testing Strategy

```mermaid
graph TD
    A[Unit tests] --> B[Contract tests]
    B --> C[Integration tests]
    C --> D[Lazy loading tests]
    D --> E[Isolation tests]
    E --> F[E2E tests]
```

## Performance Characteristics

### Loading Performance

| Scenario | Time | Notes |
|----------|------|-------|
| Startup (no commands) | < 100ms | Only core loaded |
| First command | 200-500ms | Module loaded on demand |
| Subsequent commands | < 100ms | Module already loaded |
| All modules loaded | 1-2s | Rare case |

### Memory Usage

| Component | Memory | Notes |
|-----------|--------|-------|
| Core runtime | 10-20MB | Always loaded |
| Single module | 2-5MB | Loaded on demand |
| All modules | 50-80MB | Worst case |

## Module Security

### Security Boundaries

```mermaid
graph TD
    A[Core runtime] --> B[Module sandbox]
    B --> C[Contract validation]
    C --> D[Type checking]
    D --> E[Resource limits]
    E --> F[Timeout enforcement]
```

### Security Practices

1. **Contract-first**: All module interfaces have runtime contracts
2. **Type safety**: @beartype for runtime type checking
3. **Isolation**: No direct core imports from modules
4. **Validation**: Module manifests validated at load time
5. **Timeouts**: Command execution timeouts enforced

## Module Versioning and Compatibility

### Versioning Strategy

```mermaid
graph TD
    A[Module v1.0.0] --> B[Core v0.27.0]
    B --> C[Module v1.1.0]
    C --> D[Core v0.27.0-0.28.0]
    D --> E[Module v2.0.0]
    E --> F[Core v0.28.0+]
```

### Compatibility Matrix

| Module Version | Core Compatibility | Notes |
|----------------|-------------------|-------|
| 1.x.x | ^0.27.0 | Initial module system |
| 2.x.x | ^0.28.0 | Enhanced features |
| 3.x.x | ^0.29.0 | Breaking changes |

## Module Registry Implementation Details

### CommandRegistry Class

```python
class CommandRegistry:
    def __init__(self):
        self._commands: dict[str, tuple[Callable, CommandMetadata]] = {}
        self._help_cache: dict[str, str] = {}
    
    def register_command(
        self,
        name: str,
        loader: Callable[[], typer.Typer],
        metadata: CommandMetadata
    ) -> None:
        """Register a command with the registry."""
        self._commands[name] = (loader, metadata)
    
    def get_typer_app(self, name: str) -> typer.Typer:
        """Get Typer app for command (lazy load)."""
        if name not in self._commands:
            raise ValueError(f"Command {name} not registered")
        
        loader, _ = self._commands[name]
        return loader()
    
    def list_commands(self) -> list[CommandMetadata]:
        """List all registered commands."""
        return [meta for _, meta in self._commands.values()]
```

### Module Loader Implementation

```python
class ModuleLoader:
    def __init__(self, module_path: Path, manifest: ModuleManifest):
        self.module_path = module_path
        self.manifest = manifest
        self._app: typer.Typer | None = None
    
    def load(self) -> typer.Typer:
        """Lazy load the module."""
        if self._app is None:
            # Import the module dynamically
            spec = importlib.util.spec_from_file_location(
                f"specfact_cli.modules.{self.manifest.name}.src.app",
                self.module_path / "src" / "app.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._app = module.app
        
        return self._app
```

## Module Marketplace Integration

### Marketplace Architecture

```mermaid
graph TD
    A[CLI] --> B[Registry Client]
    B --> C[Marketplace API]
    C --> D[Module Index]
    D --> E[Module Download]
    E --> F[Local Installation]
    F --> G[Module Registration]
```

### Installation Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Registry
    participant Marketplace
    participant Local
    
    User->>CLI: specfact module install specfact/backlog
    CLI->>Registry: fetch_index()
    Registry->>Marketplace: GET /index.json
    Marketplace-->>Registry: module metadata
    Registry-->>CLI: available modules
    
    CLI->>Marketplace: GET /download/specfact/backlog/v1.0.0
    Marketplace-->>CLI: module tarball
    
    CLI->>Local: extract_to(~/.specfact/marketplace-modules/)
    Local->>Local: verify_checksum()
    Local->>Local: validate_compatibility()
    
    Local->>CLI: register_module()
    CLI->>Registry: register_command()
    
    CLI-->>User: Installation complete
```

## Module Testing Strategy

### Test Pyramid

```mermaid
graph TD
    A[Unit Tests] --> B[Module Tests]
    B --> C[Integration Tests]
    C --> D[Registry Tests]
    D --> E[E2E Tests]
```

### Test Coverage Targets

| Test Type | Coverage Target | Focus |
|-----------|----------------|-------|
| Unit tests | 80%+ | Individual functions |
| Contract tests | 90%+ | Public interfaces |
| Integration tests | 70%+ | Module interactions |
| E2E tests | Key scenarios | User workflows |

## Module Documentation Requirements

### Required Documentation

1. **Module README**: Overview and usage
2. **Command help**: Typer help text
3. **Interface contracts**: @icontract decorators
4. **Examples**: Usage examples
5. **Error handling**: Documented error cases

### Documentation Structure

```bash
modules/<name>/
├── README.md              # Module overview
├── USAGE.md               # Usage examples
├── CONTRACTS.md           # Interface contracts
└── CHANGELOG.md           # Module changes
```

## Module Evolution and Deprecation

### Deprecation Policy

```mermaid
graph TD
    A[v1.0.0 - Current] --> B[v1.1.0 - Enhanced]
    B --> C[v2.0.0 - Breaking]
    C --> D[v1.0.0 - Deprecated]
    D --> E[v1.0.0 - Removed]
```

### Migration Path

1. **Announce deprecation** in release notes
2. **Add deprecation warnings** to console output
3. **Provide migration guide** in documentation
4. **Maintain backward compatibility** for 2 major versions
5. **Remove deprecated features** in next major version

## Future Enhancements

### Planned Features

1. **Dynamic module loading** from remote sources
2. **Module update notifications**
3. **Module dependency graph** visualization
4. **Module performance profiling**
5. **Enhanced security sandboxing**

### Roadmap

```mermaid
gantt
    title Module System Roadmap
    dateFormat  YYYY-MM
    section Core Features
    Lazy Loading           :done, core-001, 2025-12, 2026-01
    Module Registry        :done, core-002, 2026-01, 2026-02
    
    section Enhancements
    Marketplace Integration :active, enh-001, 2026-02, 2026-04
    Dependency Management  :enh-002, 2026-03, 2026-05
    Performance Optimization: enh-003, 2026-04, 2026-06
```
