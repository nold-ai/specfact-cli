# Tasks: dogfooding-01-full-chain-e2e-proof

## 1. Branch and dataset setup

- [ ] 1.1 Create dedicated worktree branch `feature/dogfooding-01-full-chain-e2e-proof` from `dev`: `scripts/worktree.sh create feature/dogfooding-01-full-chain-e2e-proof`.
- [ ] 1.2 Select and document the canonical backlog slice for proof.
- [ ] 1.3 Map slice items to requirements and traceability IDs.

## 2. Test-first and failing evidence

- [ ] 2.1 Add integration tests covering backlog->requirements->architecture->validation flow.
- [ ] 2.2 Run tests expecting initial failure and capture in `TDD_EVIDENCE.md`.
- [ ] 2.3 Add validation checks for evidence schema and traceability completeness.

## 3. Implementation and verification

- [ ] 3.1 Implement minimal changes required for full-chain proof generation.
- [ ] 3.2 Generate evidence outputs and traceability matrix artifacts.
- [ ] 3.3 Re-run tests and quality gates until all proof scenarios pass.

## 4. Delivery

- [ ] 4.1 Update docs (`README.md`, `docs/index.md`, validation guide) with proof references.
- [ ] 4.2 Run `openspec validate dogfooding-01-full-chain-e2e-proof --strict`.
- [ ] 4.3 Open PR to `dev` with dogfooding evidence package.
