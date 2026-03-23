# Change: Restructure Core Docs Site Information Architecture

## Why

The core docs site at docs.specfact.io has a flat 5-section sidebar (Getting Started, Guides, DevOps & Backlog Sync, Reference, Examples) with 50+ guide files in a single guides/ folder mixing beginner, intermediate, and advanced content. There is no clear learning path, module-specific content is duplicated from the modules site, and users cannot tell where to start or how to progress. The site needs a progressive hierarchy that separates core platform concerns from module-specific workflows.

## What Changes

- Restructure the core docs sidebar from 5 flat sections to 6 focused sections: Getting Started, Core CLI, Module System, Architecture, Reference, Migration
- Create new directories: `docs/core-cli/`, `docs/module-system/`, `docs/migration/`
- Move files from `guides/` and `reference/` into their correct new locations within core
- Rewrite `docs/index.md` as a focused portal landing page
- Rewrite `docs/getting-started/` to remove module tutorials (which belong on modules site) and add a 5-minute quickstart
- Write 4 new core CLI reference pages: init.md, module.md, upgrade.md, quickstart.md
- Update `docs/_layouts/default.html` sidebar navigation to the new 6-section structure
- Add `jekyll-redirect-from` entries for all moved URLs to preserve existing links
- Delete marketing/internal docs: competitive-analysis, ux-features, common-tasks, workflows, testing-terminal-output

## Capabilities

### New Capabilities

- `core-docs-progressive-nav`: 6-section sidebar with clear beginner-to-advanced progression for core platform docs
- `core-cli-reference`: dedicated reference pages for specfact init, specfact module, and specfact upgrade commands

### Modified Capabilities

- `documentation-alignment`: core site focuses exclusively on platform/runtime concerns; module-specific content redirects to modules.specfact.io

## Impact

- Affected docs: `docs/_layouts/default.html` (sidebar), `docs/index.md` (landing), all files in `docs/guides/`, `docs/reference/modes.md`, `docs/reference/debug-logging.md`, `docs/reference/architecture.md`, `docs/getting-started/`
- New directories: `docs/core-cli/`, `docs/module-system/`, `docs/migration/`
- New files: `docs/core-cli/init.md`, `docs/core-cli/module.md`, `docs/core-cli/upgrade.md`, `docs/getting-started/quickstart.md`
- Deleted files: `docs/guides/competitive-analysis.md`, `docs/guides/ux-features.md`, `docs/guides/common-tasks.md`, `docs/guides/workflows.md`, `docs/guides/testing-terminal-output.md`, `docs/guides/README.md`
- User-facing: docs.specfact.io navigation is clearer with progressive disclosure from beginner to advanced

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #438
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/438
- **Last Synced Status**: synced
- **Sanitized**: true
