# Implementation Summary: docs-01-core-modules-docs-alignment

## Audited coverage

- Root entrypoints: `README.md`, `docs/index.md`, `docs/README.md`
- Navigation and information architecture: `docs/_layouts/default.html`, command/reference landing pages
- Marketplace and lifecycle docs: install, marketplace, publishing, signing, trust, dependency resolution
- Architecture and ownership docs: architecture reference, implementation status, directory structure, module contracts
- Bundle-focused guides/tutorials/adapters: backlog, DevOps, ADO/GitHub, policy, refinement, sidecar, contract workflow

## Notable corrections

- Replaced stale flat-command examples across live docs with grouped command paths (`project`, `backlog`, `code`, `spec`, `govern`) while preserving explicit migration tables that intentionally document removed commands.
- Added/standardized temporary-hosting notes on bundle-specific pages still published from the core docs site.
- Corrected post-migration ownership language so official workflow bundle implementation and publishing point to `nold-ai/specfact-cli-modules`.
- Updated publishing docs to describe the current protected-branch-safe `publish-modules.yml` behavior in the modules repository.
- Corrected invalid config/path examples introduced during earlier bulk edits (for example `.specfact/backlog-config.yaml`, `.specfact/backlog.yaml`, `.specfact/backlog-baseline.json`).
- Added lightweight docs parity tests for the post-migration command surface and docs-hosting expectations.

## Follow-up items

- Move bundle-specific guides from the core docs set to the future `specfact-cli-modules` docs site once that site becomes the canonical bundle-docs home.
- Mirror the final corrected pages from `specfact-cli` into `specfact-cli-modules` where the modules repo already carries temporary docs copies.
