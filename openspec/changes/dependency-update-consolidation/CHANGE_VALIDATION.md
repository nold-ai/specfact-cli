# Change validation: dependency-update-consolidation

**Date:** 2026-09-21, Europe/Berlin. **Result:** proposal validated; implementation and candidate promotion remain unstarted.

## Scope and interface analysis

The approved deliverable is a planning change and matching issue. The isolated proposal worktree starts at origin/dev commit `5db1f213f1cd6dca283b86c6710379deb61bad94`. It changes only OpenSpec artifacts and change ordering. There are no changed Python interfaces, CLI commands, schemas, dependency declarations, authoritative locks, signed assets, or release versions. Interface scaffold simulation is therefore not applicable; metadata-only candidate resolution was performed in a separate disposable workspace.

The future implementation must synchronize the two Hatchling declarations, `tests/unit/scripts/test_reproducible_delivery.py`, the primary lock/export, and applicable isolated Code Review inputs. setup.py runtime declarations currently match pyproject.toml. Completed #651/#686 are foundations, not outstanding issue dependencies. No public interface break is proposed; actual dependency compatibility is unproven until the planned tests pass.

## Completed checks

- `openspec validate dependency-update-consolidation --strict`: passed.
- Scenario inspection: seven requirements cover inventory, compatible boundaries, independent screening, exact evidence, trust policy, frozen delivery, and honest planning status. Given/When/Then scenarios and planned Requirements mappings are present.
- `requirements_evidence_delivery_gate.py --staged --required-maturity planned`: passed using the repository-pinned module fixture commit `69f075819be5e1ceca1446b026b0417f19e584ca`. The report explicitly leaves implementation evidence unavailable.
- `pre-commit run`: passed on 2026-09-21 at approximately 10:19 Europe/Berlin using an isolated Python 3.12.13 environment installed from the unchanged, hash-protected baseline export. No candidate packages were installed.
- Hook scope: version-source synchronization, planned Requirements evidence, and changed Markdown passed. SpecFact's review wrapper found no staged Python files; contract-test-status reported no contract input changes. These are scoped hook skips, not a claim that runtime tests or a candidate code review executed. No hook bypass was used.
- The YAML wrapper returned success but printed existing errors in archived requirements-08 and active requirements-07 files. Those files are unchanged. Direct `yamllint -c .yamllint` of both new YAML files passed; the wrapper result does not establish repository-wide YAML cleanliness.
- Four existing vulnerability-gate runs passed, and explicit OSV queries returned no advisories for all 241 baseline/candidate package-version pairs. The 187-package inventory has a disposition for every package and records source identities and evidence gaps. See [DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md) and [dependency-inventory.json](dependency-inventory.json).
- GitHub issue [#747](https://github.com/nold-ai/specfact-cli/issues/747) was read back with parent #194, all four requested labels, and SpecFact CLI project Todo status. No outstanding blocked-by issue was returned. Hierarchy metadata was refreshed.

## Acceptance boundary and remaining risks

Review follow-up on 2026-09-21 accepted both dependency-inventory findings: optional dependency traversal incorrectly placed two primary packages in the isolated graph, and conditional incoming edges were missing. The corrected inventory preserves every ordinary/optional edge, parent version, requested extra, edge marker, and record/fork marker for both primary snapshots. Independent comparison against the hash-bound source locks matched 347 baseline and 344 candidate edges, with every external version represented. Focused checks confirmed the dev/Textual/linkify activation chain, removed `uc-micro-py`, and libcst's `pyyaml-ft` selection on Python 3.13 but not 3.11/3.12. These are metadata checks, not candidate installation or runtime tests.

The Markdown line-length annotation was rejected as a lint defect: `.markdownlint.json` explicitly disables MD013, and configured lint passes. The Cursor rule describes 120 characters as a general best practice; the review identifies no rendering or readability defect, and wrapping pipe-table rows would break their structure. Existing CI notices about runner/action versions, cache/artifact absence, and the separate maintainer-authority requirement do not originate in this planning diff. No workflow or trust control is changed to silence them. The issue's project status is now In Progress for proposal review; dependency implementation remains unstarted.

All implementation tasks remain unchecked. A negative vulnerability result is not malicious-package clearance: exact-artifact Socket/upstream review, provenance and binary coverage, intervening-release/license review, and Python 3.11–3.13/profile tests remain required before promotion. The existing Socket check on #744 skipped inspection and is not acceptance evidence.

Confidence is high in proposal scope and the recorded snapshot; compatibility and malware clearance are not yet established. New releases, advisories, registry artifacts, or a changed final graph can invalidate candidate choices. Revalidate these inputs before implementation and before release as specified in the design.

The proposal itself has low rollback cost: revert these planning files and update issue tracking. Implementation cost depends on the number of retained candidates and required release/artifact reviews; tasks must be split into units of at most two hours. An eventual implementation rollback must restore declarations, locks, exports, policy, tests, and release metadata coherently to a reviewed safe baseline. No source Dependabot PR is closed by this proposal.
