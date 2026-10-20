# Change validation

## Result

Planning proposal only. The final direction is independent upstream native
replacement investigation. A later review superseded the initial isolation choice
after identifying a real adoption cycle and unconfigured producer. Production
implementation and adoption remain blocked on exact publisher/component evidence,
actual parity, native acceptance and installed-user patch compatibility. No implementation RED/GREEN, clean security
audit, version bump, duplicate closure or promotion is claimed.

## Repository and dependency evidence

Reviewed on 2026-10-20 Europe/Berlin against dev
`db5b249ec4533f6a96aca81a7de05b7ce5c47247` and main
`5262efb0881e4fac7697d629b0530250342bc656`.

| Open PR | Direct target in dev | Disposition |
| --- | --- | --- |
| #762 | redirect-from 0.17.0 | Already covered; incidental transitives need separate disposition. |
| #764 | feed 0.18.0 | Already covered; incidental transitives need separate disposition. |
| #765 | relative-links 0.9.1 | Already covered; incidental transitives need separate disposition. |
| #766 | Hatchling 1.32.4 | Already covered in declarations and frozen inputs. |
| #777 | JSON 3.1.0 absent | Do not apply wholesale; it downgrades Jekyll 4.4.1 to 4.3.4. |

All five PRs target main. Their direct fixes remain absent there. They were not
closed during planning. Current dev retains JSON `>=2.21.2,<3` with 2.21.2 locked.

Current open GitHub alert ranges were compared with dev's frozen versions.
GitPython 3.2.0, PyJWT 2.15.1, urllib3 2.8.0 and virtualenv 21.11.0 exclude the
other reported ranges. MCP 1.29.0 remains affected by GHSA-84m7-p3x7-pcfv.
This comparison is not a claim that the full required audit passed.

PR #782's frozen Security Audit subsequently also reported certifi 2026.7.22
against GHSA-6q48-6c7w-9gw2, published on 2026-10-20. The maintainer identifies
2026.10.18 as patched. Both certifi and MCP failures come from unchanged frozen
inputs. Updating certifi alone would leave MCP failing; neither alert is waived.

## Reproduced blocker

An isolated temporary project used Python 3.12 and these requirements.

```toml
[project]
name = "specfact-security-resolution-probe"
version = "0.0.0"
requires-python = ">=3.11"
dependencies = ["semgrep==1.181.0", "mcp>=1.30.0,<2"]
```

`uv lock` exited 1 with the intended dependency conflict.

```text
No solution found when resolving dependencies:
Because semgrep==1.181.0 depends on mcp==1.29.0 and your project depends
on mcp>=1.30.0,<2, ... your project's requirements are unsatisfiable.
```

Exact PyPI metadata for dev's Semgrep 1.179.0 and current latest 1.181.0 both
declared `mcp==1.29.0`. Other checked supported release versions 1.175.0,
1.176.0, 1.177.0, 1.178.0 and 1.180.0 had the same dependency. The maintainer
advisory identifies 1.30.0 as the patched MCP 1.x release. These facts require
refresh before implementation.

This probe ran outside the repository. It installed no scanner and modified no
production input. Its resolver failure does not substitute for scenario-derived
application RED evidence.

## Architectural comparison and independent review

Three independent architect candidates used gpt-6-astra, gpt-6.1-sol and
gpt-6-luna. A separate gpt-6.1-sol cross-judge recommended isolation. The parent
read each candidate and initially accepted that base. The later cycle review below
supersedes that initial selection; these scores are historical comparison evidence.

| Criterion, scored 1-5 | Isolation | Replacement | Direct adoption |
| --- | --- | --- | --- |
| Authorized isolation/replacement scope | 5 | 5 | 1 |
| Complete audit coverage | 5 | 4 | 5 |
| SAST and installed semantics | 4 | 3 | 5 |
| Honest authority/readiness | 5 | 5 | 5 |
| Small boundary and release impact | 3 | 3 | 5 |
| Verifiable tests/native proof | 4 | 5 | 3 |

These are design judgments, not measured runtime results. The final replacement design avoids a generic environment registry or public
scanner type hierarchy, preserves existing client result contracts and retains
installed-wheel, complete audit, signature/cache and real scan acceptance from
the isolation candidate. Replacement parity and native component evidence remain
unproved.

### Superseding adoption-cycle review

A fresh independent gpt-6-astra review inspected #779's actual protected-producer
source. Its workflow_dispatch path on dev unconditionally exits with production
bootstrap unconfigured. Live Security Audit job 118347168646 in run 39336445204
also reports `FAIL: mcp==1.29.0 vuln=CVE-2026-59951`. Trusted Requirements Authority
is independently failing. Requiring #779 adoption before repairing the graph
therefore creates an adoption cycle; merging that candidate alone cannot supply
production artifacts.

The parent accepted this finding and changed the selected investigation direction
to independently published native replacement, with OpenGrep v1.31.0 only an
inventoried candidate. Remove the native blocked-by #772 edge; keep #772/#779
related and unchanged. No replacement proof, signature validation, component audit
or real parity run is claimed. Independent publisher verification and existing
protected review must precede adoption; candidate policy cannot approve itself.

This corrects dependency direction without waiving a failed audit or authority
check. The planning PR is not an invented prerequisite merge before corrective
work. Actual governing gates still apply to the eventual implementation.

## Release limits

Dev declares 0.55.10; live PyPI reported 0.55.4. A future verified patch after that
dev snapshot is 0.55.11, but this planning PR changes no version. The scanning-extra
installation contract must meet patch compatibility before selecting a version.
Current dev has 102 commits beyond main, including runtime security changes.
Its wholesale promotion cannot be represented as dependency-only.

## Validation commands

Planning checks completed on 2026-10-20 Europe/Berlin.

- `openspec validate isolate-semgrep-security-runtime --strict` passed.
- `markdownlint --config .markdownlint.json` over every change Markdown file passed.
- `git diff --check` and staged whitespace checks passed.
- Fresh independent gpt-6.1-sol final review passed core planning consistency.
  Its one stale local-trail finding was superseded in the local review record;
  no source change or security exception was required.
- The unchanged planned Requirements gate passed using the verified clean module
  fixture at locked commit 69f075819be5e1ceca1446b026b0417f19e584ca. Its report
  states proposal-only, planned, implementation evidence not yet available.
  The map covers all five requirements and fourteen scenarios by inspection.
- Direct yamllint passed both new YAML files. The repo-wide wrapper printed
  pre-existing errors but returned 0; that separate false-pass defect is tracked
  in [#781](https://github.com/nold-ai/specfact-cli/issues/781). No global clean
  YAML result is claimed.
- Native GitHub readback confirms parent #747, project Todo, required labels and
  blocked-by modules #523 for dependency removal and completed cutover. Candidate
  investigation can proceed before migration. #772 is related only.
- External module migration is tracked in
  [modules #523](https://github.com/nold-ai/specfact-cli-modules/issues/523),
  with native parent #163, Project 1 Todo and a one-way edge blocking core #780.
  It has no blocked-by issue or reverse dependency. It covers command
  paths, packaged rules, bundle resources, integrity, version and CI/CD signing.
  Core acceptance cannot establish end-to-end replacement while the module still
  uses Semgrep. Verified module migration also blocks shared dependency removal;
  tracking alone is insufficient. Existing reset sequence and owners remain intact.
- The matching internal wiki source was aligned and `wiki_rebuild_graph.py` ran
  from the internal repository root, preserving pre-existing dirty source files.

No runtime test suite, frozen-audit pass, native artifact execution, signature
verification, package release check or implementation review is claimed. Those
checks remain unchecked implementation tasks, and adoption remains blocked.

## PR review and CI triage

The active-tree count was corrected from 47 to the observed 48 directories,
excluding `archive`. The module follow-up above addresses the separate migration
finding and is represented by a new planned scenario and inspection case.

A subsequent P1 review identified a real sequencing gap. The current external
module invokes `semgrep`, while `requirements/code-review/locked.txt` does not
install it. Task 4.4 could therefore remove its executable before mandatory final
review. The spec, design and task order now block removal until modules #523
proves the installed module's required clean-code, bug and AI-bloat passes,
packaged resources and bundle integrity in a fresh delivery environment with
Python Semgrep absent. A new planned scenario and inspection case retain this
prerequisite. Investigation can precede the cutover; actual migration remains
unimplemented and no new runtime proof is claimed.

CodeRabbit also identified an unused, directly constructible prepared-handle
sketch that did not bind command construction. The design removes that unused
handle and separate helper rather than adding another caller-facing capability.
The existing single command owner now explicitly performs offline validation
against current admission and installed components on each invocation. Prior
preparation, stale cache or caller-created state cannot bypass those checks.
The normative requirement and existing stale-cache inspection case retain this
boundary. No implemented API or runtime verification is claimed.

The original CI Linting job failed because Ruff formats Python fenced blocks in
Markdown. `hatch run ruff format . --check` reproduced that failure in `design.md`.
Formatting that sketch restored the required blank lines; the full command then
passed with 1122 files already formatted. No production code changed.

Security Audit remains failed on the two unchanged frozen dependencies above.
The current dev base is an ancestor of this branch, so neither stale-base drift
nor a flaky job explains those failures. No retry, exclusion or gate bypass is
used. Trusted Requirements Authority independently requires a distinct unedited
maintainer approval bound to the final commit and tree. General PR babysitting
permission supplies no such approval. Request it only after the review wave is
published, then rerun the authority workflow for that unchanged head.
The owner approved revision `100fb416` while the subsequent P1 review arrived.
That approval was not posted because the required correction changes the commit
and tree. It cannot authorize the revised head.

## Sources

Accessed 2026-10-20.

- [MCP maintainer advisory](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-84m7-p3x7-pcfv).
- [Certifi maintainer advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2).
- [Semgrep 1.179.0 metadata](https://pypi.org/pypi/semgrep/1.179.0/json).
- [Semgrep 1.181.0 metadata](https://pypi.org/pypi/semgrep/1.181.0/json).
- [Current core package metadata](https://pypi.org/pypi/specfact-cli/json).
- [Downstream owner #772](https://github.com/nold-ai/specfact-cli/issues/772),
  [candidate #779](https://github.com/nold-ai/specfact-cli/pull/779) and
  [promotion #771](https://github.com/nold-ai/specfact-cli/pull/771).
- [PR #782 CI run](https://github.com/nold-ai/specfact-cli/actions/runs/39487998471).
- [Pinned authority policy](https://github.com/nold-ai/.github/blob/0787cc7e45a12e4651e22d9447d21a29e31e98b4/docs/trusted-requirements-authority.md).

Confidence is high for observed repository state and reproduced resolver conflict,
medium for the selected design, and low for production feasibility until the
explicit artifact, compatibility and native evidence is available.

## Signing and publication

The first normal commit attempt stopped at an unavailable local module fixture.
Selecting the existing clean fixture at the unchanged locked commit resolved that
environment failure. The second normal attempt passed the applicable planning
hooks, with the global YAML limitation above, then Git exited 128 at signing:

```text
gpg: skipped configured identity: No secret key
fatal: failed to write commit object
```

That attempt produced no commit, push or PR. The owner then explicitly directed
on 2026-10-20 that signing be handled only through a CI/CD follow-up, not locally.
This task-specific direction supersedes the local signing handoff. Publish the
planning commit without a local signature, preserving normal validation hooks
and leaving signing to that follow-up. No persistent Git signing configuration
is changed. Package version, dependency inputs, existing dependency PR states
and promotion remain unchanged.
