# Documentation fixture pytest parity evidence

## Scope and sequence

New specifications and six mapped native pytest cases precede any fixture-lock change.
At the RED phase, the documentation fixture was pinned to module commit `2e095f1350fecb7e7eda0bcfba6bad89a6d82c88`
(tree `8846ce1b47538ea78d600b7c82bfd2ccd1761ee2`, review bundle `0.50.0`).
The original docs-16 proof and independent Requirements fixture remain unchanged.

## Local RED

On 2026-09-16 at 08:31:08 Europe/Berlin, the final harness produced six behavioral assertion failures,
zero errors and zero skips in 5.267 seconds. The independent core authenticator verified all seven bundles
from a private public-HTTPS exact-commit fetch. Each native subprocess exited zero; actual skip, XFAIL,
non-strict XPASS, empty-reason XPASS, missing reviewed-source coverage and low reviewed-source coverage
were observed before replay through the real portable adapter yielded no findings.

Command (from the dedicated worktree environment):

```sh
python -m pytest tests/unit/docs/test_code_review_fixture_pytest_policy.py -q -o addopts= \
  --basetemp=/private/tmp/specfact-docs17-native-red --junitxml=/private/tmp/specfact-731-fresh-red.xml
```

`LOCAL_RED.json` records the source identities, input hashes and concise outcomes. Every JUnit case carries
`docs_fixture_acquisition` and `docs_fixture_native_evidence` properties for protected CI artifact retention.
Raw local output is `/private/tmp/specfact-731-fresh-red.log` and its adjacent XML report. Earlier harness
setup failures and sandbox network errors are not behavioral RED and are not accepted proof.
This proves native pytest and adapter contracts, not full capsule operation or publication acceptance.

## Mapping and review

The independent root Codex agent reviewed the complete specifications, harness and six-case mapping,
including the final quality refactor. Its acceptance is recorded in `requirements-proof/review-evidence.json`
and public issue #728 comment 5693030621. This is an agent review, not a human approval or CI result.

Strict OpenSpec validation, focused Ruff formatting/lint, authoritative BasedPyright (zero errors/warnings),
and mapping YAML lint passed. Fresh SpecFact bug-hunt review at 2026-09-16T06:24:18Z passed with score 120
and zero findings. The local report is `/private/tmp/specfact-docs17-code-review.json`.
Normal signed commit hooks and protected test-authored CI evidence remain required.

An independent preflight authenticated signed source `b21e89e7ae1c16375c33e8c3bc19376c930e219b`
and confirmed all six current assertions can pass without changing their inputs. That probe establishes API
feasibility only; it is not GREEN for the selected fixture and does not authorize an unaccepted lock update.

## Pending protected evidence and GREEN

Retain a signed test-first commit and protected CI RED with six failures, zero errors/skips, frozen test and
mapping hashes, and acquisition/native JUnit properties. Only then select an accepted CI-signed module
source in the documentation lock. Preserve frozen evidence and prove GREEN, old 38-case compatibility,
documentation parity and required delivery checks before closing #728 or promoting release #731.

## Protected RED and accepted fixture GREEN — 2026-09-16 Europe/Berlin

The final test-only head `07e6ac41fd861e9f83d29e45a5f315f20ad1adc6` descends from unchanged current dev
`921fa3a41a1fed13d7edbf03db1dc8d569362d02`. Canonical Requirements run
[35073224094](https://github.com/nold-ai/specfact-cli/actions/runs/35073224094) retained artifact
`10437380772` with `delivery_status: failing-first-proven` and no findings. All six unique mapped cases
failed assertions with zero errors/skips. JUnit SHA256:
`7cccb3237e611c84c240239a093f39dfd5a6a21e783398378f76b29c59c122c2`.
The mapping, harness, accepted review receipt, old docs-16 proof and separate Requirements fixture stay unchanged.

The docs lock now selects merged modules source `046d366c190af7a188d6f48953a96edb65e766db`, tree
`c5b44db3477d1c9ea8dae1dceab2af276d265353`, after accepted PR #478. The trusted core verifier authenticated
all seven exported bundles from a clean public-origin exact-commit checkout. Review bundle `0.50.1` manifest
SHA256 is `af4a62ac6731c399413e8cf5b2b76ea69fe0050aa28cbb32f6f8e0d35b7ff000`. These are canonical CI-signed
module bytes; this fixture update does not claim public marketplace installation acceptance.

Actual frozen six-case execution passed in 3.66 seconds with zero errors/skips. Its JUnit retains per-case
authenticated acquisition and actual native evidence properties. The original 38 mapped cases passed in
5.24 seconds, and 60 documentation parity/authentication controls passed in 6.57 seconds. Raw artifacts:
`/private/tmp/specfact-737-final-six-green.xml`, `/private/tmp/specfact-737-old38-green.xml`, and adjacent logs.
Documentation checks passed: 393 unique command prefixes, 117 generated command paths, generated overview
freshness, and accountability. No generated command artifact needed changes. This remains native pytest/adapter
contract proof, separate from the full Linux capsule corpus accepted on modules PR #478.

Protected GREEN reconciliation, current-head review closure and normal merge remain outstanding until the
new signed core commit has completed its required checks. No historical RED report is rewritten.

Fresh explicit-file SpecFact `--bug-hunt --enforcement changed` review of the frozen new harness at
`2026-09-16T21:59:23Z` completed with no findings; report
`/private/tmp/specfact-737-final-code-review.json`. It uses the normal core developer review context and
is not protected capsule or Requirements reconciliation evidence.

## Declared local test environment precondition — 2026-09-17 Europe/Berlin

The first full smart-test run passed 3,201 tests with nine existing skips but raised six setup errors because
the dedicated Hatch test environment omitted `pytest-cov`. It is already present in the development dependencies
and pinned to `7.1.0` in the frozen CI export. A fresh focused run against that unrepaired environment reproduced
all six setup errors in 2.17 seconds (`/private/tmp/specfact-737-hatch-plugin-setup-red.log`). These errors are
setup-failure evidence only and do not replace the retained six behavioral assertion failures.

The test environment now declares `pytest-cov>=7.0.0`, matching the existing development requirement. Normal Hatch
dependency reconciliation installed the plugin; all six unchanged cases passed in 2.97 seconds. No local-only
package injection, test changes, lock regeneration or threshold changes were used. Reproducible delivery,
`uv lock --check`, frozen npm type-tool setup, authoritative type JSON and security audits passed. The frozen
CI requirements and all proof inputs remain byte-identical. The full smart-test gate is rerun after this correction.

Final full smart-test passed: **3,206 passed, 10 skipped, two existing warnings**, 158.78 seconds,
Python 3.13; configured line-coverage gate passed at 64 percent (50 percent configured floor).
This is not an 80/100-percent coverage claim. The six new cases passed without skips.
Log: `/private/tmp/specfact-737-smart-final-authorized.log`. The preceding sandboxed retry was blocked
by the existing network smoke test and host metadata-write test; unchanged execution with normal host
access passed. No test-selection, policy, timeout or coverage threshold was relaxed.
Formatting, lint, YAML, cached unchanged-contract selection, strict OpenSpec, staged planned Requirements,
and the additional frozen-delivery/type/security gates passed. Full typing retained 1,526 baseline
advisories with zero errors; fresh scoped review had no findings.
