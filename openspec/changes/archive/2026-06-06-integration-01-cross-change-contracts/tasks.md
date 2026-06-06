# Tasks: integration-01-cross-change-contracts

## 1. Branch and authority setup

- [ ] 1.1 Create dedicated worktree branch `feature/integration-01-cross-change-contracts` from `dev`: `scripts/worktree.sh create feature/integration-01-cross-change-contracts`.
- [ ] 1.2 Confirm all architecture-plan changes reference this umbrella contract.
- [ ] 1.3 Establish owner matrix for shared interfaces/files.

## 2. Spec and validation-first

- [ ] 2.1 Finalize integration contract spec scenarios.
- [ ] 2.2 Add/align validation checks for ownership and compatibility evidence.
- [ ] 2.3 Run failing-first checks for contract enforcement and record in `TDD_EVIDENCE.md`.

## 3. Integration controls

- [ ] 3.1 Add wave gate criteria and apply-phase guidance across dependent changes.
- [ ] 3.2 Add docs references for integration contract usage.
- [ ] 3.3 Re-run `openspec validate integration-01-cross-change-contracts --strict`.

## 4. Delivery

- [ ] 4.1 Update `openspec/CHANGE_ORDER.md` with final issue links and blockers.
- [ ] 4.2 Open PR to `dev` with cross-change contract evidence.
