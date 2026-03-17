# Docs Ownership Map

## Keep In Core

- `README.md`
- `docs/index.md`
- `docs/README.md`
- `docs/_layouts/default.html`
- `docs/reference/commands.md`
- `docs/reference/module-contracts.md`
- `docs/reference/module-security.md`
- `docs/reference/module-categories.md`

These pages remain core-owned because they explain the runtime, command topology, marketplace lifecycle, or the docs navigation contract itself.

## Convert To Handoff Pages Or Handoff Notes

- `docs/adapters/azuredevops.md`
- `docs/adapters/github.md`
- `docs/getting-started/tutorial-backlog-quickstart-demo.md`
- `docs/getting-started/tutorial-backlog-refine-ai-ide.md`
- `docs/getting-started/tutorial-daily-standup-sprint-review.md`
- `docs/guides/agile-scrum-workflows.md`
- `docs/guides/backlog-delta-commands.md`
- `docs/guides/backlog-dependency-analysis.md`
- `docs/guides/backlog-refinement.md`
- `docs/guides/contract-testing-workflow.md`
- `docs/guides/custom-field-mapping.md`
- `docs/guides/devops-adapter-integration.md`
- `docs/guides/dual-stack-enrichment.md`
- `docs/guides/import-features.md`
- `docs/guides/installing-modules.md`
- `docs/guides/marketplace.md`
- `docs/guides/module-development.md`
- `docs/guides/module-marketplace.md`
- `docs/guides/module-signing-and-key-rotation.md`
- `docs/guides/policy-engine-commands.md`
- `docs/guides/project-devops-flow.md`
- `docs/guides/publishing-modules.md`
- `docs/guides/sidecar-validation.md`
- `docs/reference/authentication.md`

These pages remain available in core for release-line continuity, but they should carry a consistent handoff note pointing readers to the canonical modules docs site for bundle-specific deep guidance.

## Retire Later

- No page is removed in this change.

The follow-up removal step should happen only after:

1. the aligned modules docs pages are live,
2. handoff links or redirects are verified, and
3. the Cloudflare/public-domain cutover plan is ready.
