# CLI Modular Packages and Registry – Implementation Plan (arch-01 extension)

**Repository**: nold-ai/specfact-cli (public)  
**OpenSpec change**: Extends arch-01-cli-modular-command-registry  
**Date**: 2026-02-03

---

## 1. Vision and goals

- **Logical packages by feature**, not only by command group: each unit is a **package** for a coherent feature (e.g. "backlog refine", "backlog daily", "validate sidecar"). A package includes its CLI surface and **all related resources** (slash prompts in resources/, templates, mappings, schemas) and any dependency that is **not** core CLI logic.
- **Extensible packaging and registry**: design for an ecosystem where the **core CLI** stays stable and **packages** can be developed and upgraded independently, with dependency/version management and future delivery via GitHub with checksum validation.
- **First phase (this refactor)**: **No selective install yet**; we still ship the full CLI with all packages. Refactor must **not block** future selective install: structure and metadata must support it (discovery, version, dependencies, enable/disable).
- **Now**: Introduce **modules/packages** layout, **discovery**, **metadata per package** (name, version, pip deps, inter-module deps), and **specfact init** that discovers modules, enables all by default, stores state (enabled/disabled, version), and allows enable/disable overrides that persist across inits.

---

## 2. Requirements (summary)

1. **Grouping**: Group all current modules into **core logic** vs **module packages**. A package can span multiple current files/directories (e.g. backlog refine + backlog daily + resources/prompts/specfact.backlog-*.md + resources/templates/backlog/ = one or more logical packages).
2. **Reorganize layout**: Introduce a **modules** (or **extensions** / **addons**) folder. Each module in a dedicated subfolder with **fixed structure**: src/, templates/ (or resources/), tests/, and **metadata** (name, version, pip dependencies, dependencies on other modules). Move code and resources from current flat layout into these package folders.
3. **specfact init**: Discover all available modules; enable all by default; store module list with **version** and **state** (enabled/disabled) under ~/.specfact/ (e.g. registry/modules.json); allow --enable-module / --disable-module; on next init respect manual deselection and inform user that some modules were manually deselected.

---

## 3. Core vs module package grouping (target state)

- **Core**: Bootstrapping, CommandRegistry, init (without module discovery), auth/runtime/config, shared utils, shared models used by multiple packages. No feature-specific commands or resources.
- **Module packages** (logical features): backlog-refine (backlog refine + prompts + templates), backlog-daily (backlog daily + prompts), backlog-sync, validate (validate sidecar + resources), plus import/plan/compare/enforce/repro/contract/drift/generate/migrate/project/sdd/spec/sync/update/analyze as appropriate with their resources. Any resource used only by one feature lives in that package folder; shared resources stay in core or shared package.

---

## 4. Folder structure (per package)

Each module under e.g. src/specfact_cli/modules/ or modules/ at repo root:

- \<package_id\>/ (e.g. backlog_refine, backlog_daily, validate_sidecar)
  - module-package.yaml: name, version, pip_dependencies, module_dependencies, commands[]
  - src/: Python package for this module
  - resources/: prompts/, templates/ – package-specific
  - tests/

Discovery: scan modules root, read metadata.yaml, register packages; command registration uses package loaders.

---

## 5. specfact init behavior (detailed)

- Discovery: enumerate all modules from modules root + metadata; default enabled=true.
- State file: ~/.specfact/registry/modules.json with per-module id, version, enabled. Read existing state first.
- Override: if user previously set enabled=false, keep it on next init; new modules get enabled=true.
- CLI: specfact init [--enable-module \<id\>] [--disable-module \<id\>]; write state after init.
- Message: if any module disabled by override, print "The following modules are disabled by your configuration: \<list\>. Re-enable with specfact init --enable-module \<id\>."

---

## 6. Out of scope for first refactor

- Selective install and checksum/GitHub delivery: not in this phase; only metadata and layout prepared.

---

## 7. Files summary (specfact-cli)

- New: modules root with subfolders per package (metadata.yaml, src/, resources/, tests/).
- New: Module discovery loader; registry fed by discovery.
- Change: cli.py – no direct command imports; use registry from module discovery.
- Change: specfact init – discovery, state file, enable/disable options, override persistence, user message.
- Change: Move existing commands/resources into module folders (incremental).
- Docs: Update for module layout and init behavior.

---

## 8. Dependency on arch-01

Extends arch-01: adds package-level structure, metadata, module discovery, init enable/disable and state. CommandRegistry, lazy load, help cache remain and become package-aware.
