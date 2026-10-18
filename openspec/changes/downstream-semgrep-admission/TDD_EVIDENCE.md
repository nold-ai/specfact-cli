# Downstream Semgrep evidence

## Specification and authored RED

Signed specification commit: `40dc5c93d2a25284550247ce04147ae4e8509df6`.
Normal hooks and strict OpenSpec validation passed before authored tests were
copied into the worktree. The pinned planned Requirements validator accepted
all four native requirement mappings without findings.

Actual worktree run before production code existed:

```text
python -m pytest tests/unit/scripts/test_downstream_semgrep.py -q --tb=short
40 failed in 0.47s
JUnit: 40 tests, 40 AssertionError failures, 0 errors, 0 skips
```

The failures assert that the real build/admission boundary is absent. They are
initial missing-behavior evidence, not a claim that every rejection input exposed
a separate existing vulnerability. Synthetic wheel, provenance and audit fixtures
exercise the contract; they are not authenticated production admission.

The owner accepted exact mapping
`sha256:83f12bcec0ff756681c2cc1188c431fce1327e6d3371fae6bc4df4bf1ddd8425`
on 2026-10-16 at 23:04 Europe/Berlin. The separate accepted record identifies the
actual human reply. The native matrix inspection obligation remains pending.

The mapped complete-audit case was strengthened with candidate-only audit
assertions under the same accepted mapping. Actual pre-extension run:
`1 failed in 0.09s`, AssertionError `Candidate audit proof is absent`.
The original frozen test proposal, both RED runs and hashes remain retained in
`/private/tmp/specfact-downstream-semgrep-20261016/` during local preparation.

## Local MCP candidate experiments

A separate non-listening control on MCP 1.29.0 fails eight lifecycle/default
controls, with zero errors. Actual DELETE and refused opening requests retain a
registered session. MCP 1.30.0 passes those eight checks and the actual Semgrep
stdio initialize/list/custom-scan probe. Additional local checks verify the real
Semgrep HTTP factory rejects missing/malformed credentials and the SDK binds a
session to the verified test principal. These are isolated candidate experiments,
not seven-platform proof or protected producer admission.

## Pending

- Signed authored-test commit and exact commit-bound RED retention.
- Final build/admission GREEN and independent review.
- All 21 real platform/Python cells, including full SAST and MCP evidence.
- Normal native/FULL, quality, dependency/provider trust and signature gates.
- Protected producer bootstrap and separately reviewed production adoption.

No production pin, existing audit/floor or trusted provider has been changed. The
existing frozen MCP audit remains a release blocker. No merge is authorized.

## Native proof branch

The first implementation PR #773 correctly failed the unchanged hosted
Requirements gate with `prior-red-proof-missing`. The earlier local signed test
snapshot is real failing evidence, but cannot substitute for the hosted receipt.
This branch retains the original specification and authored-test ancestors and
freezes the final forty-selector test file before implementation. It contains no
implementation changes. The first hosted run must produce actual RED evidence.
The old PR, commits and failed artifacts remain preserved. No history is rewritten
and no existing gate or provider is changed.

## Corrected test-only local RED addendum, 2026-10-17 Europe/Berlin

This addendum supersedes the earlier claim that the forty-selector test file was
final. Historical commits and evidence above remain preserved. Test-local
Protocols replace the static type-only production import so future implementation
bytes are not imported into the authored test dependency surface. The synthetic
recipe now contains a runtime-policy object and its canonical SHA-256. All 40
original selectors and their 48 assertion nodes are unchanged. The accepted
requirements mapping file is byte-for-byte unchanged; no new requirement,
scenario, mapping case or acceptance record was added.

Ten supplemental review cases cover protected attestation identity, rejection of
an approved but invalid matrix, and preserved ZIP member attributes. Eight further
supplemental cases cover five runtime-policy rejection inputs and three real
subprocess encoding checks. The encoding checks simulate the Windows cp1252 text
default, assert UTF-8 stdout/stderr text and retained evidence, and require invalid
UTF-8 on either stream to fail closed. They do not replace native Windows proof.

Before production code exists in this worktree, the final local run was:

```text
hatch run python -m pytest tests/unit/scripts/test_downstream_semgrep.py tests/unit/scripts/test_downstream_semgrep_review_guards.py tests/unit/scripts/test_downstream_semgrep_runtime_evidence.py -q --tb=short --junitxml=/private/tmp/core774-root-causes/corrected-tests-red.xml
58 failed
JUnit: 58 tests, 58 AssertionError failures, 0 errors, 0 skips
```

Failures explicitly report `Downstream admission boundary is absent` or
`Downstream matrix runner is absent`. This proves missing behavior in the
test-only ancestor, not separate exposed defects in an existing implementation.
The log and JUnit artifact are retained in `/private/tmp/core774-root-causes/` as
`corrected-tests-red.log` and `corrected-tests-red.xml`.

Scoped `hatch run ruff check`, `hatch run ruff format --check`, and
`hatch run type-check` on those three test files pass. BasedPyright reports
`0 errors, 0 warnings, 0 notes` using the canonical project configuration and the
locked checker installed by `npm ci --ignore-scripts --prefix tools/basedpyright`.
`openspec validate downstream-semgrep-admission --strict` passes.

No corrected hosted RED receipt, implementation GREEN, native matrix completion,
commit or publication is claimed here. Those gates and the unchecked internal
wiki synchronization task remain pending.

## Additional review corrections, 2026-10-17

Independent review exposed lossy timeout decoding. Supplemental timeout cases now
check legitimate UTF-8 and reject invalid bytes on either stream. CRLF and CR
cases preserve the existing universal-newline text behavior across completed and
timed-out commands. Two archive cases also reproduce unauthorized compression
and creator-version changes that the published verifier accepted with valid
RECORD contents. The comparison uses the reviewed ZIP_STORED transformation, not
the original compressed representation. Broader ZIP flag and volume semantics
remain unresolved because CPython rewrites those headers during serialization.

The final corrected test-only snapshot supersedes the 58-case snapshot above.
Its local JUnit records 67 tests, 67 AssertionError failures, zero errors and zero
skips because both production boundaries are absent. The original forty selectors
and forty-eight assertion AST nodes remain unchanged, as does the accepted mapping.
No new owner acceptance is asserted.

A disposable copy of published implementation `7a1abb75` first reproduces eight
failing cases for two causes and then two additional archive failures. The
minimal encoding, policy-binding and archive comparison patch passes all 67
corrected tests locally. This is prospective patch evidence in a disposable copy,
not implementation restoration to the test-only branch or hosted Requirements
GREEN. No protected artifact, native Windows result or complete new matrix is
claimed. The old published native matrix ended with 18 successful cells and three
Windows failures; its aggregate correctly fails.

Local artifacts are retained under `/private/tmp/core774-root-causes/`:
`test-only-67-red.xml`, `old-implementation-red.xml`, `zip-metadata-red.xml`,
`newline-red.xml`, and `candidate-final-green.xml`, with their matching logs.
Publication awaits a decision on a fresh test-first successor PR. The existing
Requirements workflow searches only the same head branch, and production already
occurs in #774 history. No history rewrite, merge, retarget, policy exclusion or
reuse of a stale hosted receipt is authorized.

The final normal unmodified pre-commit run passes. SpecFact reports `PASS` with
zero findings at all severities. Two supplemental test names were made specific.
The analyzer's initial missing pytest types were resolved by preparing `.venv`
from exact `requirements/ci/locked.txt`, without changing dependency inputs. The
released Requirements validator passes at `test-authored` maturity. Contract
execution was skipped by the native hook because its input status was unchanged;
no new contract execution is claimed. Scoped type checks and strict OpenSpec pass.

## Authenticated successor hosted RED, 2026-10-18

The owner approved the successor plan on 2026-10-18. Active PR #775 targets
`dev` and initially publishes only the signed test/specification source.
Run <https://github.com/nold-ai/specfact-cli/actions/runs/39162475090> retained
Requirements artifact `12148859551`. Its service archive digest is
`sha256:c67d2a8e0736279967474f7ee5de5f4c0f298183c7dfd0061ab5e06a327594e9`.
The archive size and hash match the GitHub artifact metadata.

The native report binds commit `398235137d1a3c2634991cc77feb237eebd86a9d`,
tree `ca5315fb1c3180bd26c4f14dea8178fbdb44742b`, base
`729a53bd4bcbba94886cff5c73d7092bef6ceb94`, the exact test-file hash,
and all 40 original mapped selectors. Its JUnit contains 40 intended
`AssertionError` failures because the admission boundary is absent, with zero
errors and zero skips. The report passed reconciliation at RED maturity with
`failing-first-proven` delivery status and no findings. The producer's later
merge-readiness enforcement correctly failed this test-only checkpoint.

The unchanged native provenance binder revalidated a copy of the retained
report and JUnit with exit code zero. Existing report bindings remained
unchanged. Runtime implementation was still absent at verification. Only after
this verification did implementation restoration begin. This receipt is not
native platform GREEN, production authority, or completed admission evidence.
The original raw hosted ZIP, report, JUnit and metadata are retained in the
durable local artifacts directory. The committed receipt contains their public
identities without substituting for normal workflow retrieval and validation.

PR #774 was closed unmerged as superseded after the successor and this RED were
verified. Its existing review findings remain tracked for the successor. No
review thread was treated as fixed merely because the old PR closed.

## Post-RED implementation and canonical archive correction, 2026-10-18

Only after authenticated hosted RED, the six retained runtime/workflow files
were restored from the published predecessor. Against the unchanged 67 tests,
the retained source produced 16 failures and 51 passes. Canonical runtime-policy
digest binding and strict caller-side UTF-8 decoding for ordinary and timeout
output restored all 67 passes. Newline behavior remains compatible with text
mode. Format, Ruff and targeted BasedPyright passed with zero diagnostics.

Independent review then reproduced four still-accepted serialized ZIP metadata
changes. Three architecture sketches selected one shared canonical writer over
an incomplete header allowlist or an additional layout parser. Nine new
supplemental tests ran before this additional script change. The eight actual
mutations failed their expected rejection with `DID NOT RAISE ValueError`; the
valid upstream UTF-8 normalization case passed. They cover member flags, volume,
extraction version, archive comment, local-header-only changes, trailing bytes,
prefix and central-directory order while preserving runtime payload and RECORD.

The final focused run passed all 76 cases, including all 67 earlier cases
unchanged. The synthetic builder output remains byte-identical before and after
the canonical writer refactor. Temporary-file OSError and ValueError probes
produce AdmissionError. Ruff format/lint, targeted BasedPyright and whitespace
checks passed. The original mapped source hash, 40 selectors, 48 assertion AST
nodes and accepted requirements mapping remain unchanged.

These are local CPython 3.12.13 results. The complete native matrix, Windows
output behavior and cross-runtime serializer equivalence remain required hosted
acceptance. No production admission, authority grant, dependency pin change,
security waiver, completed platform proof or protected producer is claimed.
The raw local logs, XML, commands and source hashes are retained under the
durable `post-red-fixes` and `zip-boundary-fix` artifact directories.

## Final local publication gates, 2026-10-18

Normal staged hooks passed with the exact locked Requirements/review fixture
and separately authenticated documentation fixture. Requirements evidence,
strict OpenSpec, formatting, canonical type checks, lint, YAML, command overview,
all 117 generated command contracts, 393 documentation command prefixes and
documentation accountability passed. The review gate returned
`PASS_WITH_ADVISORY`, with zero blocking findings.

The ten remaining warnings and two readability advisories match the
predecessor's documented preinstallation and SDK-signature dispositions. A
fresh independent source review confirmed the same scope and corrected the
SDK wording to its tested five-argument projection plus protocol `self`. No
rule, threshold, scorer or trusted gate changed. The new test helper's actual
complexity and duplicate-shape findings were fixed in code. The final 76-case
run still passes. Earlier metrics and equivalence logs predate the final
shared-header helper; the final source has separate passing-run evidence.

The native hook skipped contract execution because its input-status check
reported no changes. No new contract execution is claimed. Native matrix,
independent hosted checks, protected producer bootstrap and production adoption
remain incomplete. Local passing gates do not make this PR merge-ready.
