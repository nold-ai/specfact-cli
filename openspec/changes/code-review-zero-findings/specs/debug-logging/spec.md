## ADDED Requirements

### Requirement: Bridge logger used in all production source paths
Every production code path in `src/specfact_cli/` SHALL use `get_bridge_logger()` from `specfact_cli.common` for all diagnostic output, replacing any remaining `print()` builtin calls.

#### Scenario: Adapter module writes diagnostic output via bridge logger
- **WHEN** an adapter module (e.g., `adapters/ado.py`, `adapters/github.py`) performs a network call or state change
- **THEN** diagnostic messages are written via `logger = get_bridge_logger(__name__)` and `logger.debug(...)` / `logger.info(...)`
- **AND** no `print()` call appears in the adapter module

#### Scenario: Sync module writes diagnostic output via bridge logger
- **WHEN** `sync/bridge_sync.py` or `sync/spec_to_code.py` processes a file
- **THEN** all progress and error messages are routed through `get_bridge_logger(__name__)`
- **AND** no `print()` call appears in the sync module

### Requirement: Script-layer logging uses stdlib or Rich, not print()
Scripts in `scripts/` and `tools/` that run as standalone CLI programs SHALL use `logging.getLogger(__name__)` with a `StreamHandler` for progress output, or `rich.console.Console()` for formatted terminal output. The stdlib `print()` builtin SHALL NOT be used.

#### Scenario: Standalone script writes progress via logging
- **WHEN** a script in `scripts/` needs to write a status message to stdout
- **THEN** it calls `logging.getLogger(__name__).info(...)` or `console.print(...)` from a Rich Console instance
- **AND** semgrep `print-in-src` reports zero findings for that script
