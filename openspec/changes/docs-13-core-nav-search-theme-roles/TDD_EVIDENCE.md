# TDD Evidence

## TDD Sequence

1. Spec deltas added for shared portal parity, client search, expertise guidance, and theme toggle.
1. Tests were added or updated for docs shell parity, validation scripts, and public-site contract coverage.
1. Red-phase validation was run against the incomplete implementation and failed.
1. Production docs shell, search, filters, theme, navigation, and validator changes were implemented.
1. Green-phase validation was rerun and passed.

## Implemented Scope

- Added shared-portal docs shell parity for the core site:
  - data-driven sidebar navigation in `docs/_data/nav.yml`
  - shared includes for breadcrumbs, search, expertise filter, sidebar nav, and theme toggle
  - Jekyll-generated search index and client-side search/filter/theme scripts
  - refreshed landing page entry paths and enriched front matter on core pages
- Extended docs validation so `scripts/check-docs-commands.py` also verifies nav targets against published core routes.
- Added contract coverage for the shared portal shell in `tests/unit/test_core_docs_site_contract.py` and updated docs validation tests.

## Red Phase

### 2026-03-28T18:07:00+01:00

1. Focused docs contract and parity tests

```bash
REPO_ROOT=/path/to/specfact-cli
PATH="$REPO_ROOT/.venv/bin:$PATH" \
PYTHONPATH="$REPO_ROOT/src" \
python -m pytest \
  tests/unit/test_core_docs_site_contract.py \
  tests/unit/docs/test_release_docs_parity.py \
  tests/unit/docs/test_docs_validation_scripts.py -q
```

Result:

- `FAILED tests/unit/test_core_docs_site_contract.py::test_core_layout_exposes_shared_cross_site_navigation`
- `FAILED tests/unit/test_core_docs_site_contract.py::test_core_layout_exposes_shared_portal_features`
- `FAILED tests/unit/test_core_docs_site_contract.py::test_core_layout_keeps_sidebar_core_focused`

### 2026-03-28T18:13:00+01:00

1. Docs command validation

```bash
REPO_ROOT=/path/to/specfact-cli
PATH="$REPO_ROOT/.venv/bin:$PATH" \
PYTHONPATH="$REPO_ROOT/src" \
python scripts/check-docs-commands.py
```

Result:

- `docs/_data/nav.yml: unknown docs route /guides/ide-integration/`
- `docs/_data/nav.yml: unknown docs route /module-system/marketplace/`

### 2026-03-28T18:21:00+01:00

1. Cross-site handoff validation

```bash
REPO_ROOT=/path/to/specfact-cli
PATH="$REPO_ROOT/.venv/bin:$PATH" \
PYTHONPATH="$REPO_ROOT/src" \
python scripts/check-cross-site-links.py --warn-only
```

Result:

- `FAILED: modules.specfact.io handoff target not found for /module-system/module-marketplace/`
- `FAILED: modules.specfact.io handoff target not found for /reference/documentation-url-contract/`

## Verification Run

### Passed

1. Focused docs contract and parity tests

```bash
REPO_ROOT=/path/to/specfact-cli
PATH="$REPO_ROOT/.venv/bin:$PATH" \
PYTHONPATH="$REPO_ROOT/src" \
python -m pytest \
  tests/unit/test_core_docs_site_contract.py \
  tests/unit/docs/test_release_docs_parity.py \
  tests/unit/docs/test_docs_validation_scripts.py -q
```

Result:

- `38 passed`

1. Docs command validation

```bash
REPO_ROOT=/path/to/specfact-cli
PATH="$REPO_ROOT/.venv/bin:$PATH" \
PYTHONPATH="$REPO_ROOT/src" \
python scripts/check-docs-commands.py
```

Result:

- `check-docs-commands: OK (110 unique command prefix(es) checked)`

1. Cross-site handoff validation against live `modules.specfact.io`

```bash
REPO_ROOT=/path/to/specfact-cli
PATH="$REPO_ROOT/.venv/bin:$PATH" \
PYTHONPATH="$REPO_ROOT/src" \
python scripts/check-cross-site-links.py --warn-only
```

Result:

- `check-cross-site-links: OK (24 unique modules.specfact.io URL(s) checked)`

1. Jekyll build

```bash
cd docs
bundle install
bundle exec jekyll build
```

Result:

- Build completed successfully

1. Formatting

```bash
REPO_ROOT=/path/to/specfact-cli
PATH="$REPO_ROOT/.venv/bin:$PATH" \
ruff format . --check
```

Result:

- Passed after formatting `tests/unit/test_core_docs_site_contract.py`

1. Type check baseline

```bash
REPO_ROOT=/path/to/specfact-cli
PATH="$REPO_ROOT/.venv/bin:$PATH" \
basedpyright --pythonpath "$REPO_ROOT/.venv/bin/python"
```

Result:

- `0 errors, 6545 warnings, 0 notes`
- Warnings are existing repository baseline outside this change scope.

1. OpenSpec validation

```bash
openspec validate docs-13-core-nav-search-theme-roles --strict
```

Result:

- `Change 'docs-13-core-nav-search-theme-roles' is valid`

## Environment Notes

- `bundle exec jekyll build` initially failed because the worktree did not have the required Jekyll gems installed. Running `bundle install` in `docs/` resolved that.
- The repo’s `scripts/yaml-tools.sh lint` could not be used from this environment because the available `yamllint` entrypoint points to a missing interpreter (`/usr/bin/python`) and the canonical repo `.venv` does not have `yamllint` installed. This is an environment/tooling issue, not a docs-13 regression.
