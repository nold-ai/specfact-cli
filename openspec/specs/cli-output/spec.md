# cli-output Specification

## Purpose
TBD - created by archiving change enhance-cli-terminal-output. Update Purpose after archive.
## Requirements
### Requirement: Terminal Capability Detection

The system SHALL detect terminal capabilities to determine appropriate output formatting.

#### Scenario: Detect Color Support

- **GIVEN** terminal environment
- **WHEN** `detect_terminal_capabilities()` is called
- **THEN** detects color support via:
  - `NO_COLOR` environment variable (if set, colors disabled)
  - `FORCE_COLOR` environment variable (if "1", colors enabled)
  - `TERM` and `COLORTERM` environment variables (terminal type indicators)
  - TTY check (`sys.stdout.isatty()`)
- **AND** returns `TerminalCapabilities` with `supports_color` boolean

#### Scenario: Detect CI/CD Environment

- **GIVEN** terminal environment
- **WHEN** `detect_terminal_capabilities()` is called
- **THEN** detects CI/CD environment via:
  - `CI` environment variable (generic CI indicator)
  - `GITHUB_ACTIONS` environment variable (GitHub Actions)
  - `GITLAB_CI` environment variable (GitLab CI)
  - Other common CI environment variables
- **AND** returns `TerminalCapabilities` with `is_ci` boolean
- **AND** disables animations when `is_ci=True`

#### Scenario: Detect Interactive Terminal

- **GIVEN** terminal environment
- **WHEN** `detect_terminal_capabilities()` is called
- **THEN** detects interactive terminal via:
  - `sys.stdout.isatty()` check
  - `sys.stdin.isatty()` check (if needed)
- **AND** returns `TerminalCapabilities` with `is_interactive` boolean
- **AND** determines animation support based on interactive status and CI detection

### Requirement: Console Configuration

The system SHALL configure Rich Console based on terminal capabilities.

#### Scenario: Configure Console for Full Terminal

- **GIVEN** terminal supports colors and animations
- **WHEN** `get_console_config()` is called
- **THEN** returns Console configuration with:
  - `force_terminal=True` (if needed for Rich features)
  - `no_color=False`
  - Appropriate `width` and `legacy_windows` settings
- **AND** Console instance supports Rich markup and colors

#### Scenario: Configure Console for Basic Terminal

- **GIVEN** terminal does not support colors or animations
- **WHEN** `get_console_config()` is called
- **THEN** returns Console configuration with:
  - `force_terminal=False`
  - `no_color=True`
  - Appropriate width settings
- **AND** Console instance renders plain text without markup

#### Scenario: Configure Console for CI/CD

- **GIVEN** CI/CD environment detected
- **WHEN** `get_console_config()` is called
- **THEN** returns Console configuration with:
  - `force_terminal=False`
  - `no_color=True` (unless FORCE_COLOR=1)
  - Width appropriate for log output
- **AND** Console instance produces readable log output

### Requirement: Progress Bar Configuration

The system SHALL configure Rich Progress bars based on terminal capabilities.

#### Scenario: Configure Progress for Full Terminal

- **GIVEN** terminal supports animations
- **WHEN** `get_progress_config()` is called
- **THEN** returns Progress configuration with:
  - `SpinnerColumn()` for animated spinner
  - `BarColumn()` for progress bar
  - `TextColumn()` for descriptions and percentages
  - `TimeElapsedColumn()` for elapsed time
- **AND** Progress instance displays animated progress indicators

#### Scenario: Configure Progress for Basic Terminal

- **GIVEN** terminal does not support animations
- **WHEN** `get_progress_config()` is called
- **THEN** returns Progress configuration with:
  - `TextColumn()` only (no SpinnerColumn or BarColumn)
  - Plain text descriptions
- **AND** Progress instance displays text updates without animations

#### Scenario: Configure Progress for CI/CD

- **GIVEN** CI/CD environment detected
- **WHEN** `get_progress_config()` is called
- **THEN** returns Progress configuration with:
  - `TextColumn()` only (no animations)
  - Plain text descriptions suitable for log output
- **AND** Progress updates are visible in CI/CD logs

### Requirement: Plain Text Progress Reporting

The system SHALL provide plain text progress updates when animations are disabled.

#### Scenario: Emit Plain Text Progress Updates

- **GIVEN** terminal does not support animations
- **WHEN** long-running operation is in progress
- **THEN** emits plain text updates to stdout:
  - Format: `"{description}... {percentage}% ({current}/{total})"`
  - Updates throttled (every 1 second or 10% progress, whichever comes first)
  - Updates flushed immediately (`flush=True`)
- **AND** updates are visible in CI/CD logs and embedded terminals

#### Scenario: Throttle Progress Updates

- **GIVEN** plain text progress reporting is active
- **WHEN** progress updates are emitted
- **THEN** throttles updates to:
  - Maximum once per second (time-based throttling)
  - Or when progress increases by 10% (progress-based throttling)
  - Whichever threshold is reached first
- **AND** final update is always emitted (100% or completion)

### Requirement: Runtime Integration

The system SHALL integrate terminal detection with runtime configuration.

#### Scenario: Terminal Mode Detection

- **GIVEN** runtime configuration module
- **WHEN** `get_terminal_mode()` is called
- **THEN** returns `TerminalMode` enum value:
  - `GRAPHICAL`: Full terminal with Rich features
  - `BASIC`: Basic terminal with limited features
  - `MINIMAL`: CI/CD or non-interactive (plain text only)
- **AND** mode is determined from terminal capabilities

#### Scenario: Console Instance Caching

- **GIVEN** terminal mode is detected
- **WHEN** `get_configured_console()` is called multiple times
- **THEN** creates Console instance once per terminal mode
- **AND** caches instance for subsequent calls
- **AND** returns cached instance when terminal mode unchanged

#### Scenario: Integration with Operational Mode

- **GIVEN** operational mode detection (CI/CD vs interactive)
- **WHEN** terminal mode is determined
- **THEN** considers operational mode in terminal capability detection
- **AND** CI/CD operational mode implies basic/minimal terminal mode
- **AND** interactive operational mode allows graphical terminal mode

### Requirement: Command Module Updates

The system SHALL update all command modules to use configured Console and Progress.

#### Scenario: Import Command Uses Configured Console

- **GIVEN** `import_cmd.py` module
- **WHEN** command executes
- **THEN** uses `get_configured_console()` instead of `Console()`
- **AND** Console instance is configured based on terminal capabilities
- **AND** output formatting adapts to terminal type

#### Scenario: Sync Command Uses Configured Progress

- **GIVEN** `sync.py` module
- **WHEN** command executes with progress tracking
- **THEN** uses `get_progress_config()` for Progress configuration
- **AND** Progress instance adapts to terminal capabilities
- **AND** progress indicators work in both graphical and basic terminals

#### Scenario: All Commands Support Both Modes

- **GIVEN** any command module using Console or Progress
- **WHEN** command executes
- **THEN** works correctly in:
  - Full graphical terminals (Rich features enabled)
  - Basic terminals (plain text output)
  - CI/CD environments (log-friendly output)
- **AND** same information content in all modes

### Requirement: Backward Compatibility

The system SHALL maintain backward compatibility with existing Rich features.

#### Scenario: Full Terminals Still Use Rich Features

- **GIVEN** full terminal with Rich support
- **WHEN** command executes
- **THEN** uses Rich Console with colors and markup
- **AND** uses Rich Progress with animations
- **AND** output matches previous behavior (no regression)

#### Scenario: Environment Variable Overrides

- **GIVEN** environment variables for terminal control
- **WHEN** `NO_COLOR=1` is set
- **THEN** disables colors even in full terminals
- **AND** respects user preference
- **WHEN** `FORCE_COLOR=1` is set
- **THEN** enables colors even in CI/CD
- **AND** allows explicit override

### Requirement: Global Debug Output Control

The CLI SHALL support a global `--debug` flag that enables debug output across all commands. Debug output SHALL only be shown when explicitly requested by the user. The main CLI callback SHALL support a global `--debug` option that sets debug mode for the entire command execution. Debug mode state SHALL be managed globally via `runtime.set_debug_mode()`, and all commands SHALL be able to access debug mode via `runtime.is_debug_mode()`.

**Rationale**: Users need diagnostic information (URLs, authentication status, API details) for troubleshooting, but this information should not clutter normal output. Debug mode provides controlled access to diagnostic information.

#### Scenario: Enable Debug Mode for Troubleshooting

**Given** a user running any SpecFact CLI command  
**When** the user provides the `--debug` flag  
**Then** debug messages (URLs, authentication status, API details) should be displayed  
**And** debug messages should be suppressed when `--debug` flag is not provided

**Example**:

```bash
# Debug output enabled
specfact backlog refine ado --debug --ado-org myorg --ado-project myproject

# Debug output suppressed (default)
specfact backlog refine ado --ado-org myorg --ado-project myproject
```

#### Scenario: Debug Print Helper Function

**Given** code that needs to output diagnostic information  
**When** the code calls `debug_print()` helper function  
**Then** the message should only be displayed if `--debug` flag was provided  
**And** the message should be suppressed if `--debug` flag was not provided

**Example**:

```python
from specfact_cli.runtime import debug_print

# Only shows if --debug flag is set
debug_print(f"[dim]ADO WIQL URL: {url}[/dim]")
debug_print(f"[dim]ADO Auth: {auth_header_preview}[/dim]")
```

#### Scenario: Global Debug Flag

**Given** the main CLI application  
**When** a user provides `--debug` flag  
**Then** debug mode should be enabled globally  
**And** all `debug_print()` calls should output messages  
**And** debug mode should persist for the entire command execution

