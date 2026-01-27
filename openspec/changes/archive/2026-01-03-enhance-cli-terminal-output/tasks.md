## 1. Terminal Capability Detection

- [x] 1.1 Create `src/specfact_cli/utils/terminal.py` module
- [x] 1.2 Implement `detect_terminal_capabilities()` function
  - [x] 1.2.1 Detect color support (NO_COLOR, FORCE_COLOR, TERM, COLORTERM)
  - [x] 1.2.2 Detect terminal type (TTY vs non-interactive)
  - [x] 1.2.3 Detect CI/CD environment (CI, GITHUB_ACTIONS, GITLAB_CI, etc.)
  - [x] 1.2.4 Determine animation support based on terminal capabilities
  - [x] 1.2.5 Respect TEST_MODE environment variable (test mode = minimal terminal)
  - [x] 1.2.6 Add `@beartype` decorator for runtime type checking
  - [x] 1.2.7 Add `@icontract` decorators with `@require`/`@ensure` contracts
- [x] 1.3 Implement `get_console_config()` function
  - [x] 1.3.1 Return Rich Console kwargs based on capabilities
  - [x] 1.3.2 Set `force_terminal=False` for non-interactive terminals
  - [x] 1.3.3 Set `no_color=True` when colors not supported
  - [x] 1.3.4 Set `width` and `legacy_windows` appropriately
  - [x] 1.3.5 Add `@beartype` decorator for runtime type checking
  - [x] 1.3.6 Add `@icontract` decorators with `@require`/`@ensure` contracts
- [x] 1.4 Implement `get_progress_config()` function
  - [x] 1.4.1 Return Progress column configuration based on capabilities
  - [x] 1.4.2 Use TextColumn only (no SpinnerColumn) for basic terminals
  - [x] 1.4.3 Use BarColumn only when terminal supports it
  - [x] 1.4.4 Include TimeElapsedColumn when appropriate
  - [x] 1.4.5 Add `@beartype` decorator for runtime type checking
  - [x] 1.4.6 Add `@icontract` decorators with `@require`/`@ensure` contracts
- [x] 1.5 Add unit tests for terminal detection
  - [x] 1.5.1 Test color detection with various env vars
  - [x] 1.5.2 Test CI/CD environment detection
  - [x] 1.5.3 Test terminal type detection
  - [x] 1.5.4 Test console and progress config generation

## 2. Runtime Integration

- [x] 2.1 Extend `src/specfact_cli/runtime.py`
  - [x] 2.1.1 Add `TerminalMode` enum (GRAPHICAL, BASIC, MINIMAL)
  - [x] 2.1.2 Add `get_terminal_mode()` function
  - [x] 2.1.3 Integrate with terminal capability detection
  - [x] 2.1.4 Terminal mode detection based on capabilities (not operational mode)
- [x] 2.2 Add `get_configured_console()` helper function
  - [x] 2.2.1 Use terminal detection to configure Console
  - [x] 2.2.2 Return configured Console instance
  - [x] 2.2.3 Cache Console instance per terminal mode
- [x] 2.3 Add unit tests for runtime integration
  - [x] 2.3.1 Test terminal mode detection
  - [x] 2.3.2 Test console configuration caching
  - [x] 2.3.3 Test integration with terminal capabilities

## 3. Plain Text Progress Reporting

- [x] 3.1 Implement `print_progress()` helper function
  - [x] 3.1.1 Accept current/total counts and description
  - [x] 3.1.2 Format as plain text (e.g., "Analyzing... 45% (123/273 files)")
  - [x] 3.1.3 Emit to stdout with newline (visible in CI/CD logs)
  - [x] 3.1.4 Throttle updates (e.g., every 1 second or 10% progress)
  - [x] 3.1.5 Add `@beartype` decorator for runtime type checking
  - [x] 3.1.6 Add `@icontract` decorators with `@require`/`@ensure` contracts
- [x] 3.2 Add progress callback for basic terminal mode
  - [x] 3.2.1 Create callback that uses `print_progress()` instead of Rich Progress
  - [x] 3.2.2 Integrate with existing `create_progress_callback()` function
  - [x] 3.2.3 Specify when to use Rich Progress vs plain text (based on terminal capabilities)
  - [x] 3.2.4 Ensure same information content as Rich Progress
  - [x] 3.2.5 Integrate with `load_bundle_with_progress()` and `save_bundle_with_progress()`
- [x] 3.3 Add unit tests for plain text progress
  - [x] 3.3.1 Test progress formatting
  - [x] 3.3.2 Test update throttling
  - [x] 3.3.3 Test callback integration

## 4. Command Module Updates

- [x] 4.1 Update `src/specfact_cli/commands/import_cmd.py`
  - [x] 4.1.1 Replace `console = Console()` with `console = get_configured_console()`
  - [x] 4.1.2 Update all `Progress(...)` instances to use `get_progress_config()`
  - [x] 4.1.3 Add plain text fallback for progress updates
  - [x] 4.1.4 Test in both graphical and basic terminal modes
- [x] 4.2 Update `src/specfact_cli/commands/sync.py`
  - [x] 4.2.1 Replace `console = Console()` with `console = get_configured_console()`
  - [x] 4.2.2 Update all `Progress(...)` instances to use `get_progress_config()`
  - [x] 4.2.3 Add plain text fallback for progress updates
  - [x] 4.2.4 Test in both graphical and basic terminal modes
- [x] 4.3 Update `src/specfact_cli/commands/generate.py`
  - [x] 4.3.1 Replace `console = Console()` with `console = get_configured_console()`
  - [x] 4.3.2 Update Progress instances if any
  - [x] 4.3.3 Test in both modes
- [x] 4.4 Update `src/specfact_cli/commands/sdd.py`
  - [x] 4.4.1 Replace `console = Console()` with `console = get_configured_console()`
  - [x] 4.4.2 Update Progress instances if any
  - [x] 4.4.3 Test in both modes
- [x] 4.5 Update `src/specfact_cli/sync/bridge_sync.py`
  - [x] 4.5.1 Replace `console = Console()` with `console = get_configured_console()`
  - [x] 4.5.2 Update Progress instances if any
  - [x] 4.5.3 Test in both modes
- [x] 4.6 Update `src/specfact_cli/utils/progress.py` (CRITICAL - used by multiple commands)
  - [x] 4.6.1 Replace `console = Console()` with `console = get_configured_console()` (lazy import to avoid circular dependency)
  - [x] 4.6.2 Update `_safe_progress_display()` to consider terminal capabilities
  - [x] 4.6.3 Update `load_bundle_with_progress()` to use configured Console and Progress
  - [x] 4.6.4 Update `save_bundle_with_progress()` to use configured Console and Progress
  - [x] 4.6.5 Ensure Progress instances use `get_progress_config()`
  - [x] 4.6.6 Test in both graphical and basic terminal modes
- [x] 4.7 Update `src/specfact_cli/cli.py` (Main CLI entry point)
  - [x] 4.7.1 Replace `console = Console()` with `console = get_configured_console()`
  - [x] 4.7.2 Ensure main CLI banner and messages respect terminal capabilities
  - [x] 4.7.3 Test in both graphical and basic terminal modes

## 5. Code Quality and Contract Validation

- [x] 5.1 Apply code formatting
  - [x] 5.1.1 Run `hatch run format` to apply black and isort
  - [x] 5.1.2 Verify all files are properly formatted
  - [x] 5.1.3 Fix any formatting issues
- [x] 5.2 Run linting checks
  - [x] 5.2.1 Run `hatch run lint` to check for linting errors
  - [x] 5.2.2 Fix all pylint, ruff, and other linter errors
  - [x] 5.2.3 Verify no linting errors remain
- [x] 5.3 Run type checking
  - [x] 5.3.1 Run `hatch run type-check` to verify type annotations
  - [x] 5.3.2 Fix all basedpyright type errors
  - [x] 5.3.3 Verify no type errors remain
- [x] 5.4 Verify contract decorators
  - [x] 5.4.1 Ensure all new public functions have `@beartype` decorators
  - [x] 5.4.2 Ensure all new public functions have `@icontract` decorators with appropriate `@require`/`@ensure`
  - [x] 5.4.3 Verify contract validation works correctly

## 6. Testing and Validation

- [x] 6.1 Add new unit tests for terminal detection
  - [x] 6.1.1 Test `detect_terminal_capabilities()` with various env vars
  - [x] 6.1.2 Test `get_console_config()` and `get_progress_config()`
  - [x] 6.1.3 Test `get_terminal_mode()` and `get_configured_console()`
  - [x] 6.1.4 Test `print_progress()` helper function
  - [x] 6.1.5 Verify all new unit tests pass
- [x] 6.2 Update existing unit tests
  - [x] 6.2.1 Update tests in `tests/unit/utils/test_progress.py` if needed
  - [x] 6.2.2 Update tests in `tests/unit/runtime/` if needed (created `tests/unit/test_runtime.py`)
  - [x] 6.2.3 Update command module tests to account for terminal detection
  - [x] 6.2.4 Verify all existing unit tests still pass
- [x] 6.3 Add new integration tests for terminal modes
  - [x] 6.3.1 Test import command in basic terminal mode
  - [x] 6.3.2 Test sync command in basic terminal mode
  - [x] 6.3.3 Test with NO_COLOR environment variable
  - [x] 6.3.4 Test with CI environment variable
  - [x] 6.3.5 Verify plain text output is readable
  - [x] 6.3.6 Verify all new integration tests pass
- [x] 6.4 Update existing integration tests
  - [x] 6.4.1 Update `tests/integration/sync/test_*` tests if needed
  - [x] 6.4.2 Update `tests/integration/commands/test_*` tests if needed
  - [x] 6.4.3 Verify all existing integration tests still pass
- [x] 6.5 Add new E2E tests for terminal modes
  - [x] 6.5.1 Test full workflow in basic terminal mode
  - [x] 6.5.2 Test full workflow in graphical terminal mode
  - [x] 6.5.3 Test with various environment variable combinations
  - [x] 6.5.4 Verify all new E2E tests pass
- [x] 6.6 Update existing E2E tests
  - [x] 6.6.1 Update `tests/e2e/test_*` tests if needed
  - [x] 6.6.2 Verify all existing E2E tests still pass
- [x] 6.7 Run full test suite
  - [x] 6.7.1 Run `hatch test --cover -v` to execute all tests
  - [x] 6.7.2 Verify all tests pass (unit, integration, E2E)
  - [x] 6.7.3 Verify test coverage meets or exceeds 80%
  - [x] 6.7.4 Fix any failing tests
- [x] 6.8 Manual testing checklist
  - [x] 6.8.1 Test in Cursor terminal (embedded)
  - [x] 6.8.2 Test in full terminal (graphical)
  - [x] 6.8.3 Test in CI/CD pipeline (GitHub Actions)
  - [x] 6.8.4 Verify backward compatibility (existing Rich features still work)
- [x] 6.9 Final validation
  - [x] 6.9.1 Run `hatch run format` one final time
  - [x] 6.9.2 Run `hatch run lint` one final time
  - [x] 6.9.3 Run `hatch run type-check` one final time
  - [x] 6.9.4 Run `hatch test --cover -v` one final time
  - [x] 6.9.5 Verify no errors remain (formatting, linting, type-checking, tests)

## 7. Documentation

- [x] 7.1 Update README.md with terminal output information (removed per user request - kept concise)
- [x] 7.2 Add troubleshooting section for terminal output issues (`docs/guides/troubleshooting.md`)
- [x] 7.3 Document environment variables for terminal control (in troubleshooting guide)
- [x] 7.4 Add examples showing output in different modes (in troubleshooting guide)
- [x] 7.5 Document terminal detection behavior (comprehensive section in troubleshooting guide)
- [x] 7.6 Document contract decorators usage in new functions
- [x] 7.7 Update UX Features guide (`docs/guides/ux-features.md`) with terminal adaptation
- [x] 7.8 Update IDE Integration guide (`docs/guides/ide-integration.md`) with terminal output note
- [x] 7.9 Update Use Cases guide (`docs/guides/use-cases.md`) with CI/CD terminal output behavior
- [x] 7.10 Create testing guide (`docs/guides/testing-terminal-output.md`) for terminal output testing
- [x] 7.11 Update CHANGELOG.md with version 0.22.1 release notes
