## 1. Change Setup And Discovery

- [x] 1.1 Create worktree `../specfact-cli-worktrees/feature/docs-02-core-docs-canonical-portal` with branch `feature/docs-02-core-docs-canonical-portal` from `origin/dev`
- [x] 1.2 Inventory the current overlap between core-hosted module pages and modules-repo pages, including which pages should remain core-owned versus become handoff pages
- [x] 1.3 Confirm the Cloudflare/public-domain assumptions with the internal plan so the docs wording does not promise unsupported routing behavior

## 2. Spec Deltas First

- [x] 2.1 Add spec deltas for `module-docs-ownership` covering the stable ownership split between core docs and module docs
- [x] 2.2 Add spec deltas for `documentation-alignment` covering the canonical docs portal navigation and the two-site model
- [x] 2.3 Review the affected docs pages and map each one to keep, handoff, or retire behavior before implementation begins

## 3. Validation First

- [x] 3.1 Add failing regression coverage or docs assertions for the landing page/README ownership language and top-level docs navigation contract
- [x] 3.2 Add failing regression coverage or docs assertions proving marketplace/module reference pages point readers to module-owned deep docs instead of treating core as the permanent canonical source
- [x] 3.3 Record the failing validation evidence in `openspec/changes/docs-02-core-docs-canonical-portal/TDD_EVIDENCE.md`

## 4. Core Docs Realignment

- [x] 4.1 Update `README.md`, `docs/index.md`, and `docs/_layouts/default.html` to establish the canonical docs-home/core/modules navigation model
- [x] 4.2 Convert remaining module-specific core pages into overview/handoff pages or equivalent migration notes according to the ownership map from task 2.3
- [x] 4.3 Update marketplace/reference wording so core docs distinguish runtime-owned concepts from module-owned deep workflow documentation

## 5. Validation And Delivery

- [x] 5.1 Re-run the targeted docs validation checks and record passing evidence in `openspec/changes/docs-02-core-docs-canonical-portal/TDD_EVIDENCE.md`
- [x] 5.2 Run `openspec validate docs-02-core-docs-canonical-portal --strict`
- [x] 5.3 Run the relevant repo quality gates for touched docs/test files
- [x] 5.4 Open PR to `dev` from `feature/docs-02-core-docs-canonical-portal`
