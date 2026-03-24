## 1. Change Setup And Spec Deltas

- [x] 1.1 Update `openspec/CHANGE_ORDER.md` with `docs-05-core-site-ia-restructure` entry
- [x] 1.2 Add `core-docs-progressive-nav` capability spec for the new 6-section sidebar structure
- [x] 1.3 Add `core-cli-reference` capability spec for dedicated init/module/upgrade reference pages
- [x] 1.4 Add `documentation-alignment` delta for core-only focus and module redirect policy

## 2. Directory Structure And File Moves

- [x] 2.1 Create `docs/core-cli/`, `docs/module-system/`, `docs/migration/` directories
- [x] 2.2 Move `docs/reference/modes.md` to `docs/core-cli/modes.md` with permalink and redirect
- [x] 2.3 Move `docs/reference/debug-logging.md` to `docs/core-cli/debug-logging.md` with permalink and redirect
- [x] 2.4 Move `docs/reference/architecture.md` to `docs/architecture/overview.md` with permalink and redirect
- [x] 2.5 Move `docs/getting-started/module-bootstrap-checklist.md` to `docs/module-system/bootstrap-checklist.md`
- [x] 2.6 Move `docs/openspec-opsx-migration.md` to `docs/migration/openspec-migration.md`
- [x] 2.7 Move module-system guides from `docs/guides/` to `docs/module-system/`: installing-modules, module-marketplace, marketplace, custom-registries
- [x] 2.8 Move migration guides from `docs/guides/` to `docs/migration/`: migration-guide, migration-0.16-to-0.19, migration-cli-reorganization

## 3. New Content

- [x] 3.1 Write `docs/core-cli/init.md` reference page for specfact init (profiles, IDE setup, deps)
- [x] 3.2 Write `docs/core-cli/module.md` reference page for specfact module subcommands
- [x] 3.3 Write `docs/core-cli/upgrade.md` reference page for specfact upgrade
- [x] 3.4 Rewrite `docs/getting-started/first-steps.md` as `docs/getting-started/quickstart.md` (5-minute quickstart)

## 4. Landing Page And Navigation

- [x] 4.1 Rewrite `docs/index.md` as focused portal landing with clear core vs modules delineation
- [x] 4.2 Rewrite `docs/getting-started/README.md` to remove module tutorials, link to modules site
- [x] 4.3 Update `docs/_layouts/default.html` sidebar to new 6-section nav (Getting Started, Core CLI, Module System, Architecture, Reference, Migration)

## 5. Cleanup

- [x] 5.1 Delete `docs/guides/competitive-analysis.md`, `docs/guides/ux-features.md`, `docs/guides/common-tasks.md`, `docs/guides/workflows.md`, `docs/guides/testing-terminal-output.md`, `docs/guides/README.md`
- [x] 5.2 Add `jekyll-redirect-from` front-matter entries for all moved files

## 6. Verification

- [x] 6.1 Run `bundle exec jekyll build` and verify zero warnings (skipped: json gem version mismatch locally; CI will verify)
- [x] 6.2 Verify all sidebar links in new nav resolve correctly (31/31 passed)
- [x] 6.3 Verify redirect entries resolve old URLs to new locations (13/13 passed)
- [x] 6.4 Run repo quality gates on touched files (yaml-lint passed)
