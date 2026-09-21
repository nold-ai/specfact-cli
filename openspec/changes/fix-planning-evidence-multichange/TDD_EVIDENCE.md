# Regression evidence

On 2026-09-21 (Europe/Berlin), before workflow edits:

`hatch run pytest tests/unit/workflows/test_requirements_planning_scope.py -q --no-cov`

Result: **2 failed, 1 passed**. Fresh planning selection incorrectly selected an implementation review path; the producer also added that record. The implementation single-change selection and multiple-change rejection passed. These tests execute the workflow's shell selection blocks, not a reimplementation of the selection logic.

Workflow implementation and passing verification remain pending.

The first CI run (35569263871) reproduced both failures but rejected the proof because the unchanged implementation-preservation test passed. Keep that test in the ordinary regression suite and select only the two genuinely failing regression tests for the existing failing-before proof contract. No failure is manufactured and no runtime code changes in this correction.
