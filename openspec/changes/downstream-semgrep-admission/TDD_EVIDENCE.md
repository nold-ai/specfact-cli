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

- Signed authored-test commit and exact commit-bound RED retention.
- Final build/admission GREEN and independent review.
- All 21 real platform/Python cells, including full SAST and MCP evidence.
- Normal native/FULL, quality, dependency/provider trust and signature gates.
- Protected producer bootstrap and separately reviewed production adoption.

No production pin, existing audit/floor or trusted provider has been changed. The
existing frozen MCP audit remains a release blocker. No merge is authorized.

## Native proof branch

The first implementation PR #773 correctly failed the unchanged hosted
Requirements gate with `prior-red-proof-missing`. The earlier local signed test
snapshot is real failing evidence, but cannot substitute for the hosted receipt.
This branch retains the original specification and authored-test ancestors and
freezes the final forty-selector test file before implementation. It contains no
implementation changes. The first hosted run must produce actual RED evidence.
The old PR, commits and failed artifacts remain preserved. No history is rewritten
and no existing gate or provider is changed.
