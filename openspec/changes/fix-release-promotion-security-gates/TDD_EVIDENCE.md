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
  `/private/tmp/specfact-recovery-worktrees/bugfix/692-security-patch-clean-replay/.venv/bin/python -m pytest -q tests/unit/scripts/test_requirements_proof_provenance.py::test_pytest_plugin_provenance_ignores_local_scope_and_keeps_global_bindings`
- Result: expected failure, exit 1; `1 failed`. The unchanged validator treated
  ordinary function- and class-local declarations as effective module plugin
  bindings and returned `stale-red-proof` after only those plugin files changed.

Release-PR review regressions, completed 2026-09-03T18:24:37Z:

- Spec first: added stable malformed-license-scope and published bundled-asset
  requirements before changing the license gate or module-publishing workflow.
- Failing-before command:
  `/private/tmp/specfact-recovery-worktrees/bugfix/692-security-patch-clean-replay/.venv/bin/python -m pytest -q tests/unit/scripts/test_check_license_compliance.py::TestAllowlistLoader::test_non_string_scope_uses_stable_invalid_scope_error tests/unit/workflows/test_trustworthy_green_checks.py::test_publish_modules_verifies_release_asset_before_snapshot_update tests/unit/scripts/test_requirements_proof_provenance.py::test_pytest_plugin_provenance_ignores_local_scope_and_keeps_global_bindings`
- Result: expected failure, exit 1; `4 failed`. The unchanged license validator
  exposed `TypeError` for both list and mapping scopes, both publishing lanes
  lacked tag-qualified verified release assets, and plugin discovery still
  included ordinary local declarations.
- Publication control: retained Actions artifact `9727636292` from run
  `33296707608` contains `module-registry-0.1.35.tar.gz` with SHA-256
  `8a3013299190286d2c48d87a6a605686ee3880d6acdc92119b466724d9db6f70`,
  exactly matching the current snapshot. No GitHub release or module tag exists;
  no remote publication was performed during failing-before evidence.
