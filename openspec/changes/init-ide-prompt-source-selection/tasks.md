## 1. Spec And Dependency Setup

- [ ] 1.1 Add spec deltas for prompt-source discovery, default `all` export behavior, interactive source selection, and non-interactive `--prompts` parsing.
- [ ] 1.2 Confirm the final prompt ownership inputs from `backlog-module-ownership-cleanup`.

## 2. Test-First Prompt Source Selection

- [ ] 2.1 Add failing tests for default export of all available prompt sources.
- [ ] 2.2 Add failing tests for interactive multi-select over `core` plus installed module ids.
- [ ] 2.3 Add failing tests for non-interactive `--prompts` values including `all`, `core`, mixed selections, and invalid/non-installed module ids.
- [ ] 2.4 Record the failing evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement prompt-source discovery for core and installed/enabled modules.
- [ ] 3.2 Update `specfact init ide` interactive flow to use a source picker.
- [ ] 3.3 Add non-interactive `--prompts` selection using comma-separated source tokens.
- [ ] 3.4 Ensure copied prompt resources are namespaced by source and collision-safe.

## 4. Validation

- [ ] 4.1 Re-run the new prompt-selection tests and record passing evidence in `TDD_EVIDENCE.md`.
- [ ] 4.2 Run `openspec validate init-ide-prompt-source-selection --strict`.
