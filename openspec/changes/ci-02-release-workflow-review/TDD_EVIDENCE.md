# Release workflow review evidence

## Baseline and scope

Base dev2f9567e28e98b082801b13ff02e863933ce2f0f2, 2026-09-16 Europe/Berlin. Issue #736 owns this follow-up.
Original docs16/trigger-parity tests, mappings, retained proof and both module fixture locks remain unchanged.

## Actual local RED

After specification, the new regression executed actual authentication workflow shell against ephemeral signed module
fixtures with a hostile PR wrapper. Node regressions inspect the actual test jobs and local documented prerequisites.

```sh
hatch run python -m pytest tests/unit/workflows/test_release_workflow_review.py -q \
  --junitxml=/private/tmp/specfact-736-red.xml
```

The final mapped selection has 12 genuine assertion failures, zero errors and zero skips. WORKFLOW_RED.txt preserves
the raw output. No production edits preceded this run. This is local evidence; authenticated CI RED remains required
before implementation of governed workflow paths.

Independent review corrected exact parameter selectors and recognition of the actual smart-test command before
freezing. The initial broad run also passed two already-implemented complete push-filter controls. Those passing
controls are not part of the new all-failing RED plan. They remain required regression evidence outside that proof;
changing the original frozen mapping would invalidate its authenticated history.

## Delivery boundary

The accepted RED and local implementation evidence are recorded below. Protected GREEN and integration remain
pending. No public release acceptance is claimed.

## Independent review and local quality

Independent agent `/root/pytest_discovery_fix` accepted the final twelve-case mapping and test design with no findings.
Receipt: <https://github.com/nold-ai/specfact-cli/issues/736#issuecomment-5693072266>. Exact parameter selectors match
all twelve assertion failures; positive in-memory Node controls verify the test can pass after valid setup. The final
local RED ran in 0.472 seconds (see raw receipt for authoritative timing). Ruff lint/format and planned Requirements
validation passed. Fresh SpecFact bug-hunt review is retained outside source; protected CI RED remains outstanding.

Final bug-hunt review returned PASS with 0 findings.

## Authenticated CI RED before implementation

Requirements run35064400758 attempt2 retained artifact10433257931, digest
`sha256:4829478c0342cfa0d8b986228f26450bb8bcfae9eed720862aba42035cf3ee8b`. Its report has gate_decision pass,
observed_maturity red and failing-first-proven. It binds source7e7906925d3326c2afa65fce62076944a4f0d0a2,
tree2371b79e8b2f643fbd6d18d7af20da7223e053a0 and base2f9567e28e98b082801b13ff02e863933ce2f0f2.
JUnit contains twelve actual assertion failures, zero errors/skips, 1.186 seconds on the hosted runner.
Only after inspecting this accepted artifact were the workflow authentication blocks, Node setup and docs edited.

## Implementation and local GREEN

On 2026-09-16 (Europe/Berlin), both documentation authentication jobs were changed to load the canonical verifier and
public key directly from the separate base checkout. The reviewed wrapper is never executed. All required bundles
and additional exported source bundles must pass signature, payload and checksum validation before export. Node
24.16.0 is explicit in each native-JavaScript test job; the promotion skip remains intact. Runtime prose was wrapped
without splitting command spans.

The exact twelve mapped cases and existing authentication, fixture, trigger and follow-up regressions passed:
56 passed, zero errors/skips in 9.19 seconds. This includes the two complete push-filter preservation controls,
retained separately from the all-failing RED plan. The smart-test command selected the full baseline and returned
3201 passed, 9 existing conditional skips and 2 third-party Lark deprecation warnings in 240.55 seconds, with 64%
repository coverage. The affected 56-test selection contains no skips.

Formatting, lint, workflow lint, strict OpenSpec, documentation/command validation, reproducible delivery input
validation, frozen uv resolution and all four core module signatures passed. The authoritative full type check
reported zero errors and 1526 existing warnings; lint's targeted type surface reported zero errors/warnings.
Contract-test reused its unchanged-input cached result; normal commit hooks also enforce the contract stage.

The newly added mapping was indented to pass direct yamllint. Its parsed content, canonical mapping digest
`cf5b813e163bdc5ae711df3d0363da1c16302de6eaed8829e8b8eab04d853ce4`, independently rebuilt plan digest
`6d8e6dd70c9906ded44e319e844c13e2aa4088ae53eba8a070694b3ba0b02b5a`, and frozen test bytes remain unchanged.
Independent review confirmed this; the raw YAML formatting changed. No historical proof mapping was edited.

Repository-wide YAML output still contains nine pre-existing errors in the archived requirements08 metadata/mapping
and the requirements07 mapping. These frozen inputs are outside this change and are preserved. The wrapper exits
zero despite those messages, so its exit status is not represented as a clean full-repository YAML result. Direct
lint of this change's mapping passes, and workflow lint passes. The affected scope has no YAML exception.

Independent implementation review reported no findings after correcting two blank-line spaces and a wrapped command
span. Fresh `specfact code review run --bug-hunt --json` on the new Python test returned PASS, score120, zero findings
at 2026-09-16T06:58:57.134259Z. Logs and reports are retained in `/private/tmp/specfact-738-*`; hosted GREEN remains
the delivery authority. The reviewed test file SHA256 is
`468c7edbe079096a7c03fbeef9c175384143aec8da8bc048ba09fd1690007aa3`.

## Review clarifications

The measured 64% line coverage exceeds the unchanged executable threshold of 50% in
`pyproject.toml` `[tool.coverage.report].fail_under`. `openspec/config.yaml` explicitly makes the 80% target optional
when contract-first gates are satisfied. Both hosted Contract Validation and Contract-First CI passed at02f8ed01.
The separate 80% contract-coverage threshold is not a line-coverage threshold. No coverage configuration was changed;
we do not claim 80% total or 100% critical-path coverage. The completed task records the configured passing gates.

Review also clarified explicit pre-acceptance module-signature verification and cleanup, plus the post-acceptance
OpenSpec archive command. All four core manifests passed strict verification; this workflow-only implementation
changes no signed module assets. Generated archive changes remain a post-merge action, preserving current proof.
