## 1. Branch, coordination, and issue sync

- [ ] 1.1 Create `feature/marketplace-06-ci-module-signing` in a dedicated worktree from `origin/dev`;
  run `hatch env create`, then pre-flight status checks `hatch run smart-test-status` and
  `hatch run contract-test-status`.
- [ ] 1.2 ~~Create a GitHub User Story issue~~ Issue created: [#500](https://github.com/nold-ai/specfact-cli/issues/500) under Parent Feature
  [#353](https://github.com/nold-ai/specfact-cli/issues/353); `proposal.md` Source Tracking updated. *(done)*
- [ ] 1.3 Confirm paired `specfact-cli-modules/marketplace-06-ci-module-signing` change is available
  and note the dependency in both PR descriptions. *(human)*

## 2. Specs and TDD evidence (failing tests first)

- [ ] 2.1 Write unit tests for the pre-commit branch-detection logic in
  `tests/unit/scripts/test_pre_commit_module_signing.py` covering: non-main branch accepts unsigned,
  main branch rejects unsigned, no module changes passes without check. Run and capture failing
  output in `TDD_EVIDENCE.md`.
- [ ] 2.2 Write integration tests (or workflow-syntax tests) for the signing workflow YAML structure
  in `tests/unit/workflows/test_sign_modules_on_approval.py` — validate trigger config, required
  env vars, and commit-back step presence. Capture failing output in `TDD_EVIDENCE.md`.
- [ ] 2.3 Write tests for the updated `pr-orchestrator.yml` `verify-module-signatures` logic
  confirming the branch split (`--allow-unsigned` for dev, `--require-signature` for main). Capture
  failing output in `TDD_EVIDENCE.md`.

## 3. Pre-commit hook — branch-aware verification

- [ ] 3.1 In `scripts/pre-commit-smart-checks.sh`, refactor `run_module_signature_verification()`
  to detect the current branch via `git branch --show-current` (fallback: `git rev-parse
  --abbrev-ref HEAD`).
- [ ] 3.2 Apply policy: if branch is NOT `main`, call
  `hatch run ./scripts/verify-modules-signature.py --allow-unsigned --enforce-version-bump`;
  if branch IS `main`, keep the existing `--require-signature --enforce-version-bump` call.
- [ ] 3.3 Run the TDD unit tests from 2.1 and confirm they pass; record passing run in
  `TDD_EVIDENCE.md`.

## 4. pr-orchestrator.yml — split verify by target branch

- [ ] 4.1 In `.github/workflows/pr-orchestrator.yml`, in the `verify-module-signatures` job,
  add branch-target detection: extract `github.event.pull_request.base.ref` (for PR events) and
  `github.ref` (for push events).
- [ ] 4.2 For events targeting `dev` (PR base = `dev` or push ref = `refs/heads/dev`): replace
  `--require-signature` with no flag (or explicit `--allow-unsigned` equivalent); keep
  `--enforce-version-bump --payload-from-filesystem`.
- [ ] 4.3 For events targeting `main` (PR base = `main` or push ref = `refs/heads/main`): retain
  `--require-signature --enforce-version-bump --payload-from-filesystem`.
- [ ] 4.4 Run actionlint on the modified workflow: `hatch run lint-workflows`. Fix any findings.

## 5. sign-modules.yml — scope to main only

- [ ] 5.1 In `.github/workflows/sign-modules.yml`, change the `verify` job trigger filter from
  `branches: [dev, main]` to `branches: [main]` (push and pull_request triggers).
- [ ] 5.2 Remove `dev` from the `push.branches` and `pull_request.branches` trigger lists.
- [ ] 5.3 Leave the `reproducibility` job unchanged (already guarded by secret availability check
  and only meaningful on main).
- [ ] 5.4 Run actionlint on the modified workflow. Fix any findings.

## 6. New workflow — sign-modules-on-approval.yml

- [ ] 6.1 Create `.github/workflows/sign-modules-on-approval.yml` with trigger:
  `pull_request_review: types: [submitted]`.
- [ ] 6.2 Add job-level condition:
  `if: github.event.review.state == 'approved' && (github.event.pull_request.base.ref == 'dev' || github.event.pull_request.base.ref == 'main')`.
- [ ] 6.3 Add job steps: checkout PR head (`ref: ${{ github.event.pull_request.head.sha }}`), set up
  Python 3.12, install signing deps (`pyyaml beartype icontract cryptography cffi`).
- [ ] 6.4 Add signing step: resolve `BASE_REF` as `origin/${{ github.event.pull_request.base.ref }}`;
  run `python scripts/sign-modules.py --changed-only --base-ref "$BASE_REF" --bump-version patch
  --payload-from-filesystem` with env vars `SPECFACT_MODULE_PRIVATE_SIGN_KEY` and
  `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE` from secrets. Fail immediately if either secret is
  empty.
- [ ] 6.5 Add write-back step: configure git user (github-actions bot), `git add` changed
  `module-package.yaml` files, commit with message `chore(modules): ci sign changed modules
  [skip ci]` (skip if no files changed), push to PR branch using `GITHUB_TOKEN` with
  `permissions: contents: write`.
- [ ] 6.6 Add a final no-op step that emits a job summary showing which manifests were signed
  (or "no changes" if none).
- [ ] 6.7 Run actionlint on the new workflow. Fix any findings.

## 7. Testing and quality gates

- [ ] 7.1 Run `hatch run smart-test-status`; if stale, run `hatch run smart-test` and confirm the
  new tests from sections 2.1–2.3 pass.
- [ ] 7.2 Run `hatch run contract-test` and confirm it passes with the shell-script changes.
- [ ] 7.3 Run `hatch run lint` (ruff + basedpyright + pylint) — no Python source changes expected,
  but confirm lint is clean.
- [ ] 7.4 Run `hatch run yaml-lint` to validate all modified and new YAML workflow files.
- [ ] 7.5 Run `specfact code review run --json --out .specfact/code-review.json`; resolve every
  finding at warning or error severity before marking this change complete.
- [ ] 7.6 Record final passing test runs in `TDD_EVIDENCE.md`.

## 8. Documentation

- [ ] 8.1 Review `docs/getting-started/installation.md` and `docs/reference/` for any mention of
  local module signing requirements; update to reflect that signing is now automated via CI.
- [ ] 8.2 Add or update a note in the contributor guide (or `docs/` equivalent) explaining the
  new signing flow: "module manifests are signed automatically by CI when a PR is approved; no
  local key setup is required for development on feature or dev branches."
- [ ] 8.3 Update `CHANGELOG.md` with the version bump for this change.

## 9. PR and cleanup

- [ ] 9.1 Push the branch and open a PR targeting `dev`; verify CI passes (no `--require-signature`
  on dev PRs, so no signing needed for this change itself).
- [ ] 9.2 Link the PR to the GitHub issue created in 1.2.
- [ ] 9.3 After merge: remove the worktree (`git worktree remove`), delete the local branch, and run
  `git worktree prune`.
- [ ] 9.4 Record cleanup completion in `TDD_EVIDENCE.md`.
