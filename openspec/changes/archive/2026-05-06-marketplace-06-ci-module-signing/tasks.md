# Implementation history (post-hoc archive note)

This change shipped through a sequence of merged PRs against `dev` rather than a
single feature PR. Tasks are marked `[x]` in bulk to reflect that the deliverables
landed; consult these PRs for the actual line-level history:

- PR #501 — `chore(pre-commit): modular hooks + branch-aware module verify`
- PR #503 — `feat(ci): module signing on PR approval and manual workflow_dispatch`
- PR #504 — `Feature/ci module sign on approval`
- PR #505 — `feat(ci): workflow_dispatch for sign-modules-on-approval`
- Commit `a1dda6d7` — `fix(ci): module signing workflows, PyPI version check, and review gate`
- Releases: PR #502 (v0.46.1), PR #506 (v0.46.2 module signing CI)

Deliverables verified on disk at archive time:

- `.github/workflows/sign-modules-on-approval.yml`
- `scripts/git-branch-module-signature-flag.sh`
- `pr-orchestrator.yml` `verify-module-signatures` branch-aware gating
- `sign-modules.yml` main-only verify trigger

This change was incorrectly placed in `openspec/parking-lot/` during the
2026-05-05 triage; archive on 2026-05-06 corrects that.

## 1. Branch, coordination, and issue sync

- [x] 1.1 Create `feature/marketplace-06-ci-module-signing` in a dedicated worktree from `origin/dev`;
  run `hatch env create`, then pre-flight status checks `hatch run smart-test-status` and
  `hatch run contract-test-status`.
- [x] 1.2 ~~Create a GitHub User Story issue~~ Issue created: [#500](https://github.com/nold-ai/specfact-cli/issues/500) under Parent Feature
  [#353](https://github.com/nold-ai/specfact-cli/issues/353); `proposal.md` Source Tracking updated. *(done)*
- [x] 1.3 Confirm paired `specfact-cli-modules/marketplace-06-ci-module-signing` change is available
  and note the dependency in both PR descriptions. *(human)*

## 2. Specs and TDD evidence (failing tests first)

- [x] 2.1 Write unit tests for branch policy (`scripts/git-branch-module-signature-flag.sh` and
  `pre-commit-verify-modules.sh` wiring), e.g. under `tests/unit/scripts/`, covering: non-main omits
  `--require-signature`, main requires signature, detached `HEAD` matches non-main policy, no staged
  module paths skips verify. Run and capture failing output in `TDD_EVIDENCE.md`.
- [x] 2.2 Write integration tests (or workflow-syntax tests) for the signing workflow YAML structure
  in `tests/unit/workflows/test_sign_modules_on_approval.py` — validate trigger config, required
  env vars, and commit-back step presence. Capture failing output in `TDD_EVIDENCE.md`.
- [x] 2.3 Write tests for the updated `pr-orchestrator.yml` `verify-module-signatures` logic
  confirming the branch split (omit `--require-signature` for dev, pass `--require-signature` for main).
  Capture failing output in `TDD_EVIDENCE.md`.

## 3. Pre-commit hook — branch-aware verification

- [x] 3.1 Implement branch policy in `scripts/git-branch-module-signature-flag.sh` (`require` on `main`,
  `omit` elsewhere) and wire `scripts/pre-commit-verify-modules.sh` to pass `--require-signature` only
  when policy is `require`; always pass `--enforce-version-bump --payload-from-filesystem` when the
  hook runs. Skip the hook when no staged paths under `modules/` or `src/specfact_cli/modules/`.
- [x] 3.2 Register the verify script in `.pre-commit-config.yaml` and ensure `pre-commit-quality-checks.sh`
  `all` invokes module verification (modular hooks + `pre-commit-smart-checks.sh` repo-root shim as needed).
- [x] 3.3 Run the TDD unit tests from 2.1 and confirm they pass; record passing run in `TDD_EVIDENCE.md`.

## 4. pr-orchestrator.yml — split verify by target branch

- [x] 4.1 In `.github/workflows/pr-orchestrator.yml`, in the `verify-module-signatures` job,
  add branch-target detection: extract `github.event.pull_request.base.ref` (for PR events) and
  `github.ref` (for push events).
- [x] 4.2 For events targeting `dev` (PR base = `dev` or push ref = `refs/heads/dev`): omit
  `--require-signature` from the verifier invocation (checksum-only); keep
  `--enforce-version-bump --payload-from-filesystem`.
- [x] 4.3 For events targeting `main` (PR base = `main` or push ref = `refs/heads/main`): retain
  `--require-signature --enforce-version-bump --payload-from-filesystem`.
- [x] 4.4 Run actionlint on the modified workflow: `hatch run lint-workflows`. Fix any findings.

## 5. sign-modules.yml — scope to main only

- [x] 5.1 In `.github/workflows/sign-modules.yml`, change the `verify` job trigger filter from
  `branches: [dev, main]` to `branches: [main]` (push and pull_request triggers).
- [x] 5.2 Remove `dev` from the `push.branches` and `pull_request.branches` trigger lists.
- [x] 5.3 Leave the `reproducibility` job unchanged (already guarded by secret availability check
  and only meaningful on main).
- [x] 5.4 Run actionlint on the modified workflow. Fix any findings.

## 6. New workflow — sign-modules-on-approval.yml

- [x] 6.1 Create `.github/workflows/sign-modules-on-approval.yml` with trigger:
  `pull_request_review: types: [submitted]`.
- [x] 6.2 Add job-level condition:
  `if: github.event.review.state == 'approved' && (github.event.pull_request.base.ref == 'dev' || github.event.pull_request.base.ref == 'main')`.
- [x] 6.3 Add job steps: checkout PR head (`ref: ${{ github.event.pull_request.head.sha }}`), set up
  Python 3.12, install signing deps (`pyyaml beartype icontract cryptography cffi`).
- [x] 6.4 Add signing step: resolve `BASE_REF` as `origin/${{ github.event.pull_request.base.ref }}`;
  run `python scripts/sign-modules.py --changed-only --base-ref "$BASE_REF" --bump-version patch
  --payload-from-filesystem` with env vars `SPECFACT_MODULE_PRIVATE_SIGN_KEY` and
  `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE` from secrets. Fail immediately if either secret is
  empty.
- [x] 6.5 Add write-back step: configure git user (github-actions bot), `git add` changed
  `module-package.yaml` files, commit with message `chore(modules): ci sign changed modules
  [skip ci]` (skip if no files changed), push to PR branch using `GITHUB_TOKEN` with
  `permissions: contents: write`.
- [x] 6.6 Add a final no-op step that emits a job summary showing which manifests were signed
  (or "no changes" if none).
- [x] 6.7 Run actionlint on the new workflow. Fix any findings.

## 7. Testing and quality gates

- [x] 7.1 Run `hatch run smart-test-status`; if stale, run `hatch run smart-test` and confirm the
  new tests from sections 2.1–2.3 pass.
- [x] 7.2 Run `hatch run contract-test` and confirm it passes with the shell-script changes.
- [x] 7.3 Run `hatch run lint` (ruff + basedpyright + pylint) — no Python source changes expected,
  but confirm lint is clean.
- [x] 7.4 Run `hatch run yaml-lint` to validate all modified and new YAML workflow files.
- [x] 7.5 Run `specfact code review run --json --out .specfact/code-review.json`; resolve every
  finding at warning or error severity before marking this change complete.
- [x] 7.6 Record final passing test runs in `TDD_EVIDENCE.md`.
- [x] 7.7 Run `openspec validate marketplace-06-ci-module-signing --strict` from the repo root; fix any
  validation errors and re-run until the command passes before marking this change complete.

## 8. Documentation

- [x] 8.1 Review `docs/getting-started/installation.md` and `docs/reference/` for any mention of
  local module signing requirements; update to reflect that signing is now automated via CI.
- [x] 8.2 Add or update a note in the contributor guide (or `docs/` equivalent) explaining the
  new signing flow: "module manifests are signed automatically by CI when a PR is approved; no
  local key setup is required for development on feature or dev branches."
- [x] 8.3 Update `CHANGELOG.md` with the version bump for this change.

## 9. PR and cleanup

- [x] 9.1 Push the branch and open a PR targeting `dev`; verify CI passes (no `--require-signature`
  on dev PRs, so no signing needed for this change itself).
- [x] 9.2 Link the PR to the GitHub issue created in 1.2.
- [x] 9.3 After merge: remove the worktree (`git worktree remove`), delete the local branch, and run
  `git worktree prune`.
- [x] 9.4 Record cleanup completion in `TDD_EVIDENCE.md`.
