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

**Final-head extended-binding review proof (2026-08-28):**

- Complete review-thread readback after signed commit
  `05de7b725172888b78a0ffddbbf381a321549680` surfaced three earlier Codex
  comments that had not appeared in the prior unresolved-thread result:
  starred destructuring, non-literal mapping-pattern subjects, and `getattr`
  over `__import__("builtins")`. Direct scanner/runtime comparison reproduced
  all three: static discovery returned no plugins while Python created the
  active module binding.
- Three independent read-only reviews validated the exact-head findings and
  traced the omission through retained-proof freshness. The starred and
  mapping cases were rated medium/P2. The imported-builtins getter was rated
  high/P1 after a temporary Git history reproduced acceptance of stale proof;
  its preconditions remain contributor-controlled test support plus a changed
  plugin, rather than independent merge authority.
- The initial focused red run failed six cases with 46 controls passing. The
  expanded adjacent challenge failed 12 cases with the same 46 controls:
  prefix, suffix, nested, and starred-container namespace authority; literal
  and computed imported-builtins getters, an imported-owner alias, and a class
  body; plus keyword, pair-list, generic-call, and prebound mapping subjects.
- Extended-unpacking analysis now correlates fixed targets from both ends and
  retains authority inside the starred container. Simple `dict(...)` subjects
  are correlated by literal key; unprovable non-rest mapping captures fail
  closed. Literal and computed executor access plus aliases of a direct
  `__import__("builtins")` owner retain dynamic-execution authority.
- The final challenge passes all 58 cases and the parametrized full provenance
  suite passes all 125. Controls preserve ordinary starred values, positionally unrelated
  namespace values, simple safe `dict(...)` captures, copied mapping rests,
  definite shadows, and non-executor imported-builtins attributes. The full
  owning governance/security set passes all 347 tests. Strict OpenSpec,
  BasedPyright, Ruff, pinned Semgrep over six rules, and Bandit medium/high all
  pass with zero findings.
- The exact staged Code Review initially rejected the candidate for one mapping
  parser complexity error, two helper/test-shape warnings, and one info. The
  parser, executor-owner propagation, and compatibility controls were split
  into focused helpers/parameters; the final staged review passes with zero
  findings and no suppression.

**Final namespace-authority boundary proof (2026-08-28):**

- An independent read-only review of signed commit
  `15893404fad641aabb72c367510c5a0439641b79` confirmed the three preceding
  review findings no longer reproduced, then identified adjacent authority
  paths through nested starred containers, bound namespace-mutator methods,
  aliases of `__import__`, and imported-builtins module mappings. It also
  confirmed that a module-level generator over an empty outer iterable was a
  compatibility false positive, while mutation in the outer iterable remained
  an eager import-time operation.
- The pre-implementation challenge ran 59 cases: ten bypass/compatibility cases
  failed and 49 adjacent controls passed. Exact scanner/runtime comparison
  showed every bypass created `pytest_plugins`; the empty generator left the
  binding absent. The expanded mapped selector also failed against the signed
  ancestor before implementation.
- Namespace authority now survives constant-key container lookup and bound
  aliases of `update`, `setdefault`, `__setitem__`, and `__ior__`, including
  chained and class-body aliases. Import-factory authority survives aliases and
  computed module names, and executor access through `__dict__` or `vars(...)`
  fails closed. Only a generator with a statically empty outer list, tuple, set,
  or mapping skips deferred clauses; its outer iterable is still inspected.
- The focused challenge passes all 59 cases and the full provenance suite
  passes all 116 collected tests after the mapped selector consolidation.
  Controls preserve ordinary dictionary methods, uninvoked and
  unrelated-key namespace method aliases, definite method shadowing, ordinary
  imports, and empty-generator consumption. Ruff and strict BasedPyright pass
  with zero findings.
- The first protected retained-red run exposed three uncollected parametrized
  selectors and one compatibility selector that passed before implementation.
  The test-only branch was corrected without implementation changes: all four
  mapped selectors now collect and fail against merge base
  `3ea3d9b4492ade6ec5683fac83c5b5090b0cb547`, while the implementation branch
  passes the same four selectors.
- Protected Requirements run `33165899623` at signed test-only commit
  `709b085c57a05e221936065367967fa130344218` records `required_maturity=red`,
  `observed_maturity=red`, `delivery_status=failing-first-proven`, and no gate
  findings. Its JUnit proof contains 13 collected failing selectors, including
  `RELEASE-692-PYTEST-S01` through `S04`, with no `uncollected-selector` or
  `red-proof-passed-not-failed` finding. The source mapping remains the approved
  `sha256:ee1db17944ae22c4f127f5e0a0dcae8f7237c62b4cd98abde246088c7e2053c9`;
  the finalized combined mapping is the separately approved
  `sha256:a21fb7c1936f400ab5f17c286d382adecf1e0513b849f5a3aca1d64f1284e00a`.
- Protected final Requirements run `33166767525` at signed commit
  `bedc9e05b590cbe307463e9acec3ed99bbb52ce7` consumed that retained artifact
  and passed with `required_maturity=verified`, `observed_maturity=verified`,
  `implementation_evidence=passing-after-red-proven`, `proof_basis=red-junit`,
  and zero Requirements findings. The final mapping is
  `sha256:a21fb7c1936f400ab5f17c286d382adecf1e0513b849f5a3aca1d64f1284e00a`
  with plan digest
  `sha256:69132dab4dbb8e97d1df4f96b882d5cd8cb5672b7f8a54b017adc8fd620883db`.
- The final contextual Code Review verdict is `PASS`. Its only recommendations
  are 12 `ai-bloat.loc-vs-complexity` infos in signing-test functions last
  changed between February and April 2026. Git diff against `origin/dev`
  confirms #692 changes only the cache-boundary test at line 1222 of that file;
  none of the 12 reported functions is touched. They are preserved as a narrow
  non-regression exception because refactoring unrelated historical tests would
  expand the security patch and invalidate the authenticated red test-file
  digest. The changed #692 Code Review surface has zero findings.
- A complete unresolved-thread readback then exposed one additional applicable
  bypass from #693: `runtime = __import__("builtins")` followed by a computed
  `getattr(runtime, executor)` call. Exact scanner/runtime reproduction accepted
  the source while Python created the active plugin binding. The new S02 source
  was placed first so its pre-implementation failure is unambiguous.
- Protected Requirements run `33167193992` at signed test-only commit
  `ebb6d12177ae81e93a16b15fc74431bb0ceb12b9` records red maturity,
  `failing-first-proven`, the approved combined mapping and plan digests, and
  zero gate findings. The retained S02 failure is collected and its test-file
  digest is
  `sha256:8269de663663700c54b63de0f382ca06f63224d6f69985f36caf06e87abb1d73`.
- Computed `getattr` attributes now fail closed for every tracked dynamic-
  executor owner, including imported-builtins aliases; literal non-executor
  attributes remain compatible. No mapped test file changes after the retained
  red source.
- A fresh exact-head Codex review of `1161a52afee70046c90772f34d8adbc3b892a1ee`
  found that a builtins owner nested in a container still lost authority:
  `owners = (builtins,)` followed by `getattr(owners[0], "exec")` was accepted,
  while Python created the active `pytest_plugins` binding. The focused S05
  regression run against the test-only change exited 1 with one collected test
  and `Failed: DID NOT RAISE ValueError`, preserving failing-first evidence
  before the implementation is changed.
- Independent read-only boundary review reproduced the same omission for direct
  `.exec`/`.eval`, list/dictionary/nested containers, computed indices,
  extracted aliases, conditional and helper/lambda-returned owners, and class
  bodies. The S05 regression corpus now covers representative tuple, nested
  mapping, helper, lambda, computed-attribute, and class-body paths; it remains
  red against the unchanged production scanner.
- The implementation closes the unresolved-owner class rather than enumerating
  container syntax: any import-time `.exec`/`.eval` access is treated as dynamic
  execution, and `getattr` fails closed for `exec`, `eval`, or a non-literal
  attribute regardless of how its owner was computed. Literal non-executor
  attributes such as the container-carried `builtins.print` control remain
  accepted. The focused P1/control pair and all 117 provenance tests pass. Ruff
  and an authoritative-project BasedPyright run over the changed scanner and
  provenance test report zero errors, warnings, or information findings; the
  full repository lint gate also exits zero.
- Protected Requirements run `33168438206` correctly rejected reuse of the
  prior one-time bootstrap namespace before executing proof. The P1 corpus is
  therefore isolated as new mapped selector `RELEASE-692-PYTEST-S05`; its fresh
  mapping requires product-owner acceptance and a new protected red source
  rather than rewriting or reusing any prior evidence.
- The staged released-fixture gate derives fresh source mapping
  `sha256:ad6eb0b285116476dfcf12a4444755f6d271df34d04ecdd9a076038e0e9bfe56`,
  combined mapping
  `sha256:ce0d01e3e955956ef3996903c06f833e4dd4dea41ba0f4429e031c36be540d0b`,
  and plan digest
  `sha256:d34f6c1fe780ff4b31a5511ef8bcf901a53fb5edbc21c7c20f823b71d62afbc9`.
  Its initial `acceptance-stale` result was the required pre-approval control.
- The product owner approved the S05 source mapping at
  `sha256:ad6eb0b285116476dfcf12a4444755f6d271df34d04ecdd9a076038e0e9bfe56`
  and the combined mapping at
  `sha256:ce0d01e3e955956ef3996903c06f833e4dd4dea41ba0f4429e031c36be540d0b`.
  Protected Requirements run `33183259929` at production-free test source
  `f9aa2cb8e2060347bb2d741a91265bec493a3086` then recorded
  `required_maturity=red`, `observed_maturity=red`,
  `delivery_status=failing-first-proven`, and
  `implementation_evidence=failing-first-proven` with zero findings. Its JUnit
  artifact contains 14 collected tests and 14 failures, and binds the S05
  provenance test file at
  `sha256:69bb3ba4efd506c2cd43dbba0d3d3a7a434720bcf599e02998e2d2f4b0fe3c51`.
  Earlier runs `33168438206`, `33182490771`, and `33183027534` are diagnostic
  only: they respectively proved namespace non-reuse, rejected a
  production-descendant source, and exposed an incomplete parametrized base
  selector before the exact selector was corrected.

## S06 and amendment-cycle review follow-up (2026-08-28)

- PR #698 review comments `3881744895` and `3881744901` exposed an
  unresolved-owner fail-open bypass and an over-broad executor-method false
  positive. The test-only S06 corpus exercises container, helper, conditional,
  class, loop, named-executor, and lambda-wrapper cases while retaining inert
  `types.SimpleNamespace` controls.
- The existing Requirements workflow also proved unable to start a second
  red-to-green behavior cycle after an earlier verified PR head. Its maturity
  selection and red provenance both use the complete `origin/dev...HEAD`
  history, so any earlier production commit prevents a later tests-only review
  amendment from retaining red proof.
- Independent read-only review rejected a raw cycle-base override and a
  side-branch merge workaround. Amendment cycles must form a linear, merge-free
  chain from an externally authenticated prior green head through red and final
  commits; otherwise independently authored production can be merged after a
  red parent and appear ordered.
- Against the unchanged `origin/dev` implementation, the focused run collected
  four tests: the cycle-authority test, workflow-wiring test, and S06 hostile
  corpus failed; the statically inert executor-owner control passed. No
  governed production file was changed.
- Product-owner approval is recorded at
  `https://github.com/nold-ai/specfact-cli/issues/692#issuecomment-5454769499`
  for source mapping
  `sha256:738450020e9849a4d0d5819b43f3266e48a65cf0e48a5786cd39880e048bb7ff`.
  The authenticated released-fixture gate passed at `test-authored` maturity
  with zero findings, combined mapping
  `sha256:d4e3b9201b508eadfe5d6b1079f71f332f51e494786dc8ab97631307d895d1bf`,
  and plan digest
  `sha256:e4fce5f4a860ba54ff63503580d1b68749cfad407c20cddf40a954964f294c67`.
- The exact amendment bootstrap was subsequently approved at
  `https://github.com/nold-ai/specfact-cli/issues/692#issuecomment-5454967690`.
  It authenticates failed Requirements run `33188887973` and artifact
  `9692878707` against prior successful run `33183894104` and artifact
  `9690876746`, then normalizes exactly 3 failed selectors while preserving
  the 14 passing selectors from the approved raw report.
- The workflow now re-fetches the prior green run and artifact, validates their
  repository, PR, branch, commit, digest, and linear-history bindings, and can
  recover an authenticated retained-red artifact from an earlier failed run on
  the same non-default PR. Raw branch input never becomes cycle authority.
- The final security regression surface passes all 176 focused provenance and
  workflow tests. The exact module-backed code-review gate reports no findings;
  the independent post-patch bypass/regression review found no surviving
  computed-owner, builtins-mapping, external-setter, recursive `__call__`, or
  amendment-cycle bypass and confirmed the inert controls remain accepted.
- Signed implementation commit `ed2c5206d8661f30e6ee9d7a2aa17c7f80f737b3`
  was pushed to PR #698. All 11 review threads received fix or false-positive
  evidence and were resolved; the final staged code-review hook reported zero
  findings.

## Final PR review follow-up (2026-08-29)

- A fresh unresolved-thread readback exposed three later comments:
  `3884303092` identified module-object `pytest_plugins` writes,
  `3884316664` identified unconditional empty cycle-authority forwarding, and
  `3884316676` identified missing runtime type checking on the two new command
  scripts.
- Before the scanner fix, the adjacent review regression accepted
  `sys.modules[__name__].pytest_plugins = (...)`; after the first direct-write
  fix it still accepted the same write through an assigned module alias. Direct
  attribute writes, direct `setattr`, and both alias forms now fail closed.
- Before the workflow fix, the adjacent contract test failed because the
  retained-red lookup always forwarded the empty cycle-authority output. It now
  conditionally constructs the argument array from an environment-bound output,
  so ordinary proof reuse omits the option while authenticated amendment cycles
  retain it.
- `requirements_amendment_bootstrap.py` and `requirements_cycle_base.py` now
  pair `@beartype` with their existing public entry-point contracts, matching
  the repository command convention and the adjacent proof scripts.
- The final focused provenance/workflow run passes all 156 tests. Ruff,
  BasedPyright, actionlint, and the exact module-backed Code Review pass with
  zero errors, warnings, or findings.
- CodeRabbit's completed-head review then identified method-form current-module
  lookup in comment `3884380830`. Before the fix, both the direct hostile/control
  pair and the full focused suite accepted `sys.modules.get(__name__)`; the
  unrelated constant-key control remained accepted. Direct `get`,
  `__getitem__`, and computed-key aliases now fail closed, the control still
  passes, and the complete 156-test set is green.
- Four subsequent completed-head comments identified two related authority
  gaps. Comment `3884421760` showed that a pull request could change the
  Requirements evidence workflow or proof scripts and then nominate its own
  successful commit as the next amendment-cycle authority. Comments
  `3884421765`, `3884421768`, and `3884429427` showed remaining active-module
  aliases through imported `sys`/`sys.modules`, qualified or imported
  `builtins.setattr`, and `sys.modules.setdefault`.
- The adjacent pre-implementation run collected two exact regressions and
  failed both: the scanner did not reject the imported `sys` alias, and cycle
  history accepted a candidate green commit that introduced its own evidence
  workflow. This preserves failing-first evidence without changing the three
  product-owner-approved Requirements test files.
- Cycle-base validation now rejects a candidate when the range from the trusted
  base changes the evidence authority itself: the Requirements workflow,
  frozen-Python setup action, pinned module fixture identity, or any
  `scripts/requirements_` command. Ordinary prior green product changes remain
  eligible, preserving the amendment-cycle use case while preventing the proof
  machinery from blessing itself.
- Namespace analysis now propagates imported and assigned `sys.modules`
  mappings, recognizes `get`, `__getitem__`, and `setdefault` current-module
  lookups, and propagates qualified, imported, and assigned `setattr` authority.
  An unrelated constant module key remains an accepted control.
- The final Requirements proof/evidence unit surface collected 173 tests:
  169 passed and four released-fixture-dependent tests skipped. Ruff and strict
  BasedPyright report zero errors, warnings, or notes on the changed surface;
  the exact pinned-module Code Review reports no findings.
- A final completed-head review opened P1 comments `3884506990`, `3884506993`,
  and `3884506997`. Exact failing-first controls showed that the generic green
  boundary still accepted changes to the installed `src/specfact_cli` package
  and `pyproject.toml`, and that provenance accepted module `__dict__`,
  `vars(module)`, and a directly invoked local global binder.
- The candidate-green producer boundary now covers the installed SpecFact CLI,
  project and frozen dependency inputs, Requirements inputs and commands, the
  workflow setup, and the pinned module fixture. The existing ordinary
  `src/runtime.py` compatibility fixture remains eligible because it cannot
  produce Requirements evidence.
- Namespace authority now propagates through module `__dict__` and
  `vars(module)`. A local function or class remains deferred when merely
  defined, but a direct import-time invocation is inspected and rejected when
  its body can bind the module plugin global. Existing inert namespace and
  executor controls remain accepted.
- The expanded proof/evidence surface collected 175 tests: 171 passed and four
  released-fixture-dependent tests skipped. Ruff and strict BasedPyright report
  zero errors, warnings, or notes, and the exact pinned-module Code Review
  reports no findings.

## 2026-08-29 external amendment authority and final P1 regressions

- Approval: the product owner approved one expiring external amendment-authority capability bound to unedited MEMBER comment `5454967690` and its exact PR `#698` green/red commits, trees, runs, artifacts, and digests. The approval permits bypassing only the self-authored evidence-producer predicate; all live revalidation and proof-boundary checks remain mandatory.
- Spec-first: added scenarios for the exact external capability, module-level `__getattr__` plugin synthesis, and post-red pytest-configuration freshness.
- Failing-before command: `python -m pytest -q tests/unit/scripts/test_requirements_cycle_base_review_regressions.py tests/unit/scripts/test_requirements_proof_provenance_review_regressions.py tests/unit/workflows/test_requirements_evidence_amendment_review_regressions.py`.
- Failing-before result: `4 failed, 6 passed` on Python `3.12.13` / pytest `9.1.1`. Missing behavior was independently exposed as: no common history predicate separated from self-authorship; a newly added `pytest.ini` was accepted; module `__getattr__` synthesis was accepted; and the PR bootstrap did not emit or bind an external authority receipt.
- Independent post-patch bypass review identified two additional P1 variants. The added regressions failed before implementation: assignment-form module `__getattr__` was accepted, and a red-time repository plugin loaded through compact pytest `-pMODULE` syntax could change after red without returning `stale-red-proof` (`2 failed, 4 passed`). The same regression covers pytest's `-p=MODULE` spelling.
- Passing-after result: the adjacent authorization and bypass surface passes all `12` tests. The broader Requirements proof and workflow surface passes `211` tests with four released-fixture-dependent skips. Compact pytest plugin options now retain repository plugin inputs, and every module-scope binding of `__getattr__` fails closed while existing inert controls remain accepted.
- Live capability controls passed against comment `5454967690`: the exact current-head bootstrap, red-source bind, and final reuse paths accepted the digest-bound receipt; tampered, edited, and expired copies were each rejected. The normalized capability digest is `sha256:bb853e56145dfc7dfb5c30a690d63539cc09765a2287d8527c5c93ee305ad4eb`.
- Final local gates: strict OpenSpec validation, Ruff formatting/lint, actionlint, strict changed-surface BasedPyright (`0` errors and `0` warnings), frozen delivery reproducibility, `uv lock --check`, Bandit (no medium/high findings), Semgrep (`0` findings), and both frozen pip-audit graphs pass. The full sandboxed suite reached `3162 passed, 22 skipped`; its only two failures were unrelated local-home write restrictions for the uv cache and `~/.specfact/metadata.json`, while the affected Requirements surface remained green. Canonical repository-wide YAML lint still reports only the pre-existing Requirements 07/08 files outside this change; the changed workflow lint passes.
- The staged Code Review passed with two informational length heuristics reviewed as non-actionable. `_external_validator_command` intentionally keeps every security-bound CLI argument explicit and auditable rather than hiding the exact capability binding in a generic mapper. `_initialize_bound_red_proof` keeps one cohesive fixture builder so each synthetic Git proof is created in the same order as production binding; splitting it would move rather than remove the setup and obscure the red-proof lifecycle. Neither advisory reports a correctness, warning-level, or clean-code regression.

## 2026-08-29 consolidated PR #698 security review red evidence

- The product owner accepted the final test-authored Requirements mapping in
  this task at
  `sha256:f65edb0a35692e7a13d48c3e1e998ceb55fa66e695221602095372e04f91c2a8`;
  the provider-neutral acceptance record references PR `#698`.
- Exact review range: `3ea3d9b4492ade6ec5683fac83c5b5090b0cb547...ca2543bd85fbc92911efdb60845580cc211a6889`.
- The completed independent security-diff review reported six medium-severity evidence-integrity findings: repository-root pytest shadowing; omitted core executor/plugin and `uv.lock`; omitted selected-input package initializers; omitted dynamic repository imports; and current-module `pytest_plugins` attribute binding. It rejected the `sitecustomize` hypothesis under the exact sanitized startup and rejected JUnit outcome confusion for this immutable approved artifact because its three selected failures exactly match its three raw JUnit failures.
- Workflow inspection also confirmed the operational amendment defect previously observed on PR #698: the one-time external bootstrap exits before ordinary cycle selection on every later head, so its successful externally authorized green cannot seed another review-driven red-to-green cycle.
- Spec-first validation: `openspec validate fix-release-promotion-security-gates --strict` passed before regression tests were added.
- Failing-before command:
  `hatch run pytest -q tests/unit/scripts/test_requirements_proof_executor.py::test_executor_accepts_existing_exact_selectors_and_uses_argument_array tests/unit/scripts/test_requirements_proof_executor.py::test_executor_uses_safe_path_before_resolving_installed_pytest tests/unit/scripts/test_requirements_proof_provenance_review_regressions.py::test_review_bypasses_fail_closed tests/unit/scripts/test_requirements_proof_provenance_review_regressions.py::test_dynamic_repository_imports_are_retained_or_fail_closed tests/unit/scripts/test_requirements_proof_provenance_review_regressions.py::test_core_proof_inputs_and_selected_package_initializers_are_retained tests/unit/scripts/test_requirements_cycle_base.py::test_cycle_base_accepts_self_authored_green_only_with_matching_external_authority_digest tests/unit/workflows/test_requirements_evidence_amendment_review_regressions.py::test_exact_external_amendment_bootstraps_later_generic_cycle_selection`.
- Failing-before result: `7 failed` on Python `3.12.13` / pytest `9.1.1`. The executor omitted `-P` and executed a root shadow; current-module writes and dynamic imports were accepted; selected package initialization and all three fixed producer inputs remained fresh; cycle-base validation had no exact external-authority digest input; and the workflow still exited before generic cycle selection.
- Legitimate controls retained for passing evidence: exact selectors and argument arrays, sanitized environment, installed pytest plus the explicit proof plugin, literal external dynamic imports, ordinary non-plugin object attributes, ordinary verified cycle bases, and every external authority live-validation/history check.
- The required fresh post-candidate bypass review rejected the first candidate
  with five residual findings: computed `getattr(importlib, "import_module")`
  loaders, the explicit proof plugin's `scripts/__init__.py`, loss of the external
  digest during ordinary authority revalidation, clobbering of the external red
  proof during failed-run probing, and rejection of a provably inert local object
  attribute.
- Follow-up spec/tests-first command selected the two provenance controls, the
  harness-input control, live cycle revalidation, cycle receipt serialization,
  and external fallback workflow contract. Before the follow-up implementation
  it collected six tests and failed all six on Python 3.12.13 / pytest 9.1.1.
- After the minimal follow-up, the same six tests pass. Literal and aliased
  computed loaders are retained, computed loader names fail closed, the fixed
  plugin package initializer is freshness-bound, only an empty unshadowed local
  class instance is accepted as an ordinary attribute owner, the exact external
  digest survives receipt/live validation, and the fixed external proof is kept
  separately then restored only for fallback.
- The independent exact-fix readback found two residual variants: callable and
  mapping wrappers around the importlib loader, and ordinary receipt reuse that
  forwarded a public external digest without independently re-fetching the
  expiring capability. The two adjacent tests failed before the second
  follow-up implementation and passed afterward.
- Loader discovery now canonically unwraps literal `__call__` selection and
  recognizes literal importlib namespace mapping lookups. Ordinary receipt
  reuse re-fetches the exact external comment/run/artifact set, executes the
  exact validator (including expiry), and compares the freshly derived receipt
  digest before forwarding it to live cycle validation.
- The same independent reviewer found a final namespace-mapping alias family:
  assigning `vars(importlib)` or `importlib.__dict__` to a local name, or using
  literal `get` / `__getitem__` selection, still omitted a dynamically imported
  repository helper. The expanded exact regression fails before the resolver
  update while the already-fixed direct forms remain passing.
- After the resolver update, the expanded regression passes. Importlib namespace
  aliases and literal `get` / `__getitem__` lookups now retain the helper, while
  computed mapping keys and computed mapping selectors fail closed.
- A further readback kept the boundary blocked because aliases and literal
  `__call__` wrappers of the mapping methods themselves still evaded tracking;
  the same regression was expanded with those positive forms and a computed-key
  negative control before the resolver dataflow was extended.
- The final expanded regression passes after tracking mapping-method aliases.
  Alias calls and literal `__call__` wrappers retain the repository helper, and
  computed keys through the alias fail closed.

## 2026-08-30 final PR #698 P1 remediation and V2 authority review

- The product owner published the expiring V2 amendment capability as unedited
  repository MEMBER comment `5464938148`. Live revalidation bound repository
  `nold-ai/specfact-cli`, issue `#692`, PR `#698`, branch
  `codex/692-computed-owner-red-proof-v2`, green commit/tree/run/artifact and
  digests, red commit/tree/run/artifact and digests, mapping/plan digests, and
  expiry `2026-09-05T22:00:00Z`. Its normalized authority digest is
  `sha256:1d5cb37f5e05c43f60503b934877c7edf3d1cfe97b90a9cf73783d141480c629`;
  the normalized JUnit digest is
  `sha256:d57683e5f68359c4cbdc03d331f3ba7a434307400e95bc5ef3ac11f9074937d`.
- Three unresolved completed-head PR comments were reproduced and reviewed:
  current-module imports (`3887445675`), dynamic import discovery
  (`3887669029`), and `object.__setattr__` namespace mutation (`3887669030`).
  Their hostile cases now fail closed while literal external imports and
  ordinary non-plugin attribute controls remain accepted.
- The review-authored object-mutation pair failed before implementation with
  one hostile acceptance and one legitimate passing control. After tracking
  current-module authority through direct/imported module lookups and external
  `setattr`/`__setattr__` forms, both cases pass.
- The independent full-diff review found an additional P1 import family:
  `builtins.__import__`, imported or assigned aliases, `getattr`, namespace
  mapping/method aliases, and literal `__call__` wrappers could omit a
  dynamically imported repository helper. The direct builtins case failed
  before implementation. Fixed-point loader discovery now retains every
  literal form and rejects computed loader/key ambiguity; the complete mapped
  family passes.
- The same independent review found that a candidate artifact could copy the
  public external-authority digest and authenticate a self-authored green
  without presenting the live-produced receipt. Before implementation, the
  digest-only candidate was accepted and the receipt argument was unsupported.
  Cycle-base validation now requires the exact receipt and rechecks its fixed
  locator, expiry, canonical digest, green/red roots and trees, ancestry and
  linear history, and candidate execution-proof bindings. Exact receipt reuse
  passes; digest-only, expired, wrong-comment, changed-tree, and changed
  execution-artifact variants fail.
- Amendment red selection is now derived from unique per-selector raw JUnit
  outcomes. Editable count/summary metadata cannot choose the authorized
  failing subset; missing, duplicate, relabeled, or non-failing selected cases
  fail closed.
- The final affected Requirements/security/workflow surface passes `182` tests;
  the exact receipt/tamper subset passes `6` tests. Ruff format/lint, strict
  changed-surface BasedPyright (`0` errors, warnings, or notes), actionlint, and
  strict OpenSpec validation pass. Repository YAML lint exits successfully and
  reports only inherited R07/R08 planning findings outside this change.
- The exact PR workflow full-suite command, with the immutable modules fixture
  exported exactly as CI does, passes `3189` tests with `10` fixture-dependent
  skips and `64%` aggregate coverage. Two Lark deprecation warnings originate
  in the frozen third-party environment; no changed-code warning is present.
- A formal immutable security diff scan reviewed all `17` generated
  security-sensitive items in range
  `3ea3d9b4492ade6ec5683fac83c5b5090b0cb547..27937eb070253ef5e933c827369fce3fb764fb40`.
  It validated five candidate classes and reported zero surviving findings.
  The exact candidate tree was
  `6a06c492268ab6bcd278807d5b16cd3d1db3b6dc`; advisory TAC status was unknown
  and did not gate the repository controls.
- The additional P1 regressions expand the frozen test-authored mapping from
  `25` to `30` cases. Its source mapping digest is
  `sha256:a63a34f67aac2e893580ffd8c98135b29358ad42cd41a78016725a6785485524`.
  The product owner accepted that exact digest in unedited repository MEMBER
  comment `5467009208` on issue `#692` at `2026-08-30T05:51:24Z`.
- The repository Code Review initially reported five remaining warning-level
  maintainability/type/contract findings after the P1 fixes. Behavior-preserving
  refactors grouped dynamic-loader alias state, external authority state, and
  live cycle payloads while preserving first-match alias precedence, fixed-point
  propagation, independent digest/receipt comparison, and every mapped test
  selector. The focused V2 and cycle/provenance regression set passes `19`
  tests; strict changed-surface BasedPyright reports zero errors, warnings, or
  notes; Ruff passes; and the final Code Review reports zero errors and zero
  warnings.
- Nine Code Review information-only length heuristics remain non-blocking. The
  external-validator command intentionally retains its explicit ordered argv as
  an auditable security allowlist; the test helpers remain cohesive around
  mapped security scenarios and do not change production control flow.
- An additional whole-PR scan (all Python paths changed from `dev`, rather than
  only this final amendment) reports `54` type-safety warnings, all for pytest
  symbols such as `mark`, `parametrize`, `raises`, `MonkeyPatch`, or `skip` in
  the isolated Code Review interpreter. The report contains zero errors and no
  production-code warning; repository BasedPyright resolves the same pytest
  symbols. These are tool-environment false positives, and adding pytest to the
  security-scoped isolated Code Review dependency graph solely to silence them
  would expand the patch and its trusted dependency surface.
- The post-refactor full suite produced `3187 passed` and `10 skipped` in the
  restricted environment; its only two failures were the expected denied PyPI
  DNS lookup and denied user-metadata fixture write. Rerunning exactly those two
  tests with normal network and home access passed both, yielding the same
  effective `3189 passed`, `10 skipped` result as the earlier clean run.

## 2026-08-30 authoritative current-dev rebase and red proof

- The earlier proof and review runs in this document remain useful historical
  reproduction evidence, but their candidate commits are superseded because
  protected `dev` advanced while PR #698 was under review. They are not the
  release baseline and must not be used to omit the final rebased gates.
- The authoritative parent is refreshed `origin/dev` commit
  `4fd96d6d804da70cc7ceca83b8adce21f7da561c`. This preserves the intervening
  planning merge from PR #685, module-scope correction from PR #700, and bundled
  module snapshot from PR #701.
- The authoritative spec/test-only red commit is
  `4300f6a08084b05d528748186328238c452bf065`. Its exact 30-case plan failed
  locally with `30 failed, 0 passed` before production changes were applied.
- The test-authored Requirements mapping has `30` cases, combined mapping
  digest `sha256:a86d87fe36bfb79d740788f849fed9a0c307aed7f46dcb48b6b59760e9664bb3`,
  and plan digest
  `sha256:4b15b245d26cc88ea4cfd49ddbf0c95f55fb3b5311d5df80e449491e2d0c9e24`.
  Its source approval remains the unedited repository MEMBER comment
  `5467009208` on issue #692, binding source digest
  `sha256:a63a34f67aac2e893580ffd8c98135b29358ad42cd41a78016725a6785485524`.
- GitHub Requirements run `33297150129`, job `99218679579`, failed at the
  intended red enforcement step against the exact red commit. Artifact
  `9727771400` was unexpired when downloaded and has digest
  `sha256:3264a201731703d9288cebcba8b4e3a242369eca7885b6c6bdaed15f31ad0c69`.
  The artifact's plan, report, summary, and JUnit digests are respectively
  `8d369db089c92e3caa66ea2bb5bcc7feacdb6f5b767e68c428ac1e5843ee4c1f`,
  `e96c03f0d36c16041661eccf98dfbb7be429c996df8a8b5e2e99bcb330949947`,
  `c17464b8cc296613896045b3cc80121f4c9f783b3f6c42dc207738769d8db8ae`,
  and `2359b643154a904aee71c98b76d25aa80c1b6e5f3033f92a810b0fd5818be2e7`.
  The report binds the exact source commit, all 30 selectors, and the mapping
  and plan digests above, with no provenance findings.
- The green implementation and all release/security gates must run as a linear
  descendant of this red commit. No earlier reconstructed or bootstrap commit
  is an acceptable final proof substitute.

## 2026-08-30 completed-head PR review amendment red proof

- Two unresolved P1 review comments on the completed red head were reproduced
  against pushed green commit `22041cacdd8c34f26f09bccc91499e51e21545a8`:
  comment `3888913273` demonstrated an import-time local decorator that binds
  `pytest_plugins`, and comment `3888913276` demonstrated an imported callable
  receiving the active module namespace through `globals()`.
- Both cases are already governed by the accepted scenario “A higher-order
  callable performs a plugin namespace mutation” and its exact S17 selector;
  the OpenSpec sidecar and approved source mapping digest
  `sha256:0829a9ce09ef987f7f9253c0d9427824c49d31672743a041ba2cb247ec097b9b`
  remain unchanged.
- Failing-before command:
  `uv run --locked --no-sync pytest -q tests/unit/scripts/test_requirements_proof_provenance_review_regressions_v2.py::test_higher_order_plugin_namespace_mutator_fails_closed`.
- Failing-before result: one selected test failed while reporting both hostile
  sources as accepted. The five earlier higher-order namespace cases remained
  rejected, proving this is a two-case amendment rather than a regression in
  the already-pushed fix.
- The first implementation candidate passed both reported P1 sources and the
  legitimate namespace controls. An adjacent manual challenge then proved that
  assigning the local binder to an alias and using that alias as a decorator
  remained accepted; the same S17 selector was expanded before alias
  propagation was implemented.

## 2026-08-30 current-dev-rebased passing evidence

- The exact approved 30-case `test-authored` plan passed after implementation:
  `30 passed`. The broader Requirements, provenance, workflow, dependency, and
  signing surface passed `383` tests with `4` skips that require the released
  fixture lane.
- The exact PR Orchestrator full-suite owner ran against immutable modules
  fixture commit `69f075819be5e1ceca1446b026b0417f19e584ca`, tree
  `5d0b8e66c6cd467e6b1ad9d582e24c66b907e205`, and completed with
  `3191 passed, 10 skipped`, two third-party Lark deprecation warnings, and
  `64%` aggregate coverage.
- Ruff format and lint passed over `960` files. Full-project BasedPyright
  reported `0 errors, 0 warnings, 0 notes`; the safe-project-write guard passed.
- Strict OpenSpec validation passed all `176` specs/changes. Native
  `openspec archive fix-retained-red-proof-provenance` created
  `2026-08-30-fix-retained-red-proof-provenance`; canonical specs were already
  synchronized, so the command changed only the active/archive location.
- Actionlint, version-source synchronization from `0.55.3` to exactly `0.55.4`,
  `uv lock --check`, strict verification of all four signed module manifests,
  wheel build, and Twine validation passed.
- Dependency trust and frozen export reproducibility passed. Strict pip-audit
  passed both `requirements/ci/locked.txt` and
  `requirements/code-review/locked.txt` with no unreviewed vulnerabilities.
  The installed and isolated Code Review license scopes and all four module
  manifests passed with zero violations.
- Independent Semgrep ran six rules over `299` Python targets with zero
  findings and no accepted-baseline delta. Bandit reported no blocking
  medium/high findings.
- Full-enforcement SpecFact Code Review examined every Python path changed from
  refreshed `origin/dev`, including tests and the two new production helpers,
  with bug-hunt enabled. It reported `0` findings and score `115`.
- Independent semantic/security review found no actionable regression:
  differential analysis covered `237` staged/current import and pytest-plugin
  discovery cases with zero differences, and its focused control suite passed
  `140` tests. The independent clean-code review's five actionable warnings
  were remediated; its explicit-validator-argv observation remains an
  intentional auditable security allowlist rather than a hidden mapper.

## 2026-08-30 post-push reconstructed-history pipeline control

- GitHub Requirements run `33297997048` failed before evidence execution in
  `Locate verified amendment cycle base`. The reconstructed branch no longer
  contains the superseded externally approved green
  `ca2543bd85fbc92911efdb60845580cc211a6889`; the unconditionally attempted
  one-time bootstrap therefore correctly rejected its ancestry but `set -e`
  prevented the ordinary authoritative red search from running.
- The special bootstrap is now attempted only when its exact approved green is
  an ancestor of the current head. When the history is reconstructed from
  current `dev`, the workflow continues to the ordinary red/final path and must
  authenticate red commit `4300f6a08084b05d528748186328238c452bf065` and
  its GitHub artifact. The guard does not relax receipt, live revalidation,
  expiry, ancestry, linear-history, artifact, digest, or test-only checks when
  that external capability is applicable.
