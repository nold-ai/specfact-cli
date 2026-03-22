## Context

The docs site is published with Jekyll front matter and explicit permalinks, but authored links currently mix file-relative paths, assumed `/reference/...` routes, and page-level permalinks that do not always align. The existing docs parity tests check a few content invariants plus a minimal front-matter presence check, while the PR orchestrator treats docs-only and Markdown-only changes as ignorable. That combination allows broken published routes to ship even when the authored source page still exists.

The change needs both content repair and an enforcement path. The enforcement must stay lightweight enough for PRs, use repository-local information only, and be clear when a failure is caused by a missing page, a wrong permalink, or incomplete front matter.

## Goals / Non-Goals

**Goals:**

- Detect broken internal docs links before merge.
- Detect navigation or landing-page links that point at unpublished routes.
- Require complete Jekyll front matter for pages that are part of published docs navigation and authored-link targets.
- Ensure docs-only PRs trigger a dedicated docs review workflow without waiting for the full code-oriented pipeline.

**Non-Goals:**

- Building the full Jekyll site in PR orchestration.
- Validating external websites beyond basic scheme/host filtering.
- Enforcing that every Markdown page in `docs/` appears in global navigation; only navigation-owned and authored-link targets are in scope.

## Decisions

### Decision: Reuse the existing docs parity test module as the docs review engine

Extend `tests/unit/docs/test_release_docs_parity.py` with helpers that parse front matter, derive published routes, and validate internal authored links. This keeps the logic in the current docs-quality test surface, makes failures readable in pytest output, and avoids inventing a separate one-off script and assertion format.

Alternative considered: a standalone Python script under `scripts/`. Rejected because it would duplicate test harness behavior and add one more place to maintain path and parsing logic.

### Decision: Treat published-route resolution as the source of truth, not file paths

The validator should compute the set of valid published routes from each docs page's explicit permalink or the site default, then compare authored links against that route map. This directly models the `docs.specfact.io` behavior and catches cases where a file exists but its published URL differs from the navigation link.

Alternative considered: checking only that a target Markdown file exists on disk. Rejected because it misses the current failure mode where the file exists but the published URL is different.

### Decision: Scope mandatory metadata checks to published docs pages and navigation-linked targets

Require `layout`, `title`, and `permalink` for published docs pages that are reachable from docs navigation or internal authored links, and require a valid front-matter block for all other authored-link targets. This raises the bar where missing metadata hurts users while avoiding an unnecessarily broad rule for internal planning or auxiliary Markdown.

Alternative considered: requiring all docs Markdown files to have the full metadata set. Rejected because some auxiliary files are intentionally not part of the published navigation experience.

### Decision: Add a dedicated docs-review workflow for docs-only changes

Add a separate `.github/workflows/docs-review.yml` workflow that runs the targeted docs parity suite for docs and Markdown changes. Keep the heavier PR orchestrator focused on code-oriented validation so docs-only changes get a fast required check without waking the full runtime test matrix.

Alternative considered: adding a `docs-review` job inside `.github/workflows/pr-orchestrator.yml`. Rejected because docs-only PRs would still wait on the code-oriented orchestration workflow and the user explicitly wants a lighter mandatory check.

## Risks / Trade-offs

- [False positives from flexible Markdown links] → Limit validation to internal site-style links and normalize common relative-link forms before asserting.
- [Metadata requirements may surface many latent docs issues] → Start with navigation-owned and authored-link targets, then fix the discovered set in the same change.
- [Workflow duration increases for docs-only PRs] → Run only the targeted docs parity test file in the docs-review job.

## Migration Plan

1. Add the OpenSpec deltas and implement the stricter docs review tests.
2. Run the targeted docs parity suite and capture the failing evidence before fixing routes or workflow logic.
3. Correct broken docs permalinks and any missing navigation-linked metadata.
4. Add the dedicated `Docs Review` workflow for docs and Markdown changes.
5. Re-run the targeted docs parity suite and the affected workflow validation gates, then record passing evidence.

Rollback strategy: revert the docs route corrections and dedicated docs-review workflow as a single change if the new validator proves too noisy; the repository will return to the prior lax behavior.

## Open Questions

- None at this stage; the implementation approach is straightforward and bounded to docs/test/workflow files.
