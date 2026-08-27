# TDD Evidence: Fix Release Promotion Security Gates

## Environment

- Repository: `nold-ai/specfact-cli`
- Change: `fix-release-promotion-security-gates`
- Issue: #692
- Baseline: `origin/dev` at `3ea3d9b4492ade6ec5683fac83c5b5090b0cb547`
- Date/timezone: 2026-08-27, Europe/Berlin

## Failing-before evidence

**Command (2026-08-27, before implementation):**

```text
<PROJECT_VENV>/bin/python -m pytest \
  tests/unit/specfact_cli/registry/test_signing_artifacts.py::test_frozen_setup_action_disables_persistent_cache_before_external_fixture_execution \
  tests/unit/scripts/test_requirements_bootstrap_authority.py::test_bootstrap_authority_routes_invalid_utf8_to_input_finding \
  tests/unit/scripts/test_requirements_bootstrap_authority.py::test_bootstrap_authority_accepts_exact_owner_bound_red_history \
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_writes_reports_before_early_failure -q
```

- Result: exit 1; 2 failed, 2 passed.
- Cache boundary failed because the shared action still contained `enable-cache: true` and lacked `enable-cache: false`.
- Metadata classification failed because `UnicodeDecodeError` was consumed by the broader `ValueError` handler and exposed the decoder message instead of `authority-metadata`.
- Legitimate controls passed: exact owner-bound bootstrap authority remained valid, and ordinary Requirements early failures still wrote retained diagnostics before exiting non-zero.
- Environment: macOS, Python 3.13.14, pytest 9.1.1; repository worktree at baseline `3ea3d9b4492ade6ec5683fac83c5b5090b0cb547` plus spec/test-only changes.

An earlier test-only experiment considered reusing Requirements evidence for an
exact `dev`-to-`main` promotion. It was rejected before implementation because
it would skip finalized evidence and Code Review execution. It is not part of
the authoritative failing-before evidence or the candidate design.

**Review-finding red evidence (2026-08-27):**

- Test-first selectors for the missing Code Review dependency-trust trigger,
  environment-scoped Pylint exception, function-local `pytest_plugins`
  exclusion, and ordinary active-change deletion failed against the inherited
  implementation.
- The final independent bypass review added regressions for branch-selected
  manual fixture execution, the post-module npm cache hook, and conditional
  module-scope `pytest_plugins`; the three-selector run exited 1 with 3 failed.
- A subsequent P1 challenge proved that a literal annotated declaration and a
  computed declaration were both omitted: the two-selector run exited 1 with
  2 failed. A separate imported-binding challenge exited 1 with 1 failed.
- The final concrete bypass challenge reproduced pattern-capture and direct
  `globals()` namespace bindings: the parametrized selector exited 1 with
  2 failed before the fail-closed checks were added.
- A definition-scope challenge reproduced one P1 default-expression bypass and
  four false-positive comprehension scopes: the five-selector run exited 1
  with 5 failed before scope-aware traversal was added.
- After Semgrep 1.175.0 became available, the new frozen-graph policy selector
  exited 1 because all three repository constraints still allowed 1.171.0,
  the lock/export selected vulnerable `mcp==1.23.3`, and the obsolete MCP
  exception remained registered.
- The independent dependency-policy bypass review then replaced only MCP's
  exact lock record with vulnerable `mcp==1.23.3`. `uv lock --check`, frozen
  export, and sync dry-run all accepted the internally consistent downgrade,
  while the pre-install trust validator returned no error because its floor map
  covered Semgrep only. This proved lock consistency was not a sufficient MCP
  security boundary before the explicit `mcp>=1.28.1` floor was added.
- The first signed-commit attempt launched the Markdown auto-fix hook once per
  pre-commit filename batch. Concurrent instances both attempted `git add` and
  the hook failed with `index.lock: File exists`. The mapped configuration
  assertion then failed because `cli-block1-markdown-fix` did not declare
  `pass_filenames: false`.
- After that hook was serialized, the next commit attempt reached Block 2 and
  rejected the complete native retained-proof archive because Git represented a
  heavily rewritten `CHANGE_VALIDATION.md` as delete+add rather than a rename.
  The existing mapped archive selector reproduced the false rejection with an
  exact dated destination and no remaining active files.

## Passing-after evidence

**Focused security and review regressions (2026-08-27):**

```text
<PROJECT_VENV>/bin/python -m pytest \
  tests/unit/workflows/test_trustworthy_green_checks.py::test_manual_dependency_compatibility_rejects_unprotected_fixture_refs \
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_code_review_setup_does_not_persist_an_npm_cache \
  tests/unit/scripts/test_requirements_proof_provenance.py::test_pytest_plugin_discovery_ignores_function_local_assignments -q
```

- Result: exit 0; 3 passed.
- Full owning workflow/provenance files: exit 0; 96 passed.
- Final annotated/computed/import-bound plugin selectors: exit 0; 3 passed.
- Pattern-capture and direct globals/locals/vars namespace-binding controls:
  exit 0; 2 passed.
- Import-time definition-expression and list/set/dict/generator comprehension
  scope controls: exit 0; 5 passed.
- An independent bounded bypass/regression review found one remaining concrete
  P1 in the initial candidate: an internally consistent MCP downgrade bypassed
  the pre-install tool-floor policy. The fix adds the maximum reviewed advisory
  floor, `mcp>=1.28.1`, and a direct regression alongside the Semgrep floor.
- The independent re-review reran the original downgrade reproducer: MCP 1.28.0
  and 1.23.3 were rejected before synchronization, while the fixed boundary
  1.28.1 and selected 1.29.0 passed. No concrete bypass remained.
- The mapped pre-commit layout selector passed after the Markdown fixer disabled
  filename batching. Its staged-file discovery and unstaged-hunk controls remain
  unchanged. The exact Markdown pre-commit hook then ran once and passed without
  index contention.
- The archive selector passed after completeness was bound to the staged index:
  exactly one dated archive destination, no active paths, and a regular staged
  counterpart for every file tracked at `HEAD`. Partial archives and missing or
  non-regular counterparts remain rejected.
- The exact Block 2 hook then passed Requirements evidence at `test-authored`,
  command/documentation checks, Code Review with zero errors and warnings, and
  the contract-status control.

**Changed-scope regression set (2026-08-27):**

```text
<PROJECT_VENV>/bin/python -m pytest \
  tests/unit/scripts/test_check_license_compliance.py \
  tests/unit/scripts/test_requirements_bootstrap_authority.py \
  tests/unit/scripts/test_requirements_evidence_pre_commit.py \
  tests/unit/scripts/test_requirements_proof_provenance.py \
  tests/unit/specfact_cli/registry/test_signing_artifacts.py \
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py \
  tests/unit/workflows/test_trustworthy_green_checks.py -q
```

- Result: exit 0; 211 passed using the repository virtual environment and its
  normal Homebrew Git.
- A diagnostic run that forced Apple `/usr/bin/git` produced one pre-existing
  fixture failure because that Git initializes `main` while the fixture names
  `master`; restoring the normal repository toolchain passed the same selector.

**Workflow and dependency controls already completed:**

- `hatch run lint-workflows`: exit 0 after the final cache/trigger edits.
- Primary and frozen Code Review `pip-audit`: no vulnerabilities and no waivers
  after the compatible Semgrep/MCP update.
- License gate: primary 173 packages passed; isolated seven-package Code Review
  graph passed with the exact Pylint 4.0.7 Code Review-only exception; four
  module manifests passed.
- Strict module-signature verification: four manifests passed.

**Semgrep/MCP compatibility and advisory closure (2026-08-27):**

- Current PyPI metadata identifies Semgrep 1.175.0 as the latest release and
  declares exact `mcp==1.29.0`.
- `uv lock --dry-run --upgrade-package semgrep`: exit 0; the 184-package graph
  changed only Semgrep 1.171.0 -> 1.175.0 and MCP 1.23.3 -> 1.29.0.
- The new policy selector passed after all three Semgrep constraints, `uv.lock`,
  the hash-protected CI export, exception register, and independent MCP floor
  were updated. Its downgrade controls reject both Semgrep 1.174.0 and MCP
  1.23.3 before synchronization.
- Exact frozen synchronization installed Semgrep 1.175.0 and MCP 1.29.0.
- Isolated Python 3.11 and 3.12 frozen synchronizations each resolved the same
  184-package graph, reported Semgrep 1.175.0 / MCP 1.29.0, and passed the
  frozen-graph policy selector; Python 3.13 supplied the primary validation.
- Semgrep 1.175.0 executed the repository's six-rule SAST configuration over
  297 Python targets with zero findings; the baseline gate passed at zero.
- Final primary and Code Review frozen audits both passed with no reported
  vulnerability and no MCP exception. CVE-2026-52869, CVE-2026-52870, and
  CVE-2026-59950 no longer reproduce in either lock representation.
- A macOS sandbox trial initially selected Homebrew `pysemgrep` and lacked
  trust/log permissions. Re-running with the frozen environment first in PATH,
  its Certifi trust bundle, and normal user-state access completed cleanly; this
  was an invocation/sandbox control, not a lock incompatibility.
- Final changed-Python Code Review after the MCP-floor regression and test
  cleanup: 13 informational findings, 0 errors, 0 warnings, and no advisories.

**Repository and release controls (2026-08-27):**

- Final full repository run with the exact pinned modules fixture: exit 0;
  3066 passed, 10 skipped, two third-party deprecation warnings.
- Exact PR Orchestrator `smart_test_coverage.py run --level full` command:
  exit 0; the then-current 3075 collected cases completed with 64% aggregate coverage,
  above the configured 50% threshold.
- `hatch run lint`: exit 0; formatter, Ruff, and basedpyright passed with zero
  type errors or warnings across 938 checked files.
- `hatch run lint-workflows`: exit 0 after the final workflow changes.
- `hatch run yaml-lint`: the #692 artifacts are clean. The command still prints
  existing line-length/blank-line findings only in active R07/R08 planning
  changes and exits 0 because of the inherited wrapper behavior. Those planning
  changes are outside this patch and were not modified.
- Semgrep SAST gate: exit 0; zero findings against a zero-finding baseline.
- Bandit scan: exit 0; no blocking findings.
- Dependency trust, frozen `pip-audit`, license, reproducible-delivery,
  `uv lock --check`, strict module-signature, release-version, wheel build, and
  Twine 7 artifact checks all passed.
- Code Review: `PASS_WITH_ADVISORY`, with zero errors, zero warnings, and 13
  informational findings. The infos are pre-existing long security-policy tests
  and the explicit license-policy evaluator; changing them would be unrelated
  cleanup and no blocking finding remains.
- Contract test: exit 0; it reported no modified contract-owned files and used
  its cache. The full repository suite independently exercised the repository.

**PR #693 pipeline regression (2026-08-28):**

- The first GitHub Requirements Evidence run failed with `acceptance-missing`
  even though its report retained the approved `d6ef...` mapping digest. Git
  represented one rewritten archived ledger as delete+add, so the workflow
  counted the deleted source as a second active change and omitted
  `--review-evidence`.
- The workflow regression first failed with an empty selected change while its
  partial-archive control passed. The initial completeness fix required one
  dated archive, no committed active tree, and a regular committed counterpart
  for every base-branch source path; the later P1 proof below strengthened that
  predicate to byte-identical one-to-one archive moves.
- The first exact local Block 2 run then reproduced the same false active-change
  classification in its branch selector. The existing mapped archive test
  failed before the branch selector fix and passed after it. All 32 workflow
  and pre-commit selector tests then passed.
- Final exact Block 2 passed at `test-authored` maturity with mapping digest
  `sha256:d6ef8ed0aa4623eaa8c3b74d6c85fd1a0efd91ac700c0ded7b9a8897626e20cf`;
  command/documentation checks passed and Code Review reported zero findings.
- The final post-P1 full-suite run collected 3,078 tests: 3,061 passed, ten
  expected tests skipped, and the only seven failures were controls that require
  the global module override to be absent. Rerunning both owning files without
  that override passed all 25 tests. The run used an isolated writable home, the
  pinned module roots where required, and the frozen Python for subprocesses.

**Archive-provenance P1 red proof (2026-08-28):**

- Two independent read-only reviews reproduced the same approval-redirection
  bypass. Deleting an approved active change and adding arbitrary regular files
  at the same relative paths below one dated archive made both completeness
  predicates treat the change as archived; the workflow then selected an
  unrelated singleton review-evidence record.
- The test-first command
  `hatch run pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_requirements_evidence_workflow_rejects_fabricated_archive_fallback tests/unit/scripts/test_requirements_evidence_pre_commit.py::test_pre_commit_selects_deleted_active_change_unless_fully_archived`
  failed both tests before the selector fix. The workflow returned zero and
  printed `unrelated-change`; the pre-commit contract did not yet require exact
  rename provenance.
- After the fix, the same command passed, followed by both owning files: 33
  tests passed. The malicious fixture remains attributed to its deleted active
  change and fails for missing change-local review evidence. The legitimate
  control moves every regular source file byte-for-byte to the same relative
  path in one dated archive; partial archives, rewritten files, extra files,
  split destinations, and ordinary in-change authoring exercise the opposite
  branches.
- The exact staged `scripts/pre-commit-quality-checks.sh all` pipeline passed
  with the immutable module fixture, `test-authored` maturity, approved mapping
  digest `sha256:d6ef8ed0aa4623eaa8c3b74d6c85fd1a0efd91ac700c0ded7b9a8897626e20cf`,
  workflow lint, changed-file typing/lint, command/docs contracts, and zero Code
  Review findings. Live frozen audits reported no unreviewed vulnerabilities in
  either lock; dependency trust, reproducible inputs, license, version/lock
  parity, module signatures, Bandit, wheel build, and Twine validation passed.

**Import-time plugin namespace mutation review proof (2026-08-28):**

- The review challenge added five test-first module-scope bindings using
  `globals().__setitem__`, keyword and mapping forms of `globals().update`, an
  unresolved update mapping, and `exec`. The focused parametrized selector
  collected nine cases and exited 1 before implementation: the four existing
  direct-binding controls passed and all five namespace-mutator cases failed
  because no `ValueError` was raised.
- After the fail-closed import-time call analysis was added, both owning files
  passed: 58 tests, including legitimate controls for a statically unrelated
  module update and function-local `exec`. Strict basedpyright validation of
  the implementation and both test files completed with zero errors, warnings,
  or notes; the authority test now uses a typed protocol instead of a
  module-wide unknown-member suppression.

**Executable archive compatibility review proof (2026-08-28):**

- The two existing positive native-archive selectors were strengthened so one
  byte-identical source and destination uses regular-file mode `100755`. Before
  implementation, both selectors failed: the workflow omitted the newly
  authored active change and the staged selector incorrectly retained the
  completely archived change.
- After both mirrored archive predicates accepted mode `100755` while requiring
  the destination mode to equal the source mode, both selectors passed. The
  existing controls continue to reject symlinks, fabricated content, partial
  archives, extra files, split destinations, and non-archive authoring.

## Final verification

- Product-owner approval is retained in
  `requirements-proof/review-evidence.json` for change-local mapping digest
  `sha256:d6ef8ed0aa4623eaa8c3b74d6c85fd1a0efd91ac700c0ded7b9a8897626e20cf`.
- The final staged Requirements delivery gate passed at `test-authored`
  maturity with no findings. Test execution is proven separately by the
  ordered focused and full-suite evidence above.
- Protected GitHub PR/release gates remain pending on the follow-up commit and
  required review.
