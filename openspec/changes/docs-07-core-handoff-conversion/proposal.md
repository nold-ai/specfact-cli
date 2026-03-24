# Change: Convert Core Handoff Pages To Proper Redirects

## Why

The core docs site currently has 20+ pages that contain full duplicate content of module-specific guides. These pages carry "Modules docs handoff" banners but still serve as the full content rather than proper redirects. This creates maintenance burden (changes must be made in two places), confuses the ownership boundary, and results in stale content when only one copy is updated.

## What Changes

- Convert 20 identified handoff pages in core docs to 3-paragraph summaries with canonical links to the modules site (modules.specfact.io)
- Add `jekyll-redirect-from` metadata to preserve existing URLs
- Each converted page retains: a brief summary of what the guide covers, a note on prerequisites, and a prominent canonical link to the full guide on the modules site
- Remove all detailed content that is canonically owned by the modules docs

## Capabilities

### Modified Capabilities

- `documentation-alignment`: core handoff pages become thin summaries with canonical links instead of full duplicate content

## Impact

- Affected docs (20 files): `guides/brownfield-engineer.md`, `guides/brownfield-journey.md`, `guides/brownfield-faq.md`, `guides/brownfield-roi.md`, `guides/backlog-refinement.md`, `guides/backlog-delta-commands.md`, `guides/backlog-dependency-analysis.md`, `guides/devops-adapter-integration.md`, `guides/custom-field-mapping.md`, `guides/import-features.md`, `guides/policy-engine-commands.md`, `guides/project-devops-flow.md`, `guides/sidecar-validation.md`, `guides/contract-testing-workflow.md`, `guides/specmatic-integration.md`, `guides/agile-scrum-workflows.md`, `guides/team-collaboration-workflow.md`, `getting-started/tutorial-backlog-quickstart-demo.md`, `getting-started/tutorial-backlog-refine-ai-ide.md`, `getting-started/tutorial-daily-standup-sprint-review.md`
- Depends on: `docs-06-modules-site-ia-restructure` (target pages must exist on modules site)
- User-facing: users are directed to the canonical single source of truth for each guide

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #439
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/439
- **Last Synced Status**: synced
- **Sanitized**: true
