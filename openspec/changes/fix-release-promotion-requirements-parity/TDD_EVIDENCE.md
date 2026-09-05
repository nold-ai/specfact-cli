# TDD Evidence

## RED — 2026-09-05

The specification commit `2b2b3078` preceded test authoring. Against the
unchanged `origin/dev` implementation, the four mapped selectors failed for the
intended missing behavior:

```text
pytest -q \
  tests/unit/scripts/test_requirements_promotion_reuse.py::test_exact_protected_promotion_produces_canonical_attestation \
  tests/unit/scripts/test_requirements_promotion_reuse.py::test_lookalike_promotion_is_rejected \
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_same_named_fork_does_not_enter_promotion_path \
  tests/unit/scripts/test_requirements_promotion_reuse.py::test_incomplete_or_stale_promotion_provenance_is_rejected \
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_workflow_revalidates_promotion_reuse_in_all_stages

5 failed in 0.45s
```

The three validator selectors reported that the protected-promotion validator
was not implemented. Both workflow selectors reported that the promotion
checkout/validation steps were absent. Collection succeeded, so these are
behavior-level RED results rather than setup or selector failures.

Two independent read-only reviews then strengthened the same four selectors to
cover real commit-to-PR API multiplicity, same-named forks, nonempty
plan/JUnit binding, complete paginated metadata, executable central-validator
pin checks, the public CLI boundary, exact attestation byte transport, and the
unchanged main-relative aggregate planning scope. The rerun above is against
that final RED contract.

The independently reviewed test-authored mapping digest is
`sha256:9c34bb52969f9d9dd7c7caa41d686324f8f907ee0611e677e5615b27cdd21a1e`.

## GREEN

Pending implementation and independent verification.
