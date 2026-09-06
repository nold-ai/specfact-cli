# TDD Evidence

## Failing before implementation

2026-09-06T23:50:00Z

`hatch run pytest -q tests/unit/registry/test_dependency_resolver.py tests/unit/registry/test_module_installer.py -k 'non_index or named_pep508 or excludes_discovered or verifies_artifact_before'`

Result: **failed as expected** (6 failed, 1 passed). Unsafe requirement forms reached the pip mock, discovered project metadata reached resolution, and dependency processing ran before integrity rejection.

## Passing after implementation

2026-09-06T23:51:00Z

`hatch run pytest -q tests/unit/registry/test_dependency_resolver.py tests/unit/registry/test_module_installer.py -k 'non_index or named_pep508 or excludes_discovered or verifies_artifact_before'`

Result: **passed** (7 passed, 45 deselected).

`hatch run pytest -q tests/unit/registry/test_dependency_resolver.py tests/unit/registry/test_module_installer.py tests/unit/registry/test_dependency_resolver_properties.py tests/unit/specfact_cli/registry/test_dependency_resolver_pip_free.py`

Result: **passed** (66 passed).

## Quality gates

- `openspec validate fix-untrusted-module-pip-install --strict`: passed.
- `hatch run format`, `hatch run lint`, and `hatch run type-check`: passed; type check reported no errors.
- `hatch run contract-test`: passed from the cached contract result.
- `hatch run security-audit`: passed with no unreviewed vulnerabilities.
- `hatch run semgrep-sast --json-output=/tmp/specfact-semgrep.json` and the baseline gate: passed with zero findings.
- `hatch run bandit-scan`: passed with no medium/high findings.
- `hatch run verify-modules-signature`: passed for all four manifests.
- Frozen-delivery checks, `uv lock --check`, and the authoritative BasedPyright JSON run passed.
- `hatch run smart-test`: full-suite execution reached 3,078 collected tests but failed on pre-existing missing external module imports; its initial stale-lock/version assertion was corrected and passes in the focused rerun.
- `hatch run specfact code review run --scope full --json --out .specfact/code-review.json`: produced zero findings but returned UNKNOWN because all OCI analyzer capsules reported `verified cache entry is missing`. Independent Ruff, BasedPyright, Semgrep, Bandit, contract, and focused test gates passed; this environment limitation remains explicitly recorded rather than misrepresented as PASS.
