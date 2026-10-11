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

## Policy review repair

Review of signed head 198f4326 identified a hard policy violation: the older
Code Review fixture declares Python BasedPyright, whose wheel requires an
unofficial Node runtime. Artifact inspection and passing checks cannot override
`docs/agent-rules/55-dependency-hygiene.md`. The prior seven-package seed and its
passing results are historical diagnostics, not merge readiness.

Six new smoke policy/fixture controls failed before this repair. A separate trust
control also failed because the auxiliary graph was not checked. The repair uses
the already reviewed portable snapshot 046d366c (Code Review 0.50.1), with its
real unmodified manifests, separately from the unchanged 69f0758 Requirements
provider. CI authenticates the exact commit/tree and cleanliness before execution.
The seed now contains only Lz4 4.4.5; the existing npm BasedPyright runner stays
in use. Existing wheel-prohibition and security-floor policy now checks the
auxiliary lock as well. No native mapped selector/fixture bytes are changed.
Fresh full smart, frozen, security, review and native checks are required.

Portable fixture validation: real direct/console marketplace smoke passes;
19 initial policy/trust controls and 114 workflow controls pass. The complete
smart run passes **3,238 tests, nine skipped**, 163.06 seconds, with unchanged
64% coverage and configured threshold. All three audits, lock/export parity,
normal parent plus Lz4-child license scans, module signatures and 0.55.5 > 0.55.4
version gates pass. Full typing has zero errors and the same 1,526 baseline
warnings; all seven changed Python files have zero diagnostics. Independent
Semgrep has zero findings outside the unchanged baseline.

The review's new parameter-count warning is resolved by retaining the trust
checker's original five-parameter API: the auxiliary graph always uses its
committed authoritative paths. The focused trust controls still reject the
prohibited wheel. The remaining three contract warnings in the pre-existing
stdlib-only trust checker are the same pre-dependency boundary as documented in
its module header and dependency-hygiene rules; `python -S` positive/negative
controls pass. Importing third-party decorators before frozen bootstrap would
break that boundary. Existing `test_*process*` naming warnings describe actual
pytest subprocess invariants; their bodies/selectors are unchanged and preserve
prior test evidence. The existing version-parser information item retains an
explicit invalid-version branch for fail-closed security-floor diagnosis.
No rule or finding is suppressed and no new clean-code regression is accepted.

Two mocked launcher-lifecycle tests now model the fixture-verification seam;
the separate real Git commit/tree/dirty rejection tests and real marketplace
smoke remain active. The stale blanket license assertion is narrowed to retain
the original Code Review-only GPL boundary while requiring normal scanning of
the sole Lz4 smoke seed. An interrupted intermediate rerun is retained as
incomplete evidence, not a pass.

Final interface verification: **3,238 passed, nine skipped**, exit 0,
160.91 seconds; unchanged coverage 64%. Absolute-path changed-script contract
validation passes with zero violations. Final SpecFact self-review scores 94,
zero errors and no new clean-code regression; all remaining raw advisories have
the explicit stdlib-boundary or unchanged-selector dispositions above.

## Complete child import isolation

A second external review correctly identified that read-only parent site-packages
and inherited PYTHONPATH can mask missing or incompatible child dependencies.
Two new controls fail before implementation: the import path includes parent/
inherited directories, and the seed omits the complete frozen CI graph. The
repair installs the full hash-protected CI graph plus the Lz4 seed into each
owned child, uses only the explicit CLI source PYTHONPATH, and builds the console
entry point with its child-installed frozen backend. Normal marketplace
resolution remains enabled with no index. The direct native prefix probe and
all original mapped test/fixture bytes remain unchanged. Earlier local/hosted
passes remain historical; fresh complete validation is required on this repair.

The initial pip-only installation exposes the existing source-only CommentJSON/
Lark packages: applying wheel-only installation to the whole CI graph correctly
fails. Preserve that diagnostic. Materialize the exact full graph with the same
frozen uv protocol as CI, offline into the owned child; unavailable cached source/
build artifacts fail, with no resolver/network fallback. Then install the reviewed
Lz4 wheel through its exact hashes. This reuses frozen artifact data rather than
parent import directories and preserves all normal marketplace dependency checks.

The child cache path assertion also fails before repair (KeyError: UV_CACHE_DIR).
The implementation queries uv's original artifact-cache path before changing HOME;
offline frozen sync copies packages into the child and never adds cache/parent
directories to PYTHONPATH. See the official uv cache-directory precedence
<https://docs.astral.sh/uv/concepts/cache/> (accessed 2026-10-11).

Normal marketplace resolution needs candidate artifacts even when packages are
already installed. Two additional controls fail before wheelhouse implementation:
the frozen transitive hash selector is absent and PIP_FIND_LINKS is missing. The
repair selects only the authenticated module closure from uv.lock and exact
committed hash exports, downloads wheels with require-hashes/no-deps, and supplies
that owned directory with no index to normal pip-tools resolution. Missing graph
entries or hashes fail. The smoke project's ordinary pip-tools configuration emits
pins without duplicating transport options already supplied by its environment;
this leaves dependency validation and installation active. No force or skip-deps
flag is used. Ten positive/negative controls pass. Real direct and console smoke
both pass after full child installation and marketplace resolution. Earlier pip
network, source-only wheel, cache-miss and option-emission failures are retained as
diagnostics rather than passing evidence.

Final owned-child smart gate: **3,242 passed, nine skipped, two warnings**,
171.93 seconds, exit 0; coverage remains 64% and its existing threshold is
unchanged. Absolute-path contract validation passes with zero violations. Both
changed Python files have zero typing diagnostics. Frozen lock/export parity,
three advisory audits, dependency trust, normal license scans, signatures,
0.55.5 > PyPI 0.55.4 and zero-new-findings Semgrep gates pass. Negative-test
log messages from smart-test regression fixtures are expected captured output,
not failures of this complete run. Original native mapped selector/support bytes
remain unchanged from 0dbcc8e3. Protected exact-head authority and prerequisite
integration remain pending; these executable passes cannot replace member approval.

The final broad self-review covers all **20** prerequisite Python files (including
existing workflow regression fixtures), scores **92, PASS_WITH_ADVISORY**, zero
errors. The new CC16 selector error and new seed-length information item are
resolved with separate manifest selection, frozen graph traversal and sync helpers.
The remaining nine warnings are the five stdlib/pre-dependency contract boundaries
and four unchanged naming false positives already disposed above. The nine
information items concern the unchanged invalid-version branch and explicit
security/workflow fixture setup. Collapsing those setup assertions would reduce
reviewability of independently tested attack boundaries; no rule is disabled,
no finding is hidden, and no new clean-code regression is accepted.
An initial focused invocation without the portable fixture skipped its real smoke;
that invocation is not used as real-smoke evidence. Full smart and the separately
executed explicit-fixture console probe exercise the real authenticated fixture.

Post-review complete rerun: **3,242 passed, nine skipped, two warnings**,
168.26 seconds, exit 0, coverage 64%. Final changed-file typing has zero
diagnostics and the reviewed helper contracts pass with zero violations. The
explicit-fixture console smoke passes independently. The protected/core native
adapter remains byte-identical (SHA-256 6cc6c72de461980aba67c3c144364d7ac4f8f53fb351e77b31bfc8fcdc450d89).
