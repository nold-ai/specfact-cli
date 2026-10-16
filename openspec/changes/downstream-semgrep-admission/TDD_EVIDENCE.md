# Downstream Semgrep verification evidence

## Accepted scope and source order

The owner djm81 accepted exact mapping
`sha256:83f12bcec0ff756681c2cc1188c431fce1327e6d3371fae6bc4df4bf1ddd8425`
on 2026-10-16 at 23:04 Europe/Berlin. The forty selectors and the separate native
inspection obligation remain unchanged. Indentation-only YAML cleanup preserves
the exact canonical digest, verified with the unchanged released validator.
The actual owner record is retained in `requirements-proof/review-evidence.json`.

Signed specification `40dc5c93d2a25284550247ce04147ae4e8509df6` precedes authored
tests `4a1afa902a5dc62990e60cde00a4b45b4e78abea`. Its isolated real local snapshot
records forty AssertionError failures, zero errors and zero skips before the
initial implementation. PR #773 preserved that first implementation attempt, but
the hosted gate correctly rejected its missing native RED receipt. It is closed
and retained; no history was rewritten or gate relaxed.

## Final hosted RED

The final test-only commit is `33a1d4876a9efeadc994fea244b9c37f5b30d7e6`.
The unchanged Requirements producer executed it in run `38971008984`.
Service artifact `12077261179` has ZIP SHA-256
`9ffd890802b45019109b97ae00ab2bad4df981d7bd5fe1c7725f5ca3b032a24f`.
Its bytes match GitHub's service digest. The report binds source tree
`288a66baca5d34e813d2b522d5587be881d03db4`, base
`729a53bd4bcbba94886cff5c73d7092bef6ceb94`, all forty selectors and test-file SHA-256
`d021d87eebbb4834746fc0a71e24cadfc0586d8c5e44a3fa795fee871824e38e`.
JUnit records forty AssertionError failures, zero errors and zero skips, with four
actual producer properties per case. The source file remains unchanged after
this run. Implementation was restored to this branch only after the service
artifact and identities were verified.

These initial missing-API assertions do not claim forty independently exploited
vulnerabilities. The prior native `ce6a1eaa` receipt is retained separately and is
not reused for the changed final test bytes. Neither receipt is claimed to predate
the separate retained implementation attempt in #773.

## Implemented checks and independent review

The current forty-case suite passes. Independent review reproduced and corrected
strict audit-diagnostic and nonstandard JSON-constant defects. Actual failing
assertions preceded the corrections. Dirty or mixed-source reports, missing audit
controls and approval/source mismatches now fail closed.

The first candidate workflow exposed Windows CRLF metadata. After an actual
failing regression, the build changes only the two reviewed header values and
preserves header separators and body bytes. Two builds of the retained official
Windows wheel match, with all 177 other payload members unchanged. No Windows
binary was executed locally. A nonwriting reviewer reran the forty-case suite
and accepted the focused corrections.

An inspected native musl cell passed installation, audit, full SAST and MCP
controls, but its job failed while the host copied a root-owned private settings
file. The workflow now uploads the mounted evidence directory directly. It
excludes private settings and disposable environments, without changing file
permissions, test expectations or timeouts.

The real local macOS arm64 Python 3.13 candidate passes all eleven MCP regressions.
The vulnerable MCP 1.29.0 control fails eight lifecycle/default assertions with
zero errors. Candidate and upstream default SAST runs scan the same 306 files,
with exact findings, errors and path-set parity. Both unchanged baseline gates
pass; positive and negative controls exit one and zero respectively. These local
experiments are not a substitute for the complete committed native matrix.

## Gates and remaining obligations

Normal signed hooks, strict selected OpenSpec, canonical typing, YAML/workflow
lint and frozen input checks run without policy changes. FULL review remains
mandatory. The only retained exceptions are the exact preinstallation entry
points, external SDK factory signature and private credential-fixture readability
advisory described in `REVIEW_EXCEPTIONS.md`. No scorer or threshold was changed.

All twenty-one final platform/Python cells, final native Requirements GREEN and
exact-head authority remain pending. Production admission starts empty. Protected
producer bootstrap and production adoption remain blocked. Existing production
pins, audit and provider gates are unchanged; the frozen MCP audit remains red.
No merge, main promotion or OpenSpec archival is authorized or claimed.
