# TDD Evidence

## Failing Before

- Timestamp: 2026-03-17
- Command: `pytest tests/unit/docs/test_release_docs_parity.py -q`
- Result: failed

Observed failures before the docs updates:

- `test_readme_and_docs_index_define_core_and_modules_split`
- `test_top_navigation_exposes_docs_home_core_cli_and_modules`
- `test_command_reference_and_docs_readme_link_to_modules_canonical_site`
- `test_bundle_focused_pages_use_handoff_note_instead_of_future_migration_language`

Failure mode summary:

- README and landing docs still described module docs as temporary future migration work
- top navigation still exposed legacy `Home / Getting Started / Guides / Reference` labels instead of the docs-home/core/modules split
- docs index and command reference did not link to the canonical modules docs site
- bundle-focused pages still used the old "planned to migrate" note instead of the handoff model

## Passing After

- Timestamp: 2026-03-17
- Command: `pytest tests/unit/docs/test_release_docs_parity.py -q`
- Result: passed (`10 passed`)

- Timestamp: 2026-03-17
- Command: `hatch run pytest tests/unit/docs/test_release_docs_parity.py -q`
- Result: passed (`10 passed`)

- Timestamp: 2026-03-17
- Command: `openspec validate docs-02-core-docs-canonical-portal --strict`
- Result: passed
