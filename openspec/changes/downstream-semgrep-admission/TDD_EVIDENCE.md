# Downstream Semgrep evidence

## Specification and authored RED

Signed specification commit: `40dc5c93d2a25284550247ce04147ae4e8509df6`.
Normal hooks and strict OpenSpec validation passed before authored tests were
copied into the worktree. The pinned planned Requirements validator accepted
all four native requirement mappings without findings.

Actual worktree run before production code existed:

```text
python -m pytest tests/unit/scripts/test_downstream_semgrep.py -q --tb=short
40 failed in 0.47s
JUnit: 40 tests, 40 AssertionError failures, 0 errors, 0 skips
```

The failures assert that the real build/admission boundary is absent. They are
initial missing-behavior evidence, not a claim that every rejection input exposed
a separate existing vulnerability. Synthetic wheel, provenance and audit fixtures
exercise the contract; they are not authenticated production admission.

The owner accepted exact mapping
`sha256:83f12bcec0ff756681c2cc1188c431fce1327e6d3371fae6bc4df4bf1ddd8425`
on 2026-10-16 at 23:04 Europe/Berlin. The separate accepted record identifies the
actual human reply. The native matrix inspection obligation remains pending.

The mapped complete-audit case was strengthened with candidate-only audit
assertions under the same accepted mapping. Actual pre-extension run:
`1 failed in 0.09s`, AssertionError `Candidate audit proof is absent`.
The original frozen test proposal, both RED runs and hashes remain retained in
`/private/tmp/specfact-downstream-semgrep-20261016/` during local preparation.

## Local MCP candidate experiments

A separate non-listening control on MCP 1.29.0 fails eight lifecycle/default
controls, with zero errors. Actual DELETE and refused opening requests retain a
registered session. MCP 1.30.0 passes those eight checks and the actual Semgrep
stdio initialize/list/custom-scan probe. Additional local checks verify the real
Semgrep HTTP factory rejects missing/malformed credentials and the SDK binds a
session to the verified test principal. These are isolated candidate experiments,
not seven-platform proof or protected producer admission.

## Pending

- All 21 native platform/Python cells are still pending; no matrix acceptance is claimed.
- Final independent review and signed implementation remain pending.
- All 21 real platform/Python cells, including full SAST and MCP evidence.
- Normal native/FULL, quality, dependency/provider trust and signature gates.
- Protected producer bootstrap and separately reviewed production adoption.

No production pin, existing audit/floor or trusted provider has been changed. The
existing frozen MCP audit remains a release blocker. No merge is authorized.

## Signed test snapshot and local GREEN

Signed authored-test commit `4a1afa902a5dc62990e60cde00a4b45b4e78abea`
was exported into a separate snapshot before the implementation commit. Its real
JUnit run records 40 AssertionError failures, zero errors and zero skips.
The corresponding current implementation run records 40 passes.

Independent security review reproduced two defects in the first implementation.
The audit parser rejected pip-audit's exact clean diagnostic, and Python JSON
accepted nonstandard numeric constants. Regression assertions failed before each
fix. The corrected boundary permits only the exact clean diagnostic and rejects
NaN and both infinities. A later actual failing assertion showed that dirty or
mixed-source matrix reports were accepted. Those reports now fail; production
admission also binds the matrix source commit to the protected approval.

The unchanged FULL review on 2026-10-16 at 23:21 Europe/Berlin passed with score
95, zero errors, ten documented warnings and one retained readability advisory.
Canonical BasedPyright analyzed 704 files with zero errors and 1456 existing
warnings. None of its diagnostics concern this change. Strict selected OpenSpec,
Ruff and `uv lock --check` pass. Normal implementation hooks remain pending.
`REVIEW_EXCEPTIONS.md` identifies the narrow preinstallation and external-signature
exceptions. It does not alter the review scorer or any trust gate.

The real macOS arm64 Python 3.13 candidate environment passes all eleven MCP
regressions after fixture extraction. The vulnerable MCP 1.29.0 control fails
eight lifecycle/default assertions with zero errors. Actual default SAST runs
scan 306 files with identical candidate/control findings, errors and path sets.
Both unchanged baseline gates pass; positive and negative controls exit one and
zero respectively. These are dirty-source local experiments, not eligible
committed matrix evidence. All raw failed attempts remain retained locally.
