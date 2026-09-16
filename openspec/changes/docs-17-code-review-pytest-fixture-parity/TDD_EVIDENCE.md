# Documentation fixture pytest parity evidence

## Scope and sequence

New specifications and six mapped native pytest cases precede any fixture-lock change.
The documentation fixture remains at module commit `2e095f1350fecb7e7eda0bcfba6bad89a6d82c88`
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
