## Context

`packaging-02-cross-platform-runtime-and-module-resources` moved `specfact-cli` toward installed-resource discovery, but it explicitly left the prompt-selection UX and source-targeting behavior for this follow-up change.

That follow-up now has to cover more than a selector:

- bundle-owned prompt/template payloads are being moved into `specfact-cli-modules`
- modules can be present in multiple roots depending on how the user bootstrapped or installed them
- `specfact init ide` can be run at any time and therefore must discover the currently effective installed roots instead of assuming a one-time bootstrap copy from core-owned resources
- `specfact init ide` must not start performing marketplace download/extract work, because installation remains owned by `specfact module init` and `specfact module install`

The prompt/export flow therefore needs a source-aware and scope-aware orchestration model, not just a new option flag.

## Decision

- Define prompt sources as:
  - `core`
  - installed/enabled module ids, for example `nold-ai/specfact-backlog`
- Resolve available sources from effective module roots in repository context:
  - built-in core module root
  - project module root at `<repo>/.specfact/modules` when present
  - nearest workspace module root discovered from the repo path
  - user module root at `~/.specfact/modules`
  - optional custom roots from `SPECFACT_MODULES_ROOTS`
- Default export behavior to `all` sources.
- In interactive mode, show a multi-select picker over the available prompt sources.
- In non-interactive mode, use a comma-separated `--prompts` selector that accepts:
  - `all`
  - `core`
  - full installed module ids
  - mixed values such as `core,nold-ai/specfact-backlog`
- Keep installation responsibilities separate:
  - `specfact module init --scope user|project` seeds bundled module artifacts/resources into the selected root
  - `specfact module install --scope user|project --source <auto|bundled|marketplace>` downloads and extracts bundles into the selected root
  - `specfact init ide` only discovers already-installed resources and copies/refreshes the IDE-facing output for the current repository

## Rules

- unknown or not-installed module ids fail with actionable guidance
- exported prompt resources remain namespaced by source to avoid collisions
- `all` includes `core` plus all installed/enabled modules that contribute prompts
- root precedence and duplicate handling must remain deterministic across user/project/custom roots
- missing module-owned prompt/resources must report the owning module, the root that was inspected, and the install/bootstrap command that can satisfy the missing payload
- prompt ownership must respect active command-surface migration decisions and must not reassert obsolete import/project command paths in exported prompts or recommendations

## Non-Goals

- downloading marketplace artifacts during `specfact init ide`
- extracting archives directly from `specfact-cli-modules` source trees at runtime when the owning bundle is not installed
- reintroducing bundle-owned prompt/template payloads into the core package
- replacing `packaging-02` as the owner of low-level installed-resource discovery logic

## Validation

- add tests for default `all` behavior
- add tests for root-aware source discovery across built-in, user, project, and custom roots
- add tests for interactive picker source lists
- add tests for non-interactive parsing and validation of `--prompts`
- add tests that `init ide` surfaces scope-aware install guidance instead of downloading/installing missing modules
