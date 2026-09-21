# Regression evidence

On 2026-09-21 (Europe/Berlin), before workflow edits:

`hatch run pytest tests/unit/workflows/test_requirements_planning_scope.py -q --no-cov`

Result: **2 failed, 1 passed**. Fresh planning selection incorrectly selected an implementation review path; the producer also added that record. The implementation single-change selection and multiple-change rejection passed. These tests execute the workflow's shell selection blocks, not a reimplementation of the selection logic.

After the five-line workflow correction, the new tests and existing Requirements workflow suite pass: **29 passed** (`hatch run pytest tests/unit/workflows/test_requirements_planning_scope.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q --no-cov`).

The first CI run (35569263871) reproduced both failures but rejected the proof because the unchanged implementation-preservation test passed. Keep that test in the ordinary regression suite and select only the two genuinely failing regression tests for the existing failing-before proof contract. No failure is manufactured and no runtime code changes in this correction.

The corrected test-only commit `3e9a4ada2eed2a6a60427c3d5e517f33c5c92c79` produced the accepted RED artifact in run [35569603411](https://github.com/nold-ai/specfact-cli/actions/runs/35569603411): `gate_decision=pass`, `observed_maturity=red`, no findings. The overall failing-test run remains failed as expected; this is not a claim that its full pipeline passed.

Independent implementation review accepted the five-line guard change with no blocking findings. Reproducible-delivery validation and `uv lock --check` passed; BasedPyright in the worktree Hatch environment reported zero errors (existing repository warnings remain). The initial type invocation outside that environment could not resolve the project dependencies and is not used as passing evidence. Final remote verification is pending.
