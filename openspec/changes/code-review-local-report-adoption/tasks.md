# Planned implementation tasks

All tasks remain planned and unchecked. Planning validation is not implementation evidence.

- [ ] 1. Revalidate modules #515 delivery, GitHub hierarchy/status, exact producer schema, and ordinary consumer paths before implementation.
- [ ] 2. Confirm spec scenarios against the released producer contract before adding tests.
- [ ] 3. Add behavior tests for explicit schema dispatch, separate C15 schema 1.7 routing and retirement authority, historical 1.6 support boundaries, unsupported majors, malformed evidence, and process/report disagreement.
- [ ] 4. Add behavior tests for producer assurance/completeness and truthful shadow summaries independent of score/fixability.
- [ ] 5. Record observed RED commands, timestamps, results and causes in openspec/changes/code-review-local-report-adoption/TDD_EVIDENCE.md before production edits.
- [ ] 6. Implement narrow ordinary hook/workflow report consumption and invocation updates.
- [ ] 7. Implement only necessary module loading/discovery/install compatibility using supported external tooling or declared dependencies; preserve descriptor semantics and customer environment isolation.
- [ ] 8. Record GREEN commands, timestamps and results in openspec/changes/code-review-local-report-adoption/TDD_EVIDENCE.md after implementation, including one complete installed customer local review workflow.
- [ ] 9. Collect consumer-compatibility preflight evidence for exact installed core and signed modules across pipx, uv tool, and uvx, including no pip and a different project Python; hand it to modules #516, which owns release-level installation acceptance and the manager/platform matrix.
- [ ] 10. Run required format, type-check, lint, YAML, contract, smart-test, independent security, clean-code review, and applicable signature/version gates; resolve findings.
- [ ] 11. Update ordinary user documentation and internal wiki source alignment, then rebuild the graph from the internal repository root.
- [ ] 12. Select the owner-approved semver change for the implemented behavior; synchronize pyproject.toml, setup.py, src/__init__.py and src/specfact_cli/__init__.py, and add a dated CHANGELOG.md entry after quality gates and documentation, before opening the implementation PR.
- [ ] 13. Revalidate strictly and archive with openspec archive only after actual completed implementation and merge.
