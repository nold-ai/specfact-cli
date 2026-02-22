# TDD Evidence

## Scope

Migrate ceremony/event-driven backlog actions to `specfact backlog ceremony ...` while keeping `daily` and `refine` available for compatibility.

## Pre-Implementation Failing Run

- Timestamp: 2026-02-13T01:14:40+01:00
- Command:
  - `hatch run pytest tests/unit/commands/test_backlog_ceremony_group.py -q`
- Result: **FAIL**
- Failure summary:
  - `backlog ceremony` command group did not exist (`exit code 2`).
  - `backlog ceremony standup` and `backlog ceremony refinement` were not recognized.

## Implementation

- Added ceremony subgroup and aliases to backlog command module:
  - `src/specfact_cli/modules/backlog/src/commands.py`
  - New `ceremony` subgroup with:
    - `standup` -> delegates to `backlog daily`
    - `refinement` -> delegates to `backlog refine`
- Added tests:
  - `tests/unit/commands/test_backlog_ceremony_group.py`

## Post-Implementation Passing Run

- Timestamp: 2026-02-13T01:15:20+01:00
- Commands:
  - `hatch run pytest tests/unit/commands/test_backlog_ceremony_group.py -q`
  - `hatch run specfact backlog ceremony -h`
- Result: **PASS**
- Verification summary:
  - Backlog ceremony group is discoverable with `standup` and `refinement`.
  - Alias commands delegate successfully to existing backlog daily/refine behavior.

## Scope (3.2 extension)

Extend `backlog ceremony` with `planning`, `flow`, and `pi-summary`, and enforce graceful errors when delegated commands are not installed.

## Pre-Implementation Failing Run (3.2 extension)

- Timestamp: 2026-02-13T01:24:xx+01:00
- Command:
  - `hatch run pytest tests/unit/commands/test_backlog_ceremony_group.py -q`
- Result: **FAIL**
- Failure summary:
  - `planning`, `flow`, and `pi-summary` were missing from `backlog ceremony -h`.
  - `backlog ceremony planning` returned generic “No such command” instead of actionable module guidance.

## Implementation (3.2 extension)

- Updated command module:
  - `src/specfact_cli/modules/backlog/src/commands.py`
  - Added ceremony delegates:
    - `planning` (to `sprint-summary` when available)
    - `flow` (to `flow` when available)
    - `pi-summary` (to `pi-summary` when available)
  - Added dynamic command introspection:
    - forward `--mode` only when delegate supports it
    - print clear module-required error when delegate is unavailable
- Updated tests:
  - `tests/unit/commands/test_backlog_ceremony_group.py`

## Post-Implementation Passing Run (3.2 extension)

- Timestamp: 2026-02-13T01:26:xx+01:00
- Commands:
  - `hatch run pytest tests/unit/commands/test_backlog_ceremony_group.py -q`
  - `hatch run specfact backlog ceremony -h`
  - `hatch run specfact backlog ceremony planning github`
- Result: **PASS**
- Verification summary:
  - Ceremony help now lists `standup`, `refinement`, `planning`, `flow`, `pi-summary`.
  - Missing delegate path reports actionable error identifying required command/module.
