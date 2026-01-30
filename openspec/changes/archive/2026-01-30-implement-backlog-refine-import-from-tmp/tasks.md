# Tasks: Implement backlog refine --import-from-tmp

## 1. Create git branch

- [x] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
- [x] 1.1.2 Create branch: `git checkout -b feature/implement-backlog-refine-import-from-tmp`
- [x] 1.1.3 Verify branch: `git branch --show-current`

## 2. Parser for refined export format

- [x] 2.1.1 Add function to parse refined markdown (e.g. `_parse_refined_export_markdown(content: str) -> dict[str, dict]` returning id → {body_markdown, acceptance_criteria, title?, ...}) in `backlog_commands.py` or new module `src/specfact_cli/backlog/refine_export_parser.py`
- [x] 2.1.2 Split content by `## Item` or `---` to get per-item blocks
- [x] 2.1.3 From each block extract **ID** (required), **Body** (from ```markdown ... ```), **Acceptance Criteria** (optional), optionally **title** and metrics
- [x] 2.1.4 Add unit tests for parser (export-format sample, multiple items, missing optional fields)
- [x] 2.1.5 Run `hatch run format` and `hatch run type-check`

## 3. Import branch in backlog refine command

- [x] 3.1.1 In the `if import_from_tmp:` block, after file-exists check: read file content, call parser, build map id → parsed fields
- [x] 3.1.2 For each item in `items`, if item.id in map: set item.body_markdown, item.acceptance_criteria (and optionally title/metrics) from parsed fields
- [x] 3.1.3 If `--write` is not set: print preview ("Would update N items") and return
- [x] 3.1.4 If `--write` is set: get adapter via _build_adapter_kwargs and adapter_registry.get_adapter; for each updated item call adapter.update_backlog_item(item, update_fields=[...]) with same update_fields logic as interactive refine
- [x] 3.1.5 Print success summary (e.g. "Updated N backlog items")
- [x] 3.1.6 Remove "Import functionality pending implementation" message and TODO
- [x] 3.1.7 Run `hatch run format` and `hatch run type-check`

## 4. Tests and quality

- [x] 4.1.1 Add or extend test for refine --import-from-tmp (unit: parser; integration or unit with mock: import flow with --tmp-file and --write)
- [x] 4.1.2 Run `hatch run contract-test` (or `hatch run smart-test`)
- [x] 4.1.3 Run `hatch run lint`
- [x] 4.1.4 Run `openspec validate implement-backlog-refine-import-from-tmp --strict`

## 5. Documentation and PR

- [x] 5.1.1 Update CHANGELOG.md with fix entry
- [x] 5.1.2 Ensure help text for --import-from-tmp and --tmp-file is accurate
- [x] 5.1.3 Create Pull Request from feature/implement-backlog-refine-import-from-tmp to dev
