# Test-first evidence

## Current proof status

The prior 23-case correction received independent mapping acceptance and native
RED at commit 8cce44f449e9559d0100064d629c81991784ab41, run 39843165302 attempt 1.
Its accepted receipt is preserved in `requirements-proof/pre-advisory-review-evidence.json`.
The subsequent local production results below remain authentic history.

The owner approved GitPython 3.2.1 and the separate exact OpenTelemetry exception.
Production inputs were restored before the specification and test changes.
The 31-case advisory mapping first received independent acceptance in
`requirements-proof/advisory-mapping-review.md`. A subsequent bounded test-only
quality amendment received fresh independent AI technical acceptance in
`requirements-proof/quality-mapping-review.md` on 2026-10-23. The active receipt
uses that repository-relative report. Both earlier receipts remain historical.
Fresh native RED for the amended test bytes remains pending. No earlier native
proof approves these changed bytes. The docs floor fixture remains held for its
matching production metadata, separate from the accepted test-helper repair.

## Superseded 23-case pending note

This note records the state before the 23-case acceptance and native RED above.
Its pending claims are historical and do not describe the current 23-case status.

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

## Corrected production verification on 2026-10-22

The coordinator authenticated native RED run 39843165302 attempt 1, artifact
12453832458, for HEAD 8cce44f449e9559d0100064d629c81991784ab41 and tree
a3cfdc441190e11a0c4db22cbdc324b44a2b7f8e. All 23 selected cases failed with
no errors or skips. The record is retained at
`/private/tmp/specfact-release-20261022/correction-tests/native-ready.json`.
Production changes began only after that acceptance. All 406 frozen source,
test, mapping and review hashes still match after the verification below.

The normal targeted resolver selected virtualenv 21.14.12, python-discovery
1.6.1 and packaging 26.3. The complete graph differs from main by the nine
approved third-party updates and the core 0.55.11 version, with no package
names added or removed. The canonical export, hash-enforced environment sync,
canonical refresh, frozen parity and `uv lock --check` passed.

Fresh local GREEN passed all 23 selected cases and all seven complete files,
68 tests, with no skips or errors. The source distribution rebuilt offline
into the real wheel. Strict signatures passed for all four unchanged module
manifests. The coordinator independently compared 295 payload members and
297 guarded source files with published 0.55.4 and accepted only the authorized
version and metadata differences. Wheel SHA256 remains
`a0ca37c5030d88d33c93286aabd1e6fe27c28224031a0b7dd4cc7d9ffa8fc709`.

Normal virtualenv creation and hash-enforced installation of the built wheel
passed. Installed-wheel GitOperations, ChangeAnalyzer and CodeAnalyzer probes
passed. Official Semgrep 1.179.0 returned one positive finding with exit 1 and
zero negative findings with exit 0, both without scanner errors. The 29 analyzer
tests passed. The separate Code Review frozen audit passed. License, Bandit,
dependency trust, version parity, strict PyPI-ahead, frozen Node install, format,
type-check, lint and YAML checks passed. BasedPyright reported zero errors and
1525 warnings. The normal contract command exited zero through its
no-modified-files path; it did not execute contract scenarios.

The primary strict audit failed on GitPython 3.2.0 CVE-2026-114145 alias
GHSA-83vg-56qc-22m7 and opentelemetry-api 1.37.0 CVE-2026-114603 alias
GHSA-xcq7-p3pf-p88h. Only the previously approved exact MCP advisory was waived.
No additional exception, target update or suppression was made.

The full smart-test run collected 3252 cases and finished with 3212 passed,
29 failed, 10 skipped and one setup error in 203.282 seconds. Post-run inspection
found 37 installed distributions differing from the frozen versions. Beartype
and Semgrep installation timestamps fall inside the test run. Twenty-six
failures or errors involve inconsistent Beartype imports. The cause of these
mid-run installations remains unverified, so the run is not accepted as stable
frozen-environment compatibility evidence. Four other failures cover the old
JSON floor literal, the old Hatchling backend literal, and two staged-version
follow-up fixtures. All frozen tests remain unchanged. The private environment
was restored using the unchanged hash-pinned export and final version parity
confirmed. Repository SAST was then repeated with frozen Semgrep 1.179.0 and
passed with zero findings against the zero-finding baseline.

The earlier eight Ruby probes and both root/prefix documentation builds remain
applicable because dependency and workflow bytes match and the Ruby probe only
loses two narration comments. The prior private macOS-platform adaptation is
retained as evidence. Actual Linux frozen Bundler CI is still required.

All fresh commands, exit codes, JUnit results, failure diagnostics and hashes are
retained under `/private/tmp/specfact-release-20261022/correction-green/`.
`results.jsonl` is the command ledger and `checkpoint.md` records the handoff.
The two strict-audit findings and full-suite failures block release readiness.
No staging, commit, push, signing, merge, publication or archive occurred.

## Advisory correction local RED on 2026-10-23

The owner approved GitPython 3.2.1 and the separate exact opentelemetry-api 1.37.0
exception on 2026-10-22. This test-only correction first verified and backed up
all twelve saved production paths, then restored them to HEAD. The four reviewed
fixture files remain byte-identical to their accepted checkpoint. No environment
synchronization, production adoption, staging, commit, push, or signing occurred.

The new plan selects 31 cases. Its unchanged host-access run reports **31 failed,
0 passed, 0 errors, 0 skipped**. The supplementary run reports **23 passed,
0 failed, 0 errors, 0 skipped**. Both ran with the restored main source inputs.
The shared interpreter retains its existing tooling environment; the dependency
behavior probes separately install the exact hash-pinned frozen delivery wheels.

All three new Git metadata paths reached the mocked clone boundary exactly once
with no ValueError under frozen GitPython 3.1.61. Hook contents remained unchanged,
and neither `.gitmodules` nor module metadata was created. Ordinary `vendor/module`
and `.github/module` reached the same boundary once and passed. The original
`../outside` update probe remains unchanged and failed at its clone sentinel.
No unsafe repository was cloned and no active hook was created.

The empty restored exception register rejects the six MCP/OpenTelemetry exact-ID
and expiry-day cases. The four expired/future cases reject the finding but lack
the required invalid-record diagnostic. These are real assertion failures.
Wrong package/version, unrelated/mixed advisories, skipped dependencies and the
missing-entry control pass. Ordinary MCP evaluations use 2026-10-22; its record
still requires the original 2026-10-21 review date. Future/expiry controls remain.

The remaining failures show the compromised certifi root, seven mutated JWT option
keys, the absent source bundle-mapper inclusion, old package selections, old docs
gem selections/JSON floor, and old core version. Every actual failure message and
traceback is retained in `advisory-correction-tests/failure-diagnostics.json`.

The first sandbox run failed official wheel downloads because DNS was blocked.
Its `sandbox-*.log/xml` files remain limitation evidence and are excluded from
behavioral RED. The unchanged commands passed artifact installation with host
network access. Exact pytest argv, times and exits are in `mapped-command.json`,
`controls-command.json`, `mapped-exit.json` and `controls-exit.json` under
`/private/tmp/specfact-release-20261022/advisory-correction-tests/`.

The released canonical planning command uses the exact base and planned maturity:

```sh
. /private/tmp/specfact-release-20261022/red-owner/env.sh
export GITHUB_BASE_REF=main
python scripts/requirements_evidence_delivery_gate.py \
  --base-ref 5262efb0881e4fac7697d629b0530250342bc656 \
  --required-maturity planned \
  --output /private/tmp/specfact-release-20261022/advisory-correction-tests/planning-final.json \
  --summary /private/tmp/specfact-release-20261022/advisory-correction-tests/planning-final.md \
  --plan-output /private/tmp/specfact-release-20261022/advisory-correction-tests/plan-final.json
```

The source mapping digest is `sha256:0788c6326b39842e80a8cf4e308ac8508c754c384d9e6479b5cd61f0ca8b1c1d`.
The combined mapping digest is `sha256:d4d5c52f4194122dd0745e808dd29d9e19104cc704256c5c66414c3d247d0dbd`.
The plan identity digest is `sha256:59785c8bb37070043e729a0d06c63ce1841f39c4631038fa010e9fc7d8437a69`.
`advisory-correction-tests/mapped.xml` SHA256 is
`e39cc98cc217500edd23697c97b05de9a2306c3acf391fdd845d99585eb9a425`.
`advisory-correction-tests/controls.xml` SHA256 is
`4b568ffc2679d0712f1d51f878ca09d9b5a6eda2cceddfc7d2275a9bee70616b`.

Ruff formatting/checks, Markdown auto-fix/lint, strict OpenSpec validation and
`git diff --check` pass. These local results require fresh independent mapping
acceptance and native RED before any production adoption. Root owns that review,
the normal test-only commit and hooks, native evidence, and the internal wiki.
The coordinator reports the wiki update and graph rebuild complete. The original
23-case accepted proof remains intact and applies only to its original bytes.

## Advisory correction independent acceptance on 2026-10-23

The independent AI technical review accepted the exact 31-case mapping and
reviewed test/proposal bytes. Its durable report is
`requirements-proof/advisory-mapping-review.md`, SHA256
`b5ff286ab72e9702bf26fd70ba423bfcb5255e8c956977c07ab0458152aa358e`.
The active receipt records AI technical acceptance without human authority.
The coordinator reconciled every active status tracker to acceptance complete
and native RED pending. Earlier pending notes remain explicitly historical.

The coordinator separately executed the same safe create-submodule probe on
the installed former candidate GitPython 3.2.0. All three metadata representations
reached the mocked clone once without rejection; ordinary paths did likewise.
Hooks were unchanged and no module/config artifacts were created. This is
supplemental reproduction of CVE-2026-114145 on 3.2.0, separate from baseline
3.1.61 native-proof preparation. The managed JSON evidence SHA256 is
`154d18696b02b3d8ca47b1af83b341685fad583cac8e37141038626abfd00f09`.
No real unsafe clone or active hook was used. Native RED remains required.

The first normal test-only commit attempt correctly failed the docs security
hook because the updated JSON assertion expected its matching Gemfile change.
That one reviewed fixture is retained locally for the production commit with
the Gemfile. The 31 mapped tests, selectors and accepted proof bytes are
unchanged. No hook exception, skip or production adoption was used.

## Quality amendment and refreshed local RED on 2026-10-23

The complete PR Code Review initially reported 67 warnings and six informational
inspection recommendations. The bounded repair adds truthful module/capture types,
removes redundant smoke output, gives the malformed-byte and guidance cases precise
names, consolidates the four unchanged Markdown examples, and states the five-field
exception projection explicitly. Actual Radon complexity changes from 13 to 12.
No policy, assertion, tool configuration, suppression or production file changes.

The final actual review reports zero errors, zero warnings and six visible infos.
Its unmodified JSON SHA-256 is
`d932e26b4795aab317f9c03fb91ae536e1fc95cf6d3806c6c2f01f54c9592d5a`.
The independent review checks each retained informational recommendation against
source and records the specific provenance, policy literals, formats or mandatory
argv that justify its expanded test. These are completed inspection dispositions,
not hidden findings. A fresh comment review finds no changed comments or
suppressions and no actionable flags. No comment deletion or restoration occurs.

Root ran the exact 31 mapped selectors after the quality edits against all twelve
restored production inputs. Result is 31 failures, zero passes, errors or skips.
All 23 supplementary controls pass. Failure messages and tracebacks were inspected.
They reproduce the intended old dependency behavior, missing records, source-build
inclusion and exact selection/version mismatches. The canonical plan is unchanged.
The independent reviewer reran that planner, compared the complete plan and source
hashes, verified the XML and every assertion, and accepted this bounded amendment.
This AI technical review supplies no human authority or release approval.

The exact commands, exits, timestamps and XML remain in
`/private/tmp/specfact-release-20261022/quality-red/`. Mapped XML SHA-256 is
`7987303f817d4f24e6221873539f66d6c6f4d31a8cb8c9b954566c3008dec155`.
Controls XML SHA-256 is
`ebbab7bf849a76a60a57cc879ae006f5f5567500253e8b13d084d626aa88a777`.
The repository-relative accepted report binds all seven mapped tests, four quality
files, proposal/spec/mapping and actual evidence hashes. The source mapping digest
remains `sha256:0788c6326b39842e80a8cf4e308ac8508c754c384d9e6479b5cd61f0ca8b1c1d`.

Normal partial staging retains the old docs-floor assertion in this test-only
commit. Its already-reviewed new floor stays unstaged for the matching Gemfile
adoption. The four Markdown examples, five memberships and fresh loader behavior
are staged together. Native RED is still required before production adoption.
