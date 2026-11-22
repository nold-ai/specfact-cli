# Core Python SAST evidence

Local evidence collected on 22 November 2026 (Europe/Berlin) from core `dev` at `afae348be2989350ac7c56e5a0e1c7c2c8b283a2`.

## RED

- `pytest -o addopts='' -q tests/unit/scripts/test_core_sast_gate.py` reported 18 failures before the standalone command existed.
- After a first implementation scanned all tracked Python files, the explicit legacy-scope fixture failed because the command included top-level and nested test directories. The existing Semgrep scan confirmed that the current checkout's unscanned tracked Python paths were all in `tests/` directories.

## GREEN

- `pytest -o addopts='' -q tests/unit/scripts/test_core_sast_gate.py tests/unit/scripts/test_semgrep_sast_gate.py` passed 23 tests on Python 3.12.13. Fixtures cover all six rule IDs, accepted baseline compatibility, excluded paths, omitted input, invalid Python, and malformed baseline evidence.
- `python3.12 scripts/core_sast_gate.py --root . --baseline tools/semgrep/sast-baseline.json --output /tmp/core-sast.json` scanned all 305 eligible tracked paths with zero findings and zero diagnostics. The path set matches locked Semgrep 1.182.1 after removing the newly added untracked scanner script from the Semgrep result. Both scans reported zero findings. The replacement lists all 430 tracked test-directory paths excluded under the existing scope.
- Ruff format and lint, basedpyright on the two Python files, and strict OpenSpec validation passed.

## Independent workflow candidate

- Before wiring the replacement, four tests failed because the workflow had no Python SAST step and still called Semgrep.
- After wiring it, the workflow's shell command returned 0 for clean inputs, 1 for a new finding, and 2 for incomplete evidence. All three outcomes wrote the expected JSON. The job keeps the existing Bandit command and uploads available evidence on failure.
- The scanner and workflow test set passed all 84 tests. Actionlint, Ruff and strict OpenSpec validation passed.

## Core consumer and frozen-graph candidate

- The frozen-graph test failed on protected `dev` because the core, Hatch, and scanning declarations carried Semgrep. The combined lock and export cleared that test. All three unchanged strict audit commands passed with the active exception register empty. The lock retains the exact Socket-reviewed parser wheel and upgrades the optional telemetry family to 1.45.2.
- Four OpenAPI cases failed before the source-based converter was connected. The suite then passed with assertions on the selected operation, literal request and response, status code and legacy policy warning.
- The async command was absent before implementation, and the two Repro integration tests failed before it was wired. The combined tests passed all 38 cases, including each of the 13 legacy rule IDs, safe controls, missing source, custom policy migration and unsupported fix handling.
- The feature fixture failed before local pattern evidence was produced. It then observed model, route, authentication, CRUD and quality outcomes from the real brownfield analyzer.
- The installed wheel exposed a wrong Spec-Kit workflow template lookup. The packaged-layout regression failed before the repair. After locating the bundled template before the source checkout fallback, all seven converter tests and the rebuilt installed-wheel workflow generation passed.
- The built Python 3.12 wheel and its frozen environment contained no Semgrep resources or runtime dependency. Installed smoke covered feature analysis, async findings and OpenAPI examples. The unchanged Bandit command, dependency trust, reproducible delivery, Ruff, actionlint and strict OpenSpec validation passed locally.

Hosted verification and the jointly signed module acceptance remain pending.

### Frozen wheel parity with the protected base verifier

The first signed candidate passed the local projected export. The hosted
[Requirements producer](https://github.com/nold-ai/specfact-cli/actions/runs/45078670999/job/137381550650)
rejected it because the protected base verifier compares the committed export to
stock uv output. The fixed graph uses the official PyPI registry record,
disables source builds for pycparser, and excludes its unapproved source archive
during the frozen refresh. The same protected base verifier and bootstrap trust
check passed against the regenerated lock and unmodified pip export. All 60
focused dependency, trust, and reproducibility tests passed.

### Protected before-fix proof

The signed tests-only commit `01f4685b` retained the implementation on `dev` and
all owner-approved test bytes. Its original hosted Requirements run stopped
before pytest on the expired base dependency trust record. The replacement
proof job uses the exact signed tests-only source and installs an independently
pinned, audited hash graph. It derives the existing native plan, runs the 14
mapped pytest selectors and binds their results with the existing provenance
verifier. All 14 failed locally on the exact pre-fix tree and its protected base
verifier accepted the bound report. The existing producer, fresh execution and
final verdict verify current-run evidence by artifact ID. Ordinary gates remain
active. See [organization policy PR #7](https://github.com/nold-ai/.github/pull/7).

A focused scanner case also showed that an unrelated function or class import
could replace a module alias in the original scan. Lexical import scope now
preserves the expected findings. The new regression lives separately from all
mapped test files, leaving the approved plan and source bindings intact.
