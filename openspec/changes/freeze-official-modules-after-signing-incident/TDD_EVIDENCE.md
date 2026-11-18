# Cutoff verification

This tests-only replay starts at public `dev` commit `89d016587584fdc94556851bcda11ea0109448da`. The prior implementation on PR #792 is backed up separately at signed commit `6a99cd5209a87b436c543a11fd6819d10a09258d`.

All five mapped tests failed on the unchanged base with Python 3.11. The failures cover a modified bundled manifest, smoke archive bytes rebuilt from source, extraction before cutoff validation, a download attempt for a version outside the cutoff, and the lack of an explicit revoked-key rejection. No test failed during collection, and no tests were skipped. The hosted Requirements workflow will record the failing-first proof for this branch.

The retained proof maps the four cutoff cases in the installer and signer tests. The smoke archive comparison stays in the final CI suite. Its test imports a script that changes in the implementation, so the proof validator would reject that script as a changed test input after the failing-first run.

GitHub retained the four mapped assertion failures at signed tests-only commit `0373474147a2ef31351eec7e0faa8baab2432d0f`. The [Requirements run](https://github.com/nold-ai/specfact-cli/actions/runs/44367200921) produced [artifact 14456666993](https://github.com/nold-ai/specfact-cli/actions/runs/44367200921/artifacts/14456666993) with zero errors or skips. Its original archive SHA-256 is `1d72e1a80d01af1aea2dc851cb4fa2ac8125598d857623f1a586b51b33e6492f`. The implementation was restored after verifying that artifact. The four selected test functions are unchanged.

## Verification from the backed-up implementation

The first two cutoff regression cases failed against the prior implementation. Archive extraction ran for an unapproved cached archive, and filesystem verification accepted an unlisted official tree with unsigned mode enabled.

After the change, 114 tests passed across the touched registry, module installer, signature verifier, and module package suites on Python 3.11. The actual seven latest approved archives also passed installation, strict filesystem verification, and installed reuse in isolated roots. The four bundled module trees passed against the published PyPI wheel inventory. All 248 registry archives matched their expected SHA-256 values. The replacement PEM and cutoff data are included in the locally built wheel.

These results cover local verification. Hosted approval and production signing require the protected workflow and the replacement secrets.

The CI follow-up reproduced a bundled command disappearing after a real pip install. The added relocation case failed before the cache fix. After the fix, the case accepts only bytecode reproduced from the pinned source, rejects a changed cache, and the pip-installed wheel exposes the `module` command. The 83 focused cases passed. Runtime smoke now stages the original cutoff archives, and all seven latest approved bundles installed from that local mirror. The six documentation fixture scenarios passed against the unchanged commit and tree with an exact package-file SHA-256 binding.

The hosted macOS smoke installed Project, then rejected it as Codebase's existing dependency. A local CLI process reproduced the rejection after importing the exact Project archive through the macOS temporary-directory alias. The shared cache verifier authenticated all 47 generated caches and the Codebase dependency check passed with the original frozen archives. The local dependency resolver was stubbed for this targeted check.

On 18 November 2026, the scoped bundle tests reproduced nine failures before the fixture correction. The official integration cases passed after they installed the published cutoff archives. The generic installer cases passed with a community fixture namespace. The command audit passed after it used the same frozen archive registry as the runtime smoke test.

The runtime smoke tests reproduced three malformed-version acceptance failures with hash-pinned test archives. Restoring the existing SemVer check before archive preparation passed those three cases, the prerelease and transitive-dependency controls, and the Requirements selector collection check.

Hosted Python 3.11.18 matched the bundled registry's release-tree hash and refused its standard import cache. The standard-loader cache regression failed locally on Python 3.11.18 before the correction. After the correction, all 21 tests in the focused reproduction passed. The regression also verifies that modified cache bytes are still refused.

The full Linux suite exposed another valid cache with the same length and only two short ASCII interning-tag differences against the live compiler reference. Verification now identifies those tag positions in the authenticated compiler output. Content bytes and reference flags must still match. A separate test proves the same byte values in a literal are compared exactly.

The Python 3.11 compatibility run passed the cutoff cache regressions and failed one analyzer integration test because source discovery could exclude every file under a temporary directory containing `env`. The analyzer correction and its tests come from PR #791. With Python 3.11.18 and an `env`-named temporary directory, the integration test reproduced the same empty feature list and all six source-inclusion regressions failed before the fix. After applying it, all 41 analyzer unit and contract integration tests passed, including the three excluded-directory controls.

## Manifest binding and shared interpreter caches

The three review regressions failed on `df240c7` before the fix. Registration compared a second manifest read, and a supported cache with another interpreter or optimization caused the approved module to be rejected.

After the fix, 79 installer, cutoff and registration tests passed on each of Python 3.11 and 3.12. The shared installation passed when verified in sequence with Python 3.11, 3.12 and 3.11 again. Both interpreter cache files were present. The tests still reject a changed cache for the active interpreter. The original Requirements mapping and its selected test inputs are unchanged.
