# TDD Evidence

## Pre-Implementation Failing Run

- Timestamp: 2026-03-20T14:31:44+01:00
- Command: `hatch run pytest tests/unit/docs/test_release_docs_parity.py -q`
- Result: failed

### Failure Summary

- `test_navigation_links_resolve_to_published_docs_routes` failed because the first validator pass still treated Jekyll `{{ ... | relative_url }}` expressions and non-page assets such as `feed.xml` and `assets/main.css` as literal docs routes.
- `test_authored_internal_docs_links_resolve_to_published_docs_targets` failed because authored docs still mixed true published-route drift with links to non-published repo files and missing published targets.
- The failing run surfaced the underlying docs regressions that motivated this change, including sidebar routes such as `/reference/directory-structure/`, `/reference/architecture/`, and multiple `/guides/...` links that did not match the authored page permalinks.

## Post-Implementation Passing Run

- Timestamp: 2026-03-20T14:40:50+01:00
- Command: `hatch run pytest tests/unit/docs/test_release_docs_parity.py -q`
- Result: passed

### Verification Summary

- The route-aware docs parity suite passed after normalizing guide/reference/example permalinks to the published section routes used by sidebar navigation.
- Broken authored links to missing repo-local files were replaced with valid published docs targets or GitHub source links where the target is intentionally not a published docs page.
- The dedicated `Docs Review` workflow now provides a fast mandatory-check path for docs-only changes without waiting for the full code-oriented PR orchestrator.
