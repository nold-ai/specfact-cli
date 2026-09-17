# TDD Evidence

## Failing before implementation

- Timestamp: 2026-09-06T23:20Z
- Command: `hatch run pytest -q tests/unit/utils/test_ide_setup.py -k 'symlinked_export_root or preserves_unrelated_directory'`
- Result: **failed as expected** (`1 failed, 1 passed`). The production path
  removed the external `core` directory and wrote `specfact.test.md` through
  the repository-controlled `.cursor/commands` symlink instead of raising.

## Passing after implementation

- Timestamp: 2026-09-06T23:22Z
- Command: `hatch run pytest -q tests/unit/utils/test_ide_setup.py -k 'symlinked_export_root or preserves_unrelated_directory'`
- Result: **passed** (`2 passed, 28 deselected`).
- Command: `hatch run pytest -q tests/unit/utils/test_ide_setup.py`
- Result: **passed** (`30 passed`).
- Command: `hatch run pytest -q tests/unit/utils/test_ide_setup.py tests/unit/security/test_release_promotion_security_gates.py::test_patch_release_uses_next_version_in_all_sources tests/unit/scripts/test_reproducible_delivery.py::test_reproducible_delivery_checker_verifies_hashed_export`
- Result: **passed** (`32 passed`).

## Quality gates

- `hatch run format`: passed; 987 files unchanged.
- `hatch run type-check`: passed with 0 errors (repository baseline warnings were reported).
- `hatch run lint`: passed with 0 errors and 0 warnings.
- `hatch run yaml-lint`: command completed but reported pre-existing errors in archived and unrelated active evidence YAML.
- `openspec validate security-01-confine-ide-prompt-exports --strict`: passed.
- `hatch run python scripts/check_reproducible_delivery.py`: passed.
- `uv lock --check`: passed.
- `hatch run check-pypi-ahead`: passed; 0.55.5 is ahead of PyPI 0.55.4.
- `hatch run semgrep-sast --json --output /tmp/specfact-semgrep.json` and gate: passed with 0 findings.
- `hatch run bandit-scan`: passed with no medium/high findings.
- `hatch run verify-modules-signature`: passed for all four manifests.
- `hatch run smart-test`: 3043 passed and 34 skipped; four unrelated failures came from missing external bundle packages plus release/lock assertions that were subsequently corrected. The two corrected release/delivery tests pass in the focused 32-test run above.
- `hatch run specfact code review run --json --out .specfact/code-review.json`: produced no findings, but failed closed because the installed review module lacked verified OCI analyzer cache entries; all required analyzer evidence was `UNKNOWN`.

## Documentation and internal wiki review

- Reviewed `README.md`, `docs/`, `docs/index.md`, and navigation impact. No documentation change is needed for this repository-bound security correction.
- The sibling `specfact-cli-internal` checkout is unavailable. Follow-up: add/update `wiki/sources/security-01-confine-ide-prompt-exports.md` and run `python3 scripts/wiki_rebuild_graph.py` from that repository root.
