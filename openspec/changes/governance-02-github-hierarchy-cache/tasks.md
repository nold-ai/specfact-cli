## 1. Change setup and governance sync

- [x] 1.1 Create and sync the GitHub issue for `governance-02-github-hierarchy-cache`, link it to the correct parent Feature, and update `openspec/CHANGE_ORDER.md` plus proposal source tracking.
- [x] 1.2 Validate the change artifacts and capture the validation report in `openspec/changes/governance-02-github-hierarchy-cache/CHANGE_VALIDATION.md`.

## 2. Spec-first test setup

- [x] 2.1 Add or update tests for hierarchy fingerprinting, deterministic markdown rendering, and fast no-change exit behavior.
- [x] 2.2 Run the targeted test command, confirm it fails before implementation, and record the failing run in `openspec/changes/governance-02-github-hierarchy-cache/TDD_EVIDENCE.md`.

## 3. Implementation

- [x] 3.1 Implement the repository-local GitHub hierarchy cache sync script and state file handling under `scripts/`.
- [x] 3.2 Generate the initial `.specfact/backlog/github_hierarchy_cache.md` output and ensure reruns remain deterministic without committing it.
- [x] 3.3 Update `openspec/config.yaml` and `AGENTS.md` so GitHub issue setup and parent lookup use the cache-first workflow.

## 4. Verification

- [x] 4.1 Re-run the targeted tests and record the passing run in `openspec/changes/governance-02-github-hierarchy-cache/TDD_EVIDENCE.md`.
- [x] 4.2 Run the required repo quality gates for the touched scope, including code review JSON refresh if stale.
