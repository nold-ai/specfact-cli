## Context

Other module families already follow the intended split: core keeps framework/runtime only, while bundle repos own the feature surface. Backlog still violates that rule. `specfact-cli` contains:

- a core backlog command shim
- a core backlog group loader
- a built-in `backlog-core` module package
- backlog-specific runtime, prompt, and template logic

At the same time, `specfact-cli-modules` ships `nold-ai/specfact-backlog`, which also owns backlog behavior. That creates duplicate registration and fuzzy ownership.

## Decision

- Remove backlog feature ownership from `specfact-cli` core.
- Move backlog-specific commands, prompts, templates, and backlog-only helpers into `specfact-backlog`.
- Keep only minimal shared contracts/models/provider integrations in `specfact-cli`.

## Core That May Remain

- shared provider adapter infrastructure under `src/specfact_cli/adapters`
- generic data models used by multiple subsystems
- minimal backlog contracts/interfaces only if reused outside the backlog bundle

## Core That Must Be Removed Or Moved

- `modules/backlog-core`
- `src/specfact_cli/commands/backlog_commands.py`
- `src/specfact_cli/groups/backlog_group.py`
- backlog-specific prompt/template and refinement helpers under `src/specfact_cli/backlog`
- duplicate-overlap suppression logic that only exists to tolerate split backlog ownership

## Validation

- add tests that fail if core still exports backlog-owned commands directly
- add tests that fail if backlog prompts/templates still ship from core after migration
- validate installed/runtime command registration no longer needs duplicate backlog overlap handling
