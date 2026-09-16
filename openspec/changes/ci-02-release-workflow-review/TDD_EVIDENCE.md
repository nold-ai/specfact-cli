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

## Remaining gates

Independent final mapping receipt, canonical CI RED, implementation, GREEN, required quality gates and protected
integration remain pending. No public release acceptance is claimed.

## Independent review and local quality

Independent agent `/root/pytest_discovery_fix` accepted the final twelve-case mapping and test design with no findings.
Receipt: <https://github.com/nold-ai/specfact-cli/issues/736#issuecomment-5693072266>. Exact parameter selectors match
all twelve assertion failures; positive in-memory Node controls verify the test can pass after valid setup. The final
local RED ran in 0.472 seconds (see raw receipt for authoritative timing). Ruff lint/format and planned Requirements
validation passed. Fresh SpecFact bug-hunt review is retained outside source; protected CI RED remains outstanding.

Final bug-hunt review returned PASS with 0 findings.
