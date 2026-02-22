# SpecFact CLI State Machine Logic

## CLI Workflow State Machines

### Main CLI Execution Flow

```mermaid
stateDiagram-v2
    [*] --> Startup
    Startup --> ModeDetection: Detect operational mode
    ModeDetection --> CommandRouting: Route to appropriate handler
    
    state ModeDetection {
        [*] --> AutoDetect
        AutoDetect --> CIDCD: CI/CD mode detected
        AutoDetect --> CoPilot: CoPilot mode detected
        AutoDetect --> Default: Default to CI/CD
    }
    
    state CommandRouting {
        [*] --> RegistryLookup
        RegistryLookup --> LoadModule: Module found
        LoadModule --> ExecuteCommand
        ExecuteCommand --> [*]
    }
```

### Module Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Discovery
    Discovery --> Registration: Module found
    Registration --> StateCheck: Check enabled status
    
    state StateCheck {
        [*] --> CheckState
        CheckState --> Enabled: Module enabled
        CheckState --> Disabled: Module disabled
        
        Enabled --> LoadOnDemand: Wait for command
        Disabled --> [*]: Skip loading
        
        LoadOnDemand --> Execute: Command invoked
        Execute --> [*]: Command completes
    }
```

### Protocol FSM (Finite State Machine)

```mermaid
stateDiagram-v2
    [*] --> INIT
    INIT --> PLAN: start_planning
    PLAN --> REQUIREMENTS: approve_plan
    REQUIREMENTS --> ARCHITECTURE: requirements_complete
    ARCHITECTURE --> CODE: architecture_approved
    CODE --> REVIEW: code_complete
    REVIEW --> DEPLOY: review_passed
    DEPLOY --> [*]: deploy_complete
    
    PLAN --> [*]: plan_rejected
    REQUIREMENTS --> PLAN: requirements_rework
    ARCHITECTURE --> REQUIREMENTS: architecture_rework
    CODE --> ARCHITECTURE: code_rework
    REVIEW --> CODE: review_rework
```

## Operational Mode State Transitions

### Mode Detection Logic

```mermaid
stateDiagram-v2
    [*] --> CheckExplicitFlag
    CheckExplicitFlag --> UseExplicit: --mode flag provided
    CheckExplicitFlag --> AutoDetect: No explicit flag
    
    AutoDetect --> CheckCoPilot: Check CoPilot availability
    CheckCoPilot --> UseCoPilot: CoPilot available
    CheckCoPilot --> UseCICD: CoPilot not available
    
    UseExplicit --> FinalMode
    UseCoPilot --> FinalMode
    UseCICD --> FinalMode
    
    FinalMode --> [*]
```

### CI/CD Mode State Machine

```mermaid
stateDiagram-v2
    [*] --> FastPath
    FastPath --> DirectExecution: Execute command directly
    DirectExecution --> StructuredOutput: Generate JSON/Markdown
    StructuredOutput --> [*]: Complete
    
    FastPath --> BudgetCheck: Check time budget
    BudgetCheck --> Continue: Budget OK
    BudgetCheck --> Timeout: Budget exceeded
    Timeout --> [*]: Exit with timeout error
```

### CoPilot Mode State Machine

```mermaid
stateDiagram-v2
    [*] --> EnhancedPrompt
    EnhancedPrompt --> ContextInjection: Add IDE context
    ContextInjection --> AgentRouting: Route to agent
    
    state AgentRouting {
        [*] --> SelectAgent
        SelectAgent --> AnalyzeAgent: analyze mode
        SelectAgent --> PlanAgent: plan mode
        SelectAgent --> SyncAgent: sync mode
        
        AnalyzeAgent --> InteractiveAssistance
        PlanAgent --> GuidedWizard
        SyncAgent --> ConflictResolution
        
        InteractiveAssistance --> [*]
        GuidedWizard --> [*]
        ConflictResolution --> [*]
    }
```

## Sync Operation State Machines

### Bridge Sync Flow

```mermaid
stateDiagram-v2
    [*] --> DetectAdapter
    DetectAdapter --> ConfigureBridge: Adapter found
    ConfigureBridge --> ProbeSource: Determine sync direction
    
    state ProbeSource {
        [*] --> CheckCapabilities
        CheckCapabilities --> Bidirectional: Full sync supported
        CheckCapabilities --> ReadOnly: Read-only sync
        
        Bidirectional --> SyncBoth: Sync in both directions
        ReadOnly --> ImportOnly: Import from external tool
        
        SyncBoth --> ConflictResolution
        ImportOnly --> ImportComplete
        
        ConflictResolution --> ApplyChanges
        ApplyChanges --> [*]: Sync complete
        ImportComplete --> [*]: Import complete
    }
```

### Repository Sync State Machine

```mermaid
stateDiagram-v2
    [*] --> InitialScan
    InitialScan --> DetectChanges: Compare states
    
    state DetectChanges {
        [*] --> AnalyzeDiffs
        AnalyzeDiffs --> HasChanges: Changes detected
        AnalyzeDiffs --> NoChanges: No changes
        
        HasChanges --> UpdateArtifacts: Generate updates
        UpdateArtifacts --> Validate: Check consistency
        Validate --> Apply: Commit changes
        Apply --> [*]: Sync complete
        
        NoChanges --> [*]: No action needed
    }
```

## Validation and Enforcement State Machines

### Contract Validation Flow

```mermaid
stateDiagram-v2
    [*] --> ExtractContracts
    ExtractContracts --> ValidateRuntime: Runtime contract checks
    ValidateRuntime --> ExploreContracts: CrossHair exploration
    
    state ExploreContracts {
        [*] --> RunCrossHair
        RunCrossHair --> FoundIssues: Counterexamples found
        RunCrossHair --> NoIssues: No issues found
        
        FoundIssues --> ReportViolations
        NoIssues --> StaticAnalysis
        
        ReportViolations --> [*]: Validation failed
        StaticAnalysis --> PropertyTests
        PropertyTests --> [*]: Validation passed
    }
```

### Enforcement Gate State Machine

```mermaid
stateDiagram-v2
    [*] --> CheckStage
    CheckStage --> Shadow: Shadow mode
    CheckStage --> Warn: Warn mode
    CheckStage --> Block: Block mode
    
    Shadow --> LogOnly: Log violations
    LogOnly --> [*]: Continue pipeline
    
    Warn --> WarnMedium: Warn on medium+ violations
    WarnMedium --> BlockHigh: Block on high violations
    BlockHigh --> [*]: Pipeline decision
    
    Block --> BlockAll: Block on medium+ violations
    BlockAll --> [*]: Pipeline blocked
```

## Error Handling State Machines

### Command Execution Error Flow

```mermaid
stateDiagram-v2
    [*] --> ExecuteCommand
    ExecuteCommand --> Success: Command succeeds
    ExecuteCommand --> Error: Command fails
    
    Success --> [*]: Complete
    
    Error --> HandleError
    HandleError --> Retryable: Retry possible
    HandleError --> Fatal: Fatal error
    
    Retryable --> Retry: Attempt retry
    Retry --> Success: Retry succeeds
    Retry --> MaxRetries: Max retries reached
    MaxRetries --> [*]: Exit with error
    
    Fatal --> LogError: Log detailed error
    LogError --> Exit: Exit gracefully
    Exit --> [*]
```

### Module Loading Error Flow

```mermaid
stateDiagram-v2
    [*] --> LoadModule
    LoadModule --> Success: Module loads
    LoadModule --> ImportError: Import failure
    LoadModule --> ContractError: Contract violation
    
    Success --> [*]: Continue
    
    ImportError --> Fallback: Try fallback
    Fallback --> Success: Fallback works
    Fallback --> FinalError: Fallback fails
    
    ContractError --> Validate: Check contracts
    Validate --> Invalid: Contract invalid
    Invalid --> [*]: Exit with contract error
    
    FinalError --> [*]: Exit with import error
```

## Agent Mode State Machines

### Analyze Agent Flow

```mermaid
stateDiagram-v2
    [*] --> SetupContext
    SetupContext --> CodeUnderstanding: Analyze code
    CodeUnderstanding --> PatternDetection: Detect patterns
    PatternDetection --> ConfidenceScoring: Score confidence
    ConfidenceScoring --> GenerateOutput: Create output
    GenerateOutput --> [*]: Complete
```

### Plan Agent Flow

```mermaid
stateDiagram-v2
    [*] --> BusinessLogic: Understand business context
    BusinessLogic --> FeatureExtraction: Extract features
    FeatureExtraction --> StoryGeneration: Generate stories
    StoryGeneration --> PlanValidation: Validate plan
    PlanValidation --> InteractiveReview: User review
    InteractiveReview --> [*]: Complete
```

### Sync Agent Flow

```mermaid
stateDiagram-v2
    [*] --> SourceDetection: Detect source
    SourceDetection --> ConflictAnalysis: Analyze conflicts
    ConflictAnalysis --> ResolutionStrategy: Choose strategy
    ResolutionStrategy --> ApplyResolution: Apply changes
    ApplyResolution --> ChangeExplanation: Explain changes
    ChangeExplanation --> Preview: Show preview
    Preview --> [*]: Complete
```

## Protocol State Machine Implementation

The protocol FSM is implemented using the following model:

```python
from pydantic import BaseModel
from typing import List, Optional

class Transition(BaseModel):
    """State machine transition."""
    from_state: str
    on_event: str
    to_state: str
    guard: Optional[str] = None

class ProtocolSpec(BaseModel):
    """FSM protocol specification."""
    states: List[str]
    start: str
    transitions: List[Transition]
```

### State Transition Example

```mermaid
stateDiagram-v2
    direction LR
    
    INIT --> PLAN: start_planning
    PLAN --> REQUIREMENTS: approve_plan[guard = plan_quality_gate_passes]
    REQUIREMENTS --> ARCHITECTURE: requirements_complete
    ARCHITECTURE --> CODE: architecture_approved
    CODE --> REVIEW: code_complete
    REVIEW --> DEPLOY: review_passed
    
    PLAN --> INIT: plan_rejected
    REQUIREMENTS --> PLAN: requirements_rework
    ARCHITECTURE --> REQUIREMENTS: architecture_rework
```

## State Machine Guard Conditions

### Common Guard Conditions

- `plan_quality_gate_passes`: All quality criteria met
- `requirements_complete`: All requirements documented
- `architecture_approved`: Architecture review passed
- `code_complete`: Implementation finished
- `review_passed`: Code review approved
- `budget_not_exceeded`: Time budget remaining

### Guard Implementation

```python
def plan_quality_gate_passes(plan: PlanBundle) -> bool:
    """Check if plan meets quality criteria."""
    return (
        len(plan.features) > 0 and
        all(len(feature.stories) > 0 for feature in plan.features) and
        plan.validation_status == "passed"
    )
```

## Event-Driven Architecture

### Event Types

- **Command Events**: `command_started`, `command_completed`, `command_failed`
- **Module Events**: `module_loaded`, `module_failed`
- **Sync Events**: `sync_started`, `conflict_detected`, `sync_completed`
- **Validation Events**: `validation_started`, `violation_found`, `validation_completed`

### Event Flow Example

```mermaid
stateDiagram-v2
    [*] --> CommandStarted
    CommandStarted --> ModuleLoading
    ModuleLoading --> ModuleLoaded
    ModuleLoaded --> ExecutionStarted
    ExecutionStarted --> EventProcessing
    
    state EventProcessing {
        [*] --> ProcessEvent
        ProcessEvent --> HandleSync: sync event
        ProcessEvent --> HandleValidation: validation event
        ProcessEvent --> HandleError: error event
        
        HandleSync --> SyncComplete
        HandleValidation --> ValidationComplete
        HandleError --> ErrorHandled
        
        SyncComplete --> [*]
        ValidationComplete --> [*]
        ErrorHandled --> [*]
    }
```

## State Persistence

### Module State Persistence

```mermaid
stateDiagram-v2
    [*] --> LoadState
    LoadState --> StateLoaded: ~/.specfact/registry/modules.json exists
    LoadState --> CreateDefault: No state file
    
    StateLoaded --> UseState: Apply module enable/disable
    CreateDefault --> UseState: Use default state
    
    UseState --> ExecuteCommands
    ExecuteCommands --> SaveState: State changed
    SaveState --> [*]: Persist to file
```

### Bridge Configuration Persistence

```mermaid
stateDiagram-v2
    [*] --> LoadConfig
    LoadConfig --> ConfigLoaded: Bridge config exists
    ConfigLoaded --> UseConfig: Apply configuration
    
    UseConfig --> ExecuteSync
    ExecuteSync --> ConfigChanged: Configuration modified
    ConfigChanged --> SaveConfig: Persist changes
    SaveConfig --> [*]: Config saved
```
