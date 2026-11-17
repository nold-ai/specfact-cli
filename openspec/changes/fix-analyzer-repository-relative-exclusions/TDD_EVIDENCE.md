# Repository-relative analyzer exclusions

## Before implementation, 17 November 2026

Python3.11.15, trust-validated unchanged uv.lock, normal repository conftest.
The original nested-structure test passes in an ordinary temporary directory
but fails with the same `assert 0 >= 1` under an env-named temporary parent.
The failing CI did not retain its random directory name, so that exact name
is unknown. Controlled identical-code runs produce one feature under project
and zero under tmpenvabc, builder-project and distribution-project.

The deterministic regression run records7 assertion failures,4 passing controls,
0errors and26deselected cases. The six mapped positive-path cases all fail;
real excluded-directory controls stay outside the RED plan and pass.
Production analyzer bytes are unchanged at this checkpoint.

## Scope

One private path-filter method; no thresholds, extraction logic, public APIs,
dependencies, workflows, module payloads or authority-policy changes.
PR790’s historical dependency design/TDD edits are restored to their delivered
base, so new analyzer evidence belongs only to this new change. The existing
canonical COPY test correction remains in the parent.

## Remaining verification

Run the same regression and analyzer suites after the fix, then actual CI.
Local results do not grant native or final-head readiness credit.
The paired internal wiki checkout is absent beside this worktree. The separate
canonical internal wiki was read as context; its new source mirror is not
written or claimed updated. Mirror this change there and rebuild its graph
from that checkout as a follow-up.
