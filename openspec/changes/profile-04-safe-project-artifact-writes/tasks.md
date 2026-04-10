## 1. Branch, coordination, and issue sync

- [ ] 1.1 Create `bugfix/profile-04-safe-project-artifact-writes` in a dedicated worktree from `origin/dev` and bootstrap Hatch in that worktree.
- [ ] 1.2 Sync the change proposal to GitHub under parent feature `#365`, link bug `#487`, and update `proposal.md` Source Tracking with issue metadata.
- [ ] 1.3 Confirm the paired modules-side change `project-runtime-01-safe-artifact-write-policy` is available and note the dependency in both PR descriptions/change evidence.

## 2. Specs, regression fixtures, and failing evidence

- [ ] 2.1 Add or update regression fixtures for existing user-owned project artifacts such as `.vscode/settings.json` with unrelated custom settings.
- [ ] 2.2 Write tests from the new scenarios covering partial ownership, malformed settings fail-safe behavior, backup creation, and preservation of unrelated settings.
- [ ] 2.3 Write tests for the CI/static unsafe-write gate so direct writes to protected project artifacts are rejected unless routed through the sanctioned helper.
- [ ] 2.4 Run the targeted tests before implementation, capture the failing results, and record commands/timestamps in `openspec/changes/profile-04-safe-project-artifact-writes/TDD_EVIDENCE.md`.

## 3. Core safe-write implementation

- [ ] 3.1 Implement the core safe-write helper and ownership model with `@beartype` and `@icontract` on public APIs.
- [ ] 3.2 Route `src/specfact_cli/utils/ide_setup.py` settings mutation through the helper so `.vscode/settings.json` preserves unrelated user-managed settings and strips only SpecFact-managed entries when needed.
- [ ] 3.3 Route applicable init/setup artifact copy flows through the helper or explicit safe modes, including fail-safe handling for malformed structured files and backup creation for explicit replacement.
- [ ] 3.4 Implement the CI/static guard for protected user-project artifacts in init/setup code paths and integrate it into the relevant local/CI quality workflow.

## 4. Verification, docs, and cross-repo handoff

- [ ] 4.1 Re-run the targeted tests and any broader init/setup regression coverage, capture passing results, and update `TDD_EVIDENCE.md`.
- [ ] 4.2 Research and update affected docs (`README.md`, installation/quickstart/init references) to document preservation guarantees, backup behavior, and explicit replacement semantics.
- [ ] 4.3 Run quality gates: `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run yaml-lint`, `hatch run contract-test`, and `hatch run smart-test`.
- [ ] 4.4 Run `hatch run ./scripts/verify-modules-signature.py --require-signature`; if any bundled module manifests changed, bump versions, re-sign as required, and re-run verification.
- [ ] 4.5 Ensure `.specfact/code-review.json` is fresh, remediate all findings, and record the final review command/timestamp in `TDD_EVIDENCE.md` or PR notes.
- [ ] 4.6 Apply the appropriate version/changelog update for a bugfix release if implementation changes user-facing behavior, then open a PR to `dev` referencing the paired modules change.

## 5. Worktree cleanup

- [ ] 5.1 Remove the worktree used for this change (for example `git worktree remove ../specfact-cli-worktrees/bugfix/profile-04-safe-project-artifact-writes`).
- [ ] 5.2 Delete the local branch after merge (`git branch -d bugfix/profile-04-safe-project-artifact-writes`).
- [ ] 5.3 Prune stale worktree metadata (`git worktree prune`).
- [ ] 5.4 Record cleanup completion in `TDD_EVIDENCE.md` alongside the 4.x verification notes.
