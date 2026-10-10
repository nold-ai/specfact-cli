# Gate readiness evidence

## Authored failures — 2026-10-11 Europe/Berlin

Specs precede tests; production files remain unchanged against dev
553b46f01c6581c96dc92133b6e77404c8df7cd9. The two selected regressions fail:

- Native stack resolution: the missing adapter prevents resolving an authentic
  root boundary; the parent assertion records a real failure.
- Direct smoke isolation: querying the actual launcher reports the running
  pytest environment prefix, outside the smoke workspace.

Command: `.venv/bin/python -m pytest -q -o addopts=''` with the two mapped
selectors. Result: **2 failed in 0.67 seconds**. Raw log retained at
`/private/tmp/specfact-security-stack-20261011/prerequisite-red.log`.
The child probes never mutate a shared installation. Their test bytes and
fixture are to remain frozen through implementation and final reconciliation.

Strict OpenSpec validation passes. The new-test self-review has zero findings.
The first planned mapping diagnostic identified the released provider's
requirement-slug scenario identity constraint. Correct the mapping metadata
before authored publication; this does not change test behavior or production.
No member authority is inferred from the implementation-agent acceptance record.

## Native and implementation validation

Native authored run [38091288977](https://github.com/nold-ai/specfact-cli/actions/runs/38091288977)
retains `failing-first-proven` for both unchanged selectors, with no findings.
The report and JUnit remain original artifacts; no passing control was labeled RED.
Implementation focused suite: **29 passed in 1.70 seconds**. Direct and console
real marketplace smoke both pass; the invoking frozen pytest environment remains
unchanged. The auxiliary lock input-tamper control failed before its checker was
implemented; it now passes with the lock/export parity checks.

Organization policy: original protected-base-only verifier failed the valid native
stack test (**1 failed, 25 passed**); the implemented adapter passes all **26**
controls, including missing member authority, unrelated ancestry and stale events.
Policy tests and immutable stdlib-only adapter retain the protected execution
boundary; no PR content is imported and no required rule is disabled.

Stdlib-only stack parsing is required in the immutable policy and `python -I -S`
consumer boundary. Its contract is enforced by bounded schema validation and
negative tests rather than importing project contract decorators into that trust
boundary. This is a runtime boundary choice, not a quality-gate exclusion.

## Explicit narrow review dispositions

The self-review retains two `MISSING_ICONTRACT` warnings for
`requirements_stack_context.resolve_stack_context` and `main`. These two functions
must run under `python -I -S` in an immutable organization policy with no dependency
installation. Importing project `icontract` would break that execution boundary.
Their schema, bounded traversal, exact identity/ancestry and stable fail-closed
contracts are executable stdlib checks, covered by positive/negative regressions.
This is the rare explicit exception permitted by the agent quality rules; no
review rule, scan, or required check is disabled, and warnings remain visible.

Two existing informational readability suggestions concern unchanged functions
`_create_rootless_monorepo_demo` and `_build_local_registry`. Preserve their expanded
versioned demo/manifest fixtures: separate explicit files and fields explain the
domain contract, while a collapsed string/comprehension obscures it. Neither
function is modified by this repair. This records their inspection disposition
without suppressing findings or introducing unrelated refactors.

The first full smart run found ten failures: one leaked parent `pip-compile`
entry point and nine stale workflow/version contracts. The child PATH now
excludes the invoking interpreter's tool directory and clears its virtualenv
selection variables; normal child pip dependency installation is still exercised.
Existing workflow tests now assert the independently authenticated root base,
consumer context digest parity and retained early-failure reports. Their isolated
shell fixtures supply the new authenticated context variable. These repairs pass
**59 tests in 25.42 seconds**, including the real smoke launched through Hatch.
The new PATH control has separate genuine RED evidence; frozen native selector
files and their fixture remain byte-identical to the authored commit.

The next full run passed 3,221 tests and exposed one remaining bootstrap
archive-count expectation. The materializers now conditionally archive the frozen
smoke lock from the same authenticated base, preserving legacy bases that lack
that input. The contract test asserts that exact protected source and conditional
ordering; it still rejects invalid legacy identity/ancestry substitutions.

The existing naming advisory on
`test_invalid_utf8_authority_is_stable_metadata_failure` is a regex substring match
on **metadata**, not a generic API identifier. Its test body and selector are
unchanged and remain referenced by completed #692 evidence. Preserve that exact
selector rather than invalidate prior proof to satisfy an overbroad substring
rule. The unchanged expanded security/artifact fixture suggestions are similarly
retained for their explicit reviewed data and attack boundaries. These dispositions
remain visible in the raw review; no rule or report is suppressed.

## Completed local gates — 2026-10-11 Europe/Berlin

`hatch run smart-test-force --level full`: **3,222 passed, 13 skipped**, exit 0,
169.49 seconds. Coverage 64% meets the unchanged configured 50% line threshold;
`smart-test-status` reports no relevant changes and no full run required. Do not
confuse the separate 80% public-API contract-density threshold with line coverage.

Explicit touched-script contract validation: pass, zero violations. Changed-file
BasedPyright: zero errors and zero warnings. Full repository typing retains its
existing advisory warnings, with zero errors. Ruff, changed YAML, Actionlint and
strict OpenSpec pass. Semgrep SAST: zero findings outside the unchanged baseline;
Bandit: zero medium/high findings. All three frozen advisory audits pass. License
scans: 172 parent packages, seven Code Review smoke packages and four core module
manifests, zero violations; the exact existing Pylint Code Review-only exception
remains visible and is not widened. PyPI-ahead confirms 0.55.5 > 0.55.4.

Organization policy prerequisite [nold-ai/.github#3](https://github.com/nold-ai/.github/pull/3)
has a verified signed head and passing pinned policy CI (26 controls). Neither
prerequisite has been merged; final-head native CI and member authority remain
required before integration and dependency restacking.

The final full self-review passes (score 97), with zero errors. A new cohesive
assertion-count warning was resolved by separating smoke-lock source validation
from legacy bootstrap identities; the exact assertions remain exercised. Remaining
warnings/informational suggestions have the explicit dispositions above.

The normal commit hook rejected generated documentation drift produced with the
execution fixture. Regenerate with the separate immutable documentation fixture
046d366c190af7a188d6f48953a96edb65e766db; preserve the documented runtime/review
commands instead of committing an execution-fixture downgrade. No hook is skipped.
Live GitHub metadata validation succeeds for all five unchanged heads in #757:
each resolves root #744, protected dev 553b46f..., and consecutive parent ancestry.
