# Cutoff verification

This tests-only replay starts at public `dev` commit `89d016587584fdc94556851bcda11ea0109448da`. The prior implementation on PR #792 is backed up separately at signed commit `6a99cd5209a87b436c543a11fd6819d10a09258d`.

All five mapped tests failed on the unchanged base with Python 3.11. The failures cover a modified bundled manifest, smoke archive bytes rebuilt from source, extraction before cutoff validation, a download attempt for a version outside the cutoff, and the lack of an explicit revoked-key rejection. No test failed during collection, and no tests were skipped. The hosted Requirements workflow will record the failing-first proof for this branch.

The retained proof maps the four cutoff cases in the installer and signer tests. The smoke archive comparison stays in the final CI suite. Its test imports a script that changes in the implementation, so the proof validator would reject that script as a changed test input after the failing-first run.
