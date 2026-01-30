# Design: Improve Backlog Refine and CLI Startup

## Startup: First Output Before Checks

- **Current**: Callback runs version line then `print_startup_checks()`. If checks are slow (xagt), the version line may appear but console can feel blocked until checks finish.
- **Change**: Ensure `print_version_line()` (or welcome) is the first console output; then run startup checks. No bridge adapter or multi-repo flow. Optional: add a short timeout (e.g. 3s) to `check_pypi_version()` in `startup_checks.py` so slow networks do not block.

## Backlog Refine: Ignore-Refined and --id

- **Ignore-refined**: Extract "needs refinement" logic into a helper (e.g. `_item_needs_refinement(item, detector, registry, template_id, ...)`). After `_fetch_backlog_items`, if `ignore_refined`: filter `items` to those where the helper returns True; then if `limit` is set, `items = items[:limit]`. When both `ignore_refined` and `limit` are set, fetch may need a larger cap (e.g. `limit * 5`) so enough non-refined candidates exist; alternatively fetch without limit and filter then slice.
- **--id**: After fetch (and after ignore-refined filter if applied), if `issue_id` is set: `items = [i for i in items if str(i.id) == str(issue_id)]`. If empty, print error and exit. No adapter API change; post-filter only.

## Prompt: Interactive Refinement (Copilot)

- **Scope**: Prompt file only (`resources/prompts/specfact.backlog-refine.md`). No CLI code change for this part.
- **Content**: New section "Interactive refinement (Copilot mode)" that instructs the AI to: (1) present each refined story in a clear format; (2) list ambiguities; (3) ask PO/stakeholders for clarification; (4) re-refine with feedback and repeat until approved; (5) only then mark story done and proceed; (6) use readable formatting (tables, panels, headings) for an enjoyable refinement session.

## Contract / Testing

- New helper `_item_needs_refinement` (or equivalent) should be covered by unit tests.
- Integration or e2e: refine with `--ignore-refined --limit N` and with `--id N`; assert expected filtering and exit behavior.
