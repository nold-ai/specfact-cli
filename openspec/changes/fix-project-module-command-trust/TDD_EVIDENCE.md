# TDD Evidence

## Failing before

- **Timestamp**: 2026-09-07T01:11Z
- **Command**: `hatch run pytest tests/unit/specfact_cli/registry/test_module_packages.py -q -k 'spoofed_official_bundle_identity or unsigned_project_module_requires_integrity_and_signature or explicit_unsigned_override_preserves_project_module_development'`
- **Result**: expected red; 2 failed and 1 passed. The spoofed manifest was accepted as `specfact-requirements`, and project registration called artifact verification without requiring integrity or a signature.

## Passing after

- **Timestamp**: 2026-09-07T01:12Z
- **Command**: `hatch run pytest tests/unit/specfact_cli/registry/test_module_packages.py -q -k 'spoofed_official_bundle_identity or unsigned_project_module_requires_integrity_and_signature or explicit_unsigned_override_preserves_project_module_development or requirements_bundle_mounts_native'`
- **Result**: 4 passed.
- **Timestamp**: 2026-09-07T01:13Z
- **Command**: `hatch run pytest tests/unit/specfact_cli/registry/test_module_packages.py tests/unit/cli/test_lean_help_output.py -q`
- **Result**: 67 passed and 1 pre-existing migration skip.
- **Timestamp**: 2026-09-07T01:14Z
- **Commands**: `hatch run format`, `hatch run type-check`, `hatch run lint`, `openspec validate fix-project-module-command-trust --strict`, and `hatch run check-version-sources`.
- **Result**: passed; BasedPyright reported 0 errors with repository-existing warnings.
- **Timestamp**: 2026-09-07T01:16Z
- **Commands**: `hatch run semgrep-sast --json --output /tmp/specfact-semgrep.json`, `hatch run semgrep-sast-gate --results /tmp/specfact-semgrep.json --baseline tools/semgrep/sast-baseline.json`, `hatch run bandit-scan`, and `hatch run verify-modules-signature-pr --version-check-base HEAD~1`.
- **Result**: passed with no blocking Semgrep or Bandit findings and all four module manifests verified.
- **Timestamp**: 2026-09-07T01:17Z
- **Commands**: `uv lock`, `hatch run python scripts/check_reproducible_delivery.py`, and `uv lock --check`.
- **Result**: passed after synchronizing the project version in `uv.lock`.

## Baseline and environment limitations

- `hatch run smart-test` completed 3,044 tests with 4 failures and 34 skips. Two failures were corrected by synchronizing the new patch version and lockfile; two unrelated command-audit/import failures require absent external `specfact-backlog` and `specfact-spec` modules.
- `hatch run yaml-lint` reports pre-existing long-line/blank-line findings in archived `requirements-08-bounded-red-green-proof` evidence and active `requirements-07-runtime-proof-delivery` evidence; it exits zero and reports no finding in this change.
- `hatch run specfact code review run --json --out .specfact/code-review.json --scope changed` produced the required local report, but its verdict is `UNKNOWN` because the released review module could not acquire its verified OCI analyzer cache. Independent local Ruff, BasedPyright, Semgrep, Bandit, and contract gates were run separately.
- The sibling `specfact-cli-internal` checkout was unavailable at `/workspace/specfact-cli-internal`; mirror `fix-project-module-command-trust` into `wiki/sources/` and run `python3 scripts/wiki_rebuild_graph.py` from that repository root as a follow-up.
