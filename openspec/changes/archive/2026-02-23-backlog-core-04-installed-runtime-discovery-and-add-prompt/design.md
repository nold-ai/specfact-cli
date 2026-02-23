# Design: Installed Runtime Discovery Parity and Backlog Add Prompt

## Overview

This change addresses two consistency gaps:

1. Installed runtime (`pip`/PyPI) misses workspace modules such as `modules/backlog-core` in some invocation contexts, causing command-surface drift from development runtime.
2. `backlog add` has no dedicated slash prompt while neighboring backlog workflows do.

## Discovery strategy

- Keep existing discovery order:
  - packaged modules (`specfact_cli/modules`)
  - optional roots from `SPECFACT_MODULES_ROOTS`
- Add a safe fallback root:
  - `Path.cwd() / "modules"` when the directory exists
  - deduplicated by resolved path, preserving deterministic ordering
- Goal: when users run installed `specfact` from repo root, workspace modules are discoverable without manual env overrides.

## Prompt strategy

- Add `resources/prompts/specfact.backlog-add.md` following current frontmatter + `$ARGUMENTS` pattern.
- Include command purpose, required adapter context, core flags, and execution workflow.
- Register command name in `SPECFACT_COMMANDS` so `specfact init ide` copies it into IDE-specific command folders.

## Risks

- Discovery fallback could include unintended `modules/` folder in unrelated directories.
  - Mitigation: only add when directory exists; no behavior change when absent.
- Prompt installation drift across IDE formats.
  - Mitigation: reuse existing `SPECFACT_COMMANDS` + template processing path; cover with unit tests.
