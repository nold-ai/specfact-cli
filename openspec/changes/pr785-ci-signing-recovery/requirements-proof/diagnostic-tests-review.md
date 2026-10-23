# Independent diagnostic test acceptance

ACCEPT for the frozen test/spec package only. No blockers found within this acceptance scope. Confidence is high because I read the full working-tree diff, independently verified the frozen bytes and conservation, re-evaluated the native source mapping, and reproduced the entire 93-case focused suite. This accepts the tests as meaningful failing-before evidence. It does not accept a runtime implementation, complete live probe, immutable anchor, release readiness, or permission diagnosis.

Reviewed on 23 October 2026, Europe/Berlin, by Codex agent `/root/probe_diagnostic_test_acceptance`. The test/spec writer had stopped before this review. All review writes are private artifacts in this directory. Source, tests, OpenSpec, index and refs were not modified by this reviewer. No network, installation, signing, dispatch, API operation, comment, merge, broad suite, broad scan or delegation occurred.

## Exact accepted inputs

| Input | Verified value |
| --- | --- |
| HEAD | `54e8ee9bc807fda92981667aab28ccbebeeb5d0d` |
| HEAD tree | `6045926b1c3ca5de8502a46b30de725a38f3f48c` |
| Branch | `codex/pr785-ci-signing-recovery` |
| Test SHA-256 | `879533ee4ff8762f1575313d99bc3267ea20eea15b1a4cd82e676f68a5c1b4af` |
| Unchanged runtime SHA-256 | `416d507c43d34a0b8d6d793070f4849b676f3eeb961535ec8a5d9b7be8146358` |
| Native canonical mapping digest | `sha256:8998713988ae1df90f45940f48527a12e6196a5b0ace58e8d3f55f8fbc9fc4e4` |
| Frozen hash declaration SHA-256 | `2c50f9dad2c5f54ea78f117a8e8020c36bc155abfd320610153a15afb034a2f7` |

The independent checker verified all seven changed-file entries and all eleven evidence entries in `frozen-hashes.json`. The prior entire test file is an exact byte prefix of the accepted file, preserving all prior assertions and fixtures. All 90 old case objects remain identical, in the same requirement and original order. Other requirement metadata is unchanged. All eight requirement IDs and every Requirement/Scenario name are conserved. The only added mapping cases are PR785-PROBE-091 through PR785-PROBE-093 under signing-refusal. The 93 exact selectors equal the independently executed JUnit case set, without duplicates.

Runtime, manifest, inert probe, probe dependency lock, workflow, requirements lock, uv lock, pyproject and fixture lock match both HEAD bytes and their recorded digests. The index is unchanged and empty relative to HEAD. The stale active review receipt is absent; its private preserved copy equals HEAD bytes with SHA-256 `d51ee63212fe3f5fd4e64568b6063670aa1ba0f67bcfd448f191f627be6f7484`. This report is private acceptance evidence, not a newly authored active receipt.

## Reproduced failing-before behavior

I sourced the existing `../aux-env.sh` and used its configured Python 3.12.13. The exact argv is retained in `independent-test-check.json`. The full focused pytest invocation uses `-B`, `--no-cov`, `-o addopts=`, private JUnit and basetemp paths, and disables pytest's cache provider to avoid writes outside this evidence directory.

The run exits 1 with **90 passed, 3 failed, zero errors and zero skipped**. Each new case reaches its intended final stderr assertion after its prior receipt, persistence and disclosure assertions pass. The decisive output is:

```text
AssertionError: assert 'API refused HTTP 403' in ''
AssertionError: assert 'Execution context mismatch' in ''
AssertionError: assert '' == 'Probe refuse...I/O failure\n'
- Probe refused: Local I/O failure
```

The third pytest display abbreviates its right operand. The failure source line and deletion diff establish the full exact expected `Probe refused: Local I/O failure\n`. My first private checker expected an unabbreviated pytest display, so it stopped after a valid test run. I corrected only that private output parser and reran the same narrow suite. The accepted second run is retained. This was not a product, test, setup or import failure.

PR785-PROBE-091 exercises `main` with the existing actual urllib transport fixture. It verifies one retained verified object, prior raw responses, refused receipt, false anchor flags, empty stdout, and no credential/body marker, HTTP reason phrase or traceback in stderr before asserting the sanitized status. The persisted-response helper checks all persisted JSON for the marker.

PR785-PROBE-092 changes the execution actor and forbids network access. It requires refused context, no objects or raw directory, no credential disclosure, no traceback and the safe policy diagnostic. PR785-PROBE-093 injects arbitrary credential/body markers into an `OSError` at the first raw write. It requires no API writes, an empty raw directory, a refused receipt without objects or anchor claims, and exactly the fixed generic stderr message. These tests would reject the observed empty diagnostic and unsafe interpolation of the local exception. They do not prescribe a new internal error framework or receipt field.

## Native binding and recorded quality reports

I independently ran `verify_fixture` against the actual pinned fixture. It verifies clean fixture HEAD `69f075819be5e1ceca1446b026b0417f19e584ca` and tree `5d0b8e66c6cd467e6b1ad9d582e24c66b907e205`. I then called its actual `_lifecycle_report`. Its `_source_mapping_findings` imports the selected OpenSpec source through `import_native_requirements_to_bundle` and reconciles requirement and scenario IDs. The reproduced report equals `native-planned-report.json` exactly. It reports planned/pass, no findings, proposal-only delivery and implementation evidence not yet available. This is source binding and planned maturity, not the actual staged test-authored gate.

I inspected `checks.json`, exact commands and actual logs/results. Scoped changed lint reports zero type errors, warnings and notes and passes formatting and lint. Actual SpecFact CodeReview reports PASS with zero findings in `review.json`. Its log also records the existing bundled-modules refresh notice; the clean review verdict does not resolve that notice. YAML and strict OpenSpec logs pass. Bandit has no results or errors. Configured Semgrep records six rules, one test file and no findings or errors. The earlier fixture-root invocation failure and resolved intermediate complexity warning are retained privately. I did not rerun these scans. I independently reran `git diff --check`, which passed.

Broad inherited **1,449 type warnings and 30 YAML errors remain inherited debt**. They were not rerun, waived or represented as clean. No comments were added in the test diff. The no-comments/how delegate workflows were not run because this assignment explicitly prohibits delegation; this bounded review does not claim completion of those separate workflows.

## Live evidence, limits and next actions

I read the saved corrected live receipt and response sequence, and independently hashed the saved artifact ZIP as `002286e6b197d1aa5fa3e2033d36159bd969bb049f62ebb5061da91051aecbf0`. The saved receipt is refused for run 39923021078 attempt 1, with ten raw responses, one verified baseline object `a09c08a5580a3c4b450ff22c55e60e9ac26d42cf`, and both anchor flags false. Runtime `main` currently catches the safe policy exception and discards its reason. The saved GET tree 422 establishes no permission cause. The exact live tree-request refusal remains UNKNOWN. Synthetic HTTP 403 is a test input, not a diagnosis. I did not freshly authenticate that run or verify its signatures or anchors.

Acceptance assumes the frozen inputs remain unchanged. A later edit invalidates this review and requires a fresh review bound to its bytes. Accidental diagnostic disclosure is constrained by malicious marker controls and the exact generic OSError message; runtime acceptance must inspect every changed exception path. Partial-run adoption remains a separate risk; only root may authenticate a fresh complete run and both immutable anchors. Scope expansion is constrained by the unchanged frozen inputs and the root-owned staged gate. No cost or duration estimate follows from this local review. Reversal of the unstaged package and any Git operation remains root-owned.

The Prove It Works principle changed this review from trusting the handoff to running the actual suite and actual native source importer. Test Behavior, Not Implementation shaped acceptance around `main`, observable stderr, retained receipt/raw effects and blocked network access.

Root owns the genuine replacement acceptance receipt, actual staged gate, normal test-first commit, and explicit runtime handoff. Internal wiki alignment and graph rebuild remain pending root work. Separate release signed-prefix native 33-case RED, fresh complete live probe authentication and both anchors remain mandatory. No implementation or readiness gate is opened by this test acceptance alone.

## Independent evidence hashes

| Artifact | SHA-256 |
| --- | --- |
| `independent-test-check.py` | `1f5e239ceb475317d5813cf42310ac4c5c0d6f058d87032daeae39b9d8136f5b` |
| `independent-test-check.json` | `c30c6db6b2e62a1bf43dbfce78b6dc04486b3fade840ed58bf8e4f2883811e19` |
| `independent-red.log` | `bfbdb1fc60c6d49f27e68d3da99012487b3dd27d66fb4c3821b46c6b7f11f31d` |
| `independent-red.xml` | `781621a691a7552fb35eee614b375ff10e8d807a67985e4d8369f52d51473415` |
| `independent-native-planned-report.json` | `c2fefb27280a770d63e8cdf9e8576d547db614698b312f004800b31e42b6ff44` |
