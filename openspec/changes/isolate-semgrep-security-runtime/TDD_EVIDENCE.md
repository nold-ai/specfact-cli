# Test-first evidence

## Current proof status

The owner-approved correction now selects 23 cases. It changes virtualenv to
21.14.12 and python-discovery to 1.6.1, adds packaging 26.3, and binds the exact
certifi 2026.10.19, GitPython 3.2.0, and PyJWT 2.15.1 selections. The artifact
probes and all fifteen supplementary controls remain intact. A fresh local run has 23 failures, zero errors, and zero skips. All fifteen
supplementary controls pass. Independent acceptance and fresh native RED are
pending for this changed proof.

Every review and native result below applies only to its original mapping and
test bytes. None supplies acceptance or native RED for the corrected 23-case
mapping. The prior acceptance receipt is retained unchanged in
`requirements-proof/pre-correction-review-evidence.json`. The active receipt
has decision `pending` and a repository-relative status reference.

## Local RED before production edits

Captured on 2026-10-22 Europe/Berlin against main commit 5262efb0 in the
dedicated release worktree. The final exact mapping selects 34 tests.
Result: **19 failed, 15 passed, 0 errors, 0 skipped**. The unchanged frozen
main dependencies ran in a newly bootstrapped private Python 3.12 environment.
The baseline runtime version remains 0.55.4.

Observed failures include the compromised emSign certificate fingerprint in the
hash-pinned certifi wheel, an outside GitPython submodule reaching the clone
boundary, and PyJWT inspection mutating caller options. The source distribution
build fails because modules/bundle-mapper is absent. The other failures establish
old tooling selections, old documentation selections, missing bounded JSON floor,
the missing approved MCP record, old Semgrep selection, and old release metadata.
The expiry and future-review cases fail on the missing register's different
diagnostic. Existing negative audit cases and hostile wheel controls pass.

The exact frozen PyJWT probe also executes signed and padded token decoding.
No installed verifier PyJWT import supplies that compatibility evidence.

Local command:

```sh
. /private/tmp/specfact-release-20261022/red-owner/env.sh
python - <<'PYTEST'
import json
import subprocess
import sys
from pathlib import Path
root = Path("/private/tmp/specfact-release-20261022/red-owner")
selectors = json.loads((root / "selectors.json").read_text())
raise SystemExit(subprocess.call([
    sys.executable, "-m", "pytest", "--override-ini", "addopts=", "-q",
    f"--junitxml={root / 'mapped-local-red.xml'}", *selectors,
]))
PYTEST
```

Local artifacts:

- `/private/tmp/specfact-release-20261022/red-owner/selectors.json`
- `/private/tmp/specfact-release-20261022/red-owner/mapped-local-red.log`
- `/private/tmp/specfact-release-20261022/red-owner/mapped-local-red.xml`
- JUnit SHA256 `1de2aacfd11fc90c4bf422e2824adadaa9aeeacbeef5297eaff28081e79defec`

## Native planning and review status

`openspec validate isolate-semgrep-security-runtime --strict` passes.
Ruff checks pass for all seven changed test files.
The released immutable fixture's native staged `planned` gate passes.
Its source mapping digest is `sha256:8e3941ca05ccf9bceaea351df6cc1e642508debfc4ab87ecdc7b6b9cc45e6820`.
The combined plan digest is `sha256:9ef1ef74652759ecb82f7af7c8fa2b19c1d36b0d0bf043e2ed9b1a764bae95b2`.
Independent AI technical review accepted this exact mapping and its 34 selectors.
The retained review is `requirements-proof/independent-review.md`, SHA256
`a981d9f787bd7dab64650254f50ebaa74cef55b79af64441c41525d7ced9692e`.
The acceptance record identifies that reviewer and does not represent human authority.

Native test-authored acceptance, normal local hooks, a test-first commit, and
retained native CI RED are still required before any production changes.
Local JUnit does not replace native CI provenance. Mapping, selected tests,
ancestor conftest files, and transitive Python imports must freeze after native RED.
No prior dev admission or local signing supplies native evidence.

## Final verification still required

After native RED, verify the refreshed official artifacts and both strict audit
lanes, actual Ruby compatibility and documentation builds, changelog scope,
published-runtime byte equality except authorized versions, strict signatures,
and all required quality and CI gates. Merge and publication remain unauthorized.

## Test-first commit checks

The normal pre-commit hooks passed, including native test-authored planning,
format, lint, workflow and Markdown checks, and enforced Code Review.
Code Review reported 0 errors, 45 warnings and 3 informational observations.
All 45 warnings and two observations point to unchanged existing test bodies.
Their retention is a narrow baseline exception for this dependency-only release,
not a waiver of a required check. The new observation concerns the frozen JWT
probe's 48-line install, subprocess and assertion sequence. That explicit
sequence keeps its authenticated delivery artifact and isolated interpreter
visible. No additional wrapper or shared mutable fixture is introduced solely
to reduce its line count. Independent mapping review verified this boundary.

The exact local report and changed-line comparison are retained under
`/private/tmp/specfact-release-20261022/red-owner/test-only-code-review.json` and
`code-review-line-triage.json`. Native CI RED and final release gates remain pending.

## First native attempt and corrected proof selection

GitHub run [39809800598](https://github.com/nold-ai/specfact-cli/actions/runs/39809800598),
at test-only commit `dd1b4121944f247c4d5dff0903902e2721d8c1a6`, retained
artifact `12440155998`. It executed all 34 exact cases with genuine failures
and passing controls. Its unchanged report has `gate_decision=fail`,
`observed_maturity=incomplete` and fifteen `red-proof-passed-not-failed` findings.
This artifact is not accepted RED. Its original bytes remain unchanged.

The pinned native lifecycle requires each RED selector to fail. Earlier planning
and review incorrectly assumed passing safety controls could share that plan.
The corrected selection retains all nineteen actually failing cases. Fifteen
already-passing malformed-artifact and negative-audit controls remain unchanged
and enforced by the normal required test suite. They will run during final
verification. This changes no assertion or production behavior and waives no
check. A fresh independent review, test-only commit and accepted native RED
are required before dependency edits. The earlier 34-case review is historical
evidence, not acceptance of this corrected mapping.

## Corrected mapping acceptance and proposal bytes

Independent AI reviewer `/root/release_corrected_mapping_review` using
gpt-6-astra accepted the nineteen-case mapping. Current acceptance references
`requirements-proof/corrected-mapping-review.md` and source mapping digest
`sha256:1abe2b6dc3e8a294795a00236803b002b98ad02ec05b22b2b0deb2cbf13a2020`.
All nineteen selectors have genuine recorded CI failures. All fifteen omitted
controls remain byte-identical in required tests. Local rerun of the corrected
selectors reports nineteen failures, no errors and no skips.

The earlier report's proposal hash predates normal Markdown autolink formatting.
The new independent review examined the exact two URL-wrapper changes and
accepts current proposal SHA256
`83e860e44ebc7778c48fb0ef382ed26c4d8ebe80ccdcd18037f85c57f37d21df`.
The original report remains historical with its original byte identities.
Fresh native RED is still required before production edits.

## Frozen GitPython closure and explicit Ruby scope

The nineteen-case mapping achieved accepted native RED at commit
`08126f3f8a8e46a79c46c574dfd7b0c44e915831`, run
[39811618606](https://github.com/nold-ai/specfact-cli/actions/runs/39811618606),
artifact `12439638334`. Its unchanged report has `gate_decision=pass`,
`observed_maturity=red`, and no findings.

Subsequent review identified that the GitPython probe borrowed gitdb and smmap
from the verifier environment. The probe now installs the exact three hash-pinned
requirements into the isolated target. Its selector and assertions are unchanged.
Twelve private missing, duplicate and unhashed-declaration controls pass. A real
rerun installs the three wheels and fails at `AssertionError: clone boundary reached`.
An earlier DNS-limited invocation is not behavioral evidence. This test edit
requires fresh native RED at its new commit before production changes.

The proposal and task now explicitly name creation of the already-mapped Ruby
compatibility probe and workflow. No new production touchpoint or release scope
is added. New independent review must accept the actual current proposal bytes.

Independent AI reviewer `/root/release_probe_final_review` using gpt-6.1-sol
accepted the strengthened frozen closure, unchanged nineteen-case mapping and
current proposal SHA256
`7a448d1b6702eb3abca880172f6286ac4e77948119023f07ea21796a4b4a8f97`.
Current technical acceptance references `requirements-proof/frozen-closure-review.md`.
Earlier review reports retain their original historical boundaries. Fresh native
RED at this test-only revision remains required before production changes.

## Approved correction after the candidate audit

On 2026-10-22 Europe/Berlin the strict primary frozen audit rejected the prior
virtualenv 21.11.0 candidate for these five findings:

- CVE-2026-113726 / GHSA-5vjq-rrrf-7h2q
- CVE-2026-113776 / GHSA-8rjx-v5ww-45pp
- CVE-2026-113732 / GHSA-c947-3pg5-gm8q
- CVE-2026-113725 / GHSA-vxj4-q4g9-crj7
- CVE-2026-113722 / GHSA-c978-59m8-c77v

The actual failed audit is retained in
`/private/tmp/specfact-release-20261022/implementation/security-audits.log`.
The owner explicitly approved correction to official virtualenv 21.14.12 and
its required python-discovery 1.6.1 and packaging 26.3. The authenticated wheel
metadata and ordinary scratch resolution are retained under
`/private/tmp/specfact-release-20261022/audit/virtualenv-correction/`.
That resolution changed exactly those three versions relative to the prior
candidate, with no package added or removed. No new exception is authorized.

The previous 19-case proof was accepted at test-only commit
`a2ee2c9d96e1cce5ba1f13f733ccc49580262ffb`, run
[39813086468](https://github.com/nold-ai/specfact-cli/actions/runs/39813086468),
artifact `12441520223`. Its report has `gate_decision=pass` and
`observed_maturity=red`. It is superseded for this correction because the spec,
test table, and mapping bytes changed. Its original artifacts remain untouched.
The prior candidate's 19 selected passes and 64 regression-file passes are also
historical evidence, not verification of the newly approved graph.

Before editing the spec or tests, all twelve production paths matched the
implementation checkpoint and its saved copies. A second full patch and file
backup is retained under
`/private/tmp/specfact-release-20261022/correction-tests/`. Ten tracked production
files were restored to HEAD, and only the two backed-up new Ruby files were
removed. No production correction has been applied. The dedicated verifier
environment was preserved. Artifact probes obtain the restored baseline's exact
frozen wheels independently of that environment's installed package versions.

The existing Git consumer fixture correction remains test-only. Its recursive
staging had included `.git/config`, causing three genuine GitPython 3.2.0 setup
failures. The one-line `repo.git.add("--all")` correction preserves the consumer
assertions. The original failures and 29 passing affected tests are retained in
`implementation/git-consumer-regression.log` and
`implementation/git-consumer-regression-fixed.log` beneath the private release
directory. Independent review accepted that fixture correction in
`candidate-precorrection-review.md`. This path is outside the native mapped proof.

Review findings `PRRT_kwDOQLaPE86vRvLU` and `PRRT_kwDOQLaPE86vR4YF` are valid.
The existing parameter table now asserts exact lock and export selections for
certifi, GitPython, PyJWT, and packaging. The active acceptance reference is
repository-relative and awaits the coordinator's fresh independent reviewer
receipt. The old mutable branch URL is retained only in the historical receipt.

The canonical planned command uses the immutable release base because the local
`main` ref selects unrelated changes. The initial broader planning failure is
retained as `planning.json`; `planning-base.json` and `plan-base.json` are the
successful canonical outputs from the unchanged released CLI:

```sh
. /private/tmp/specfact-release-20261022/red-owner/env.sh
export GITHUB_BASE_REF=main
python scripts/requirements_evidence_delivery_gate.py \
  --base-ref 5262efb0881e4fac7697d629b0530250342bc656 \
  --required-maturity planned \
  --output /private/tmp/specfact-release-20261022/correction-tests/planning-base.json \
  --summary /private/tmp/specfact-release-20261022/correction-tests/planning-base.md \
  --plan-output /private/tmp/specfact-release-20261022/correction-tests/plan-base.json
```

Initial sandbox runs failed DNS resolution while fetching official wheels. Their
`sandbox-*.log` and `sandbox-*.xml` outputs are retained and are not behavioral
RED or passing control evidence. The unchanged commands were then rerun with
network access. Exact pytest argument arrays are retained in
`correction-tests/mapped-command.json` and `correction-tests/controls-command.json`.
Fresh independent acceptance, normal hooks, and genuine native RED at the new
revision remain required before production reapplication.

## Corrected local failing-first result

The network-enabled run completed with **23 failed, 0 passed, 0 errors, and
0 skipped**. The separate controls run completed with **15 passed, 0 failed,
0 errors, and 0 skipped**. These are local observations, not native CI acceptance.

The actual certifi wheel retains the compromised root. The GitPython probe
reaches `AssertionError: clone boundary reached`. PyJWT adds seven verification
options to the caller's dictionary. The ordinary offline source-to-wheel build
fails because the source archive lacks `modules/bundle-mapper`. The exact-version
cases fail on the restored older lock values, including packaging 26.2 rather
than 26.3. Other cases retain the expected old release/documentation versions
and absent MCP exception diagnostics. No network or install failure is counted
as behavioral proof in this result.

The canonical combined mapping digest is `sha256:6d114e1c20cf149c24c310009d9a3f975ee1cf4626c6d67842d0033d029c147f`.
The plan identity digest is `sha256:29af99fc48f7afd6a0dc641716e9ccb5c8bf230ef290848cf5331738a33e7880`.
`correction-tests/mapped-local-red.xml` SHA256 is
`49653320cc55fdc741b5344850631c6e9e067a4fed40598b5296175326884bd4`.
`correction-tests/controls-green.xml` SHA256 is
`c4715403faf3bcae521030eea59784ee09d645119d80a55b92a41d1e8b5a75be`.
The sibling raw logs, argument arrays, and `failure-diagnostics.json` preserve
every case's actual failure message. The artifact paths are relative to
`/private/tmp/specfact-release-20261022/`.
