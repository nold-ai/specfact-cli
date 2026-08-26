# TDD evidence: fix-retained-red-proof-provenance

## Baseline

- **Date**: 2026-08-26 (Europe/Berlin)
- **Branch base**: `origin/dev@e3a20f20df440dff49f8c6d1f73375451bea1d8c`
- **Issue**: <https://github.com/nold-ai/specfact-cli/issues/689>
- **Observed consumer failure**: PR #688 Requirements Evidence final run `33010291604` rejected retained red artifact `9622042446` as `prior-red-proof-invalid`.

## Failing-before evidence

No production file had changed on this branch when the following command ran:

```text
.venv/bin/pytest -q \
  tests/unit/scripts/test_requirements_proof_provenance.py::test_bind_red_proof_records_validator_complete_immutable_provenance \
  tests/unit/scripts/test_requirements_proof_executor.py::test_executor_records_proof_toolchain_identity_in_junit \
  tests/unit/scripts/test_requirements_proof_pytest_plugin.py::test_selector_plugin_uses_only_public_pytest_report_contract \
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_binds_red_proof_before_publication
```

- **Timestamp**: 2026-08-26 22:34 Europe/Berlin
- **Result**: exit 1; four tests collected and four intended failures.
- **Observed gaps**: no `bind_red_proof` API, no toolchain properties in executor
  JUnit, no plugin toolchain records, and no red binding branch in the workflow.
- **Legitimate control**: the proof executor successfully ran and produced the
  canonical selector property; only the newly specified toolchain properties were
  absent.

The pinned Requirements planner accepted the three exact scenario selectors with
mapping digest
`sha256:34c2a2c2777b4bda8cba33bbc5639311fac6626ddd4f06fa41a5403450f06318`
and plan digest
`sha256:487ea068dc624aafe4dde3f74026fbac9fdf3a896ce201ad623a782d891a3029`.

### Authoritative GitHub red execution

- **Signed red commit**: `dcd04b981b5e2a8e8d1fe403cdec6fddd038b678`
- **PR / workflow run**: #690 / `33011480246`
- **Artifact**: `requirements-evidence`, ID `9622698922`
- **Artifact report SHA-256**: `58ed2de28b255378d303ec3ba1f17cda309426bcc008ae9cb39ea7e339a43531`
- **Retained JUnit SHA-256**: `fa967bce9a5391c20f2ed0230a50a49e46c00bbf157aa7589a7dc4041a3f7efc`
- **Result**: the three mapped selectors failed for the intended missing binder,
  toolchain-property, and workflow behavior. The report records
  `observed_maturity: red`, `gate_decision: pass`, and the exact signed source ref.
- **Accepted execution mapping/plan**:
  `sha256:6a9413ab306eb0cf0aad62661d66c5ef684b91036766acf7021953877c9b617e` /
  `sha256:00595739da3dd81a01032fbc2661094b8c6e2836dc38e366eae0a666e4574222`.
- **Incremental red control**: after specifying explicit non-green red-run
  termination and the issue-specific ledger allowlist, the focused workflow test
  still failed at the first missing binding branch before any production edit.

### Approved self-bootstrap ledger boundary

The released producer necessarily omitted the four fields this change adds, so its
own incomplete red artifact is not passed to or accepted by the retained-proof
validator. The final #689 workflow may use only this immutable ledger prefix,
signed red commit/run, and exact execution mapping/plan through the existing
digest-bound legacy ledger input. This is not a general compatibility fallback;
every other change remains required to present a validator-complete red artifact.

<!-- approved-bootstrap-ledger-end -->

## Passing-after evidence

### Focused behavior and security controls

```text
SPECFACT_MODULES_REPO=/private/tmp/specfact-modules-fixture.sFRAtj/repo \
UV_CACHE_DIR=/private/tmp/specfact-uv-cache hatch run test \
  tests/unit/scripts/test_requirements_bootstrap_authority.py \
  tests/unit/scripts/test_requirements_proof_provenance_security.py
```

- **Result**: 14 passed. This includes entity-declaration and oversized-file
  rejection, explicit workflow JUnit binding, JSON toolchain tamper rejection,
  exact-authority acceptance, every reviewed external-metadata rejection, and
  same-ledger/plan replay without the authorized red ancestor.
- **Review-finding red control**: before the validator changes, the same command
  produced 11 passed and three intended failures: invalid `base_commit` reached
  Git, a non-string `red_commit` raised `TypeError`, and oversized JUnit reached
  `read_bytes()`.
- Authoritative final test-only red run:
  `33013274590` at signed commit
  `04b6c02eb63f779309d8dced48085f3ef0efe029`; artifact `9623426074`.
- External one-time authority:
  `https://github.com/nold-ai/specfact-cli/issues/689#issuecomment-5431081643`.

### Local quality and security gates

```text
SPECFACT_MODULES_REPO=/private/tmp/specfact-modules-fixture.sFRAtj/repo \
UV_CACHE_DIR=/private/tmp/specfact-uv-cache hatch run test
```

- **Current expanded-suite result**: 3,033 passed and 9 skipped. Two environment
  controls failed locally: the sandbox denied PyPI DNS during a temporary
  runtime-discovery install, and denied a test write to the user metadata home.
  Rerunning the runtime-discovery test with network access passed (1 passed).
  The GitHub Tests job runs the full command in its isolated writable runner and
  is the terminal control for the home-write case.
- **Earlier pre-review-fix control**: the full repository suite passed at the
  prior PR head before these eight security-boundary tests were added.
- Ruff format/lint: pass; basedpyright: 0 errors (repository baseline warnings
  unchanged); OpenSpec strict validation: pass.
- SpecFact full-enforcement code review: pass with zero findings after all
  blocking, warning, and advisory findings were remediated.
- Bandit medium/high scan: zero findings and zero `nosec` suppressions.
- Semgrep auto rules: 290 rules across three changed scripts, zero findings.
- Module signature policy and license compliance: pass.
- `UV_CACHE_DIR=/private/tmp/specfact-uv-cache hatch run lint-workflows`: exit 0.
- YAML wrapper exits 0 and continues to report only the pre-existing R07/R08
  OpenSpec YAML style findings; the changed workflow parses and its focused
  workflow tests pass.

### GitHub Actions authority-association compatibility

- Final workflow run `33015938817` rejected the exact immutable authority at
  `authority-comment-association`: the Actions token surfaces the private
  organization member as `COLLABORATOR`, while the authenticated local API
  surfaces the same login as `MEMBER`.
- Read-only repository and organization APIs confirm `djm81` has repository
  `admin` permission and active direct organization membership.
- A test-only commit first reproduced rejection of the otherwise identical
  `COLLABORATOR` comment. The implementation then admitted GitHub's three
  maintainer associations (`OWNER`, `MEMBER`, and `COLLABORATOR`) while retaining
  every exact comment, login, signed-commit, run, artifact, expiry, and ancestry
  binding. Focused authority and producer-regression tests pass (6 passed).

### Final Code Review toolchain and finding remediation

- Passing run `33016260828` proved the corrected final Requirements flow, but its
  retained Code Review report exposed two `tool_error` warnings because
  BasedPyright and Pylint were not available on the runner PATH, plus two
  readability advisories in changed test helpers.
- A workflow contract test first failed because no frozen review-tool setup
  existed. A second audit-contract test first failed because the isolated tool
  lock was not included in the CVE gate.
- BasedPyright remains npm-lock bound at `1.39.9`. Pylint `4.0.7` and its six
  transitive packages are hash-locked in an isolated Python 3.12 environment so
  they cannot mutate the project environment. Installing that lock succeeds and
  `pip-audit` reports no known vulnerabilities.
- Both readability advisories were removed by extracting static workflow command
  data and the governed-rename test helper. Full-enforcement Code Review with the
  exact isolated tools reports `PASS` with no findings.

### Combined delivery without a multi-change bypass

- The local pre-commit gate demonstrated that two active issue-linked mappings
  fail closed with `Requirements evidence spans multiple active changes`; the
  pinned tool accepts only one mapping-specific review record.
- The completed #686 change was therefore finalized through native
  `openspec archive`, which applied its `dep-license-gate` delta to the canonical
  specification and preserved its evidence ledger under the dated archive. #689
  remains the only active mapping for #690's externally authorized plan.
- No generic or issue-specific multi-change selector was retained. The dependency
  graph remains independently governed by its focused tests and terminal Security
  Audit.

The internal wiki source follow-up remains intentionally unmodified because the
user excluded internal wiki PR #38 and its planning branch from this task.
