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
