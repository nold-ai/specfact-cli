## 1. Scope Inventory and Audit Baseline

- [ ] 1.1 Create a complete inventory of live first-party Markdown docs to review (`README.md` and `docs/**`), explicitly excluding generated `_site`, vendored content, and archived OpenSpec artifacts.
- [ ] 1.2 Classify each reviewed document as core-owned, module-owned-but-temporarily-hosted, shared, historical, or out-of-scope generated/vendor content.
- [ ] 1.3 Record the audit baseline and target file groups in a working artifact within this change folder.
- [ ] 1.4 Update `openspec/CHANGE_ORDER.md` with this new docs alignment change in the appropriate table/wave section.

## 2. Entry Points and Information Architecture

- [ ] 2.1 Review and update `README.md` so the top-level product story, install flow, and command examples reflect lean core plus marketplace-installed bundles.
- [ ] 2.2 Review and update `docs/index.md` and `docs/README.md` so landing-page guidance matches the current core/module architecture.
- [ ] 2.3 Add consistent docs-ownership language explaining that module-specific docs are temporarily hosted in core and will migrate to `specfact-cli-modules`.
- [ ] 2.4 Update navigation/cross-links in `docs/_layouts/default.html` and affected page links so marketplace, module categories, and command-reference pages are discoverable.

## 3. Command and Marketplace Documentation Alignment

- [ ] 3.1 Review and update command reference docs so core commands are separated from marketplace-delivered bundle commands.
- [ ] 3.2 Review and update marketplace/install/publish/trust/signing docs for consistency across guides and reference pages.
- [ ] 3.3 Review and update getting-started and tutorial docs so command examples use current grouped command paths and installation expectations.
- [ ] 3.4 Review and update module category, module contract, and module security docs to reflect current bundle/package boundaries and ownership.

## 4. Architecture, Directory, and Dependency Documentation Alignment

- [ ] 4.1 Review and update architecture pages to describe the lean core, dedicated modules repository, and current ownership split accurately.
- [ ] 4.2 Review and update `docs/reference/directory-structure.md` and related structure docs to reflect the post-migration repository layout.
- [ ] 4.3 Review and update `docs/reference/dependency-resolution.md` and related dependency docs to match marketplace-installed official bundle behavior.
- [ ] 4.4 Review and update module development guidance so contributors are directed to the correct repository and documentation ownership model.

## 5. Module-Specific Guides and Adapter Docs

- [ ] 5.1 Review all module-focused guides, adapters, and workflow/tutorial pages for stale flat-command instructions or wrong ownership assumptions.
- [ ] 5.2 Add or standardize temporary-hosting migration notes on pages that are bundle-specific but still live in the core docs set.
- [ ] 5.3 Remove or rewrite duplicate command inventories so package/category-specific docs point to the correct canonical pages.

## 6. Validation and Closeout

- [ ] 6.1 Add or update lightweight docs parity validation/tests where practical for command-surface and ownership-note expectations.
- [ ] 6.2 Run required validation for the docs set (`openspec validate ... --strict`, markdown/yaml/docs checks, and any targeted tests) and capture results in `CHANGE_VALIDATION.md` and `TDD_EVIDENCE.md` where applicable.
- [ ] 6.3 Update `CHANGELOG.md` if the documentation reorganization materially changes user guidance for the pending `0.40.0` release notes.
- [ ] 6.4 Prepare PR-ready summary notes describing audited coverage, notable doc corrections, and remaining follow-up items for eventual docs migration to `specfact-cli-modules`.
