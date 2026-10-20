# Certificate trust-store regression

## Failing before dependency changes

On 2026-10-20 Europe/Berlin, the existing frozen lock was installed with
`uv sync --locked --all-extras` into an isolated environment using Python 3.13.14.
It installed certifi 2026.7.22. No dependency input had been edited.

Command from this worktree:

```bash
/private/tmp/specfact-dependency-audit-20261020/certifi-tools/bin/python -m pytest tests/unit/security/test_certificate_trust_store.py -q --no-cov
```

The actual SSL trust-store comparison failed as intended:

```text
Extra items in the left set:
'86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b'
1 failed in 0.06s
```

The installed bundle still trusted the compromised emSign ECC Root CA - G3.
The full local capture is
`/private/tmp/specfact-dependency-audit-20261020/certifi-root-red.log`.
The frozen audit independently reported GHSA-6q48-6c7w-9gw2 and the separate MCP
finding. Passing-after evidence must use the same test against the refreshed
frozen installation. This local record does not replace native CI execution proof.

## Native CI failing-first proof

The typed test was published at commit
`d6d8f9089bb55f8e834a55dfcac43a8a5e4c61ca` before dependency changes.
[Requirements run 39498007620](https://github.com/nold-ai/specfact-cli/actions/runs/39498007620)
retained artifact `12297219535`, digest
`sha256:10fefe0c9b89815a6a7b29cbe5bca56680fe0fed3aefae693328dfbe6e5406e8`.
The actual JUnit records one intended fingerprint failure, no errors and no skips
on Python 3.12.15. Native reconciliation reports `observed_maturity: red`,
`gate_decision: pass`, and `implementation_evidence: failing-first-proven`.
The run's delivery checks remain blocked at this intermediate failing-test stage.
This is not final implementation or authority evidence.

## Passing after frozen refresh

The canonical `hatch run refresh-frozen-delivery` regenerated the Python lock and
hash-protected CI export after the certifi minimum and 0.55.11 metadata changes.
`uv sync --locked --all-extras` then installed the exact graph in the isolated
environment. The same typed test passed on Python 3.13.14 with certifi 2026.10.19:

```text
1 passed in 0.05s
```

The lock retains 184 packages. Only certifi 2026.7.22 to 2026.10.19 and the project
0.55.10 to 0.55.11 changed version. The installed store has 120 roots and excludes
the compromised fingerprint. Delivery/export parity, lock consistency, license,
dependency trust, synchronized versions, strict PyPI-ahead and Bandit checks pass.
The full audit still fails solely on MCP 1.29.0 / CVE-2026-59951. Both other frozen
exports pass their actual audits. No audit exclusion or resolver override exists.

These passing-after observations describe the local implementation working tree.
Final commit-bound CI evidence and new exact-head authority remain required.
The local logs and package accounting are in
`/private/tmp/specfact-dependency-audit-20261020/certifi-fix-result.txt`.

## Release verification corrections

The broader smart-test attempt had 3427 passes and two failures. Its launcher
selected the Requirements fixture instead of the separately pinned smoke fixture.
Using the exact smoke fixture, then warming the new hash-locked certifi wheel for
its offline child, made the real launcher pass. The first failed results remain
in the local trail and are not reported as passes.

The other failure was the existing release test's fixed 0.55.10 expectation against
the required 0.55.11 patch. Updating only that expected value preserves all original
assertions. All 20 release/security and CA tests then passed. The final full
smart-test rerun is recorded separately after completion; targeted passes do not
turn the earlier failed run into a green gate.

## Final local smart gate

With the separately pinned smoke fixture and frozen cache prepared,
`hatch run smart-test` exited 0. Its actual result was:

```text
3429 passed, 11 skipped, 2 warnings in 262.82s
```

The two warnings are dependency deprecations, not failed tests. The earlier failed
run remains retained. Final local success does not waive MCP, final native CI or
exact-head human authority. Normal dependency commit remains blocked by the
unchanged `frozen-cve-audit` failure.

## Published certificate correction and new artifact cycle, 2026-10-21

The owner approved the exact one-time local hook exception after the checkpoint
above. Commit 66ee3d58959e7798a6a7a5a1ed5c41d1db37fbc0 is pushed. Other hooks and
CI stayed enforced; the exception is consumed. Actual final package/runtime and
quality checks pass, while the frozen audit still reports MCP 1.29.0 alone.
The fresh Requirements consumer exposes the distinct old-verifier-bundle mismatch.

The revised scope retains the installed test and adds inert exact frozen-wheel
certificate proof plus a packaging-only MCP artifact contract. Its mapping digest
is sha256:9260bf98d7d3e53daf5e8ebc039ea4757d638fc78be639e17a3f527ffb3e12b1.
Independent test design review reproduced certificate GREEN and actual upstream
MCP metadata RED using the untouched older Hatch environment. Before a producer
exists, selected bytes are the pinned official Semgrep wheel. The intended diff
is `['mcp==1.29.0'] != ['mcp==1.30.0']`. No new native RED or final GREEN is claimed
until an authenticated workflow actually produces it for these exact selectors.

Historical certifi RED above remains real evidence of the earlier correction;
it is not relabelled as proof for the revised map. The new cycle deliberately
retains already-passing certificate coverage and the new failing scanner artifact
case. Independent acceptance, exact test digest and native records follow only
after actual review and execution. Canonical dependency inputs remain unchanged.

Independent AI technical acceptance is recorded at <https://github.com/nold-ai/specfact-cli/pull/782#issuecomment-6303112841>. It binds
the mapping above, recipe SHA256 bcb7d9ce9cb05fb479069af7c0eaebe816adbea338ceb269642c731de18bcb0c
and exact test SHA256 f47e9084a040512d872e4dd1db97260776011542a29136087bd2d05ad2bd6dce.
The independent final run has 13 passes and one intended MCP metadata assertion
failure under Python 3.12 with old installed certifi. The certificate artifact
case and all malformed-input/description controls pass. No native record or human
authority is inferred from this local technical acceptance.
