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

## Historical CODE2 local verification

The analyzer implementation change replaces absolute-path substring matching with
whole directory components relative to the selected repository. Relative
private-method inputs remain supported. Existing test-file exclusions and
the excluded-directory list are unchanged.

The Python3.11 unit and integration analyzer suites pass52 cases. Both
parameterized nested-service cases also pass under the forced env-named
temporary parent. Ruff check and format pass for all3 Python files.
These are local results; actual CI and its proof/authority gates remain open.

The core repository locks BasedPyright1.39.9. Its matching project-scoped
check over the3 touched Python files reports0 errors, warnings or information
after annotating the new pytest parameter. The modules repository’s different
tool pin is not used as core verification authority.

## Delivery verification correction

The first published TEST producer stopped at missing acceptance metadata before
executing tests. Its original run44158191520 and artifact14362061882 retain zero
RED credit. The added record identifies the actual independent AI mapping reviewer;
it grants no owner authority. The corrected TEST run44159719819 attempt1 reports
six assertion failures, zero errors/skips, and failing-first-proven maturity.

Signed CODE7e64b049 retains six passing-after-red-proven cases. Actual CI also
requires a patch-version/changelog bundle for packaged source changes, so this
follow-up prepares0.55.13 in all four canonical sources and only the local-project
version entry in uv.lock. No dependency selection or artifact hash changes.
The existing0.55.12 delivery and its historical evidence remain unchanged.

The original integration file is restored to delivered bytes. The six focused
unit regressions remain and the original integration case continues to run in
ordinary CI and in the forced-parent reproduction. The removed parameterization
was unnecessary for the fix and selected unrelated existing complexity errors.
No unrelated test helpers, analyzer APIs or review policies are refactored.
Existing advisory findings remain disclosed without validation or waiver credit.

## Lean delivery preparation

With the original integration file restored, the Python3.11.15 analyzer suites
pass51 cases, and the original unmodified nested-structure case passes under
the forced env-named temporary parent. Ruff check/format pass for the five
changed Python files. Pinned core BasedPyright1.39.9 reports0 errors, warnings
and information across those five files. These remain local results until
actual CI verifies the new published head.
