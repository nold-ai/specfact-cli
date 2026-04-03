## 1. Branch and change setup

- [x] 1.1 Work on managed cloud branch `cursor/readme-star-conversion-a583`
- [ ] 1.2 Create worktree from `origin/dev` for `cursor/readme-star-conversion-a583`
  - cloud-managed branch is already active in this session, but AGENTS.md requires the worktree step to be tracked explicitly
- [ ] 1.3 Run `hatch env create` in the active worktree
- [ ] 1.4 Run pre-flight checks in the active worktree:
  - `hatch run smart-test-status`
  - `hatch run contract-test-status`
- [x] 1.5 Create OpenSpec change folder `openspec/changes/readme-star-conversion-01/`
- [x] 1.6 Add proposal and README-focused spec delta
- [x] 1.7 Validate change with OpenSpec CLI

## 2. Tests first (strict TDD order)

- [ ] 2.1 Update README contract tests to encode the new proof-first structure
- [ ] 2.2 Run targeted docs tests and capture a failing result before editing `README.md`
- [ ] 2.3 Record the failing command, timestamp, and failure summary in
  `openspec/changes/readme-star-conversion-01/TDD_EVIDENCE.md`

## 3. Evidence capture

- [ ] 3.1 Add `docs/_support/readme-first-contact/capture-readme-output.sh`
- [ ] 3.2 Capture raw `specfact code review run` output against `specfact-demo-repo`
- [ ] 3.3 Store raw output and run metadata under `docs/_support/readme-first-contact/sample-output/`
- [ ] 3.4 Pin the CLI version used by the capture and document rerun steps in the evidence folder

## 4. README restructure

- [ ] 4.1 Rewrite the README top screen around a concrete hook, badges, quickstart, sample output,
  and CTA
- [ ] 4.2 Add a concrete "What SpecFact does" summary near the top
- [ ] 4.3 Add pre-commit and GitHub Actions snippets in the upper half of the README
- [ ] 4.4 Add a short "How SpecFact is built" trust section
- [ ] 4.5 Move team / enterprise, module-system, and documentation-topology sections below the fold
- [ ] 4.6 Update `docs/index.md` only if needed to preserve first-contact parity with the README

## 5. Verify and document

- [ ] 5.1 Re-run the targeted docs tests and record passing evidence in
  `openspec/changes/readme-star-conversion-01/TDD_EVIDENCE.md`
- [ ] 5.2 Run required quality gates for the changed files:
  - `hatch run format`
  - `hatch run type-check`
  - `hatch run lint`
  - `hatch run yaml-lint`
  - `hatch run contract-test`
  - `hatch run smart-test`
- [ ] 5.3 Refresh `.specfact/code-review.json` and resolve any findings
- [ ] 5.4 Run `hatch run ./scripts/verify-modules-signature.py --require-signature`
- [ ] 5.5 Update `openspec/CHANGE_ORDER.md` with this change entry

## 6. Git and PR

- [ ] 6.1 Commit the OpenSpec + README conversion change with a conventional commit message
- [ ] 6.2 Push branch `cursor/readme-star-conversion-a583`
- [ ] 6.3 Create or update the PR against `dev`
- [ ] 6.4 After merge, remove/prune the worktree per AGENTS.md cleanup policy
