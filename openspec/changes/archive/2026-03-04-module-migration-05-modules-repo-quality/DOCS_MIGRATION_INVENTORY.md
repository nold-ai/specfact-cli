# Docs Migration Inventory

Date: 2026-03-04

## Source docs identified in `specfact-cli`

### Bundle and module oriented guides

- `docs/guides/marketplace.md`
- `docs/guides/import-features.md`
- `docs/guides/backlog-refinement.md`
- `docs/guides/backlog-dependency-analysis.md`
- `docs/guides/backlog-delta-commands.md`
- `docs/guides/project-devops-flow.md`
- `docs/guides/policy-engine-commands.md`
- `docs/guides/sidecar-validation.md`
- `docs/getting-started/module-bootstrap-checklist.md`

### Module command/reference docs

- `docs/reference/commands.md`
- `docs/reference/module-categories.md`
- `docs/reference/module-contracts.md`
- `docs/reference/module-security.md`

## Migrated target in `specfact-cli-modules`

- `docs/guides/` (copied from `specfact-cli/docs/guides/`)
- `docs/getting-started/` (copied from `specfact-cli/docs/getting-started/`)
- `docs/reference/` (copied from `specfact-cli/docs/reference/`)
- `docs/adapters/` (copied from `specfact-cli/docs/adapters/`)
- Jekyll baseline: `docs/_config.yml`, `docs/_layouts/default.html`, `docs/assets/main.scss`, `docs/index.md`

## Cross-link updates in `specfact-cli`

- `README.md` module marketplace section now links to:
  - `https://nold-ai.github.io/specfact-cli-modules/`
- `docs/index.md` module marketplace section now links to:
  - `https://nold-ai.github.io/specfact-cli-modules/`
