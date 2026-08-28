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

**Review-red bootstrap branch binding proof (2026-08-28):**

- Signed test-only commit `2f5cb18c66b133a09a24234c982d2366f3de07d4`
  was created from exact dev baseline
  `3ea3d9b4492ade6ec5683fac83c5b5090b0cb547`. It changes only the approved
  OpenSpec bundle and seven mapped test files; all ten mapped selectors fail
  against the baseline.
- Draft evidence PR #694 retained Requirements run `33124192051`, whose bounded
  report passed at `red` maturity with all ten selectors, no findings, the
  expected base commit, and immutable artifact digest
  `sha256:518065784e6fcccd5aba2f39c94c4baeafc46998a8cb00debf9f69070f2c404a`.
  The draft PR was closed without merge after the signed red commit became a
  no-tree-change second parent of PR #693.
- A test-first authority challenge changed only the retained run branch while
  keeping the final PR branch bound separately. Before implementation, the
  explicit distinct-branch acceptance selector failed and its unbound-branch
  control passed. After the authority record gained an explicit `red_branch`
  binding with backward-compatible same-branch behavior, all 13 authority
  tests passed and strict basedpyright reported zero findings.

**Issue #692 bootstrap authority workflow proof (2026-08-28):**

- Repository-member comment `5448719352` was unedited and matched the approved
  authority payload byte-for-byte. The local authority validator accepted its
  signed red commit, failed red workflow run, immutable artifact metadata, all
  three artifact-file digests, distinct red branch, final branch, and ancestry.
- Test-first workflow coverage failed in two selectors before implementation:
  the shared issue argument was still hard-coded to issue #689 and no #692
  ledger/run/comment binding existed. The existing #689 and new #692 contracts
  pass after selecting immutable per-change constants and using the shared
  validated issue argument.

**Post-authority final verification (2026-08-28):**

- The focused authority, delivery-workflow, provenance, pre-commit, and trusted
  green-check suite passed 146 tests. The full suite's mutually exclusive
  module-discovery environments were verified separately: 2,978 tests passed
  in the core environment; all 129 owning tests for environment-only failures
  passed with a hermetic home and frozen interpreter path; and all seven
  module-import controls passed against the immutable companion fixture.
- The exact staged quality pipeline passed at approved `test-authored` mapping
  digest `sha256:d6ef8ed0aa4623eaa8c3b74d6c85fd1a0efd91ac700c0ded7b9a8897626e20cf`,
  including workflow lint, changed-file typing and linting, Requirements
  evidence, command/documentation contracts, and Code Review with zero
  findings. Strict OpenSpec validation and repository-wide Ruff,
  BasedPyright, and safe-write gates also passed.
- Both frozen pip-audit gates found no unreviewed vulnerabilities. Semgrep
  1.175.0 and Bandit found zero findings; dependency trust, reproducible
  delivery, version parity, and primary plus isolated Code Review license
  scopes passed. The locked `0.55.2` wheel built without isolation and Twine
  7.0.0 accepted its package metadata.

**Final review-finding red proof (2026-08-28):**

- The computed-key and class-body plugin challenge first collected 14 focused
  cases and exited 1 with four failures: both end-to-end histories accepted a
  post-red plugin change, and both direct parser controls omitted the active
  binding. Ten literal, namespace-mutator, and local-scope controls passed.
- The first candidate closed those direct forms, but the required independent
  bypass/regression review reproduced indirect class-body mutation through
  `eval`, `getattr(globals(), "update")`, and an `exec` alias, plus a legitimate
  unconsumed generator body that was incorrectly treated as import-time code.
  The added 26-case challenge exited 1 with five failures before the shared
  boundary was corrected; 21 controls passed.
- The Code Review dependency-boundary investigation proved that stale input
  binding was caught later by reproducibility CI, while a blocked package found
  only in the isolated review lock passed the native dependency-trust gate.
  Four test-first isolated-graph selectors all failed before implementation.
- The one-cycle independent trust-fix review then reproduced PEP 440-equivalent
  `pycparser==v3.0` and `pycparser==03.0` pins accepted by pip but omitted by the
  string comparison. The six-spelling test exited 1 with those two forms and
  the equivalent zero-epoch form failing; the three existing spellings passed.

**Final review-finding green proof (2026-08-28):**

- The provenance scanner now fails closed on computed namespace keys and on
  import-time class code that exposes `globals`, `exec`, or `eval`, while
  retaining ordinary class-local bindings, function/method bodies, and the
  deferred body of an unconsumed class-attribute generator. All 26 focused
  plugin cases and all 57 provenance tests passed.
- The standard-library pre-install trust checker now verifies the exact Code
  Review input digest, parses every isolated exact pin fail-closed, and applies
  the blocked-release, prohibited-wheel, and security-floor policy to both
  frozen graphs. Numeric PEP 440 release components normalize the `v` prefix,
  leading zeroes, and zero epoch. All 22 dependency-trust tests passed.
- The combined authority, delivery, provenance, staged-index, workflow,
  producer, and dependency-trust set passed 173 tests. Repository-wide strict
  basedpyright reported zero errors, warnings, or notes; Ruff and strict
  OpenSpec validation passed. The approved Requirements mapping and review
  evidence were not modified. The final exact staged pipeline then passed at
  `test-authored` maturity with zero Code Review findings and no contract-input
  changes requiring a contract-suite rerun.
- The final core-environment suite passed 2,997 tests with 36 skips and the same
  five companion-package import failures expected when module roots are absent;
  all seven owning controls passed against immutable fixture commit
  `69f075819be5e1ceca1446b026b0417f19e584ca`. Both frozen pip-audit runs,
  dependency trust, reproducible delivery, focused Semgrep, and focused Bandit
  passed with no findings or unreviewed vulnerabilities.

**Final-head namespace-alias review proof (2026-08-28):**

- Fresh review of commit `4921ca0086385885c82e1b4fb9255763e4dbe635`
  identified a module-namespace alias bypass and an over-broad rejection of
  read-only class-body `globals()` access. The expanded 24-case focused
  challenge exited 1 before implementation with seven failures and 17 passing
  controls: object aliases from `globals()`, `locals()`, and `vars()`, a chained
  alias, a namespace-factory alias, `getattr(..., "update")`, and an `exec`
  alias bypassed discovery, while the legitimate read-only class case failed.
- The scanner now resolves namespace-factory, namespace-object, and dynamic-
  execution aliases within the applicable import-time scope. It applies the
  existing key-aware mutation policy through those aliases and `getattr`, while
  permitting read-only `get`, subscript, and read-only `getattr` access.
- The same focused challenge passed all 24 cases after implementation. The full
  provenance suite passed all 65 tests, strict BasedPyright reported zero
  errors, warnings, or notes, and Ruff lint passed before formatting the one
  changed source file.
- The expanded owning governance/security set passed all 282 tests. The final
  core-environment suite passed 3,006 tests with 35 skips and only the same five
  companion-package import failures expected when module roots are absent. The
  five import controls and two networked runtime controls then passed against
  immutable fixture commit `69f075819be5e1ceca1446b026b0417f19e584ca`;
  the runtime controls required PyPI access only inside their temporary install
  environments. Code Review reported zero findings after the alias propagation
  helper was split below its complexity threshold.
- Both final frozen vulnerability audits passed with no unreviewed findings. A
  clean hash-locked primary environment replaced its venv bootstrap pip 26.1.2
  with locked pip 26.2.1 and installed MCP 1.29.0, Semgrep 1.175.0, and Twine
  7.0.0; the primary plus isolated Code Review license scopes then passed with
  zero violations. The exact staged pre-commit pipeline passed at
  `test-authored` maturity with zero Code Review findings and no contract-input
  change requiring a contract-suite rerun.

**Final-head per-pin hash review proof (2026-08-28):**

- CodeRabbit review of signed commit
  `1f0160d1e1cc59c9837a16db773626123d9cd059` identified that the
  standard-library trust parser ignored hash continuations without requiring
  one for every exact Code Review pin. The missing-hash and malformed-hash
  selectors both failed before implementation while the existing 22 trust
  controls remained available.
- The parser now associates valid 64-hex SHA-256 continuations with the current
  exact pin and reports every package lacking a valid digest. Both focused red
  selectors and all 24 dependency-trust tests pass after implementation; the
  checker still passes under `python -S`, and strict changed-file BasedPyright,
  Ruff lint, and formatting are clean. The combined owning governance/security
  set passes all 284 tests, and the changed trust checker plus its tests produce
  zero Code Review findings.

**Final-head qualified-executor and compound-alias review proof (2026-08-28):**

- Fresh Codex review of signed commit
  `87f9bd636c079fe522e752bf4c6f25ed3ffbcaba` identified qualified built-in
  dynamic execution and compound namespace bindings as two remaining ways to
  create an active module-level `pytest_plugins` binding without adding its
  plugin to retained-proof inputs. The first focused red run failed eight cases
  with 27 controls passing: `builtins.exec`/`eval`, their import aliases, loop,
  destructuring, and eager-comprehension namespace aliases all reproduced.
- Independent read-only boundary validation against the exact signed head
  confirmed both P2 findings by comparing accepted static discovery with
  runtime module mutation. It also identified context-manager and match
  bindings, compound executor aliases, enclosing-module aliases used by class
  bodies, and `__builtins__`/`__import__("builtins")` lookup as adjacent forms.
  The incremental red run failed six added cases with 35 controls passing.
- The scanner now tracks qualified built-in executors and applies scoped,
  position-preserving alias propagation to assignments, loops, eager
  comprehensions, context managers, match captures, and class bodies. It does
  not leak comprehension aliases into later module statements or treat an
  unrelated positional target as the module namespace.
- The final provenance suite passes all 84 cases, including read-only access,
  ordinary mappings, positional destructuring, later shadowing, function-body,
  deferred-generator, and comprehension-target controls. Strict changed-file
  BasedPyright and Ruff pass, and Code Review reports zero findings. The full
  changed-scope governance/security set passes all 303 tests with the writable
  UV cache and immutable modules fixture, and strict OpenSpec validation passes.

**Final-head detached-hash review proof (2026-08-28):**

- Codex review of signed commit
  `87f9bd636c079fe522e752bf4c6f25ed3ffbcaba` identified that a valid
  standalone hash line could be credited to the preceding package even when
  that pin lacked a continuation marker. The exact detached-hash selector
  failed before implementation because the trust checker returned no errors.
- The parser now retains package state only across an explicit logical-line
  continuation, rejects an unattached hash line, and still reports the package
  as missing a valid attached digest. The focused selector and all 25
  dependency-trust tests pass; the checker passes under `python -S`, and strict
  changed-file typing, Ruff, and formatting are clean. The expanded changed-
  scope set passes all 304 tests, strict OpenSpec validation passes, and Code
  Review reports zero findings after the parser branches were split below the
  repository complexity thresholds.

**Final-head statement-order and mapping-capture review proof (2026-08-28):**

- Codex review of signed commit
  `bb44c15b988c78bd0a2b55147747de8d96cdf667` identified aliases of the
  imported `builtins` owner, mapping-pattern namespace captures, and an
  add-only alias false positive after definite shadowing. Independent
  read-only validation against exact head
  `a872a36fc91aa34ce3bb08dafcc8ccbb75add9e5` reproduced the two retained-proof
  bypasses and the compatibility regression by comparing static discovery
  with import-time module mutation.
- The first focused red run failed seven cases and passed three controls:
  direct and chained builtins-owner aliases plus direct, reordered, and nested
  mapping captures were silently accepted, while a definitely shadowed
  ordinary alias was rejected. An adjacent statement-order challenge then
  failed four cases for conditional re-aliasing and names that persist after
  `for`, `with`, and `match`; a final mapping-unpack selector remained red after
  the initial implementation.
- The scanner now propagates imported-builtins owner authority, correlates
  literal mapping keys recursively, uses a distinct unresolved-key sentinel,
  and conservatively inspects dictionary-unpack values without treating
  `**rest` as the original namespace. It merges persistent compound bindings
  only for subsequent statements and permits a definite ordinary shadow only
  when no intervening uncertain path can restore authority. Comprehension
  targets remain local.
- The final focused set passes all 17 cases and the full provenance suite passes
  all 100 cases. Controls cover ordinary and `None`-key mapping values,
  copied-rest mutation, mutation before shadow, shadow then re-alias,
  conditional shadow/re-alias, builtins-owner shadow, and non-leaking
  comprehension targets. Strict changed-file BasedPyright reports zero errors,
  warnings, or notes; Ruff lint and formatting pass; and strict OpenSpec
  validation passes.
- The complete changed-scope governance/security set passes all 320 tests with
  the writable UV cache and immutable modules fixture. Pinned Semgrep 1.175.0
  ran six focused SAST rules over the changed validator with zero findings, and
  Bandit reported no medium/high findings. The exact staged Code Review surface
  reports zero findings after the alias helpers were split below the clean-code
  complexity and nesting thresholds.
- Product owner `djm81` approved the refreshed `test-authored` Requirements
  mapping at
  `sha256:ee1db17944ae22c4f127f5e0a0dcae8f7237c62b4cd98abde246088c7e2053c9`
  on 2026-08-28 after the final security scenarios were mapped.

**Final-head logical-line and augmented-union review proof (2026-08-28):**

- Codex review of signed commit
  `a872a36fc91aa34ce3bb08dafcc8ccbb75add9e5` identified two additional
  checker/runtime mismatches. A blank or comment-only line did not terminate
  the dependency parser's package state as it does pip's logical requirement,
  and `namespace = globals(); namespace |= {...}` could create an active
  `pytest_plugins` binding without invalidating retained proof.
- Independent read-only reviews reproduced both findings against exact signed
  head `c518b9fd72b2fb55408498feb02c449b5a5f112c`. Pip 26.2.1 rejected both
  interrupted hash forms, while the dependency-trust checker accepted them;
  the provenance scanner returned no plugins for the augmented union while
  Python mutated module globals at import time. The namespace bypass also
  reproduced in a class body and was rated medium severity.
- After adding the OpenSpec scenarios and tests, the focused pre-implementation
  run failed four cases with 38 controls passing: two interrupted hash forms,
  the module-scope augmented union, and its combined compatibility challenge.
  No implementation changed before this red evidence was captured.
- The dependency parser now clears continuation state at blank and comment-only
  physical lines. The provenance scanner rejects a key-relevant `|=` operation
  through a live active-namespace alias at module or import-time class scope,
  while preserving ordinary mappings, unrelated literal keys, definite
  shadows, and fail-closed conditional re-aliasing.
- The post-implementation focused challenge passes all 53 cases, including
  both pip-aligned interruption cases, module and class bypasses, and adjacent
  compatibility controls.
- The complete owning governance/security set passes all 325 tests. Strict
  BasedPyright, Ruff, OpenSpec validation, the standard-library-only trust
  checker control, pinned Semgrep 1.175.0 over six focused rules, and Bandit at
  medium/high severity all pass with zero findings. The exact staged pipeline
  initially reported one complexity warning and then one redundant-branch info;
  both were refactored without changing behavior, and the final Code Review
  result is `PASS` with zero findings.
