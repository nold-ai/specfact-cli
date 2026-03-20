## 1. Change Setup And Discovery

- [x] 1.1 Create worktree `../specfact-cli-worktrees/feature/docs-03-command-syntax-parity` with branch `feature/docs-03-command-syntax-parity` from `origin/dev`
- [x] 1.2 Verify the shipped command surface from the active worktree using live CLI help and relevant integration tests for `init`, `module`, `backlog`, `project`, `code`, `spec`, and `govern`
- [x] 1.3 Finalize `openspec/changes/docs-03-command-syntax-parity/COMMAND_SYNTAX_AUDIT.md` so every authored doc file with stale syntax is mapped to a required rewrite outcome

## 2. Spec Deltas First

- [x] 2.1 Add the `documentation-alignment` spec delta covering authored-doc command examples and migration guidance
- [x] 2.2 Add the `cli-output` spec delta covering docs parity enforcement for removed syntax families
- [x] 2.3 Review every audited doc file and confirm whether each stale example should be replaced, reframed as historical context, or removed

## 3. Validation First

- [x] 3.1 Add failing docs parity coverage for removed syntax families across authored docs (`project plan`, `project import from-bridge`, `backlog policy`, retired `spec` subgroup trees)
- [x] 3.2 Add failing docs parity coverage for the corrected current command families and parameter forms that should remain present after remediation
- [x] 3.3 Record the failing validation evidence in `openspec/changes/docs-03-command-syntax-parity/TDD_EVIDENCE.md`

## 4. Docs Syntax Remediation

- [x] 4.1 Update entry and landing docs: `README.md`, `docs/index.md`, `docs/README.md`
- [x] 4.2 Update reference docs: `docs/reference/README.md`, `docs/reference/commands.md`, `docs/reference/command-syntax-policy.md`, `docs/reference/directory-structure.md`, `docs/reference/feature-keys.md`
- [x] 4.3 Update getting-started docs: `docs/getting-started/README.md`, `docs/getting-started/first-steps.md`, `docs/getting-started/installation.md`, `docs/getting-started/tutorial-openspec-speckit.md`
- [x] 4.4 Update workflow and migration guides: `docs/guides/agile-scrum-workflows.md`, `docs/guides/ai-ide-workflow.md`, `docs/guides/brownfield-journey.md`, `docs/guides/command-chains.md`, `docs/guides/common-tasks.md`, `docs/guides/competitive-analysis.md`, `docs/guides/devops-adapter-integration.md`, `docs/guides/dual-stack-enrichment.md`, `docs/guides/ide-integration.md`, `docs/guides/migration-0.16-to-0.19.md`, `docs/guides/migration-cli-reorganization.md`, `docs/guides/migration-guide.md`, `docs/guides/policy-engine-commands.md`, `docs/guides/speckit-comparison.md`, `docs/guides/speckit-journey.md`, `docs/guides/specmatic-integration.md`, `docs/guides/troubleshooting.md`, `docs/guides/use-cases.md`, `docs/guides/using-module-security-and-extensions.md`, `docs/guides/ux-features.md`, `docs/guides/workflows.md`
- [x] 4.5 Update examples and brownfield walkthroughs: `docs/examples/quick-examples.md`, `docs/examples/dogfooding-specfact-cli.md`, `docs/examples/brownfield-django-modernization.md`, `docs/examples/brownfield-data-pipeline.md`, `docs/examples/brownfield-flask-api.md`
- [x] 4.6 Update prompt-oriented docs and internal docs references: `docs/prompts/README.md`, `docs/prompts/PROMPT_VALIDATION_CHECKLIST.md`
- [x] 4.7 Review which module-specific deep docs now belong in `specfact-cli-modules/docs`, keep only core-process and core-runtime content in this repo, and add/adjust handoff language where migration is required

## 5. Validation And Delivery

- [x] 5.1 Re-run the targeted docs parity checks and record passing evidence in `openspec/changes/docs-03-command-syntax-parity/TDD_EVIDENCE.md`
- [x] 5.2 Run `openspec validate docs-03-command-syntax-parity --strict`
- [x] 5.3 Run the relevant repo quality gates for touched docs/test files
- [ ] 5.4 Update `CHANGELOG.md` and apply the required patch-version bump if this docs fix ships as a releaseable change
- [ ] 5.5 Open PR to `dev` from `feature/docs-03-command-syntax-parity`
