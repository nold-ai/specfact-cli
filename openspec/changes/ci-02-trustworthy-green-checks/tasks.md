# Tasks: ci-02-trustworthy-green-checks

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for any behavior-changing task. Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last. Do not implement workflow/config changes until tests or validation checks exist and have been run with failing evidence where behavior changes are enforced.

---

## 1. Create git worktree for this change

- [x] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [x] 1.1.1 `git fetch origin`
  - [x] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/ci-02-trustworthy-green-checks -b feature/ci-02-trustworthy-green-checks origin/dev`
  - [x] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/ci-02-trustworthy-green-checks`
  - [x] 1.1.4 Run `hatch env create` in the worktree to create the virtual environment and install
    the dev dependencies required by the documented repository workflow.
  - [x] 1.1.5 Verify the branch: `git branch --show-current`

## 2. Spec-first preparation

- [x] 2.1 Finalize the gate taxonomy in `specs/trustworthy-green-checks/spec.md`.
- [x] 2.2 Audit current enforcement semantics in:
  - [x] 2.2.1 `.github/workflows/pr-orchestrator.yml`
  - [x] 2.2.2 `.github/workflows/pre-merge-check.yml`
  - [x] 2.2.3 `.pre-commit-config.yaml`
  - [x] 2.2.4 `scripts/pre-commit-smart-checks.sh`
  - [x] 2.2.5 `.coderabbit.yaml`
  - [x] 2.2.6 archived/main doc-frontmatter specs, changelog, and contributor docs for review-driven markdown/spec drift

## 3. Test-first / validation-first evidence

- [x] 3.1 Add or update workflow/unit tests that prove required jobs fail when underlying tools fail and that advisory jobs are explicitly marked as advisory.
- [x] 3.2 Add or update tests for `dev -> main` skip semantics so follow-up commits invalidate unsafe fast-path assumptions.
- [x] 3.3 Add or update tests/spec assertions that required checks still report on docs-only or otherwise out-of-scope PR commits instead of disappearing behind workflow-level path filters.
- [x] 3.4 Add or update tests for pre-commit parity or supported-hook installation behavior.
- [x] 3.5 Add or update tests for review JSON failure handling and doc-frontmatter helper expectations.
- [x] 3.6 Run the new/updated tests before implementation and capture failing evidence in `TDD_EVIDENCE.md`.

## 4. Implementation: CI hardening

- [x] 4.1 Remove failure-swallowing patterns from required jobs in `pr-orchestrator.yml`.
- [x] 4.2 Rename or isolate remaining advisory jobs so their non-blocking status is explicit in job names and logs.
- [x] 4.3 Add mandatory workflow validation in CI for `.github/workflows/**` changes.
- [x] 4.4 Rework required-check triggers so required branch-protection checks always emit a status on every PR head commit, including docs-only follow-up pushes.
- [x] 4.5 Normalize overlapping check/job names between orchestrator and dedicated workflows so branch protection targets a single canonical name per gate.
- [x] 4.6 Rework `dev -> main` skip logic so only provably safe parity skips are allowed; otherwise run the required validation set.
- [x] 4.7 Keep docs-only validation behavior explicit and compatible with docs-review workflow ownership.

## 5. Implementation: local and review parity

- [x] 5.1 Align `.pre-commit-config.yaml` with the supported smart-check path, or make the supported hook-install path authoritative and explicit in repo docs.
- [x] 5.2 Update `.coderabbit.yaml` so automatic review coverage includes both `dev` and `main` PR targets.
- [x] 5.3 Document which review outputs are advisory versus merge-blocking.

## 6. Implementation: review remediation and publication readiness

- [x] 6.1 Fix valid markdownlint/style findings in `CHANGELOG.md`, `CONTRIBUTING.md`, and `docs/contributing/docs-sync.md`.
- [x] 6.2 Fix valid archived/main OpenSpec spec publication issues (purpose text, heading spacing, unique headings, API-name drift, and scenario completeness).
- [x] 6.3 Harden `scripts/pre_commit_code_review.py` report parsing/output handling and `scripts/check_doc_frontmatter.py` parse-failure diagnostics.
- [x] 6.4 Align helper fixtures/tests with implemented doc-frontmatter behavior.

## 7. Quality gates and documentation

- [x] 7.1 `hatch run format`
- [x] 7.2 `hatch run type-check`
- [x] 7.3 `hatch run lint`
- [x] 7.4 `hatch run yaml-lint`
- [x] 7.5 `hatch run lint-workflows`
- [x] 7.6 Run targeted tests for workflow, hook, and doc-frontmatter remediation changes.
- [x] 7.7 Update contributor docs / CI docs describing trustworthy green-check semantics.
- [x] 7.8 Run `openspec validate ci-02-trustworthy-green-checks --strict` and resolve all issues.

## 8. Delivery

- [x] 8.1 Update `openspec/CHANGE_ORDER.md` with implementation status when work begins/lands.
- [x] 8.2 Stage and commit with a Conventional Commit message.
- [x] 8.3 Push `feature/ci-02-trustworthy-green-checks` and open a PR to `dev`.
