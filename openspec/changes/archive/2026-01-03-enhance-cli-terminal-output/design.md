# Design: Enhanced CLI Terminal Output

## Context

SpecFact CLI uses Rich Console and Progress bars for user feedback, but these don't work well in embedded terminals (Cursor, VS Code) or CI/CD environments. Users see no progress indicators, making long-running commands appear "stuck."

## Goals

- Provide visible progress feedback in all terminal environments
- Maintain backward compatibility with existing Rich features
- Auto-detect terminal capabilities (no manual configuration required)
- Support both graphical (full Rich) and basic (plain text) output modes

## Non-Goals

- Custom terminal rendering (use Rich's built-in capabilities)
- Removing Rich Console (keep for full terminals)
- New CLI flags for terminal mode (auto-detection only)
- Supporting all possible terminal types (focus on common cases)

## Decisions

### Decision 1: Terminal Capability Detection

**What**: Detect terminal capabilities via environment variables and TTY checks

**Why**:

- Rich Console supports `force_terminal`, `no_color`, `is_terminal` parameters
- Environment variables (NO_COLOR, FORCE_COLOR, CI) are standard indicators
- TTY detection distinguishes interactive vs non-interactive terminals

**Alternatives considered**:

- Manual `--no-color` flag: Adds complexity, users forget to use it
- Always use plain text: Loses Rich features in full terminals
- Terminal library: Adds dependency, Rich already has detection

**Implementation**:

```python
def detect_terminal_capabilities() -> TerminalCapabilities:
    """Detect terminal capabilities from environment and TTY."""
    # Check NO_COLOR (standard env var)
    no_color = os.environ.get("NO_COLOR") is not None
    # Check FORCE_COLOR (override)
    force_color = os.environ.get("FORCE_COLOR") == "1"
    # Check CI environment
    is_ci = any(os.environ.get(var) for var in ["CI", "GITHUB_ACTIONS", "GITLAB_CI"])
    # Check TTY
    is_tty = sys.stdout.isatty() if sys.stdout else False
    
    return TerminalCapabilities(
        supports_color=not no_color and (force_color or (is_tty and not is_ci)),
        supports_animations=is_tty and not is_ci,
        is_interactive=is_tty,
        is_ci=is_ci
    )
```

### Decision 2: Dual-Mode Progress Reporting

**What**: Use Rich Progress for full terminals, plain text for basic terminals

**Why**:

- Rich Progress with animations doesn't work in embedded terminals
- Plain text updates are visible in CI/CD logs
- Same information content in both modes

**Alternatives considered**:

- Always use Rich: Breaks in embedded terminals
- Always use plain text: Loses Rich features unnecessarily
- Custom progress library: Adds dependency, Rich is already used

**Implementation**:

```python
def get_progress_config() -> dict:
    """Get Progress configuration based on terminal capabilities."""
    caps = detect_terminal_capabilities()
    
    if caps.supports_animations:
        # Full Rich Progress with animations
        return {
            "columns": (
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
            ),
            "console": get_configured_console(),
        }
    else:
        # Basic Progress with text only
        return {
            "columns": (
                TextColumn("{task.description}"),
            ),
            "console": get_configured_console(),
            "disable": False,  # Still use Progress, just without animations
        }
```

### Decision 3: Console Configuration Caching

**What**: Cache Console instance per terminal mode to avoid repeated detection

**Why**:

- Terminal capabilities don't change during command execution
- Console creation is lightweight but detection logic should run once
- Simplifies usage in command modules

**Alternatives considered**:

- Create Console per command: Works but redundant detection
- Global Console instance: Breaks when terminal mode changes (unlikely but possible)
- No caching: Works but inefficient

**Implementation**:

```python
_console_cache: dict[TerminalMode, Console] = {}

def get_configured_console() -> Console:
    """Get or create configured Console instance."""
    mode = get_terminal_mode()
    if mode not in _console_cache:
        config = get_console_config()
        _console_cache[mode] = Console(**config)
    return _console_cache[mode]
```

### Decision 4: Plain Text Fallback Messages

**What**: Emit periodic plain text status updates when animations disabled

**Why**:

- Users need feedback that command is working
- CI/CD logs need readable progress information
- Plain text is universally supported

**Alternatives considered**:

- No fallback: Users see nothing (current problem)
- Always emit: Works but verbose in graphical terminals
- Throttled updates: Best balance (chosen)

**Implementation**:

```python
def print_progress(description: str, current: int, total: int) -> None:
    """Print plain text progress update."""
    if total > 0:
        percentage = (current / total) * 100
        print(f"{description}... {percentage:.0f}% ({current}/{total})", flush=True)
    else:
        print(f"{description}...", flush=True)
```

## Risks / Trade-offs

### Risk 1: Terminal Detection False Positives

**Risk**: Auto-detection incorrectly identifies terminal capabilities

**Mitigation**:

- Use standard environment variables (NO_COLOR, FORCE_COLOR)
- Prefer explicit overrides (FORCE_COLOR=1)
- Fall back to basic mode when uncertain

### Risk 2: Performance Impact

**Risk**: Terminal detection adds overhead to command startup

**Mitigation**:

- Cache detection results
- Detection is fast (env var reads, TTY check)
- One-time cost per command execution

### Risk 3: Backward Compatibility

**Risk**: Changes break existing Rich features in full terminals

**Mitigation**:

- Test in both graphical and basic modes
- Use Rich's built-in capabilities (no custom rendering)
- Maintain same Console/Progress API usage

## Migration Plan

1. **Phase 1**: Add terminal detection utility (no breaking changes)
2. **Phase 2**: Update command modules to use configured Console/Progress
3. **Phase 3**: Add plain text fallback for basic terminal mode
4. **Phase 4**: Test in all environments (full terminal, embedded, CI/CD)
5. **Phase 5**: Update documentation

**Rollback**: If issues arise, can revert to `Console()` and `Progress(...)` defaults (backward compatible)

## Open Questions

- Should we support `--force-terminal` flag for testing? (Decision: No, use FORCE_COLOR env var)
- Should we emit progress to stderr vs stdout? (Decision: stdout for compatibility)
- How often should plain text updates be emitted? (Decision: Every 1 second or 10% progress, whichever comes first)
