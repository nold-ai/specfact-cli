# TDD Evidence: cli-val-05-ci-integration

## Failing-before

### 2026-06-13 00:00 Europe/Berlin

Command:

```bash
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py tests/unit/registry/test_dependency_resolver_properties.py -q
```

Result: failed as expected before implementation.

Summary:

- 27 focused tests collected.
- 18 passed.
- 9 failed.
- Expected workflow failures: missing `independent-static-analysis`, `package-runtime-matrix`, `runtime-smoke-macos`, `runtime-smoke-windows`, and `mutation-baseline`; `quality-gates` still named advisory; release fast path still uses `skip_tests_dev_to_main`.
- Expected resolver/property failure: `_collect_constraints` dedupes before trimming, producing duplicate constraints for whitespace variants.
- Test generator adjustment needed: generated module IDs must satisfy the installer namespace pattern requiring at least two characters after the slash.

## Passing-after

### 2026-06-13 00:00 Europe/Berlin

Command:

```bash
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py tests/unit/registry/test_dependency_resolver_properties.py -q
```

Result: passed after implementation.

Summary:

- 30 focused tests collected.
- 30 passed.
- Workflow policy coverage proves blocking `Quality Gates`, independent Semgrep/Bandit evidence, built-wheel package runtime matrix, staged macOS/Windows smoke, release fast-path safety, and advisory mutation baseline.
- Property coverage now probes dependency constraint dedupe, bundle dependency string/object parsing, registry id trimming/rejection, malformed manifests, version specifier satisfaction, and direct self-dependency recursion avoidance.

Command:

```bash
hatch run pytest tests/unit/registry/test_dependency_resolver.py tests/unit/registry/test_dependency_resolver_properties.py -q
```

Result: passed after implementation.

Summary:

- 16 resolver-focused tests collected.
- 16 passed.

Command:

```bash
openspec validate cli-val-05-ci-integration --strict
```

Result: passed.

Command:

```bash
hatch run python -c 'import pathlib, yaml; [yaml.safe_load(p.read_text(encoding="utf-8")) for p in pathlib.Path(".github/workflows").glob("*.yml")]; print("all workflow yaml ok")'
```

Result: passed.

Command:

```bash
hatch run lint
```

Result: passed with elevated execution after the sandbox blocked pylint process-pool system calls.

Command:

```bash
hatch run type-check
```

Result: passed with 0 errors and existing repository warnings.

Command:

```bash
hatch run bandit-scan
```

Result: passed after resolving/suppressing existing medium/high findings with local rationale.

Command:

```bash
semgrep scan --config tools/semgrep/sast.yml --json --output /private/tmp/specfact-semgrep.json
hatch run semgrep-sast-gate --results /private/tmp/specfact-semgrep.json --baseline tools/semgrep/sast-baseline.json
```

Result: passed with 39 current Semgrep OSS SAST findings accepted as initial baseline; new findings fail CI.

Command:

```bash
hatch run python scripts/check_doc_frontmatter.py
npx --yes markdownlint-cli --config .markdownlint.json docs/agent-rules/50-quality-gates-and-review.md docs/modules/code-review.md
```

Result: passed. `npx` required elevated network access because the sandbox could not resolve `registry.npmjs.org`.

## PR #610 Codex review remediation — Semgrep config hardening

Command:

```bash
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py::test_semgrep_sast_hatch_script_uses_dedicated_checked_in_sast_config -q
```

Result before production edit: failed because `semgrep-sast` used `semgrep scan --config auto {args}`.

Fix: changed `semgrep-sast` and the baseline command metadata to use the checked-in `tools/semgrep/sast.yml` profile, so the SAST rule selection is independent of auto config creation and does not inherit `SEMGREP_SEND_METRICS=off`.

Follow-up after PR #610 CI: `--config tools/semgrep` was too broad and ran the repository's custom development rule directory (74 custom rules, 8,967 findings). The final remediation splits a dedicated checked-in `tools/semgrep/sast.yml` profile containing only the security rules.

Command:

```bash
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py::test_semgrep_sast_hatch_script_uses_dedicated_checked_in_sast_config tests/integration/test_bundle_install.py::test_installing_spec_bundle_skips_dependency_when_already_present -q
hatch -e py311 run pytest tests/integration/test_bundle_install.py::test_installing_spec_bundle_skips_dependency_when_already_present -q
```

Result: passed. The Python 3.11 compatibility failure from PR #610 was addressed by routing marketplace install success output through Typer's output path instead of Rich console printing for those plain success lines.

## Direct-to-main module signature hardening follow-up

Command:

```bash
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py -q
```

Result: passed after implementation.

Summary:

- 24 workflow policy tests collected.
- 24 passed.
- Added regression coverage proving `pr-orchestrator.yml` uses `VERIFY_MODULES_STRICT` for pull requests targeting `main` and pushes to `main`, while keeping `VERIFY_MODULES_PR` for development PRs and `VERIFY_MODULES_PUSH_ORCHESTRATOR` for `dev` pushes.

Command:

```bash
openspec validate cli-val-05-ci-integration --strict
```

Result: passed.

Command:

```bash
hatch run python - <<'PY'
from pathlib import Path
import yaml
for path in [Path('.github/workflows/pr-orchestrator.yml'), Path('.github/workflows/sign-modules.yml')]:
    with path.open(encoding='utf-8') as f:
        yaml.safe_load(f)
    print(f'OK {path}')
PY
```

Result: passed.

Command:

```bash
hatch run python scripts/check_doc_frontmatter.py
/opt/homebrew/bin/markdownlint --config .markdownlint.json docs/reference/module-security.md docs/guides/module-signing-and-key-rotation.md docs/agent-rules/50-quality-gates-and-review.md
```

Result: passed. The local `/opt/homebrew/bin/markdownlint` binary was used instead of network-backed `npx`.

## GitHub signing remediation follow-up

Command:

```bash
hatch run pytest tests/unit/workflows/test_sign_modules_on_approval.py tests/unit/workflows/test_trustworthy_green_checks.py -q
```

Result: passed after implementation.

Summary:

- 28 workflow policy tests collected.
- 28 passed.
- Added regression coverage proving signing remediation commits do not include `[skip ci]`, so approval-time/manual signing and auto-sign PR commits can rerun the checks that verify the signed manifests.

Command:

```bash
hatch run python - <<'PY'
from pathlib import Path
import yaml
for path in [Path('.github/workflows/pr-orchestrator.yml'), Path('.github/workflows/sign-modules.yml'), Path('.github/workflows/sign-modules-on-approval.yml'), Path('.github/workflows/publish-modules.yml')]:
    with path.open(encoding='utf-8') as f:
        yaml.safe_load(f)
    print(f'OK {path}')
PY
```

Result: passed.

Command:

```bash
openspec validate cli-val-05-ci-integration --strict
```

Result: passed.

Note: `hatch run lint-workflows` could not run fully in this local environment because `actionlint` is not installed and the machine has no `go` binary available to install the pinned `actionlint@v1.7.11`. A sandboxed Semgrep invocation failed before analysis while initializing its local X509 trust store (`ca-certs: empty trust anchors`). The earlier auto-config baseline command was superseded by the PR #610 remediation above, which uses a dedicated checked-in SAST profile.

## PR #610 CodeRabbit and macOS CI remediation follow-up

CodeRabbit annotations on 2026-06-13 requested OpenSpec traceability fixes:

- Add `cli-validation-ci-gates` to the proposal impact map.
- Make the tasks checklist explicitly cover circular-dependency/self-reference and upgrade/version-detection regression cases.

Additional PR #610 CI failures showed that the local macOS default Bash 3.2 cannot run the pre-commit module verifier's Bash 4-only `mapfile` usage, and the bundle install test could still inherit stale Rich console state after runtime smoke work in the Python 3.12 full-suite job.

Commands:

```bash
hatch run pytest tests/integration/test_bundle_install.py tests/unit/scripts/test_pre_commit_verify_modules.py tests/unit/workflows/test_trustworthy_green_checks.py::test_semgrep_sast_hatch_script_uses_dedicated_checked_in_sast_config -q
hatch -e py311 run pytest tests/integration/test_bundle_install.py::test_installing_spec_bundle_skips_dependency_when_already_present -q
env SEMGREP_ENABLE_VERSION_CHECK=0 SEMGREP_SEND_METRICS=off semgrep scan --config tools/semgrep/sast.yml --json --output /private/tmp/specfact-sast-semgrep.json .
hatch run semgrep-sast-gate --results /private/tmp/specfact-sast-semgrep.json --baseline tools/semgrep/sast-baseline.json
hatch run ruff check src/specfact_cli/modules/module_registry/src/commands.py tests/integration/test_bundle_install.py tests/unit/workflows/test_trustworthy_green_checks.py tests/unit/scripts/test_pre_commit_verify_modules.py
hatch run pylint src/specfact_cli/modules/module_registry/src/commands.py tests/integration/test_bundle_install.py tests/unit/workflows/test_trustworthy_green_checks.py tests/unit/scripts/test_pre_commit_verify_modules.py
openspec validate cli-val-05-ci-integration --strict
git diff --check
```

Result: passed. The focused pytest run collected 24 tests: 23 passed and 1 skipped (`specfact_codebase.validate` not installed locally). Python 3.11 compatibility passed for the formerly failing bundle install test. Semgrep SAST scanned 281 Python targets with 6 security rules and found 0 findings; the SAST baseline gate reported 0 current and 0 accepted baseline findings. Ruff passed, pylint rated the modified Python files 10.00/10, OpenSpec strict validation passed, and `git diff --check` passed.
