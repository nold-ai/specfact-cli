# Change: IDE Prompt Source Selection

## Why


`specfact init ide` needs a stable prompt-source model once backlog prompts/templates move into modules. Users should get all relevant prompts by default, and they need both interactive selection and non-interactive source targeting when they only want core prompts or a subset of installed module prompts.

## What Changes


- Redesign prompt export in `specfact init ide` around prompt sources rather than assuming prompts are core-owned.
- Default to exporting all prompt sources.
- Add interactive multi-select for installed prompt sources and non-interactive `--prompts` selection with `all`, `core`, and full module ids.
- Keep exported prompt resources namespaced by source so module prompt collisions remain deterministic and readable.

## Capabilities
### New Capabilities

- `init-ide-prompt-selection`: `specfact init ide` can export prompts from core and selected installed modules with consistent interactive and non-interactive behavior.

## Acceptance Criteria
- `specfact init ide` exports all available prompt sources by default.
- Interactive mode shows a multi-select picker containing `core` plus installed module ids.
- Non-interactive mode accepts `--prompts all`, `--prompts core`, and comma-separated full module ids.
- The command fails clearly when a requested module id is not installed or does not expose prompt resources.
- Exported prompt files are grouped by source so prompt provenance remains visible.

## Dependencies
- `backlog-module-ownership-cleanup` must land first so backlog prompt ownership is no longer split across core and module.
- Existing `init ide` resource-copy logic in `specfact-cli` provides the base export path that this change extends.


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #382
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/382>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: fc82ab6be9832592 -->