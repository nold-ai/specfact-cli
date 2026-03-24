## ADDED Requirements

### Requirement: CLI output SHALL degrade safely on non-UTF-8 terminals
The SpecFact CLI SHALL render help, startup, and other common command output without raising encoding exceptions on supported Windows, Linux, and macOS terminals. When the active output stream cannot encode configured Unicode glyphs, the CLI SHALL switch to an ASCII-safe fallback for affected symbols instead of crashing.

#### Scenario: Windows help rendering on a legacy code page
- **WHEN** a user runs a help or startup command in a terminal whose output encoding cannot represent the configured Unicode icons
- **THEN** the CLI completes successfully
- **AND** the rendered output uses encoding-safe fallback symbols for the unsupported glyphs

#### Scenario: UTF-8 terminal preserves rich symbols
- **WHEN** a user runs the same help or startup command in a UTF-8-capable terminal
- **THEN** the CLI completes successfully
- **AND** the configured rich Unicode symbols remain enabled

### Requirement: Runtime mismatch diagnostics SHALL be actionable
When automation or programmatic invocation reaches a SpecFact installation whose runtime, module path, or compiled dependencies are incompatible with the calling environment, the CLI SHALL fail with a compatibility error that identifies the failing component and the resolved installation context.

#### Scenario: External interpreter cannot load installed SpecFact module runtime
- **WHEN** a caller invokes backlog automation from a different interpreter environment than the one hosting the installed SpecFact stack
- **THEN** the CLI fails with a compatibility error instead of a raw low-level import traceback
- **AND** the error reports the unresolved module or compiled dependency
- **AND** the error explains which interpreter or installation boundary must be used

#### Scenario: Compatible installation resolves without manual path injection
- **WHEN** a caller invokes a supported SpecFact workflow from the interpreter that hosts the installed SpecFact runtime and module resources
- **THEN** the CLI resolves the required runtime and module paths without requiring manual `.specfact/modules/...` injection
