# TDD evidence — audit-01-reproducible-delivery

All times are Europe/Berlin (2026-07-23 to 2026-07-25).

## Audit metadata

- **Impacted files:** frozen setup action; PR, docs, and contract workflows;
  dependency-trust, license, refresh, and SBOM scripts; type configuration;
  pre-commit; reviewed lock metadata; and their focused tests.
- **Breaking-change scan:** no public CLI, module, or adapter interface changed.
  Published dependency metadata relaxes `pycparser` from an exact pin to
  `>=2.22,!=3.0`; the committed lock retains `2.22` and the trust gate blocks
  the alerted `3.0` family.
- **Failing artifacts:** terminal output is captured in this evidence under
  “Security remediation evidence” and “Review remediation evidence”; focused
  test files are the durable reproductions.
- **Passing artifacts:** GitHub Actions run
  [`30132168259`](https://github.com/nold-ai/specfact-cli/actions/runs/30132168259)
  retains the `type-check-results` BasedPyright JSON artifact; CI also uploads frozen
  dependency and SBOM evidence.

## Failing-first evidence

Before the frozen-delivery files and workflow changes were added, this focused policy
suite was run:

```text
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py \
  tests/unit/scripts/test_reproducible_delivery.py -q

36 collected; 31 passed; 5 failed
```

The failures established the missing controls: no `ci/module-fixture.lock.json`, no
committed `uv.lock`, no 3.11–3.13 runtime matrix, a competing `pyrightconfig.json`,
and no frozen-delivery verifier. The tests were added before the corresponding CI,
lock, fixture, and verifier implementation.

After extending the policy to the standalone contract and documentation command
validation workflows, the focused workflow suite also failed as expected:

```text
36 collected; 34 passed; 2 failed
```

Both failures identified a branch-selected companion-module checkout and dynamic pip/
Hatch installation. Those workflows now use the same reviewed fixture lock and frozen
setup action as the blocking orchestrator jobs.

## Passing evidence

```text
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py \
  tests/unit/scripts/test_reproducible_delivery.py \
  tests/unit/specfact_cli/registry/test_signing_artifacts.py -q
84 passed, 1 sandbox cache warning

hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py -q
36 passed, 1 sandbox cache warning

uv run --locked pytest tests/unit/docs/ tests/unit/scripts/test_doc_frontmatter/ \
  tests/integration/scripts/test_doc_frontmatter/ -q
109 passed, 1 skipped, 3 warnings

hatch run lint-workflows
exit 0

openspec validate audit-01-reproducible-delivery --strict
Change 'audit-01-reproducible-delivery' is valid

hatch run python scripts/check_reproducible_delivery.py
reproducible delivery inputs are valid

uv run --locked basedpyright --project pyproject.toml --outputjson
filesAnalyzed: 602; errorCount: 0; warningCount: 1626; informationCount: 0

hatch run license-check
PASS — overall exit code: 0

hatch run security-audit
Security audit passed. No high-severity vulnerabilities found

hatch run bandit-scan
No issues identified (0 medium/high findings)

hatch run specfact code review run --json --out .specfact/code-review.json
Review completed with no findings; findings: 0

python tools/smart_test_coverage.py run --level full
2882 passed, 9 skipped, 2 warnings; coverage 64%
```

The BasedPyright warnings are the existing diagnostic baseline. The sole authority is
now the `[tool.basedpyright]` section in `pyproject.toml`; the former competing
`pyrightconfig.json` was removed. The JSON report is the CI artifact and was retained
locally at `/tmp/specfact-basedpyright.json` for this verification run.

## Built-wheel evidence

The original local wheel proof is superseded by the security remediation below: it
used `cyclonedx-py`, which is no longer an accepted delivery dependency. The current
blocking job renders each SBOM from its local `pip inspect` report with
`scripts/render_locked_sbom.py`, then compares the deterministic SPDX 2.3 documents.
The 3.11, 3.12, and 3.13 built-wheel matrix remains merge-blocking; hosted proof is
pending the updated pull-request run.

`ruff format --check .` currently reports formatting violations in unrelated tracked
documentation/archive files. The four Python files introduced by this change passed
both scoped `ruff format --check` and `ruff check`; no global reformat was applied.

The final focused policy command used an isolated temporary uv cache because this
sandbox cannot open the caller's existing `~/.cache/uv` Git metadata. The same
checker succeeds with that writable cache; CI uses its own writable cache.

## Security remediation evidence — 2026-07-24

Socket Security identified `cyclonedx-bom@7.3.1`, newly added by this change for
SBOM rendering, as a potential-malware AI signal. The alert was not waived, ignored,
or resolved. The package was removed rather than accepted as a delivery dependency.

The reproducible-delivery OpenSpec delta was updated and validated before the
replacement tests were added:

```text
openspec validate audit-01-reproducible-delivery --strict
Change 'audit-01-reproducible-delivery' is valid

hatch run pytest tests/unit/scripts/test_reproducible_delivery.py \
  tests/unit/workflows/test_trustworthy_green_checks.py -q
41 collected; 38 passed; 3 failed
```

Two failures proved the missing renderer and the prohibited `cyclonedx-py` workflow
call. The remaining failure was the pre-existing sandbox restriction on the shared uv
cache while the test checked the stale export. No production replacement had been
applied at that point.

After removal and frozen-input refresh:

```text
hatch run refresh-frozen-delivery
Resolved 188 packages
Removed cyclonedx-bom v7.3.1 and its generator-only transitive dependencies
reproducible delivery inputs are valid

hatch run pytest tests/unit/scripts/test_reproducible_delivery.py \
  tests/unit/workflows/test_trustworthy_green_checks.py -q
41 passed

hatch run python tools/smart_test_coverage.py run --level full
2884 passed, 9 skipped, 2 warnings; coverage 64%
```

The replacement `scripts/render_locked_sbom.py` uses only the Python standard library
to render deterministic SPDX 2.3 JSON from each local `pip inspect` report. Existing
Socket warnings for `dill`, `nodejs-wheel-binaries`, and `pycparser` remain unwaived;
they are pre-existing dependency paths and require separate review before being
accepted or changed.

`cyclonedx-python-lib` remains in the frozen export only because the pre-existing
`pip-audit` development tool depends on it; delivery CI neither invokes it nor uses it
to render SBOM evidence.

## CI regression evidence — 2026-07-24

GitHub Actions run `30048392658` failed the Package Runtime Matrix pipx launcher
because pipx delegated to uv with `--no-deps` already present, while the workflow
also supplied `--pip-args="--no-deps"`. uv rejected the duplicate flag before the
wheel launcher could be exercised.

The new workflow-policy test was added before the workflow edit:

```text
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py -q
38 collected; 37 passed; 1 failed
```

After removing only the redundant pipx argument, while retaining the subsequent
hash-verified frozen dependency install:

```text
hatch run pytest tests/unit/scripts/test_reproducible_delivery.py \
  tests/unit/workflows/test_trustworthy_green_checks.py -q
42 passed

hatch run lint-workflows
exit 0

hatch run python scripts/check_reproducible_delivery.py
reproducible delivery inputs are valid
```

## Known environmental limitation

The sibling internal wiki worktree was already dirty before this change (`wiki/graph.md`
and unrelated source pages). The new `wiki/sources/audit-01-reproducible-delivery.md`
was added without overwriting those changes, but `wiki_rebuild_graph.py` is deferred
until the existing graph edits are reconciled.

## Pipx runtime repair — 2026-07-25

GitHub Actions run `30132168259` failed all three pipx matrix jobs (Python 3.11,
3.12, and 3.13) with `Pipx Internal Error: cannot find package 'azure-identity'
metadata.` The prior sequence installed the wheel with `--no-deps` and attempted to
add the frozen dependencies only afterwards; pipx inspects installed package metadata
before that second command can run.

The focused policy test was updated before the workflow:

```text
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py -q
44 collected; 43 passed; 1 failed
```

The pipx lane now exports a temporary PEP 751 `pylock.toml` from the committed
`uv.lock` with `--no-emit-project`, then supplies it to `pipx install --lock` with
the built wheel. Pipx installs the locked dependencies first, adds the wheel without
dependency resolution, and runs `pip check` before exposing the launchers.

```text
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py -q
44 passed

hatch run lint-workflows
exit 0

uv export --locked --format pylock.toml --no-emit-project \
  --output-file /private/tmp/pylock.specfact-deps.toml
Resolved 182 packages

pipx 1.16.2 install --lock <temporary pylock> <built wheel>
pip check: exit 0
/private/tmp/.../specfact --help: exit 0
```

The local runtime exercise used Python 3.13 on macOS. The updated PR matrix remains
the required hosted proof for Python 3.11, 3.12, and 3.13.

## Dependabot frozen-lock repair — 2026-07-25

Dependabot PR [#655](https://github.com/nold-ai/specfact-cli/pull/655) updates the
development-only build backend from `hatchling==1.28.0` to `1.31.0` and PyCG from
`0.0.7` to `0.0.8`. Its `Verify Module Signatures`, `Docs Review`, and `Contract
Validation` workflows all failed before their task-specific checks because their
shared setup ran `uv sync --locked --all-extras` against a lockfile that still
described the old pins.

The policy test was updated before the dependency metadata and frozen artifacts:

```text
hatch run pytest tests/unit/scripts/test_reproducible_delivery.py -q
2 failed, 6 passed
```

The two failures required the reviewed Hatchling and PyCG versions across every
development tool group. After changing only those declared pins and regenerating the
committed lock and CI export:

```text
hatch run refresh-frozen-delivery
Resolved 184 packages
Updated hatchling v1.28.0 -> v1.31.0
Updated pycg v0.0.7 -> v0.0.8
reproducible delivery inputs are valid

hatch run pytest tests/unit/scripts/test_reproducible_delivery.py -q
8 passed

uv lock --check
Resolved 184 packages in 3ms

uv sync --locked --all-extras
Installed hatchling==1.31.0
Installed pycg==0.0.8

hatch run python scripts/check_reproducible_delivery.py
reproducible delivery inputs are valid

hatch run python scripts/check_dependency_trust_exceptions.py
Dependency trust register is valid

hatch run license-check
PASS — overall exit code: 0
```

The remediation is applied directly to `dev` as requested; it does not merge or
modify PR #655's Dependabot branch or `main`. No release version or changelog entry
is needed because this is a development-only frozen-input repair.

## Review-comment remediation — 2026-07-25

The remaining PR #652 review threads required a durable BasedPyright artifact
reference, corrected evidence date range and documentation line length, a real
license-gate specification purpose, and complete exclusion of the alerted
`pycparser` 3.0 release family.

The package-metadata regression was changed before the requirement constraints:

```text
hatch run pytest \
  tests/unit/packaging/test_core_package_includes.py::test_core_dependency_bounds_allow_patched_click_and_typer_releases -q
1 failed: pyproject.toml still declared pycparser>=2.22,!=3.0
```

After changing both published metadata surfaces to `!=3.0.*` and regenerating the
lock without changing the resolved `pycparser==2.22` artifact:

```text
uv lock
Resolved 182 packages

hatch run pytest \
  tests/unit/packaging/test_core_package_includes.py::test_core_dependency_bounds_allow_patched_click_and_typer_releases -q
1 passed
```

The regression proves PEP 440 exclusion of `3.0`, `3.0.1`, and `3.0.post1`, while
retaining `2.22`. Because the published dependency metadata changed, the required
release gate advanced the four synchronized version sources to `0.53.4` and added
the matching changelog entry. The full review-fix validation is recorded in
[`CHANGE_VALIDATION.md`](./CHANGE_VALIDATION.md).

The follow-up CodeRabbit review added four test/documentation-hardening requests.
Three were valid and were implemented: the validation report now uses the
repository-managed `hatch run openspec` command; version checks parse literal
`__version__` assignments and the literal `setup()` keyword values; and the
dependency checks preserve every declaration, require the pyproject and setup
lists to match, and reject duplicate `pycparser` declarations. The requested
evidence-date rollback was not applied because the recorded verification occurred
on 2026-07-25. This is test/documentation hardening only; it does not change
runtime behavior or published metadata.

```text
hatch run pytest tests/unit/packaging/test_core_package_includes.py -q
9 passed, 1 sandbox cache warning

hatch run openspec validate audit-01-reproducible-delivery --strict
Change 'audit-01-reproducible-delivery' is valid

hatch run format && hatch run type-check && hatch run lint && hatch run contract-test
format: 891 files formatted; type-check: 0 errors, 1642 existing warnings;
lint: 0 errors, 0 warnings; contract scenarios: 21 passed

hatch run python scripts/pre_commit_code_review.py \
  tests/unit/packaging/test_core_package_includes.py \
  openspec/changes/audit-01-reproducible-delivery/CHANGE_VALIDATION.md
Code review summary: 0 finding(s); overall_verdict='PASS'
```

## Review remediation evidence — 2026-07-24

Codex and CodeRabbit review feedback was read through the PR review API. The
actionable CI/security items were implemented before this evidence was recorded:
unique package-runtime artifact names, frozen pipx installation, portable
Windows virtualenv PATH, configured Python before fixture parsing, exact
per-package artifact binding, canonical blocked-release checks, strict type
checking for the pre-install trust boundary, exact mixed-license exception
versions, and reviewed Semgrep minimum version enforcement.

At the start of review, `uv.lock` pinned `semgrep==1.170.1`, not `1.70.1`.
The later locked-advisory remediation below updates it to `1.171.0` and raises
the checked-in floor accordingly. Pre-commit validates that reviewed floor
locally; it does not make an unreviewed moving “latest” lookup.

The review also identified repository-wide BasedPyright strict-mode debt. The
security-critical pre-install trust script now runs under per-path strict
diagnostics. Other delivery scripts remain in the pre-existing visible JSON
baseline; converting all existing warnings to strict errors is a separately
scoped migration, not a safe incidental change to this security repair.

Failing-first regression evidence:

```text
94 collected; 7 failed
```

The failures exercised the blocked `pycparser` release-family spelling,
Semgrep floor downgrade, SBOM PURL omission, duplicate runtime artifacts,
Windows virtualenv path, missing `scripts/` type scope, and non-frozen
pre-commit invocation. They were added before the corresponding implementation.

Passing evidence:

```text
Python 3.12 focused policy suite
97 passed, 1 sandbox cache warning

bash tools/run_basedpyright.sh --project pyproject.toml --outputjson
filesAnalyzed: 635; errorCount: 0; warningCount: 1638

uv lock --check
Resolved 182 packages in 1ms

python scripts/check_dependency_trust_exceptions.py
Dependency trust register is valid
```

The sandbox cannot write the worktree's Hatch metadata or default uv cache.
Focused tests therefore used the existing frozen Hatch Python with an isolated
`UV_CACHE_DIR`; CI uses its own writable cache and performs the same frozen
commands.

## Locked advisory audit remediation — 2026-07-24

The prior CVE gate audited the active environment after frozen synchronization
and treated CVSS below 7.0 as non-blocking. A direct audit of the committed
`requirements/ci/locked.txt` exposed six advisories in three packages:

```text
click==8.1.8       PYSEC-2026-2132 / CVE-2026-7246      fixed: 8.3.3
mcp==1.23.3        PYSEC-2026-3481, -3482, -3483        fixed: 1.28.1
setuptools==81.0.0 PYSEC-2026-3447 / CVE-2026-59890     fixed: 83.0.0
```

Failing-first tests changed the security gate contract to audit the frozen
requirements file in strict mode and fail every advisory, not only high-CVSS
records. Before implementation, the focused suite reported five expected
failures for the old runner, old version caps, and old Semgrep floor.

After updating compatible direct constraints and regenerating the frozen inputs:

```text
uv lock --upgrade-package semgrep
Updated click v8.1.8 -> v8.4.2
Updated semgrep v1.170.1 -> v1.171.0
Updated setuptools v81.0.0 -> v83.0.0
Updated typer v0.23.1 -> v0.27.0

pytest tests/unit/scripts/test_security_audit_gate.py \
  tests/unit/packaging/test_core_package_includes.py \
  tests/unit/scripts/test_dependency_trust_review.py \
  tests/unit/workflows/test_trustworthy_green_checks.py -q
74 passed, 1 sandbox cache warning
```

Semgrep `1.171.0` is the newest available release and declares
`mcp==1.23.3` exactly; this prevents resolution to the MCP `1.28.1` advisory
fix. `ci/vulnerability-audit-exceptions.json` therefore records only the three
exact MCP advisory IDs, their non-reachable server-only scope, mitigation, and
2026-08-07 expiry. The gate rejects an unknown, mismatched, or expired record.

```text
python scripts/security_audit_gate.py
WAIVED: mcp==1.23.3 PYSEC-2026-3481, -3482, -3483
Security audit passed. No unreviewed vulnerabilities found in the frozen requirements.
```

The new `frozen-cve-audit` pre-commit hook and blocking CI job invoke this
same requirements-file gate. Dependabot is configured to propose weekly
patch/minor Python dependency updates; updates remain reviewable and must pass
the frozen-delivery and advisory gates before merge.

## Dependency-warning remediation — 2026-07-24

The OpenSpec delta was extended before implementation to cover replacement of the
unofficial Node wheel, removal of Pylint/Dill, reviewed Pycparser provenance, and a
conservative mixed-license classifier. The new tests were added before production or
dependency edits and failed as expected:

```text
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py \
  tests/unit/scripts/test_check_license_compliance.py \
  tests/unit/scripts/test_dependency_trust_review.py -q

66 collected; 61 passed; 5 failed
```

The failures proved the absent SHA-pinned Node/npm type-runner path, present
BasedPyright/Pylint/Dill Python dependencies, missing Pycparser review record, and
the license gate's incorrect GPL-substring diagnosis for mixed Docutils metadata.

The expiry and exact-version checks were also introduced with failing tests: an
unimplemented trust-register checker raised `FileNotFoundError`, and a stale
Docutils `0.22` exception incorrectly accepted installed `0.23` metadata.

After the implementation and frozen-lock refresh:

```text
UV_CACHE_DIR=/private/tmp/specfact-uv-cache uv lock --check
Resolved 182 packages in 1ms

hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py \
  tests/unit/scripts/test_reproducible_delivery.py \
  tests/unit/scripts/test_run_changed_lint.py \
  tests/unit/scripts/test_dependency_trust_review.py \
  tests/unit/scripts/test_check_license_compliance.py -q
75 passed, 1 sandbox cache warning

ruff format --check .
651 files already formatted

ruff check .
All checks passed!

hatch run type-check
0 errors, 1626 existing warnings

python scripts/check_dependency_trust_exceptions.py
Dependency trust register is valid

/private/tmp/specfact-locked-license-venv/bin/python scripts/check_license_compliance.py
PASS — overall exit code: 0
```

The license proof used a newly created Python 3.12 environment installed solely
from `requirements/ci/locked.txt` with `--require-hashes`; it did not reuse the
pre-existing Hatch environment, which still contained removed Pylint/Dill packages.

The local `pip-audit` advisory query was not run because the execution environment
rejected sending the repository's complete locked dependency inventory to an external
service. The existing blocking GitHub Actions `security-audit` job remains the
authoritative remote proof and must pass on the pushed commit.

The frozen Hatch lint command initially exposed 47 pre-existing formatting violations
that a different shell Ruff binary did not report. The non-executable legacy template,
archive, and documentation-example locations are now explicitly excluded from Ruff's
source-format scope; current source, active OpenSpec, CI, and user documentation remain
checked. Final proof:

```text
hatch run lint
889 files already formatted
0 errors, 0 warnings, 0 notes
All checks passed!
```

The initial local code-review command could not run its module-backed checks because
this fresh worktree had no `nold-ai/specfact-codebase` project module installed. The
pre-commit hook subsequently initialized its required review surface and found one
blocking `CC21` complexity error in the new trust checker. After extraction into small
validation helpers, the scoped review passed with zero errors (two advisory contract
warnings remain); hosted CI/module-fixture validation remains required evidence for
the full repository review surface.

## Socket obfuscation remediation and CI repair — 2026-07-24

The prior dependency-trust record allowed `pycparser==3.0` after a Socket obfuscation
alert. This was an inadequate control: a reviewed record must not approve a known-alerted
release. The following test was added before the policy change and failed as expected:

```text
tests/unit/scripts/test_dependency_trust_review.py::test_alerted_pycparser_release_is_blocked_even_with_a_review_record
FAILED: expected `pycparser==3.0 is blocked after a security-obfuscation alert`; got []
```

The remediation pins `pycparser==2.22`, regenerates `uv.lock` and the hash-protected CI
export, and records its exact wheel URL and SHA-256. The native policy now blocks the
alerted `3.0` release even when an exception record exists, and it binds every remaining
review record to the frozen lock artifact. It is invoked by a staged dependency-input
pre-commit hook and by the always-run `Dependency Trust Gate` CI job. Socket's project
and pull-request checks are independently required by the protected `dev` and `main`
rulesets (verified read-only on 2026-07-24).

The two failed hosted tests were made deterministic: the Typer metavariable assertion is
case-insensitive and the marketplace-uninstall test isolates the user module root rather
than reading a CI runner's state. Passing focused proof:

```text
uv run --locked python -m pytest \
  tests/unit/scripts/test_dependency_trust_review.py \
  tests/unit/workflows/test_trustworthy_green_checks.py::test_pr_orchestrator_package_validation_waits_for_dependency_gates \
  tests/unit/workflows/test_trustworthy_green_checks.py::test_dependency_trust_is_a_standalone_ci_and_pre_commit_gate \
  tests/unit/cli/test_lean_help_output.py::test_lazy_delegate_missing_option_value_shows_leaf_help \
  tests/unit/specfact_cli/modules/test_multi_module_install_uninstall.py::test_module_uninstall_multi_missing_first_reports_error_still_uninstalls_rest_exits_nonzero -q
9 passed

uv run --locked python scripts/check_dependency_trust_exceptions.py
Dependency trust register is valid

uv run --locked python scripts/check_reproducible_delivery.py
reproducible delivery inputs are valid

uv lock --check
Resolved 182 packages
```

## Current PR regression repair and signing boundary — 2026-07-24

The complete smart-test run was run before the final repairs and reported two
failures: a broken link in the new security review document and the
multi-module uninstall continuation test under Typer 0.27.0. The documentation
link was corrected and the command now catches `typer.Exit`, which is no
longer a subclass of Click's exit exception in that Typer release. The exact
affected regression suite then passed:

```text
76 passed
```

The module-registry command change is a signed module asset. Its manifest has
therefore been patch-bumped from `0.1.32` to `0.1.33` using the repository
version-only signer, and the feature-branch manifest policy passed. Producing
the manifest checksum and signature is deliberately not possible in this local
environment because the private signing key is held only by the protected
repository signing workflow. After the PR branch is pushed, that workflow must
create the trusted signature commit before strict module-integrity checks and
the full suite can be recorded as green.

## CI bootstrap trust-check repair — 2026-07-25

The PR's Workflow Lint, Contract Validation, Docs Review, and signature
verification jobs all failed before dependency synchronization because the
bootstrap trust checker imported `icontract`. The checker runs before `uv sync`,
so that import was unavailable by design. The checker is now explicitly
standard-library-only and has a regression test that runs it with site-packages
disabled:

```text
python -S scripts/check_dependency_trust_exceptions.py
Dependency trust register is valid

tests/unit/scripts/test_dependency_trust_review.py
11 passed
```

## PR #654 review remediation — 2026-07-25

The review fixes were specified by the existing reproducible-delivery change.
Tests were added before production changes for fail-closed strict-audit output,
PEP 440-equivalent blocked-release spellings, bounded `uv` execution, local
BasedPyright bootstrap, immutable fixture repository validation, lock-sensitive
license gating, the updated pinned Node action, and omitted multi-module output.
The initial focused run demonstrated the gaps:

```text
10 failed, 76 passed
```

After implementation, the focused regression proof passed:

```text
hatch run pytest tests/unit/scripts/test_security_audit_gate.py \
  tests/unit/scripts/test_dependency_trust_review.py \
  tests/unit/scripts/test_reproducible_delivery.py \
  tests/unit/scripts/test_run_changed_lint.py \
  tests/unit/specfact_cli/modules/test_multi_module_install_uninstall.py \
  tests/unit/workflows/test_trustworthy_green_checks.py -q
86 passed
```

The frozen backend is now `hatchling==1.28.0`, included in the frozen dev
input, and the reproducible-release job builds with `--no-build-isolation`.
The lock and hash-protected export were regenerated from that reviewed input.
The complete configured type gate reports no errors; its 1,652 warnings are
the pre-existing repository baseline and remain non-blocking under the
configured error-level CI threshold:

```text
hatch run type-check
0 errors, 1652 warnings, 0 notes
```

## PR #654 follow-up review remediation — 2026-07-25

Two newly actionable, non-outdated review threads required an immutable fixture
identity proof and failure-path coverage for the local BasedPyright bootstrap.
The workflow assertions were added before the workflow change and failed as
expected because the lockfile repository value had syntax validation only:

```text
2 failed, 4 passed
```

Both checkout workflows now require the exact canonical source repository
`nold-ai/specfact-cli-modules` before exporting its value or fetching code. The
lint bootstrap regression suite also proves a failed `npm ci` returns its exit
status and does not run BasedPyright or later gates. Passing evidence:

```text
hatch run pytest tests/unit/scripts/test_run_changed_lint.py \
  tests/unit/workflows/test_trustworthy_green_checks.py::test_docs_review_uses_immutable_modules_fixture_and_frozen_environment \
  tests/unit/workflows/test_trustworthy_green_checks.py::test_specfact_contract_workflow_uses_immutable_modules_fixture_and_frozen_environment -q
6 passed

hatch run workflows-lint
hatch run lint-changed scripts/run_changed_lint.py \
  tests/unit/scripts/test_run_changed_lint.py \
  tests/unit/workflows/test_trustworthy_green_checks.py
0 errors, 0 warnings, 0 notes
```

## Dependabot alert classification and docs lock repair — 2026-07-25

The seven open Dependabot alerts represent two resolved dependency records, not
seven independent packages. Three high alerts appear twice because
`mcp==1.23.3` is present in both `uv.lock` and the generated CI export; the
seventh is Ruby `json==2.17.1.2` in `docs/Gemfile.lock`.

The wheel metadata proof establishes that `mcp` is not a base-package runtime
requirement. It is transitively installed only when a user selects the published
`dev` or `scanning` Semgrep extras. PyPI metadata checked on 2026-07-25 confirms
Semgrep `1.171.0` is the newest upstream release and pins `mcp==1.23.3` exactly;
the fixed MCP advisory floor is `1.28.1`. The existing exception remains visible,
exact, and time-bounded while upstream has no compatible release. No `0.53.6`
release was prepared because it could not truthfully remediate that optional-extra
dependency.

Upstream Semgrep [PR #11808](https://github.com/semgrep/semgrep/pull/11808)
contains the matching `mcp==1.28.1` dependency update, but it remained open and
unreleased when checked on 2026-07-25. The exception must be removed only after
a released Semgrep version carries that fix and the frozen export verifies it.

The Ruby documentation lock was outside the previous Python-only frozen CVE
gate and Dependabot configuration. Tests were added before the configuration and
lock update:

```text
hatch run pytest tests/unit/docs/test_docs_validation_scripts.py -q
1 failed, 16 passed

hatch run pytest \
  tests/unit/workflows/test_trustworthy_green_checks.py::test_docs_ruby_lock_has_dependabot_and_security_floor_gates -q
1 failed
```

The docs Gemfile now declares `json>=2.19.9`, the generated lock resolves
`json==2.21.1`, Dependabot monitors `/docs` as a Bundler project, Docs Review
runs the focused floor test, and pre-commit runs that same test when the Gemfile,
lock, Dependabot configuration, or test changes.

```text
hatch run pytest tests/unit/docs/test_docs_validation_scripts.py \
  tests/unit/workflows/test_trustworthy_green_checks.py::test_docs_ruby_lock_has_dependabot_and_security_floor_gates -q
18 passed

Ruby 3.2 / Bundler 2.3.5 isolated Jekyll build
done

hatch run security-audit
Security audit passed. No unreviewed vulnerabilities found in the frozen requirements.
```

A temporary import blocker proved that Semgrep cannot currently run supported
SAST without the declared MCP dependency: `semgrep scan` imports
`semgrep.commands.mcp` at CLI startup and then imports `mcp.server`. The project
therefore does not use an unsupported `--no-deps` installation. A workflow-policy
test then rejected `semgrep mcp` across its initial invocation surfaces:
`pyproject.toml`, the PR Orchestrator workflow, `scripts/`, and `src/`. The
later remediation below extends that coverage to all GitHub automation and
pre-commit configuration, preventing the affected server transports from being
started accidentally:

```text
hatch run pytest \
  tests/unit/workflows/test_trustworthy_green_checks.py::test_semgrep_mcp_server_is_not_invoked_by_project_automation \
  tests/unit/workflows/test_trustworthy_green_checks.py::test_docs_ruby_lock_has_dependabot_and_security_floor_gates \
  tests/unit/docs/test_docs_validation_scripts.py -q
19 passed
```

## CodeRabbit automation-surface remediation — 2026-07-26

CodeRabbit identified that the initial `semgrep mcp` policy test did not inspect
GitHub workflow or composite-action files, nor `.pre-commit-config.yaml`. The
policy test now scans the complete `.github/` tree and the pre-commit
configuration in addition to Python, shell, and TOML automation surfaces. This
is an enforcement-test coverage repair; it does not change Semgrep runtime
behavior.

```text
hatch run pytest \
  tests/unit/workflows/test_trustworthy_green_checks.py::test_semgrep_mcp_server_is_not_invoked_by_project_automation -q
1 passed
```
