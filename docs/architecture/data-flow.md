# SpecFact CLI Data Flow Architecture

## Command execution flow

```mermaid
graph LR
    Input[CLI Input] --> Parse[Typer Parse]
    Parse --> Lookup[Registry Lookup]
    Lookup --> Load[Lazy Module Load]
    Load --> Execute[Command Execute]
    Execute --> AdapterOrAnalysis[Adapter or Analysis Layer]
    AdapterOrAnalysis --> Output[Console or File Output]
```

## Bridge sync flow

```mermaid
sequenceDiagram
    participant User
    participant Command as sync bridge
    participant Probe as Bridge Probe
    participant Adapter as BridgeAdapter
    participant Bundle as ProjectBundle

    User->>Command: run sync
    Command->>Probe: select adapter via detect/capabilities
    Probe->>Adapter: detect + get_capabilities
    Adapter->>Bundle: import/export artifacts
    Command-->>User: summary + status
```

## Error flow

- Validate inputs with contracts.
- Convert operational failures into actionable command errors.
- Log adapter and lifecycle non-fatal issues with bridge logger.
