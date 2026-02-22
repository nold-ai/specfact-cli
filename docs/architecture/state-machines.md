# SpecFact CLI State Machine Logic

## CLI command lifecycle

```mermaid
stateDiagram-v2
    [*] --> Parse
    Parse --> ResolveCommand
    ResolveCommand --> LoadModule
    LoadModule --> Execute
    Execute --> Report
    Report --> [*]
```

## Mode selection (implemented)

```mermaid
stateDiagram-v2
    [*] --> ExplicitFlag
    ExplicitFlag --> Final: --mode provided
    ExplicitFlag --> Detect: no flag
    Detect --> Final
```

## Protocol FSM status

Protocol states and transitions are modeled in OpenSpec artifacts and data models.
Runtime FSM engine behavior is currently limited and tracked as planned work in `architecture-01-solution-layer`.
