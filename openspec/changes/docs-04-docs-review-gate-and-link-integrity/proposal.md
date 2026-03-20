# Change: Repair Published Docs Links And Add A Docs Review Gate

## Why

Published docs currently contain broken links because authored navigation and landing-page links do not consistently match the pages' actual Jekyll permalinks. The PR orchestrator also ignores docs-only and Markdown-only changes, so link drift, missing front matter, and missing docs coverage can ship without any review gate.

## What Changes

- Audit the current published-doc navigation and landing-page links, then correct broken routes and any missing linked docs coverage in core docs.
- Add automated docs review validation that checks Jekyll front matter, published-route resolution, and authored internal links for docs pages.
- Add a dedicated docs review workflow so docs-only changes run fast validation without waiting for the full code-oriented PR orchestrator.
- Record and enforce a discoverability contract for navigation-owned docs pages so broken or missing linked pages fail fast in CI.

## Capabilities

### New Capabilities

- `docs-review-gate`: validate published docs links, front matter, and navigation-owned page coverage during local and CI docs review.

### Modified Capabilities

- `documentation-alignment`: docs landing pages, sidebar links, and authored internal links must resolve to the actual published permalinks for the current docs site.

## Impact

- Affected docs: `docs/index.md`, `docs/_layouts/default.html`, `docs/reference/directory-structure.md`, and any additional docs pages found during link audit.
- Affected validation: `tests/unit/docs/test_release_docs_parity.py` and any new docs-review helpers or fixtures needed for route/link validation.
- Affected CI: `.github/workflows/docs-review.yml` provides the dedicated docs-only validation path and can be configured as a required GitHub check.
- User-facing impact: linked pages on `https://docs.specfact.io` resolve correctly, and future docs regressions fail in PRs before merge.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: pending
- **Issue URL**: pending
- **Last Synced Status**: local-proposal
- **Sanitized**: true
