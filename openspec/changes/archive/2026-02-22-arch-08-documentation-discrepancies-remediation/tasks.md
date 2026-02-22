# Implementation Tasks: arch-08-documentation-discrepancies-remediation

## TDD / SDD Order (Enforced)

Per config.yaml: spec deltas first, then verification criteria (for doc-only change: checklist and link/consistency checks), then documentation implementation. No production code; documentation updates are the "implementation."

---

## 1. Create git branch from dev

- [x] 1.1 Create feature branch from dev
  - [x] 1.1.1 `git checkout dev && git pull origin dev`
  - [x] 1.1.2 `git checkout -b feature/arch-08-documentation-discrepancies-remediation`
  - [x] 1.1.3 `git branch --show-current`

## 2. Spec deltas (documentation capabilities)

- [x] 2.1 Add/update spec for documentation-alignment
  - [x] 2.1.1 Ensure `specs/documentation-alignment/spec.md` exists with scenarios: module system described as production-ready; BridgeAdapter interface complete; layers and modes accurate; CommandRegistry and module structure documented; ToolCapabilities and error handling documented; terminology and version refs consistent; diagrams only reference existing components.
- [x] 2.2 Add spec for adr-template
  - [x] 2.2.1 Ensure `specs/adr-template/spec.md` exists with scenarios: ADR template available; at least one ADR present; linked from architecture docs.
- [x] 2.3 Add spec for module-development-guide
  - [x] 2.3.1 Ensure `specs/module-development-guide/spec.md` exists with scenarios: required module structure and manifest documented; naming and contracts mentioned; discoverable from docs nav.
- [x] 2.4 Add spec for adapter-development-guide
  - [x] 2.4.1 Ensure `specs/adapter-development-guide/spec.md` exists with scenarios: BridgeAdapter full interface and ToolCapabilities documented; examples or link to code; discoverable from docs nav.
- [x] 2.5 Add spec for implementation-status-docs
  - [x] 2.5.1 Ensure `specs/implementation-status-docs/spec.md` exists with scenarios: single place describes implemented vs planned; pointers to OpenSpec changes for planned features; change tracking and protocol FSM limitations stated.

## 3. Verification criteria (pre-implementation)

- [x] 3.1 Define documentation verification checklist
  - [x] 3.1.1 List required updates from discrepancies report (items 1–7, 11–13, 17–19, 20–22) and map to files/sections.
  - [x] 3.1.2 Document checklist in change folder (e.g. `DOC_VERIFICATION_CHECKLIST.md`) for use after edits.

## 4. Update architecture and reference documentation

- [x] 4.1 Update `docs/reference/architecture.md`
  - [x] 4.1.1 Replace "transitioning" with production-ready module system (since v0.27).
  - [x] 4.1.2 Add or expand BridgeAdapter interface: `detect`, `import_artifact`, `export_artifact`, `load_change_tracking`, `save_change_tracking`.
  - [x] 4.1.3 Describe actual layers: Specification, Contract, Enforcement, plus Adapter, Analysis, Module layers where applicable.
  - [x] 4.1.4 Clarify operational modes: current detector behavior; mode-specific behavior as planned; link to implementation-status if created.
  - [x] 4.1.5 Add CommandRegistry implementation details (lazy loading, metadata caching) and reference to module package structure.
  - [x] 4.1.6 Add section or link to ToolCapabilities and adapter selection.
  - [x] 4.1.7 Add error handling patterns / conventions (custom exceptions, logging).
  - [x] 4.1.8 Update or remove outdated performance metrics; use current benchmarks or remove specific numbers.
  - [x] 4.1.9 Standardize terminology (Project Bundle, Plan Bundle) and version references.
- [x] 4.2 Update `docs/architecture/` assets
  - [x] 4.2.1 Fix component-graph and other diagrams: remove or relabel non-existent components (e.g. DevOps Adapters).
  - [x] 4.2.2 Align module-system.md, data-flow.md, state-machines.md, interface-contracts.md with code (registry, adapters, protocol models).
  - [x] 4.2.3 Ensure README and discrepancies-report cross-references remain correct after edits.

## 5. Create ADR template and initial ADR(s)

- [x] 5.1 Create ADR template
  - [x] 5.1.1 Create `docs/architecture/adr/` directory.
  - [x] 5.1.2 Add `template.md` (title, status, context, decision, consequences).
  - [x] 5.1.3 Add `README.md` in adr/ explaining how to create ADRs.
- [x] 5.2 Add at least one ADR
  - [x] 5.2.1 Add ADR for module-first architecture (e.g. `0001-module-first-architecture.md`) using template.
  - [x] 5.2.2 Link ADR from `docs/architecture/README.md` and/or `docs/reference/architecture.md`.

## 6. Create module development guide

- [x] 6.1 Create `docs/guides/module-development.md` (or equivalent path)
  - [x] 6.1.1 Document required directory structure (`modules/<name>/`, `module-package.yaml`, `src/<name>/`, `main.py`, etc.).
  - [x] 6.1.2 Document `module-package.yaml` schema (name, version, commands, dependencies, schema_extensions, service_bridges).
  - [x] 6.1.3 Document naming conventions and contract requirements (@icontract, @beartype).
  - [x] 6.1.4 Add link from architecture docs and from docs nav.
- [x] 6.2 Add Jekyll front-matter and navigation
  - [x] 6.2.1 Set layout, title, permalink, description.
  - [x] 6.2.2 Update `docs/_layouts/default.html` so the guide appears in the menu.

## 7. Create or extend adapter development guide

- [x] 7.1 Create or update adapter guide
  - [x] 7.1.1 Add or extend `docs/guides/adapter-development.md` (or integrate into `creating-custom-bridges.md`): full BridgeAdapter interface, change tracking methods, ToolCapabilities model and adapter selection.
  - [x] 7.1.2 Include code references or minimal examples (e.g. `src/specfact_cli/adapters/base.py`, `models/bridge.py`).
- [x] 7.2 Add Jekyll front-matter and navigation
  - [x] 7.2.1 Set layout, title, permalink, description for new page.
  - [x] 7.2.2 Update `docs/_layouts/default.html` if new page added.

## 8. Add implementation status documentation

- [x] 8.1 Create `docs/architecture/implementation-status.md` (or equivalent)
  - [x] 8.1.1 List what is implemented vs planned (architecture commands, protocol FSM, change tracking scope, adapters: OpenSpec/SpecKit vs GitHub/ADO).
  - [x] 8.1.2 Point to OpenSpec changes (e.g. architecture-01-solution-layer) for planned features.
  - [x] 8.1.3 Link from architecture README and reference architecture page.
- [x] 8.2 Add Jekyll front-matter and navigation
  - [x] 8.2.1 Set layout, title, permalink, description.
  - [x] 8.2.2 Update `docs/_layouts/default.html` if needed.

## 9. Documentation verification and quality gates

- [x] 9.1 Run documentation verification
  - [x] 9.1.1 Complete `DOC_VERIFICATION_CHECKLIST.md` against updated docs.
  - [x] 9.1.2 Run link check (e.g. `hatch run yaml-lint` or project link-check script if any).
  - [x] 9.1.3 Confirm no remaining "transitioning" / "experimental" for module system in architecture docs; confirm BridgeAdapter and layers are accurate.
- [x] 9.2 Format and lint
  - [x] 9.2.1 `hatch run format`
  - [x] 9.2.2 `hatch run type-check` (no code change; verify no regressions)
  - [x] 9.2.3 `hatch run lint` (or equivalent)

## 10. Version and changelog (if applicable)

- [x] 10.1 Only if project policy requires a patch bump for doc-only release
  - [x] 10.1.1 Bump patch in `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`.
  - [x] 10.1.2 Add CHANGELOG.md entry under new version: Documentation – architecture discrepancies remediation.

## 11. GitHub issue and PR

- [x] 11.1 Create GitHub issue (public repo)
  - [x] 11.1.1 Title: `[Change] Architecture documentation discrepancies remediation`
  - [x] 11.1.2 Labels: `enhancement`, `change-proposal`
  - [x] 11.1.3 Body: Why and What Changes from proposal; footer: `*OpenSpec Change Proposal: arch-08-documentation-discrepancies-remediation*`
  - [x] 11.1.4 Update proposal.md Source Tracking with issue number, URL, status.
- [x] 11.2 Create PR
  - [x] 11.2.1 Push branch and open PR to `dev`.
  - [x] 11.2.2 PR description references this change and discrepancies report.
