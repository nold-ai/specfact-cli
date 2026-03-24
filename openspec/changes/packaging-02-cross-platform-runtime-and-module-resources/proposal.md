## Why

Windows and mixed-environment automation currently fail in two places that should be installation-safe: Rich output can crash on non-UTF-8 terminals, and module/resource discovery for backlog automation and `specfact init ide` still assumes core-owned assets and interpreter-coupled paths. We need one change that makes CLI output portable across Windows, Linux, and macOS while moving IDE prompt ownership to the modules that actually provide those workflows.

## What Changes

- Add a cross-platform runtime portability contract for console output, Unicode/icon fallback, and actionable interpreter-compatibility errors when automation calls into a mismatched SpecFact installation.
- Make module and resource discovery installation-scoped so callers do not need to inject `.specfact/modules/...` paths manually when invoking supported workflows.
- Redesign `specfact init ide` prompt export to discover prompt resources from installed modules and their packaged resource locations instead of from `specfact_cli/resources/prompts`.
- Move core init/install flows that still copy module-owned resources, such as backlog field mapping templates, to resolve those assets from installed module packages.
- Remove bundle/workflow prompt ownership from the core CLI package; core may only export prompts or templates that are explicitly declared by core modules.
- Consume the linked modules-repo change `packaging-01-bundle-resource-payloads`, which will package prompt templates and other module-owned resources in the owning bundles.

## Capabilities

### New Capabilities
- `runtime-portability`: The CLI renders safely across terminal encodings and reports clear runtime-compatibility guidance for installation/interpreter mismatches.
- `module-owned-ide-prompts`: `specfact init ide` discovers and exports prompt resources from installed modules and their packaged resource roots instead of from core-owned workflow prompt files.
- `module-owned-runtime-resources`: core init/install flows resolve module-owned templates and similar assets from installed module packages rather than from core-owned fallback directories.

### Modified Capabilities

None.

## Impact

- Affected code: `src/specfact_cli/runtime.py`, `src/specfact_cli/utils/terminal.py`, `src/specfact_cli/utils/ide_setup.py`, `src/specfact_cli/modules/init/src/*.py`, module/resource discovery helpers, and packaging tests.
- Affected behavior: startup/help rendering, Windows console safety, programmatic backlog automation, and `specfact init ide` prompt copying.
- Affected docs: `README.md`, `docs/`, and module packaging guidance for prompt resources.
- Cross-repo coordination: this change now depends on `specfact-cli-modules/packaging-01-bundle-resource-payloads` for the actual packaged prompt/template payloads that core will discover and copy.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #441
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/441>
- **Last Synced Status**: proposed
- **Sanitized**: false
