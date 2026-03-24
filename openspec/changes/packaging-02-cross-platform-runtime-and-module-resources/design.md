## Context

The current implementation mixes three responsibilities that need clearer boundaries:

- terminal rendering assumes Unicode-capable output even when Windows is running a legacy code page
- runtime/resource lookup relies on the caller's interpreter and `sys.path`, which is brittle for helpers that invoke SpecFact from a different environment
- `specfact init ide` still resolves workflow prompts from `specfact_cli/resources/prompts`, even though the prompt set maps to bundle workflows rather than to core commands such as `init`, `module`, or `upgrade`
- core init flows still copy backlog field mapping templates from a core-owned `resources/templates/backlog/field_mappings` location even though that asset belongs to the backlog bundle

This is a cross-cutting change because it touches runtime behavior, module discovery, packaging boundaries, and IDE bootstrap flows. It also provides the ownership foundation required before `init-ide-prompt-source-selection` can safely select among prompt sources. The follow-up audit confirmed that the bundle packages in `specfact-cli-modules` currently do not ship the prompt payloads, so this core change now has an explicit paired dependency on `specfact-cli-modules/packaging-01-bundle-resource-payloads`.

## Goals / Non-Goals

**Goals:**

- make startup/help rendering and other common CLI output safe on non-UTF-8 terminals without requiring manual environment variables
- surface explicit compatibility diagnostics when automation hits interpreter- or installation-coupled module/runtime mismatches
- make prompt/resource discovery derive from installed module packages and packaged resource directories
- make non-prompt module-owned resource copying, starting with backlog field mapping templates, resolve from installed bundle packages
- ensure core CLI stops acting as the owner of bundle/workflow prompt resources
- preserve a path for future prompt-source selection (`all`, `core`, module ids) without duplicating that feature in this change

**Non-Goals:**

- redesign the prompt-selection UX already scoped in `init-ide-prompt-source-selection`
- define new prompt content or rewrite workflow prompt texts
- solve arbitrary cross-interpreter embedding beyond supported CLI invocation and actionable failure diagnostics
- migrate unrelated non-prompt resources out of core unless they are directly needed for this packaging boundary

## Decisions

### 1. Add an explicit terminal output safety layer

The runtime should derive a safe output mode from terminal interactivity and stream encoding, not just from TTY/color detection. When the active output encoding cannot represent configured Unicode glyphs, the CLI should either substitute ASCII-safe markers or run Rich in a mode that avoids unsupported glyph emission.

Why this over "document UTF-8 only":
- the bug is user-facing on a supported platform
- help/startup must be robust without bootstrap flags
- graceful degradation is cheaper and more predictable than asking every caller to preconfigure environment variables

### 2. Treat runtime mismatches as a compatibility contract, not an import accident

Programmatic callers that land in the wrong interpreter or compiled dependency set should receive a SpecFact-level compatibility error that explains:

- which interpreter executed the command
- which installation/resource root was resolved
- which module or compiled dependency could not be loaded
- what supported invocation path the caller should use instead

Why this over continuing with ad hoc `sys.path` fallback:
- path injection masks the real problem
- compiled extensions such as `pydantic_core` cannot be made safe by string-based path hacks
- explicit diagnostics give us a stable contract for Windows/Linux/macOS automation

### 3. Move IDE prompt discovery and module-owned template lookup to module-owned resource catalogs

`specfact init ide` should build its prompt export set from installed module packages and their packaged resource directories. Core init/install flows should use the same installed-package lookup model for other module-owned assets, beginning with backlog field mapping templates. The current hardcoded workflow prompt list is bundle-owned, so it should not live under `specfact_cli/resources/prompts`.

Why this over keeping a core fallback:
- current prompt files represent workflow bundles, not core lifecycle commands
- ownership should match installability and module provenance
- dynamic discovery is the only way to stay correct when modules are optional or installed from different roots

### 4. Keep the core change as the orchestration owner and consume a paired modules change

This repo owns the runtime safety layer, installed-resource discovery contract, export/copy orchestration, and docs. The paired modules-repo change `packaging-01-bundle-resource-payloads` owns moving prompts and other bundle-owned resources into the released bundle packages.

Why this split is now required:
- issue `#441` is rooted in the core CLI runtime and export flow
- the audit verified the modules repo does not currently package the prompt payloads
- the two repos now have distinct responsibilities that should be tracked separately

## Risks / Trade-offs

- `[Compatibility drift between core and published modules]` -> enforce prompt discovery contracts in tests against installed-module metadata and packaged resource paths.
- `[ASCII fallback reduces visual polish on legacy terminals]` -> prefer fidelity on UTF-8 terminals and degrade only when encoding safety requires it.
- `[Dynamic discovery can hide missing prompt assets until runtime]` -> fail with actionable diagnostics when selected modules declare no prompt resources.
- `[Cross-repo rollout may leave core temporarily expecting resources that older bundles do not ship]` -> sequence the modules-repo packaging change with compatibility-aware fallback or version gating in core.

## Migration Plan

1. Define spec deltas for runtime portability and module-owned IDE prompts.
2. Add failing tests for non-UTF-8 rendering, compatibility diagnostics, and module-based prompt discovery/export.
3. Implement the runtime safety and prompt catalog changes in core CLI.
4. Integrate with `specfact-cli-modules/packaging-01-bundle-resource-payloads` so core discovery targets the packaged resource layout shipped by official bundles.
5. Update docs to explain prompt ownership, platform behavior, and supported automation patterns.

## Open Questions

- Whether any prompt or template remains legitimately core-owned after the audit. Current evidence suggests the exported workflow prompts and backlog field mapping templates are module-owned, but implementation should verify residual core-only assets.
- Whether compatibility diagnostics should include a dedicated exit code for interpreter/runtime mismatch.
