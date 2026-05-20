# TDD Evidence: upgrade-02-pipx-spaced-home-output

## Readiness

- Issue `#570` is a core CLI upgrade-output bug: `specfact upgrade` delegates to pipx and currently lets pipx's successful-upgrade warning block appear in normal output.
- Change issue `#572` was created with `bug`, `openspec`, `change-proposal`, and `QA` labels.
- Issue `#572` was added as a sub-issue of Feature `#375`.
- Issue `#570` was marked blocked by `#572`.
- Issue `#572` is assigned to the `SpecFact CLI` project with Todo status.

## Failing Before

- **Command**: `hatch run pytest tests/unit/commands/test_update.py -q`
- **Result**: failed as expected before production edits (`6 failed, 15 passed`).
- **Observed failures**:
  - Existing subprocess call assertions expected captured stdout/stderr but `_execute_upgrade_command` still invoked `subprocess.run(..., check=False, timeout=300)`.
  - Successful pipx upgrade output was not replayed through SpecFact, so it could not be filtered deterministically.
  - Failed pipx upgrade stdout/stderr was not replayed, so child diagnostics were lost.
  - The fake pipx executable under a path containing spaces printed the warning block directly to captured stdout, proving the current command lets the upstream warning leak.

## Passing After

- **Command**: `hatch run pytest tests/unit/commands/test_update.py -q`
- **Result**: passed (`23 passed, 2 warnings` after main PR review follow-up).
- **Validated behavior**:
  - Successful pipx upgrade output suppresses the known spaced-home warning block.
  - Failed pipx upgrade output preserves child stdout and stderr diagnostics.
  - Timed-out upgrade output preserves partial child stdout and stderr diagnostics before the timeout summary.
  - Fake pipx executable under a temporary `Application Support` path exits successfully without leaking the warning block.

## Quality Gates

- **PR review follow-up**: addressed PR annotations by replaying `TimeoutExpired` partial stdout/stderr, decoding byte output safely, adding timeout regression coverage, and aligning proposal/design/spec wording with the implemented timeout and OS-error contract.
- **Main PR review follow-up**: addressed main PR annotations by capturing raw subprocess bytes in the upgrade execution path, decoding with replacement during replay, adding invalid-byte regression coverage, and expanding the `0.46.26` changelog entry with timeout replay behavior.
- **Follow-up release hygiene**: bumped canonical package version files to `0.46.27`, added a changelog entry for invalid-byte output hardening, and bumped the touched bundled `upgrade` module manifest version to `0.1.19`.
- **Format**: `hatch run format` passed; 624 files left unchanged.
- **OpenSpec**: `openspec validate upgrade-02-pipx-spaced-home-output --strict` passed.
- **Targeted tests**: `hatch run pytest tests/unit/commands/test_update.py -q` passed (`23 passed, 2 warnings` after main PR review follow-up).
- **Lint**: `hatch run lint` passed with 0 errors and 0 warnings.
- **Type check**: `hatch run type-check` passed with 0 errors and the existing repository warning baseline.
- **Contract test**: `hatch run contract-test` passed with cached results for no modified contract files.
- **Smart test**: `hatch run smart-test` was run twice. Both full-suite cache-building runs failed on the same unrelated timeout in `tests/unit/models/test_project.py::TestProjectBundle::test_save_to_directory_large_bundle_worker_reduction`; the isolated test passed with `hatch run pytest tests/unit/models/test_project.py::TestProjectBundle::test_save_to_directory_large_bundle_worker_reduction -q`.
- **SpecFact code review**: `SPECFACT_MODULES_ROOTS=/home/dom/git/nold-ai/specfact-cli-modules/packages hatch run specfact code review run --json --out .specfact/code-review.changed.json --scope changed` completed with 0 blocking findings.
- **Code review exception**: The JSON report contains 29 non-blocking, non-fixable basedpyright warnings for existing Typer/Rich unknown-member typing in `src/specfact_cli/modules/upgrade/src/commands.py`. This file-wide typed-dependency warning set pre-exists the change and is accepted here because the normal `hatch run type-check` gate passed with 0 errors and the warning baseline is unrelated to the pipx output filtering behavior.
- **Version source check**: `hatch run check-version-sources` passed after bumping canonical package version files to `0.46.26`.
- **PyPI ahead check**: `hatch run check-pypi-ahead` passed; local `0.46.26` is ahead of PyPI latest `0.46.25`.
- **Changelog**: added the `CHANGELOG.md` `0.46.26` entry for the pipx spaced-home upgrade-output fix.
- **Module verification**: bumped the touched bundled `upgrade` module manifest version to `0.1.16`; `hatch run verify-modules-signature-pr --version-check-base origin/dev` passed.
- **Internal wiki**: Added `wiki/sources/upgrade-02-pipx-spaced-home-output.md` in the sibling internal repo and ran `python3 scripts/wiki_rebuild_graph.py` from that repo root.
