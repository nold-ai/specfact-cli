## Readiness and baseline

- [x] Verify live issue hierarchy, project status, dependencies and implementation ownership.
- [ ] Inventory active Semgrep packs, language/scope, package edges, commands, output consumers, exceptions and independent CI baselines.
- [x] Bind fixture selectors and record genuine RED on the existing independent CI entry point.
- [x] Bind and run standalone Python SAST fixtures against the six current rule IDs and compare tracked paths with the existing scanner.

## Replacement

- [ ] Prove one independent CI slice with Ruff/Bandit and a source-bound compatible baseline.
- [x] Replace the independent workflow's Semgrep command in the local candidate and prove the new step's blocking exit codes and evidence.
- [ ] Complete rule dispositions and handle any supported non-Python structural requirements with audited tooling.
- [ ] Migrate feature, quality and async paths and their consumers while preserving required coverage and failure reporting.
- [ ] Remove Semgrep provisioning, commands, rules, dependency and lock edges, and scanner-specific audit records after the replacement is green.

## Cutover

- [ ] Verify exact built wheels, extras, locks, supported external installs and independent security/audit gates.
- [ ] Coordinate core #769 and modules #516 to verify the exact compatible signed pair without the retired scanner graph.
- [ ] Update docs, migration guidance and rollback, run required review and release checks, and archive after merge.
