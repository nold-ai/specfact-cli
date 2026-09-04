# TDD Evidence

Change: `fix-release-promotion-security-gates`

Baseline: `origin/dev@4fd96d6d804da70cc7ceca83b8adce21f7da561c`

## Failing before

Timestamp: 2026-09-02 00:17:45 Europe/Berlin

Environment: macOS arm64, Python 3.13.14, pytest 9.1.1. The interpreter came
from the existing repository-frozen environment; the clean replay worktree had
no synchronized environment yet. Production files remained identical to
`origin/dev` apart from the OpenSpec-native archive of already-completed #689.

Command:

```text
/Users/dom/.codex/worktrees/323f/specfact-cli/.venv/bin/python -m pytest \
  tests/unit/security/test_release_promotion_security_gates.py -q
```

Result: expected failure, exit 1; 11 collected, 11 failed. Each scenario failed
at its intended pre-fix observation: uv cache enabled; manual dispatch present;
npm cache present; Semgrep/MCP old graph and waiver; Code Review lock unbound;
Pylint exception leaked; archive Git results unchecked; `python -m pytest`
shadowable; invalid UTF-8 diagnostic leaked; `rg` lacked `--`; version remained
0.55.3.

## Passing after

Timestamp: 2026-09-02 01:43 Europe/Berlin

The independent frozen diff scan added four boundary regressions after the
initial red commit: exact regenerated Code Review closure, one immutable merge
base, credential-free proof execution, and a separate fresh-runner review
handoff that authenticates the exact head and installs tools before artifact
download.
Before their implementation, the extended focused run collected 18 tests and
failed 7 at those new contract points.

Focused passing command:

```text
.venv/bin/pytest -q \
  tests/unit/security/test_release_promotion_security_gates.py \
  tests/unit/scripts/test_check_license_compliance.py \
  tests/unit/scripts/test_dependency_trust_review.py \
  tests/unit/scripts/test_requirements_evidence_pre_commit.py \
  tests/unit/scripts/test_requirements_proof_executor.py \
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py \
  tests/unit/workflows/test_requirements_evidence_producer_regressions.py \
  tests/unit/workflows/test_trustworthy_green_checks.py
```

Result: exit 0; 153 passed.

Final CI-equivalent full gate used the repository's
`tools/smart_test_coverage.py run --level full` on Python 3.12 with the locked
module fixture commit `69f075819be5e1ceca1446b026b0417f19e584ca` and tree
`5d0b8e66c6cd467e6b1ad9d582e24c66b907e205`. Result: exit 0; 3,068
passed, 10 skipped, no failures; coverage collection completed at 64%.

Additional passing evidence:

- exact frozen closure regeneration and `uv lock --check`;
- both frozen `security_audit_gate.py` invocations with no unreviewed advisories;
- environment-scoped license gate with Pylint 4.0.7 isolated to Code Review;
- Ruff formatting/lint, BasedPyright (0 errors), actionlint, yamllint, docs contracts;
- strict module signatures for all four bundled manifests;
- Semgrep SAST (0 findings) and Bandit (0 medium/high findings).

Final review iteration, 2026-09-02 11:24 Europe/Berlin:

- 219 focused release/security/workflow tests passed on Python 3.13.14;
- the full suite completed 3,049 passes and 26 expected skips, with its six
  environment-dependent failures rerun successfully against the pinned module
  fixture and isolated writable home/cache paths;
- OpenSpec strict validation, Ruff formatting/lint, BasedPyright, actionlint,
  Bash syntax, frozen closure regeneration, `uv lock --check`, version-source,
  strict module-signature, dependency-trust, license, Semgrep, Bandit, package
  build, Twine, and PyPI-ahead gates passed;
- both final frozen sets passed `pip-audit` with no unreviewed vulnerabilities;
- an independent review's candidate-Pylint-config control reproduced
  `init-hook` execution with Pylint 4.0.7 before the fix. The final wrapper
  forced the protected-base config and `--` path separation; the same control
  left the marker absent.

Exact-head CI correction, 2026-09-02 11:54 Europe/Berlin:

- GitHub run `33616249786` proved the producer green, then the fresh consumer
  failed because its isolated CLI launcher left the two trusted bootstrap paths
  in `sys.argv`; Click correctly rejected the first path as an unknown command.
- The focused launcher contract was added first and failed 1/1 against that
  implementation. Both fresh-consumer CLI invocations now delete only those two
  bootstrap arguments before dispatch while retaining all real CLI arguments.
- The focused authority/workflow set then passed 33/33, and an exact launcher
  control reached `specfact requirements --help` instead of treating the
  site-packages path as a command.
- The same run then reached fresh reconciliation and Code Review, proving the
  launcher fix, but the final verdict exposed two trusted-tool wiring defects:
  the wrapper authenticated `pyproject.toml` instead of the repository's real
  `.pylintrc`, and the installed verifier tools were absent from the review
  step's `PATH`. The focused protected-config/tool-path contract was added
  first and failed 2/2.
- The protected base `.pylintrc` is now materialized and passed explicitly to
  Pylint, while the already frozen verifier environment is exposed after the
  explicit Pylint wrapper. The focused set again passed 33/33. A full local
  review control reduced the artifact from 573 findings and 32 blocking errors
  to no source-level blocking finding; its only two remaining errors were the
  known macOS sandbox CA-store failure from Semgrep, which the Ubuntu CI runner
  does not reproduce in the separate green static-analysis gate.

Ready-for-review corrections, 2026-09-02 12:30 Europe/Berlin:

- The fresh consumer's sole-active review-evidence fallback contract was added
  first and failed 1/1 because only changed evidence records were selected.
  The consumer now mirrors the producer only when no changed record exists and
  adopts the fallback only when exactly one active, non-archived record exists.
- The merge-history authority test was reproduced under
  `init.defaultBranch=main` and failed at its hard-coded `master` switch. It now
  returns to the branch reported by Git after initialization.
- The corrected focused workflow, authority, dependency-trust, and release
  security set passed 62/62, including the alternate-default-branch control.
- GitHub run `33617881577` disproved the reported artifact nesting: each scalar
  artifact ID extracted directly into its requested directory, and fresh
  reconciliation completed successfully.
- The approved mapping and selected security-test bytes remain unchanged at
  `sha256:a28a89742e1b4f65d3eac1879b10c77632c2e4d906d96711e80ae9172ada6c36`
  and `sha256:923cbf836f4bc18c1167a57f8d81923bde807d6aaff6a614bf7d74543309de44`.

Fresh-consumer execution correction, 2026-09-02 13:41 Europe/Berlin:

- Independent review validated that the producer-controlled executor or proof
  plugin could synthesize passing JUnit while the fresh consumer regenerated
  only the plan and reconciled those producer bytes.
- The new mapped consumer-execution contract was added before workflow changes.
  Its focused run collected two tests and failed 2/2 because the consumer did
  not materialize authenticated proof components, execute pytest, or produce
  its own JUnit.
- After implementation, the final focused workflow/security set passed 128/128.
  A direct control materialized the executor and proof plugin from
  `origin/dev@4fd96d6d804da70cc7ceca83b8adce21f7da561c`, independently executed
  all 16 selectors from PR run `33623640940`, and wrote trusted JUnit with
  16 passes. The first control also exposed and reproduced an invalid
  `runpy` module name; a named, registered import replaced it and the control
  then passed.
- Final reconciliation now uses only `${RUNNER_TEMP}/requirements-proof-consumer.xml`.
  The producer-report byte comparison was removed because its JUnit digest is
  expected to differ from independently generated proof; exact plan equality
  remains enforced.
- The independent bypass review then reproduced a candidate `conftest.py` hook
  changing a failing mapped assertion into exit-zero passing JUnit, and found
  that the direct consumer call lacked the executor's time bound. The executable
  hook control plus workflow contracts were added first and failed 3/3.
  Consumer pytest now uses `--noconftest`, and its complete reconciliation step
  has a 12-minute timeout; the same three checks then passed 3/3.
- The first remote RED attempt exposed a test-fixture portability defect before
  reaching the conftest control, so it is not counted as proof. The corrected
  test-only RED commit is
  `9a8cc901a6a84184de17b98c3280c67df0cc43ac` with tree
  `b4780097f199075d149b00f95e9b49509ef89b32`.
- GitHub Requirements Evidence run `33635003608` retained artifact
  `9848403071` with service digest
  `sha256:02fefa1834c74011652d415431e455ef841a81f2aed364ef49d1cdcd62c38e58`.
  Its JUnit digest is
  `sha256:c019fefe3e3fd6bf664e0a83557b4edae0158b9a37d4f61dd0b1f1ba9b3993b9`.
  S16 failed because the pre-fix consumer did not materialize the trusted
  executor/plugin; S17 first demonstrated that the malicious conftest forged
  an exit-zero pass, then failed because the pre-fix workflow omitted
  `--noconftest`.
- Post-correction gates passed strict OpenSpec validation, Ruff formatting and
  lint, BasedPyright with zero errors, actionlint, module signatures, both
  frozen `pip-audit` sets, license policy, Semgrep SAST with zero findings,
  Bandit with zero medium/high findings, docs contracts, synchronized version
  sources, the governed `uv build --wheel`, Twine, and the PyPI-ahead check.
- The full Python 3.12 run completed 3,071 passes and 9 expected skips. Ten of
  its 11 failures passed unchanged after removing the deliberately injected
  module-root test environment, assigning the isolated uv cache, or allowing
  the two marketplace controls network access. The remaining test writes
  `~/.specfact/metadata.json`; the local workspace sandbox correctly denied
  that home-directory mutation, so the clean GitHub runner remains the final
  control for it.

Final review-amendment correction, 2026-09-02 19:52 Europe/Berlin:

- The last review cycle begins at signed commit
  `8c388b0864a803f47810ec23fb226b6ca68c2f9c` with tree
  `773155beccc7a81c153c7ecddd728d015ef469af`.
- The final test-only RED commit is
  `470679c23ce2aed8baf26576bbf5f13885061a6c` with tree
  `11b7a4fafcca35c2d4fa2cd2f554626c6b1322c9`. GitHub Requirements Evidence
  run `33663767134` retained artifact `9859738216` with service digest
  `sha256:f5e1dc8e2af699831dafc457b2d89e5c4de5e87752c213eb969bdd67ba74db13`.
- The retained report, plan, and JUnit digests are respectively
  `sha256:525fd11a399fcdfab9a57e39a6b17197c096567cd39d5e0dcb0a4f0349f67be9`,
  `sha256:bd5462715ed4217dab84a03e2d795d38ffa98dbaaacfc5cc52a3354cb5ee4cac`,
  and `sha256:a65ad7291e3c13c4a5f566dbdb5f2eb906c5361fcd70509bf2ce46aa5e2c4b0a`.
  Exactly eight mapped checks failed: the four reviewed regressions plus four
  existing orchestration and closure contracts updated to require the same
  fresh final job and isolated verifier. The approved mapping digest remained
  unchanged.
- After implementation, the eight-file security/workflow focus passed 167/167.
  The complete local suite produced 3,055 passes and 9 expected skips; its 30
  failures were environment-only controls caused by the deliberately pinned
  module fixture, the restricted default uv cache, the shell's non-project
  Python, and the protected user metadata directory. The module-discovery and
  review-environment subset passed 13/13 after removing the injected fixture;
  reproducible-delivery and all signing controls passed 46/46 with an isolated
  uv cache and the frozen project interpreter. The user-home mutation remains
  delegated to the clean GitHub runner.
- The last independent boundary review reproduced a module-level
  `pytest_plugins` hook forging a failing test into an exit-zero pass, found
  candidate code executing before authority in the producer, found retained
  proof bytes remaining writable until same-runner consumption, and reproduced
  the authentic RED artifact being rejected only because its unique selector
  sets used different legitimate orderings.
- The amended implementation rejects selected-module plugin declarations at
  collection, runs producer authority before the candidate local action,
  authenticates and reconciles the execution artifact and late RED proof again
  in the required fresh final job, and compares unique selector sets while
  continuing to reject duplicates, omissions, additions, and wrong failures.
- The final focused workflow/security files pass 43/43. The broader changed-test
  set passes 203/203 outside the signing subprocess controls; those controls
  pass 45/45 with the frozen project interpreter first on `PATH`.
- Final review additionally closed the module-level `__getattr__` plugin-loader
  bypass, rejected path-only writes to `GITHUB_ENV`, included partial OpenSpec
  deletions in consumer selection, and limited the #703 late-RED lane to its
  exact PR and branch. The ordinary fresh final re-plan, reconciliation, and
  Code Review boundary remains active for later pull requests. The full staged
  pre-commit pipeline passed before the exact-head push.

Same-process proof boundary and exact-head compatibility, 2026-09-02 20:44 Europe/Berlin:

- GitHub Requirements Evidence run `33667861056` authenticated the exact member
  authority and completed its producer, then the fresh execution job failed the
  approved `test_doc_owner_rg_terminates_options` selector because isolated
  pytest could not import the candidate checkout's `src/specfact_cli` package.
- The compatibility correction appends `repo_root/src` only after installed
  pytest and the authenticated proof plugin are loaded. An exact isolated
  reproduction changed from the run's `ModuleNotFoundError` to one passing
  selector; the expanded focused workflow/security set passed 94/94.
- Two independent reviews then confirmed that consumer-generated JUnit does not
  provide sandbox integrity against intentionally hostile Python executing in
  the same pytest process. Approved test bytes and retained RED prove test-first
  provenance, but imported final production code has the same process authority
  as the JUnit writer.
- The user selected the narrow, explicit trust model: mapped tests and imported
  production code are review-trusted and assumed not to tamper deliberately with
  pytest, its exit status, or JUnit. The gate continues to protect producer
  artifacts, exact plans, pytest configuration and plugins, startup hooks,
  credentials, prefetched evidence, and the separate final review runner. A
  hostile-code sandbox is outside this patch and would require an external
  execution boundary, not another in-process guard.
- The full exact-working-tree repository suite passed 3,085 tests with 9
  documented skips and no failures in 142.57 seconds.
- The full staged pre-commit pipeline, strict OpenSpec validation, and both
  frozen-set security audits passed. A fresh independent bypass/regression
  review reported no P0-P2 finding within the selected model and confirmed the
  retained isolation, configuration, plugin, credential, artifact, plan,
  timeout, and fresh-runner controls.

Canonical selector compatibility correction, 2026-09-02 23:05 Europe/Berlin:

- Requirements Evidence run `33671334359` accepted exact authority and passed
  its producer. Its fresh execution passed all 22 selected tests, but
  reconciliation correctly rejected the truncated `::test_name` identities
  produced when `-c /dev/null` made pytest choose `/dev` as its root.
- The first correction commit `8e414fe490cc6d78ef7e9e2a4dbcd1f126a630eb`
  added a standalone regression to an earlier RED proof-input file. Run
  `33675662619` then accepted exact authority and rejected that retained proof
  as stale. The correction was not treated as passing evidence.
- To preserve published history and proof freshness, signed cycle base
  `c4ceacb9847557359b39a4502f8cdc40c89ed2f6` restored the buggy invocation and
  made only PR #703's superseded late-RED lane unreachable. Its direct signed
  RED child `654f49c85e630877d235afa102eb3ee39d7fba1e` changed only the already mapped
  `test_fresh_consumer_reexecutes_trusted_plan` selector.
- That selector failed locally because `"--rootdir", repo_root` was absent.
  Hosted Requirements run `33682811859` reproduced the same failure across the
  unchanged 22-case plan and uploaded immutable artifact `9866927781`, digest
  `sha256:22736d3f6d673ff2682bee02bf7f99d039686a7e5dcfefd9d685de0bd774a565`.
  Its report, plan, and JUnit digests are respectively
  `sha256:908b44c7705ba7243e3fa05adcccba674fc8fc10e76a89d069d4ce56ac9b56d9`,
  `sha256:bd5462715ed4217dab84a03e2d795d38ffa98dbaaacfc5cc52a3354cb5ee4cac`,
  and `sha256:ccf46126cd866b53ab1ba8d2978a4659c41b087ef0917765d6fadd5da58628a2`.
- The GREEN candidate restores every temporary branch predicate and passes the
  authenticated repository root through pytest's fixed `--rootdir` option.
  Null configuration, disabled conftest/plugin autoload, trusted plugin
  bootstrap, exact mapping/plan identity, and fresh reconciliation remain
  enforced. The retained RED manifest now binds the exact C/R history and
  hosted artifact above.
- Focused proof/security regression tests passed `94 passed`; workflow lint and
  the frozen dependency security audit passed, with no unreviewed
  vulnerabilities. The full repository suite passed `3085 passed, 9 skipped`
  using the PR workflow's pinned modules-repository environment shape.
- A fresh independent read-only review found no P0-P2 issue in the four-file
  GREEN patch and confirmed its C/R topology, exact manifest bindings, 17
  restored branch predicates, retained pytest isolation controls, and absence
  of changes to the mapped RED test input.

Clean-code proof recovery, 2026-09-03 00:18 Europe/Berlin:

- Signed cycle base `4c4c6e7fd0bd1a79f9ec4a911f9cb2b937bc5f3f` with tree
  `11ce0a390ca3ed77b13f1c88526e20bae24b3b50` changed only the 17 PR #703
  branch predicates to the unreachable proof-cycle branch and temporarily
  removed only `"-c", os.devnull` from the fresh consumer pytest arguments.
- Its direct signed test-only child
  `331ee620791a0438ef31103835033db1c41b37af` with tree
  `b9bcdb305452d2ec11a13a81e097bf4674d5c9db` refactored only the two mapped
  security/workflow test files. All 22 mapped selector names and all security
  assertions remain present.
- GitHub Requirements Evidence run `33689564917` retained artifact
  `9869485777` with service digest
  `sha256:60f213d0859f6c706f877a3fc3bf65817bbee9c152860e9009a8e02ee818e3ac`.
  Its report, plan, and JUnit digests are respectively
  `sha256:d2960d71ca6c45ac25c886c1c9afa842202a4dea2cd79ed14745faf869e105ae`,
  `sha256:bd5462715ed4217dab84a03e2d795d38ffa98dbaaacfc5cc52a3354cb5ee4cac`,
  and `sha256:3dcae213c417addc8dcf046cae0c0ed256e0450b692d966e0d1e3ac20718ea83`.
  Exactly the mapped conftest-forgery selector failed because the temporary
  cycle base omitted isolated pytest configuration; the other 21 selectors
  passed. Mapping and plan digests remained unchanged.
- The refactor reduced the blocking CC17 and CC27 functions to CC1 and CC4,
  reduced the related CC13 function to CC2, and replaced the eight- and
  six-parameter fixture APIs with a frozen options value. The branch-wide
  native Code Review passed full enforcement with zero blocking findings.
- Independent read-only review confirmed the same metrics, unchanged mapped
  selectors, preserved security assertions, and one nonblocking scanner false
  positive: the generic-name regex matches `data` inside the domain term
  `metadata` in a required mapped selector. The selector is retained unchanged
  to preserve the approved mapping; no rule or security gate is weakened.
- The final candidate restores all 17 exact branch predicates and
  `"-c", os.devnull` while retaining `--noconftest`, authenticated `--rootdir`,
  plugin isolation, time bounds, fresh execution, and artifact/digest checks.

GitPython frozen-graph remediation, 2026-09-03 Europe/Berlin:

- Hosted PR Orchestrator run `33777509057`, job `100722917093`, provided the
  failing-before evidence: the frozen `gitpython==3.1.58` graph reported
  PYSEC-2026-3785 through PYSEC-2026-3788 (CVE-2026-78675 through
  CVE-2026-78678).
- Upstream release evidence showed that 3.1.59 fixed those four findings but
  retained three follow-on advisories, while 3.1.60 accidentally removed the
  public `Actor.name_email_regex` attribute. The candidate therefore uses
  3.1.61, which restores that compatibility surface while retaining the fixes.
- Both dependency declarations, `uv.lock`, and `requirements/ci/locked.txt`
  now select 3.1.61 with its exact wheel and source hashes. No other package in
  either frozen graph changed.
- Both frozen-set security audits pass with no unreviewed vulnerabilities.
  The focused analyzer/versioning suite, linked-worktree smoke, full repository
  suite (`3092 passed, 9 skipped`), pinned BasedPyright error gate, Semgrep,
  Bandit, reproducible-delivery, license, and packaged-wheel smoke all pass.
  The built 0.55.4 wheel declares `gitpython>=3.1.61` and imports GitPython
  3.1.61 in a clean hash-locked environment.

Branch-level version-gate correction, 2026-09-03 Europe/Berlin:

- A new regression staged a dependency-only `setup.py` follow-up after a
  complete 1.2.3 to 1.2.4 release bundle relative to `origin/dev`. Before the
  implementation, the local gate failed by demanding another four-file version
  bundle for the same unreleased change.
- The gate now discovers the fetched target branch only for local staged mode;
  missing target refs keep the existing per-commit behavior. Independent review
  then identified two fail-open boundaries: an invalid explicit `--changed-vs`
  ref returned success, and a staged 1.2.5 to 1.2.4 downgrade could reuse the
  earlier branch-level 1.2.3 baseline. Both new regressions failed before the
  correction. A third regression proved that a staged changelog deletion could
  reuse the committed header and also failed before the correction.
- Explicit base enumeration now fails closed, branch-level reuse requires the
  candidate version to equal `HEAD`, real version changes remain strict
  `HEAD`-relative bumps, and candidate evidence is read from the index plus
  `HEAD`. The complete version-gate test file passes `11 passed, 1 skipped`;
  the subsequent full repository run passes `3094 passed, 10 skipped` with 64%
  coverage.

Release-PR provenance regression, 2026-09-03T18:08:18Z:

- Spec first: added the module-namespace binding requirement and its local,
  class, module, and explicit-global declaration scenario before changing the
  validator.
- Failing-before command:
  `<isolated-security-worktree>/.venv/bin/python -m pytest -q tests/unit/scripts/test_requirements_proof_provenance.py::test_pytest_plugin_provenance_ignores_local_scope_and_keeps_global_bindings`
- Result: expected failure, exit 1; `1 failed`. The unchanged validator treated
  ordinary function- and class-local declarations as effective module plugin
  bindings and returned `stale-red-proof` after only those plugin files changed.

Release-PR review regressions, completed 2026-09-03T18:24:37Z:

- Spec first: added stable malformed-license-scope and published bundled-asset
  requirements before changing the license gate or module-publishing workflow.
- Failing-before command:
  `<isolated-security-worktree>/.venv/bin/python -m pytest -q tests/unit/scripts/test_check_license_compliance.py::TestAllowlistLoader::test_non_string_scope_uses_stable_invalid_scope_error tests/unit/workflows/test_trustworthy_green_checks.py::test_publish_modules_verifies_release_asset_before_snapshot_update tests/unit/scripts/test_requirements_proof_provenance.py::test_pytest_plugin_provenance_ignores_local_scope_and_keeps_global_bindings`
- Result: expected failure, exit 1; `4 failed`. The unchanged license validator
  exposed `TypeError` for both list and mapping scopes, both publishing lanes
  lacked tag-qualified verified release assets, and plugin discovery still
  included ordinary local declarations.
- Publication control: retained Actions artifact `9727636292` from run
  `33296707608` contains `module-registry-0.1.35.tar.gz` with SHA-256
  `8a3013299190286d2c48d87a6a605686ee3880d6acdc92119b466724d9db6f70`,
  exactly matching the current snapshot. No GitHub release or module tag exists;
  no remote publication was performed during failing-before evidence.

Final review RED and local passing evidence, 2026-09-03 Europe/Berlin:

- The final test-only head `f7fd96b0aeda254b849b66c7980b8d22a67d0471`
  retained the approved 25-case mapping and incorporated only review-quality
  corrections before implementation.
- GitHub Requirements Evidence run `33808710389` started at
  2026-09-03T21:34:54Z and retained artifact `9913948112`, service digest
  `sha256:369ba41c06fc851e9d647b9d5c80811a04d9c372c7353722205d29a227866f5e`.
  Its JUnit digest is
  `sha256:35eba3275a3668a34ad95af7302fea19a33dd9fcfcca716d5805db75cc4da59e`.
- The JUnit contains exactly the four expected failures: two non-string
  allowlist scopes, missing verified module-release publication, and stale
  plugin provenance caused by ordinary local/class declarations. Authority,
  mapping, fixture, and infrastructure setup completed successfully.
- After the implementation, the focused five-case regression/control command
  passed. The complete provenance, license, publishing/workflow, and release
  gate suites then passed 33, 32, 80, and 19 tests respectively; actionlint and
  `git diff --check` also passed.
- No dependency or version source changed. No remote module tag or release was
  created during validation; publication remains a post-merge operational step.

Independent final-review RED, 2026-09-04 Europe/Berlin:

- Signed test-only commit `b4d1b9c581c5628c9e8dfd70fd43b53a5db0998d`
  strengthened the existing mapped plugin-provenance and module-publication
  selectors and added one focused reproducible-archive control after independent
  reviewers identified class-global, annotated-assignment, source-binding, and
  retry gaps.
- Requirements Evidence run `33810222523` retained artifact `9914498650`,
  service digest
  `sha256:6799940eff42853f3d6cca10802396c154e6ce33939d79e3991f7fe6d7fb119b`,
  and JUnit digest
  `sha256:bf918344e817db436d300da68307659139ea40c5e4a1a71076f1dae8ecfb72a9`.
  The run produced exactly six expected failures and 22 passes: two malformed
  license scopes, the release-publication contract, and all three scoped plugin
  variants against the unchanged over-broad baseline detector. Authority,
  mapping, fixture, and artifact publication completed successfully.
- The implementation removes publication-time signing, strictly verifies clean
  checked-in manifests at the authenticated source commit, uses exact tags,
  makes archives reproducible, and verifies or safely reuses an exact published
  asset before changing snapshot metadata. The absent `module-registry-v0.1.35`
  release remains deliberately absent from the checked-in snapshot until the
  corrected workflow is merged and run.
- Passing-after evidence: the focused six regression/control cases passed;
  strict OpenSpec validation passed; and the combined provenance, license,
  publishing, workflow, Requirements-delivery, and release-security suite passed
  all 185 tests. Actionlint, repository format/lint, type checking (zero errors),
  and `git diff --check` passed. The repository-wide YAML lint still reports only
  pre-existing findings in the abandoned Requirements 08 archive and the active
  Requirements 07 mapping, neither touched by this follow-up.

Final publication-boundary RED, 2026-09-04 Europe/Berlin:

- Signed test-only commit `b4aac69b22854049b9016ba2aa81dec9212e7a34`
  retained the mapped selector identity while splitting its assertions below
  the clean-code complexity threshold and adding destructured plugin-binding,
  Git-invisible file-mode, unpublished-release, late-untracked-file, and
  protected-PR-base regressions.
- Requirements Evidence run `33811488807` retained artifact `9914965827`,
  service digest
  `sha256:11acb8371be6bd5a9abb7b766c2a41caf6a552bd4af40ed28493c48885386216`,
  and JUnit digest
  `sha256:0291e7931ed7e744ac6a3c53a9c9a742b0ff68c836d423f60e5f43ed217a4602`.
  The approved plan produced exactly seven expected failures and 22 passes:
  two malformed license scopes, the module-release selector, and four scoped
  plugin variants. Authority, mapping, fixture, and artifact publication passed.
- The two new standalone publication tests and the destructured plugin variant
  produced four expected local failures against the intermediate candidate:
  non-reproducible mode metadata, missing published-release state validation,
  missing late-untracked/protected-base checks, and missing destructured plugin
  provenance.

Final independent-review RED and passing evidence, 2026-09-04 Europe/Berlin:

- Signed test-only commits `ac98b65476930debcdc8bff454358ba839ee6d98`,
  `aa44c0bf594debabb8e9dce5054a16525daa1f11`, and
  `eed94e01d1b97eef337b8aa2f699ce698a8b642d` added only the final reviewed
  regressions and removed their type-review warning before implementation.
  They cover starred, augmented, and named-expression module plugin bindings,
  including definition-time expressions, explicit rejection of module symlinks,
  and safe manual-release retries after the selected protected branch advances.
- Requirements Evidence run `33812971823` retained artifact `9915498910`,
  service digest
  `sha256:4376ae97cb9bacb28e0b14183736b4bbac841e8f8d9608cc835bd1ed766d82e3`,
  and JUnit digest
  `sha256:3ba2e1224c83bd3d8ea638292e2801a62c404e44cbfa3bb8b764a3d301035673`.
  Its approved plan digest remained
  `sha256:8ef3da33b39d72ccd344ca694cbdaa38f25110794fc351d16a766e2c04341535`.
  The immutable run produced 11 failures and 22 passes: the two malformed
  license cases, the release-publication contract, and all seven scoped plugin
  variants plus the definition-time variant failed against the unchanged
  production baseline while authority,
  fixture, and artifact creation completed.
- The narrow implementation models literal Python unpacking semantics and
  augmented/named assignments for effective module plugin bindings, rejects
  module symlinks rather than publishing an incomplete signed archive, and
  authenticates manual publication by selected protected-branch ancestry so an
  exact-source retry remains valid after normal branch advancement.
- Passing-after evidence: the focused 14 regression/control cases passed, and
  the combined provenance, license, publishing, workflow,
  Requirements-delivery, and release-security suite passed all 194 tests.
  Repository format/lint, actionlint, strict OpenSpec validation, type checking
  (zero errors), and `git diff --check` also passed.
- Both frozen dependency audits passed against the live PyPI advisory service
  with no unreviewed vulnerabilities. The scoped Code Review result has no
  errors and no new warnings; its two parameter-count warnings are unchanged
  file-level findings on `_write_index_fragment` and `publish_bundle`, whose
  declarations and call shapes are outside this patch. The three informational
  readability notices were inspected and preserve explicit security-test and
  command-flow clarity.
- Independent security-boundary and release-path re-reviews reported no
  remaining actionable P1/P2 findings after the definition-time traversal,
  symlink rejection, and protected-ancestor retry fixes.

Parameterized-selector proof recovery, 2026-09-04 Europe/Berlin:

- Strict normalization maps each unique concrete pytest parameter case to
  exactly one approved selector, rejects ambiguous or malformed prefixes, and
  still requires complete selector coverage and one consistent toolchain.
- Signed cycle base `519b7bcda4a3f0d012770021b85d9c566361f42f`
  with tree `cbaf747adfef7ac955c7c69e042b2fb7336abc7b` changed only the
  late-RED script constants to PR #704 and
  `bugfix/692-release-review-followup`; definition-time traversal remained
  disabled and all 17 workflow predicates remained unreachable.
- Its direct signed test-only child
  `fed178205f79fb4467ab8079077f594dea424df5` with tree
  `89ef840b3c38c76d6e34e1f9022b13dbb3e7bdc0` changed only four synthetic
  fixture values. The late-amendment control passed, while the default-value
  and return-annotation cases failed under the same mapped plugin selector.
- Requirements Evidence run `33845908431` retained artifact `9926518461`
  with service digest
  `sha256:57ce81936788c45298f50023e56e8f30a8024a88d4faed1fd2397ba318aea2e5`.
  Report, plan-report, and JUnit digests are respectively
  `sha256:f32be138a0636b94bdd00b96776d63002897b2b42c813eb38f37befc041777a7`,
  `sha256:8ef3da33b39d72ccd344ca694cbdaa38f25110794fc351d16a766e2c04341535`,
  and `sha256:075b4fd97a3136082fb6ac16cc62831a6b5d066f61d50dea3074ffa80d3bc592`.
  Exactly the two concrete definition-time cases failed and normalize to the
  single mapped plugin-provenance selector; all other mapped selectors passed.
- Mapping and plan digests remained
  `sha256:302fa2d64f2bba475fbf7ed31922e80d835c433ca46cadcc68f75d0e623d4d08`
  and `sha256:ac492798da29548664d23c0378596dee7073e9f1e3f5792153ca8358ec226f0e`.
  The final candidate restores definition-time traversal and retargets all
  late-RED predicates exactly to PR #704 and the current branch.

Exact parameter-selector delivery recovery, 2026-09-04 Europe/Berlin:

- Product-owner comment
  `https://github.com/nold-ai/specfact-cli/issues/692#issuecomment-5537842252`
  approved the revised test-authored mapping digest
  `sha256:644805b601e2e88eb39551c70150bacc6fb3f61a414a515546da682d25e24b7f`.
  The two existing parameterized regressions retain independent execution but
  now bind each value directly to a stable selector-safe ID; the mapping lists
  all 11 concrete selectors and no overlapping base selector.
- Signed cycle base `fd7a0a3bb9aca6adf6d82729cee104cff51eba9f`
  with tree `274aa5af7b18975d5c7dc01395aee9585d06019f` temporarily disabled only
  definition-time plugin traversal and redirected the 17 PR-specific late-RED
  expressions to the unreachable proof-cycle branch.
- Its direct signed test-and-evidence-only child
  `508bbc00c63d6c14956cf0bd343de3561e717a2a` with tree
  `deb582ca5255cde86881918a5d49db70172f80fa` added the stable IDs, exact
  selector mappings, and matching accepted review evidence. Requirements
  Evidence run `33853864883` retained artifact `9929395781` with service digest
  `sha256:6f7de5fd8a9d01a678877d74e82626104c33218abd51d52b948cca34124c5264`.
- The immutable report, plan-report, JUnit, and summary digests are respectively
  `sha256:70f98fdaba3e2d995022b6088df0791cb62b45dc887297c2f335dd0a4fda014f`,
  `sha256:bfb3e9c4a8dd65d67cee02a2997c7ffe6e49583bf69979f274abb86e3b71b6a4`,
  `sha256:c86972e327a3028474a7e7af3ffe87ca9beb916f725953bde874b72ecb162647`,
  and `sha256:af5b0cc03c94f1b281f23212f8450e9909d7863d0423f952f6b11f7af091170d`.
  Mapping and plan digests are
  `sha256:f2b2a823494b10dd2fd8be022c213f49b34e4cb9857506715ed8a3733ff36808`
  and `sha256:0be546afae288733a0233df36864bcbe0f2abcac75de5b300d1d2b9a2bedcf4d`.
- The run collected all 34 exact selectors: 31 passed and three failed by
  assertion, with zero errors and zero skips. The two definition-time cases
  failed against disabled traversal; the mapped late-amendment self-test also
  failed against the intentionally unreachable workflow predicates. Restoring
  traversal and those predicates made all three focused selectors pass without
  changing test, mapping, executor, plugin, module, or JUnit bytes.
