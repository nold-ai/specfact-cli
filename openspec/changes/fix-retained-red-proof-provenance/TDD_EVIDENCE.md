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

## Passing-after evidence

Pending implementation.
