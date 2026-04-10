# Change: Enhance CLI Terminal Output for Embedded Terminals and CI/CD

## Why

When running SpecFact CLI commands in embedded terminals (like Cursor's terminal, CI/CD pipelines, or non-interactive environments), users don't see progress animations, colors, or Rich console features. This makes it appear as if "no progress" is happening, especially during long-running operations like `import from-code` which can take 2-5 minutes.

The CLI currently uses Rich Console and Progress bars with animations (SpinnerColumn, BarColumn) without terminal capability detection. This causes:

1. **No visual feedback** in embedded terminals - users can't tell if the command is working
2. **Broken output** in CI/CD environments - Rich features may not render correctly
3. **Poor user experience** - commands appear "stuck" when they're actually processing

Rich Console supports terminal detection via `force_terminal`, `no_color`, and `is_terminal` parameters, but we're not using them. We need to:

- Detect terminal capabilities (colors, animations, interactive features)
- Provide fallback to plain text output for CI/CD/embedded terminals
- Ensure progress indicators work in both graphical and basic terminal modes
- Maintain backward compatibility with existing Rich features for full terminals

**Alignment with project.md**: This follows the brownfield-first principle by improving existing CLI output without breaking current functionality. It uses the existing Rich/Typer infrastructure but adds proper terminal detection.

## What Changes

- **NEW**: `src/specfact_cli/utils/terminal.py` (terminal capability detection utility)
  - `detect_terminal_capabilities()` function to detect:
    - Color support (via `NO_COLOR`, `FORCE_COLOR`, `TERM`, `COLORTERM` env vars)
    - Terminal type (interactive TTY vs non-interactive)
    - CI/CD environment detection (via `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, etc.)
    - Animation support (based on terminal type and capabilities)
  - `get_console_config()` function to return Rich Console configuration based on capabilities
  - `get_progress_config()` function to return Progress bar configuration (with/without animations)

- **EXTEND**: `src/specfact_cli/runtime.py`
  - Add `get_terminal_mode()` function to return terminal mode (graphical, basic, minimal)
  - Integrate with existing `is_non_interactive()` and `get_operational_mode()` functions
  - Add terminal mode to operational mode detection

- **EXTEND**: All command modules using `Console()` and `Progress()`
  - `src/specfact_cli/commands/import_cmd.py`
  - `src/specfact_cli/commands/sync.py`
  - `src/specfact_cli/commands/generate.py`
  - `src/specfact_cli/commands/sdd.py`
  - `src/specfact_cli/sync/bridge_sync.py`
  - Replace `console = Console()` with `console = get_configured_console()`
  - Replace `Progress(...)` with `Progress(..., **get_progress_config())`
  - Add plain text fallback messages when animations are disabled

- **EXTEND**: Progress indicators
  - When animations disabled: Use simple text updates instead of SpinnerColumn
  - When colors disabled: Remove color markup from progress descriptions
  - When basic terminal: Use percentage/count text instead of progress bars
  - Maintain same information content in both modes

- **NEW**: Plain text progress reporting
  - Add `print_progress()` helper function for basic terminal mode
  - Emit periodic status updates (e.g., "Analyzing... 45% complete (123/273 files)")
  - Ensure updates are visible in CI/CD logs and embedded terminals

## Impact

- **Affected specs**: New capability `cli-output` (terminal output handling)
- **Affected code**:
  - All command modules using Rich Console/Progress
  - Runtime configuration module
  - New terminal utility module
- **Integration points**:
  - Runtime mode detection (already exists)
  - Operational mode (CI/CD vs interactive)
  - Existing Rich/Typer infrastructure

## Non-Goals

- **Not changing**: Rich Console library or Typer framework
- **Not removing**: Existing graphical terminal features (still works in full terminals)
- **Not implementing**: Custom terminal rendering (using Rich's built-in capabilities)
- **Not adding**: New CLI flags for terminal mode (auto-detection only)

---

## Source Tracking

- **GitHub Issue**: #77
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/77>
- **Last Synced Status**: applied
- **Sanitized**: true
<!-- content_hash: 5eb377c4a737ed70 -->