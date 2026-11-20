# Promotion docs fixture evidence

The old Docs Review and CLI Command Validation authentication steps failed on the actual locked fixture at `046d366c` with `The previous SpecFact module signing key is revoked`. Both new protected-lock acceptance tests failed before the workflow edit.

After the change, the same two workflow steps independently authenticated all seven documentation bundles using the protected base lock. The 64 focused tests passed, including digest and tree mismatches, a candidate-only lock, existing strict signature checks, rejection of a candidate wrapper, and module cutoff checks. Actionlint passed for both workflows.

The [first hosted run](https://github.com/nold-ai/specfact-cli/actions/runs/44835410132) stopped before the tests because the independent mapping review receipt was missing. After adding that receipt, the [test-only run](https://github.com/nold-ai/specfact-cli/actions/runs/44835834783) retained proof for both expected missing-signature failures in artifact 14678396496. The two local documentation parity suites also passed all 24 cases.
