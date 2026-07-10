# TDD Evidence: cli-val-05-ci-integration

## Documentation-accountability failing-before

### 2026-07-10 Europe/Berlin

Command:

```bash
hatch run pytest tests/unit/docs/test_llms_overview_freshness.py tests/unit/docs/test_documentation_accountability.py -q
```

Result: failed as expected before implementation.

Summary:

- `docs/reference/commands.generated.json` has no `specfact requirements`
  record owned by `nold-ai/specfact-requirements`.
- `scripts/check-documentation-accountability.py` does not exist.
- The always-run local pre-commit path and `docs-review.yml` do not invoke a
  documentation-accountability command.
- Existing command-overview freshness coverage skipped in this worktree because
  its modules-repository discovery does not find the documented sibling
  checkout, demonstrating that it cannot be relied on as a fail-closed proof.

## Documentation-accountability passing-after

### 2026-07-10 Europe/Berlin

Command:

```bash
SPECFACT_MODULES_REPO=/Users/dom/git/nold-ai/specfact-cli-modules hatch run pytest tests/unit/docs/test_llms_overview_freshness.py tests/unit/docs/test_documentation_accountability.py -q
SPECFACT_MODULES_REPO=/Users/dom/git/nold-ai/specfact-cli-modules hatch run check-documentation-accountability
```

Result: passed after implementation.

Summary:

- 10 documentation-accountability tests passed.
- The generated command artifacts now include `specfact requirements` owned by
  `nold-ai/specfact-requirements`.
- The accountability contract derives the seven official packages from the
  modules manifests and marketplace registry, rejects disagreement or a missing
  source, and confirms every designated core catalogue and ownership statement.
- The same fail-closed command is invoked by the always-run pre-commit path and
  the blocking Docs Review PR workflow.

## Documentation-accountability final quality evidence

### 2026-07-10 Europe/Berlin

Commands:

```bash
SPECFACT_MODULES_REPO=/Users/dom/git/nold-ai/specfact-cli-modules hatch run pytest \
  tests/unit/docs/test_llms_overview_freshness.py \
  tests/unit/docs/test_documentation_accountability.py \
  tests/unit/registry/test_category_groups.py -q
SPECFACT_MODULES_REPO=/Users/dom/git/nold-ai/specfact-cli-modules hatch run docs-validate
hatch run type-check
hatch run lint
hatch run contract-test
hatch run smart-test
hatch run bandit-scan
```

Result: passed after remediation.

Summary:

- 17 focused tests passed. They prove catalogue omissions, missing generated
  command records, and contradictory ownership claims fail for official module
  roots, in addition to requirements inventory and missing-source coverage.
- The full suite passed: 2,832 tests passed, 10 skipped, with 64% coverage
  against the configured 50% fail-under gate.
- The first full run exposed a stale category-group expectation that omitted
  the already shipped `requirements` root; the test was corrected and the full
  suite was rerun successfully.
- Type checking completed with 0 errors (existing repository warnings remain);
  full lint, contract tests, workflow/YAML validation, Bandit, and strict
  OpenSpec validation passed.

## Clean-code review evidence and explicit exceptions

### 2026-07-10 Europe/Berlin

Command:

```bash
bash scripts/pre-commit-quality-checks.sh
```

Result: passed. The staged hook ran the same fail-closed documentation gate,
command checks, lint, workflow checks, and code-review wrapper used before a
commit.

- The review report has **0 errors** and `PASS_WITH_ADVISORY`.
- All new-checker and changed-test findings were remediated: complexity,
  nesting, output handling, type narrowing, design-by-contract coverage, and
  duplicate test shape.
- 13 residual warnings are pre-existing static-analysis limitations in the
  two legacy command-artifact scripts (`check-command-contract.py` and
  `generate-command-overview.py`) plus Typer's dynamic `commands` attribute in
  the existing category-group tests. They are non-blocking, produce no
  type-check errors, and are outside this accountability scope; the report is
  retained at `.specfact/code-review.json` for follow-up cleanup.

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

## PR #610 Python 3.11 full-suite stdout capture follow-up

The Python 3.11 full-suite job still exposed a closed Click stdout capture in
`test_installing_spec_bundle_skips_dependency_when_already_present`. CI logs
showed the install command reached the expected behavior and emitted the expected
messages, but `CliRunner.invoke()` failed while reading its closed internal
stdout buffer. The fix keeps direct module-registry invocations resilient to
stale loaded consoles and moves the dependency-skip behavior regression onto the
install implementation with pytest `capsys`, avoiding an unrelated Click capture
layer for this behavior-only assertion. Follow-up CodeRabbit annotations were
also applied by decorating the public module-registry callback with `@beartype`
and using pytest `monkeypatch` to roll back the temporary stale-console test
state.

Commands:

```bash
hatch -e py311 run pytest tests/integration/test_bundle_install.py -q
hatch run pytest tests/integration/test_bundle_install.py -q
hatch run ruff check src/specfact_cli/modules/module_registry/src/commands.py tests/integration/test_bundle_install.py
hatch run pylint --jobs=1 src/specfact_cli/modules/module_registry/src/commands.py tests/integration/test_bundle_install.py
hatch run check-version-sources
hatch run verify-modules-signature-pr --version-check-base origin/dev
```

Result: passed. The Python 3.11 and Python 3.12 bundle install files each
collected 6 tests: 5 passed and 1 skipped (`specfact_codebase.validate` not
installed locally). Ruff passed, pylint rated the touched Python files 10.00/10,
version sources are synchronized at 0.47.11, and PR-style module signature
verification passed with the module-registry manifest signed by automation at
0.1.31.
