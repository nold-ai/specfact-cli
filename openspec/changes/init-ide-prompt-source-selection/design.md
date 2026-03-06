## Context

Today `init ide` is effectively designed around core-owned prompt resources. That breaks down once backlog and other domain prompt assets are properly owned by modules. The export flow needs a source-aware model that works for both interactive and automation-friendly use.

## Decision

- Define prompt sources as:
  - `core`
  - installed/enabled module ids, for example `nold-ai/specfact-backlog`
- Default export behavior to `all` sources.
- In interactive mode, show a multi-select picker over the available prompt sources.
- In non-interactive mode, use a comma-separated `--prompts` selector that accepts:
  - `all`
  - `core`
  - full installed module ids
  - mixed values such as `core,nold-ai/specfact-backlog`

## Rules

- unknown or not-installed module ids fail with actionable guidance
- exported prompt resources remain namespaced by source to avoid collisions
- `all` includes `core` plus all installed/enabled modules that contribute prompts

## Validation

- add tests for default `all` behavior
- add tests for interactive picker source lists
- add tests for non-interactive parsing and validation of `--prompts`
