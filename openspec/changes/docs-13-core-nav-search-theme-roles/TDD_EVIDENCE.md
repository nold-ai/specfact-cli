# TDD Evidence

## Implemented Scope

- Added shared-portal docs shell parity for the core site:
  - data-driven sidebar navigation in `docs/_data/nav.yml`
  - shared includes for breadcrumbs, search, expertise filter, sidebar nav, and theme toggle
  - Jekyll-generated search index and client-side search/filter/theme scripts
  - refreshed landing page entry paths and enriched front matter on core pages
- Extended docs validation so `scripts/check-docs-commands.py` also verifies nav targets against published core routes.
- Added contract coverage for the shared portal shell in `tests/unit/test_core_docs_site_contract.py` and updated docs validation tests.

## Verification Run

### Passed

1. Focused docs contract and parity tests

```bash
PATH=/home/dom/git/nold-ai/specfact-cli/.venv/bin:$PATH \
PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-13-core-nav-search-theme-roles/src \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/python -m pytest \
  tests/unit/test_core_docs_site_contract.py \
  tests/unit/docs/test_release_docs_parity.py \
  tests/unit/docs/test_docs_validation_scripts.py -q
```

Result:

- `38 passed`

2. Docs command validation

```bash
PATH=/home/dom/git/nold-ai/specfact-cli/.venv/bin:$PATH \
PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-13-core-nav-search-theme-roles/src \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/python scripts/check-docs-commands.py
```

Result:

- `check-docs-commands: OK (110 unique command prefix(es) checked)`

3. Cross-site handoff validation against live `modules.specfact.io`

```bash
PATH=/home/dom/git/nold-ai/specfact-cli/.venv/bin:$PATH \
PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-13-core-nav-search-theme-roles/src \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/python scripts/check-cross-site-links.py --warn-only
```

Result:

- `check-cross-site-links: OK (24 unique modules.specfact.io URL(s) checked)`

4. Jekyll build

```bash
cd docs
bundle install
bundle exec jekyll build
```

Result:

- Build completed successfully

5. Formatting

```bash
PATH=/home/dom/git/nold-ai/specfact-cli/.venv/bin:$PATH \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/ruff format . --check
```

Result:

- Passed after formatting `tests/unit/test_core_docs_site_contract.py`

6. Type check baseline

```bash
PATH=/home/dom/git/nold-ai/specfact-cli/.venv/bin:$PATH \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/basedpyright \
  --pythonpath /home/dom/git/nold-ai/specfact-cli/.venv/bin/python
```

Result:

- `0 errors, 6545 warnings, 0 notes`
- Warnings are existing repository baseline outside this change scope.

7. OpenSpec validation

```bash
openspec validate docs-13-core-nav-search-theme-roles --strict
```

Result:

- `Change 'docs-13-core-nav-search-theme-roles' is valid`

## Environment Notes

- `bundle exec jekyll build` initially failed because the worktree did not have the required Jekyll gems installed. Running `bundle install` in `docs/` resolved that.
- The repo’s `scripts/yaml-tools.sh lint` could not be used from this environment because the available `yamllint` entrypoint points to a missing interpreter (`/usr/bin/python`) and the canonical repo `.venv` does not have `yamllint` installed. This is an environment/tooling issue, not a docs-13 regression.
