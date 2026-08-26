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

Pending implementation.
