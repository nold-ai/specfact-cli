## 1. Change Setup And Spec Deltas

- [x] 1.1 Update `openspec/CHANGE_ORDER.md` with the new `docs-04-docs-review-gate-and-link-integrity` entry
- [x] 1.2 Add the `docs-review-gate` capability spec for published-route, front-matter, and docs-only CI validation
- [x] 1.3 Add the `documentation-alignment` delta covering navigation-owned permalink integrity and same-change remediation of broken routes

## 2. Validation First

- [x] 2.1 Extend `tests/unit/docs/test_release_docs_parity.py` to validate internal docs routes, linked-page metadata, and navigation-owned links
- [x] 2.2 Run the targeted docs parity suite and capture a failing result in `openspec/changes/docs-04-docs-review-gate-and-link-integrity/TDD_EVIDENCE.md`

## 3. Remediation And Workflow Enforcement

- [x] 3.1 Fix broken docs permalinks and any linked-page front-matter gaps discovered by the new validation
- [x] 3.2 Add `.github/workflows/docs-review.yml` so docs-only and Markdown-only changes run a dedicated docs-review workflow

## 4. Verification And Delivery

- [x] 4.1 Re-run the targeted docs parity suite and record the passing result in `openspec/changes/docs-04-docs-review-gate-and-link-integrity/TDD_EVIDENCE.md`
- [x] 4.2 Run `openspec validate docs-04-docs-review-gate-and-link-integrity --strict` and save the result to `CHANGE_VALIDATION.md`
- [x] 4.3 Run the affected repo quality gates for touched docs/test/workflow files
