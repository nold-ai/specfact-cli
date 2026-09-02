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

Canonical selector compatibility correction, 2026-09-02 21:39 Europe/Berlin:

- Requirements Evidence run `33671334359` accepted exact authority and passed
  its producer. The fresh execution then passed all 22 selected tests but
  reconciliation rejected every selector as uncollected.
- Execution artifact `9863663683`, digest
  `sha256:79d981f0b53acf74907d970edc52d888e04dbbab62edb825fe1c74f03ae5d8b6`,
  proved that `-c /dev/null` made pytest select `/dev` as its root and record
  each property as only `::test_name` instead of the plan's canonical
  `tests/...::test_name`.
- A focused regression test first failed because the trusted invocation lacked
  an explicit root directory. The workflow now passes the authenticated
  `repo_root` through pytest's fixed `--rootdir` option while retaining the
  null configuration, disabled conftest and plugin autoload, and trusted plugin
  bootstrap.
- The regression test then passed. A complete local 22-selector reproduction
  passed and reconciliation reported no uncollected selectors; its only local
  finding was the expected absence of the hosted prior-RED artifact. The
  expanded focused workflow/security set passed 95/95.
- Independent diagnosis confirmed that changing `junit_family` was unnecessary
  and that the fixed root directory introduces no additional execution
  authority or plugin/configuration path.
- The full exact-working-tree suite passed 3,086 tests with 9 documented skips
  and no failures. The canonical mapping digest remained
  `sha256:c8dfbd1876abf04902f3bd3d302ba73bd0c8698ce958730b79465cd683da628e`,
  and the raw plan hash remained
  `sha256:bd5462715ed4217dab84a03e2d795d38ffa98dbaaacfc5cc52a3354cb5ee4cac`.
- The full staged pre-commit pipeline passed, including changed-file lint,
  workflow lint, local Requirements evidence, command contracts, documentation
  accountability, and the code-review gate. That review reported no blocking
  finding on changed lines; its eight retained findings are legacy complexity
  and size observations on the pre-existing late-RED fixture helpers, which are
  outside this compatibility correction.
