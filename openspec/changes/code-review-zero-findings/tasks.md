## 0. GitHub issue

- [x] 0.1 Create GitHub issue with title `[Change] Zero-finding code review — dogfooding specfact review on specfact-cli`, labels `enhancement` and `change-proposal`, body following `.github/ISSUE_TEMPLATE/change_proposal.md` (Why and What Changes sections from proposal), footer `*OpenSpec Change Proposal: code-review-zero-findings*`
- [x] 0.2 Update `proposal.md` Source Tracking section with the new issue number, URL, and status `open`

## 1. Branch and baseline

- [x] 1.1 Create worktree: `git worktree add ../specfact-cli-worktrees/bugfix/code-review-zero-findings -b bugfix/code-review-zero-findings origin/dev`
- [x] 1.2 Bootstrap Hatch in worktree: `hatch env create`
- [x] 1.3 Run `specfact review` and capture baseline report to `openspec/changes/code-review-zero-findings/TDD_EVIDENCE.md` (pre-fix run — expected FAIL with 2539 findings)
- [x] 1.4 Fix pylint invocation error (install binary or fix PATH in Hatch env) and re-run review to confirm tool_error finding is gone

## 2. Write failing tests from spec scenarios (TDD step 2)

- [x] 2.1 Add test `tests/unit/specfact_cli/test_dogfood_self_review.py` — assert `specfact review` exits 0 on repo root (expect FAIL before fix)
- [x] 2.2 Add test asserting zero basedpyright `reportUnknownMemberType` findings in `src/` (expect FAIL before fix)
- [x] 2.3 Add test asserting zero semgrep `print-in-src` findings in `src/`, `scripts/`, `tools/` (expect FAIL before fix)
- [x] 2.4 Add test asserting zero `MISSING_ICONTRACT` findings in `src/` (expect FAIL before fix)
- [x] 2.5 Add test asserting no radon CC≥16 findings in `src/`, `scripts/`, `tools/` (expect FAIL before fix)
- [x] 2.6 Record failing test run results in `TDD_EVIDENCE.md`

## 3. Phase 1 — Type annotations (basedpyright, 1,616 findings)

- [ ] 3.1 Add type annotations to `sync/bridge_sync.py` (205 findings) — use `TypedDict` for dict shapes, `Protocol` for duck-typed interfaces; run `hatch run type-check` after
- [ ] 3.2 Add type annotations to `tools/smart_test_coverage.py` (157 findings) — run `hatch run type-check` after
- [ ] 3.3 Add type annotations to `adapters/ado.py` (150 findings) — run `hatch run type-check` after
- [ ] 3.4 Add type annotations to `adapters/github.py` (139 findings) — run `hatch run type-check` after
- [ ] 3.5 Add type annotations to `validators/sidecar/harness_generator.py` (122 findings) — run `hatch run type-check` after
- [ ] 3.6 Fix `reportUnsupportedDunderAll` findings (17): correct `__all__` export lists in affected modules
- [ ] 3.7 Fix remaining `reportAttributeAccessIssue`, `reportInvalidTypeForm`, `reportOptionalMemberAccess`, and `reportCallIssue` findings across all other files
- [ ] 3.8 Run `hatch run type-check` — confirm 0 basedpyright errors and warnings

## 4. Phase 2 — Logging migration (semgrep, 352 + 6 findings)

- [ ] 4.1 Audit `print()` calls in `src/specfact_cli/` to classify: debug/info (→ bridge logger) vs. intentional stdout (→ Rich Console)
- [ ] 4.2 Replace all `print()` calls in `src/specfact_cli/` with `get_bridge_logger(__name__)` calls; confirm no unintended output routing change
- [ ] 4.3 Replace all `print()` calls in `scripts/` with `logging.getLogger(__name__)` or `rich.console.Console().print()`
- [ ] 4.4 Replace all `print()` calls in `tools/` with `logging.getLogger(__name__)` or `rich.console.Console().print()`
- [ ] 4.5 Fix 6 `get-modify-same-method` semgrep findings — separate getter and modifier responsibilities
- [ ] 4.6 Run `hatch run lint` — confirm 0 semgrep architecture findings

## 5. Phase 3 — Contract coverage (contract_runner, 291 findings)

- [ ] 5.1 Add `@require` / `@ensure` / `@beartype` to all public functions in `src/specfact_cli/sync/` flagged by contract_runner
- [ ] 5.2 Add contracts to all public functions in `src/specfact_cli/adapters/` flagged by contract_runner
- [ ] 5.3 Add contracts to all public functions in `src/specfact_cli/validators/` flagged by contract_runner
- [ ] 5.4 Add contracts to all public functions in `src/specfact_cli/generators/` flagged by contract_runner
- [ ] 5.5 Add contracts to all remaining public functions in `src/specfact_cli/` flagged by contract_runner
- [ ] 5.6 Ensure all review CLI command functions (`code review run`, `ledger`, `rules`) have contracts (per `review-cli-contracts` spec)
- [ ] 5.7 Run `hatch run contract-test` — confirm 0 `MISSING_ICONTRACT` findings

## 6. Phase 4 — Complexity refactoring (radon, 279 findings)

- [ ] 6.1 Refactor functions with CC≥30 in `sync/bridge_sync.py` — extract private helpers; run `hatch run smart-test` after
- [ ] 6.2 Refactor functions with CC≥30 in `sync/spec_to_code.py` — extract private helpers; run `hatch run smart-test` after
- [ ] 6.3 Refactor functions with CC≥20 in `scripts/publish-module.py` (`publish_bundle()` and `main()`) — extract step functions
- [ ] 6.4 Refactor all remaining functions with CC≥16 across `src/`, `scripts/`, `tools/` — working through radon error-band findings systematically
- [ ] 6.5 Reduce CC13–15 warning-band functions where refactoring is safe and straightforward (target CC<13)
- [ ] 6.6 Run `hatch run lint` (radon check) — confirm 0 CC≥16 error findings, and 0 CC≥13 warnings

## 7. Verify and evidence

- [ ] 7.1 Run full quality gate: `hatch run format && hatch run type-check && hatch run lint && hatch run contract-test && hatch run smart-test`
- [ ] 7.2 Run `specfact review` — confirm `overall_verdict: PASS` and 0 findings
- [ ] 7.3 Record passing test and review run in `TDD_EVIDENCE.md` (post-fix run)
- [ ] 7.4 Run `hatch test --cover -v` — confirm no regressions

## 8. CI gate integration

- [ ] 8.1 Add `specfact review run --ci` as a blocking step in `.github/workflows/specfact.yml` (after lint, before build)
- [ ] 8.2 Confirm CI passes on the PR branch with the new gate active

## 9. Documentation research and update

- [ ] 9.1 Identify all affected docs: check `docs/` (reference, guides, CI, code-review), `README.md`, `docs/index.md`
- [ ] 9.2 Add or update a section in the code review guide (`docs/`) documenting the self-review CI gate and zero-finding policy
- [ ] 9.3 Add CI reference entry for `specfact review run --ci` gate in the CI reference page
- [ ] 9.4 Verify front-matter (layout, title, permalink, description) on any new or modified doc pages; update `docs/_layouts/default.html` sidebar if a new page is added

## 10. Module signing quality gate

- [ ] 10.1 Run `hatch run ./scripts/verify-modules-signature.py --require-signature`; if any module manifest changed, re-sign with `hatch run python scripts/sign-modules.py --key-file <private-key.pem> <module-package.yaml ...>`
- [ ] 10.2 Bump module version for any changed module (patch increment) before re-signing
- [ ] 10.3 Re-run verification until fully green: `hatch run ./scripts/verify-modules-signature.py --require-signature`

## 11. Version and changelog

- [ ] 11.1 Bump patch version (bugfix branch): sync across `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`
- [ ] 11.2 Add `CHANGELOG.md` entry under a new `[X.Y.Z] - 2026-MM-DD` section with `Fixed` (pylint invocation, type annotations, print→logging) and `Changed` (contract coverage, complexity refactoring, CI gate)

## 12. PR and cleanup

- [ ] 12.1 Note: `openspec/CHANGE_ORDER.md` entry for `code-review-zero-findings` already added during change creation — verify it is present
- [ ] 12.2 Open PR from `bugfix/code-review-zero-findings` to `dev`; ensure all CI checks pass (including the new `specfact review` gate)
- [ ] 12.3 After PR is merged to `dev`: run `git worktree remove ../specfact-cli-worktrees/bugfix/code-review-zero-findings && git branch -d bugfix/code-review-zero-findings && git worktree prune`
