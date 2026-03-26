## 1. Change Setup And Spec Deltas

- [ ] 1.1 Update `openspec/CHANGE_ORDER.md` with `docs-07-core-handoff-conversion` entry
- [ ] 1.2 Add `documentation-alignment` delta for handoff-to-redirect conversion pattern

## 2. Verify Target Pages Exist

- [ ] 2.1 Verify that docs-06-modules-site-ia-restructure has created all target pages on the modules site before proceeding (use `docs/reference/documentation-url-contract.md` on each repo and each target file’s `permalink` in `specfact-cli-modules`)
- [ ] 2.2 Create a checklist mapping each core handoff file to its modules target URL (do not assume `/guides/` on modules matches core; prefer bundle paths and `/reference/documentation-url-contract/` on modules for authoritative rules)

## 3. Convert Handoff Pages

- [ ] 3.1 Convert brownfield guides (4 files): brownfield-engineer, brownfield-journey, brownfield-faq, brownfield-roi
- [ ] 3.2 Convert backlog guides (3 files): backlog-refinement, backlog-delta-commands, backlog-dependency-analysis
- [ ] 3.3 Convert project/code guides (4 files): devops-adapter-integration, import-features, project-devops-flow, sidecar-validation
- [ ] 3.4 Convert policy/spec guides (3 files): policy-engine-commands, custom-field-mapping, contract-testing-workflow
- [ ] 3.5 Convert integration guides (2 files): specmatic-integration, agile-scrum-workflows, team-collaboration-workflow
- [ ] 3.6 Convert getting-started tutorials (3 files): tutorial-backlog-quickstart-demo, tutorial-backlog-refine-ai-ide, tutorial-daily-standup-sprint-review

## 4. Verification

- [ ] 4.1 Run `bundle exec jekyll build` and verify zero warnings
- [ ] 4.2 Verify all redirect entries resolve correctly
- [ ] 4.3 Verify each converted page contains: summary paragraph, prerequisites note, canonical link
- [ ] 4.4 Run repo quality gates on touched files
