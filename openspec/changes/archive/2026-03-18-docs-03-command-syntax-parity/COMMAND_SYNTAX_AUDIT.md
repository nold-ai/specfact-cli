# Command Syntax Audit

## Verified Current Command Surface

Verified from the current CLI in `dev`:

- Core commands: `specfact init`, `specfact module`, `specfact upgrade`
- Bundle groups: `specfact backlog`, `specfact code`, `specfact govern`, `specfact project`, `specfact spec`

Verified notable current groups and parameters:

- `specfact backlog`
  - supports `ceremony`, `delta`, `auth`, `sync`, `verify-readiness`, `analyze-deps`, `diff`, `promote`, `refine`, `daily`, `init-config`, `map-fields`, `add`
  - does not expose `backlog policy`
- `specfact project`
  - supports `link-backlog`, `health-check`, `devops-flow`, `snapshot`, `regenerate`, `export-roadmap`, persona import/export/locks, `version`, `sync`
  - does not expose `project plan`
  - `project import` is persona Markdown import, not bridge import
- `specfact project sync bridge`
  - supports bridge-sync options such as `--bundle`, `--mode`, `--change-ids`, `--backlog-ids`, `--repo-owner`, `--repo-name`, `--ado-org`, `--ado-project`
- `specfact code`
  - supports `review`, `import`, `analyze`, `drift`, `validate`, `repro`
  - `code validate` exposes `sidecar`
  - integration tests confirm bridge import flows now live under `code import ... from-bridge ...`, not `project import from-bridge ...`
- `specfact govern enforce sdd [BUNDLE]`
  - remains valid and uses positional bundle input plus `--sdd`, `--output-format`, `--out`, `--no-interactive`
- `specfact spec`
  - supports `validate`, `backward-compat`, `generate-tests`, `mock`
  - does not expose `spec contract`, `spec api`, `spec sdd`, or `spec generate`

## Removed Or Transitional Syntax Families To Eliminate

1. `specfact project plan ...`
2. `specfact project import from-bridge ...`
3. `specfact backlog policy ...`
4. `specfact spec contract ...`
5. `specfact spec api ...`
6. `specfact spec sdd ...`
7. `specfact spec generate ...`
8. migration tables that map removed flat commands to other removed/transitional commands rather than to current shipped surfaces

## Affected Authored Docs

The following authored docs contain at least one stale syntax family and must be updated during implementation:

- `README.md`
- `docs/README.md`
- `docs/index.md`
- `docs/reference/README.md`
- `docs/reference/commands.md`
- `docs/reference/command-syntax-policy.md`
- `docs/reference/directory-structure.md`
- `docs/reference/feature-keys.md`
- `docs/getting-started/README.md`
- `docs/getting-started/first-steps.md`
- `docs/getting-started/installation.md`
- `docs/getting-started/tutorial-openspec-speckit.md`
- `docs/examples/quick-examples.md`
- `docs/examples/dogfooding-specfact-cli.md`
- `docs/examples/brownfield-django-modernization.md`
- `docs/examples/brownfield-data-pipeline.md`
- `docs/examples/brownfield-flask-api.md`
- `docs/guides/agile-scrum-workflows.md`
- `docs/guides/ai-ide-workflow.md`
- `docs/guides/brownfield-engineer.md`
- `docs/guides/brownfield-journey.md`
- `docs/guides/command-chains.md`
- `docs/guides/common-tasks.md`
- `docs/guides/competitive-analysis.md`
- `docs/guides/contract-testing-workflow.md`
- `docs/guides/devops-adapter-integration.md`
- `docs/guides/dual-stack-enrichment.md`
- `docs/guides/ide-integration.md`
- `docs/guides/migration-0.16-to-0.19.md`
- `docs/guides/migration-cli-reorganization.md`
- `docs/guides/migration-guide.md`
- `docs/guides/policy-engine-commands.md`
- `docs/guides/speckit-comparison.md`
- `docs/guides/speckit-journey.md`
- `docs/guides/specmatic-integration.md`
- `docs/guides/troubleshooting.md`
- `docs/guides/use-cases.md`
- `docs/guides/using-module-security-and-extensions.md`
- `docs/guides/ux-features.md`
- `docs/guides/workflows.md`
- `docs/prompts/README.md`
- `docs/prompts/PROMPT_VALIDATION_CHECKLIST.md`

## File-Level Mismatch Clusters

### `project plan` Family

- `README.md`
- `docs/examples/brownfield-data-pipeline.md`
- `docs/examples/brownfield-django-modernization.md`
- `docs/examples/brownfield-flask-api.md`
- `docs/examples/dogfooding-specfact-cli.md`
- `docs/examples/quick-examples.md`
- `docs/getting-started/README.md`
- `docs/getting-started/first-steps.md`
- `docs/getting-started/installation.md`
- `docs/getting-started/tutorial-openspec-speckit.md`
- `docs/guides/ai-ide-workflow.md`
- `docs/guides/brownfield-journey.md`
- `docs/guides/command-chains.md`
- `docs/guides/common-tasks.md`
- `docs/guides/competitive-analysis.md`
- `docs/guides/dual-stack-enrichment.md`
- `docs/guides/ide-integration.md`
- `docs/guides/migration-cli-reorganization.md`
- `docs/guides/migration-guide.md`
- `docs/guides/speckit-journey.md`
- `docs/guides/specmatic-integration.md`
- `docs/guides/troubleshooting.md`
- `docs/guides/use-cases.md`
- `docs/guides/using-module-security-and-extensions.md`
- `docs/guides/ux-features.md`
- `docs/guides/workflows.md`
- `docs/prompts/README.md`
- `docs/prompts/PROMPT_VALIDATION_CHECKLIST.md`
- `docs/reference/README.md`
- `docs/reference/commands.md`
- `docs/reference/command-syntax-policy.md`
- `docs/reference/directory-structure.md`
- `docs/reference/feature-keys.md`

### `project import from-bridge` Family

- `docs/examples/quick-examples.md`
- `docs/getting-started/first-steps.md`
- `docs/getting-started/installation.md`
- `docs/getting-started/tutorial-openspec-speckit.md`
- `docs/guides/command-chains.md`
- `docs/guides/common-tasks.md`
- `docs/guides/competitive-analysis.md`
- `docs/guides/speckit-comparison.md`
- `docs/guides/speckit-journey.md`
- `docs/guides/troubleshooting.md`
- `docs/guides/use-cases.md`
- `docs/guides/workflows.md`
- `docs/reference/README.md`

### `backlog policy` Family

- `README.md`
- `docs/README.md`
- `docs/index.md`
- `docs/getting-started/README.md`
- `docs/guides/agile-scrum-workflows.md`
- `docs/guides/devops-adapter-integration.md`
- `docs/guides/policy-engine-commands.md`

### Retired `spec` Subgroup Family

- `docs/examples/dogfooding-specfact-cli.md`
- `docs/guides/brownfield-engineer.md`
- `docs/guides/ide-integration.md`
- `docs/guides/speckit-journey.md`
- `docs/guides/troubleshooting.md`
- `docs/reference/commands.md`

### `govern enforce sdd` Parameter/Context Review

These files reference a still-valid command, but examples and surrounding text must be checked against the current positional-bundle form and current workflow context:

- `docs/examples/brownfield-data-pipeline.md`
- `docs/examples/brownfield-django-modernization.md`
- `docs/examples/brownfield-flask-api.md`
- `docs/examples/quick-examples.md`
- `docs/getting-started/first-steps.md`
- `docs/guides/ai-ide-workflow.md`
- `docs/guides/command-chains.md`
- `docs/guides/common-tasks.md`
- `docs/guides/dual-stack-enrichment.md`
- `docs/guides/ide-integration.md`
- `docs/guides/migration-0.16-to-0.19.md`
- `docs/guides/migration-cli-reorganization.md`
- `docs/guides/migration-guide.md`
- `docs/guides/specmatic-integration.md`
- `docs/guides/ux-features.md`
- `docs/prompts/README.md`
