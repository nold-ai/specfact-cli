# Test-first evidence

## Current proof status

The supported pycparser 3.12 correction has fresh independent AI technical
acceptance and genuine local RED for all 33 selected cases, with 33 passing
supplementary controls. Fresh native RED is now authenticated for commit `2eef82529a8eb166b9a18898316ae92ce170f02a`.
The active receipt points to `requirements-proof/parser-mapping-review.md`. Earlier measured
results remain historical and supply no acceptance for the changed bytes.

The prior 23-case correction received independent mapping acceptance and native
RED at commit 8cce44f449e9559d0100064d629c81991784ab41, run 39843165302 attempt 1.
Its accepted receipt is preserved in `requirements-proof/pre-advisory-review-evidence.json`.
The subsequent local production results below remain authentic history.

The owner approved GitPython 3.2.1 and the separate exact OpenTelemetry exception.
Production inputs were restored before the specification and test changes.
The 31-case advisory mapping first received independent acceptance in
`requirements-proof/advisory-mapping-review.md`. A subsequent bounded test-only
quality amendment received fresh independent AI technical acceptance in
`requirements-proof/quality-mapping-review.md` on 2026-10-23. The historical quality receipt
uses that repository-relative report and is preserved in
`requirements-proof/pre-trust-review-evidence.json`. Earlier receipts remain historical.
Fresh native RED for the amended test bytes is authenticated at commit
4936750186fcb339913a8710f3034cf1d2be901f, run 39866724812 attempt 1, artifact
12463204671. All 31 cases fail with no errors or skips. No earlier native proof
approves these changed bytes. The docs floor fixture remains held for its
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

## Authenticated quality-amendment native RED on 2026-10-23

GitHub run 39866724812 attempt 1 belongs to PR785's current test-only commit
`4936750186fcb339913a8710f3034cf1d2be901f`, tree
`a95395aaf17130d8c7835fe2ee19d3e3c251f818`, main base
`5262efb0881e4fac7697d629b0530250342bc656`. Artifact 12463204671 is named
requirements-evidence and is unexpired. Its downloaded ZIP SHA-256 matches the
GitHub API digest `11744aa3911b4583a6ad116a9ac101de4bf18c2412d58a28d55d919c0c4fefdf`.
The four bounded archive members have unique safe paths and no symbolic links.

The native report states passed, gate pass, red and failing-first-proven, with
no findings. The XML has exactly 31 genuine failures, zero errors and zero skips.
Its SHA-256 is `ed49f886df8d0c6dd0924ca9666b76fb9ba021f33758a8801ee94dae23ea8abe`.
Root inspected all failure messages and the substantive Git/source-build traces.
The source build reaches the backend and fails on the absent bundle-mapper
forced inclusion. Git reaches only mocked clone sentinels. No setup failure is
counted as a successful behavioral reproduction.

Source commit, complete tree, merge base, all seven test-file digests and all
31 unique selectors match current reviewed source and the genuine XML. The full
native plan equals the independently reviewed planned plan except the two
expected maturity fields, which advance from planned to test-authored. All
canonical identities and inner cases remain equal. An exploratory local
standalone test-authored planner invocation without its acceptance input refused
acceptance-missing. It is retained as a command limitation, not used as proof.
No machine report or artifact was edited to produce this comparison.

Exact metadata, downloaded archive, extracted native files and root identity
record remain in `/private/tmp/specfact-release-20261022/quality-red/`, including
native-ready.json. Normal test-only hooks passed with the docs-floor hunk held.
That proof authorized the prior twelve-path candidate. The parser correction
below requires its own fresh native proof before production. Root freezes all
other tracked content, including mapped tests, conftest and transitive imports. Final local and native GREEN, independent production review,
current-head authority, all required CI and Linux frozen Ruby proof remain open.

## Supported parser test preparation on 2026-10-23 Europe/Berlin

The twelve production paths remain restored to 4936750186fcb339913a8710f3034cf1d2be901f.
The active mapping adds pycparser 3.12 lock/export selection and its exact provenance
record, giving 33 selectors. All prior 31 selector identities remain. The wrong-hash
and wrong-package fixtures use the record's version and review date solely to isolate
the identity rejection. The actual-date checker and all hard-block/expiry controls
are unchanged. No mapped pytest was run before independent acceptance.

The controlled smoke probe executes the existing fixture's environment-construction
statements and launches real Python in a disposable environment. Before correction,
the sentinel case imported the parent-only module, and the owner's default environment
exposed repository src on sys.path. Both child processes inherited PYTHONHOME.
The isolation check exited 1. Removing only PYTHONPATH and PYTHONHOME makes both
observations false and both environment values absent; the unchanged probe exits 0.
This is a child-interpreter environment proof, not a full bootstrap/CLI smoke result.
All original bootstrap, CLI success and parent package inventory assertions remain.

Actual before/after JSON and logs, probe source, exact source hashes, command lists,
and the prepared mapping are retained under
`/private/tmp/specfact-release-20261022/trust-correction-tests/`.
Fresh independent acceptance and local RED are recorded below. Native RED and
later full smoke execution remain required. Production, trust checker/register, Code Review toolchain and signed
assets were not edited. The held docs-floor hunk was preserved byte for byte.

## Published companion execution boundary

The coordinator's read-only trace is retained at
`/private/tmp/specfact-release-20261022/audit/semgrep-contract-trace.md`.
The measured 1.179.0 CLI positive/negative probes and schema 1.2 Code Review result
exercise pinned companion fixture 0.48.15 through ordinary PATH-based passes.
They are not proof of current signed-capsule admission. Published main 0.51.2
and dev 0.51.4 use isolated capsules with `-I -S`, cleared environment, dedicated
PATH, and expected capsule analyzer versions. Failure returns UNKNOWN without
core analyzer fallback. The trace inspected both published archives and verified
their registry hashes. It did not verify their signatures or execute the capsules.

Review comments 4354335589 and 4354335598 correctly identify the companion's admitted
versions, but their claimed core-upgrade-to-capsule mismatch is unsupported by the
inspected execution path. A future capsule version change requires a separate
companion policy/integrity change. No such asset or gate is changed by this release.

## Accepted parser mapping and local RED on 2026-10-23 Europe/Berlin

Independent AI technical reviewer `/root/parser_mapping_acceptance` accepted the
exact mapping, source correspondence, controlled fixture changes and actual local
proof in `requirements-proof/parser-mapping-review.md`. This is technical
acceptance, without human risk, release or merge authority. All original 31
selectors remain and only the exact parser selection and provenance cases are added.
The source mapping digest is `sha256:b192853e22bfc854a30366891d76942d5c2ba9cc47260197c3c4df7bd77c923c`.
The combined digest is `sha256:7752d805c6911e719e9aa3dcb985526f8b10f3e587ebfb1d37c5e67c5703718f`.
The plan identity is `sha256:105b01868f04e3d382b9266bc38111825ca06ad0d00a42d477ac8f5e322e805b`.

Actual final local execution on 2026-10-22 at 23:23 UTC, equivalent to
2026-10-23 at 01:23 Europe/Berlin, produced 33 failures, zero errors and zero
skips. All 33 supplementary controls passed. XML SHA-256 values are
`99b63cef7ee46814a86ca3e66f1c2bebffc280e72e113389a2990b0c659fd697`
and `ac3479cf77e1dbcc6ff99744fbc58bb352d6115a55f036f3f3d3c0eec61f7686`.
Root and the independent reviewer inspected every failure message and the actual
source-build, certificate, JWT and Git clone-boundary traces. No setup failure
was counted as behavioral RED. Earlier pre-comment execution remains historical.

The actual final whole-PR Code Review covers 13 Python paths. Its unmodified
report has zero errors, zero warnings and six visible informational findings with
fresh source-specific preservation reasons in the independent report. Initial
three duplication warnings prompted literal parameter tables for five unmapped
negative fixtures; all inputs, dates, expected errors and expanded AST bodies
remain equivalent. Two redundant new docstrings were removed after a separate
comment review. No suppression, policy change or report normalization occurred.
Final trust-test SHA-256 is `bb20822cb58c8f773f8ed7a54628feef2e1eadbf5cc5c53936422223986ee7ac`.
Actual outputs, commands, hashes and historical reports are retained under
`/private/tmp/specfact-release-20261022/trust-correction-tests/`.

Production paths and the trust register/checker remain restored and unchanged.
Normal test-only hooks, a fresh native 33-case RED artifact, the pending internal
wiki scope decision, production adoption and full local/native GREEN remain.
The held docs-floor assertion stays with its later matching production metadata.

## Authenticated parser-correction native RED

Native Requirements run `39872159349`, attempt 1, retained exact artifact
`12466049727` for commit `2eef82529a8eb166b9a18898316ae92ce170f02a`,
tree `f82634e9b0f290cfce89a35199dfe5d6216fd54f`, main base
`5262efb0881e4fac7697d629b0530250342bc656`. GitHub API metadata binds the
artifact to that run and head, reports it unexpired, and supplies ZIP SHA-256
`3299a6b6dc8c25f4ce8b4e38abf9c05507972ffafc3a85abfc766e24f511a08a`.
The actual downloaded bytes match. Its four unique bounded plain files contain
the unchanged machine proof, plan, Markdown summary and JUnit. No artifact was edited.

The actual machine verdict is pass with RED maturity and failing-first-proven
delivery. All 33 unique selectors fail for their intended causes, with zero errors
and zero skips. JUnit SHA-256 is
`2b249d0c3f273e9766fee45cc9d9323dcfdd574d12d5cc6c8c9c8acee5176536`.
Root verified every selector, all eight current and committed test hashes, exact
head/tree/base, the complete inner plan and canonical identities against local
acceptance. Root read every failure message and the source-build and Git
clone-boundary traces. No download/setup failure stands in for behavioral proof.

Raw API records, ZIP, four extracted files and authenticated native-ready.json
are retained under `/private/tmp/specfact-release-20261022/trust-correction-tests/`.
This source-specific native proof opens only the reviewed production unit. The
expected test-first CI and missing final-head authority failures are not retried.
Production GREEN, independent final review, all required CI, Linux frozen Ruby
proof and the pending internal wiki authorization remain open. Do not merge.

## Final design binding and bounded packaging correction

Review thread 4354615606 exposed a genuine design hash mismatch after operational
status edits. Fresh independent AI review in
`requirements-proof/parser-design-binding-review.md` binds final design
`9f7fbb3c15f4f4fb560ae71d027c27692d05b753b19dfcf27e67211342a446d6`.
Its report SHA-256 is `62ef2afd23f9b0e1131c16199e78cab97d3a88143cecca28d1fff208bc94995f`.
The active receipt references that report directly. The original report remains
unchanged. The complete canonical plan equals the authenticated native plan after
the receipt change. All eight selected test hashes remain unchanged, so the fresh
review confirms that the authentic 33-case RED remains applicable. The design is frozen.

The official ten-update production graph was normally resolved and hash-synced.
All 33 mapped cases, 33 supplementary controls and 97 complete-file cases pass.
Both strict advisory lanes pass with only the exact owner-approved MCP and
OpenTelemetry exceptions. Installed-wheel Git and official Semgrep controls,
source-to-wheel rebuild, strict signatures, licenses, Bandit, real-clock trust,
full runtime smoke and fresh root/preview Ruby builds pass. The parent environment
retains the same 178 distributions and locations. Native Linux Ruby evidence remains required.

The first complete smart suite produced 3257 passes, two failures, ten skips and
zero errors across 3269 cases. Both failures were unchanged packaging assertions
requiring the obsolete 2.22 parser minimum. A focused before-run reproduced the
same two failures with seven passes. The bounded fixture correction now accepts
3.12 and rejects 2.22, while retaining all prior 3.0-family rejection assertions.
Its focused after-run has nine passes, zero failures, errors or skips. Ruff lint,
format and diff checks pass. Raw argv, times, logs and JUnit remain under
`/private/tmp/specfact-release-20261022/parser-packaging-fixture/`.
The corrected full suite, independent review and native GREEN remain separate gates.

The actual source-built wheel SHA-256 is
`803e8da8d92428aeeffeae4019d090947044037d556db4e1923048f5bbc5fe7f`.
Comparison with published 0.55.4 finds the same 295 payload members and 297 guarded
source files, except two version strings and the explicitly allowed dependency
metadata. Fifteen negative controls reject unauthorized payload or metadata drift.
The persistent supplemental result is `artifacts/parser312-published-wheel-comparison.json`.
This evidence does not claim that all public-install transitive versions are fixed.

Whole-PR Code Review before the packaging correction reports zero errors, zero
warnings and six visible source-bound accepted infos. BasedPyright reports zero
errors and 1449 existing warnings over 674 files. The YAML wrapper exits zero with
existing raw diagnostics. The contract gate reports cached unchanged-file results.
Fresh full-suite and native checks remain required. No local signing, check bypass,
merge, publication or protected deployment occurred. The internal wiki scope request
remains pending after automatic approval review rejected the sibling write.

## Independent production boundary review

The fresh read-only review `artifacts/parser312-candidate-bypass-review.md`
found no concrete parser bypass or ordinary CFFI regression in the exact thirteen
production files. Its SHA-256 is
`323eb4054772839503fc78118c27a4f8654d147e3fc4b00f7de241f72fc91b10`.
The review's conditional PyJWT observation received a separate independent source
trace in `artifacts/pyjwt-public-boundary-independent-triage.md`, SHA-256
`73447609e3ef2928814fdf6750a5d9f8a17bb9b27c49106e73aaa817ae7f2793`.
Both reports are retained through persistent supplemental artifact storage.

Public dependency metadata still permits PyJWT 2.13.0 through Azure Identity
1.25.3 and MSAL 1.37.0. The accepted release contract targets the exact frozen
PyJWT wheel, which is 2.15.1. The actual device-code path uses MSAL's own JSON
and base64 token decoder. The only PyJWT call found in those installed packages
is assertion encoding. Core ADO records token.expires_on and has no changed
authentication source. No PyJWT decode/options-reuse application path or candidate
regression was established. The conditional finding is dismissed for this bounded
release contract. A public PyJWT floor remains separately scoped hardening.
This is not a CVE exception or a guarantee for every public resolver outcome.

The bounded packaging fixture received fresh independent acceptance in
`requirements-proof/parser-packaging-independent-review.md`, SHA-256
`91ebf32f6257b0534ad0105df4e9fdfd160f097b17355bebc83bf835214fb59e`.
The reviewer recomputed raw diff, before/after XML and all selected hashes,
confirmed the unchanged full canonical plan and mapped import context, and found
no actionable code or comment issue. The authentic native RED remains applicable.

The corrected full suite's first attempt ran within the restricted sandbox.
It produced eleven infrastructure failures, 3248 passes and ten skips. The
failures were blocked package DNS/downloads, the isolated bootstrap, and a
PermissionError on the normal user metadata cache. The two packaging cases pass.
A direct DNS probe separately reproduced the sandbox restriction. Raw XML, logs,
parent inventory and failure traces are retained as full-after.* under the fixture
evidence directory. The same unchanged suite is running once with normal host
access. No timeout, TLS, dependency hash, test expectation or policy was relaxed.

## Corrected full-suite GREEN on 2026-10-23 Europe/Berlin

The unchanged normal-host `hatch run smart-test-full` completed from
2026-10-22T23:55:16Z through 23:58:27Z, equivalent to 2026-10-23
01:55:16 through 01:58:27 Europe/Berlin. It exited zero with 3259 passes,
ten skips, zero failures and zero errors across 3269 cases. Both bounded parser
packaging cases pass. Actual JUnit SHA-256 is
`54dfe658f69b4708aa1d6bd9d6f0c7cc7021d1a514d609310f3ded844677eb1f`.
The parent inventory before and after contains the same 178 distributions,
versions and locations. Raw argv, timestamps, log, XML and inventory are retained
as full-host-after.*and host-parent-*.json in the packaging-fixture evidence directory.
The sandbox failure remains separate infrastructure evidence. No test, timeout,
TLS, resolver or gate changed between these two executions. Native CI remains required.

The final whole-PR Code Review covers all 17 changed Python files and reports
zero errors, zero warnings and the identical six visible infos. Every finding
and its source bytes equal the prior independently accepted dispositions. The
new packaging file contributes no findings. The unmodified machine report,
actual command, times and exact source binding are retained as final-code-review.*
and final-source-binding.json in the fixture evidence directory. Final canonical
planning passes and its complete plan equals the authenticated native plan.
OpenSpec strict validation and git diff --check pass. Final native CI is pending.
