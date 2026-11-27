# Tasks: dogfooding-01-full-chain-e2e-proof

## Scope rescope — 2026-09-20

Measure bounded defect-detection and operational overhead on real changes. Use existing CI artifacts; retain failures/reproductions that demonstrate test sensitivity. No mandatory immutable RED history or repeated seal approvals for the lean dogfood path. Stronger assurance experiments remain explicitly selected.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../requirements-09-minimal-evidence/proposal.md).

Implementation discipline: use focused regression/reproduction and current-run results. Any task requiring immutable hosted RED, frozen test authoring or approval receipts merely to implement this feature is superseded; tests of an explicitly selected optional seal feature remain in scope.

## 1. Branch and proof setup

- [ ] 1.1 Create dedicated worktree branch `feature/dogfooding-01-full-chain-e2e-proof` from `dev`: `scripts/worktree.sh create feature/dogfooding-01-full-chain-e2e-proof`.
- [ ] 1.2 Select and document the canonical PR or demo repository slice for proof.
- [ ] 1.3 Capture the baseline command sequence, JSON output path, and evidence comparison criteria.

## 2. Test-first and failing evidence

- [ ] 2.1 Add integration cases for ordinary review -> existing CI evidence -> remediation -> rerun comparison without full-chain/RED requirements; separately retain missing-link failures for explicitly selected full-chain experiments.
- [ ] 2.2 Observe relevant regression failures before implementation and summarize them briefly; retain detailed output in ordinary CI artifacts.
- [ ] 2.3 Add validation checks for evidence schema, AI-bloat findings, remediation packet references, and rerun deltas.

## 3. Implementation and verification

- [ ] 3.1 Implement the bounded validation loop using existing CI outputs; require full-chain link evidence only when that experiment is explicitly selected.
- [ ] 3.2 Reuse JSON outputs, remediation packets and rerun artifacts; summarize detected regressions and operational overhead.
- [ ] 3.3 Re-run tests and quality gates until all proof scenarios pass.

## 4. Delivery

- [ ] 4.1 Update docs (`README.md`, `docs/index.md`, validation guide) with proof references.
- [ ] 4.2 Run `openspec validate dogfooding-01-full-chain-e2e-proof --strict`.
- [ ] 4.3 Open PR to `dev` with dogfooding evidence package.
