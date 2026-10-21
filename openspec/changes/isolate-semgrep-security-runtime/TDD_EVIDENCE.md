# Certificate trust-store regression

## Failing before dependency changes

On 2026-10-20 Europe/Berlin, the existing frozen lock was installed with
`uv sync --locked --all-extras` into an isolated environment using Python 3.13.14.
It installed certifi 2026.7.22. No dependency input had been edited.

Command from this worktree:

```bash
/private/tmp/specfact-dependency-audit-20261020/certifi-tools/bin/python -m pytest tests/unit/security/test_certificate_trust_store.py -q --no-cov
```

The actual SSL trust-store comparison failed as intended:

```text
Extra items in the left set:
'86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b'
1 failed in 0.06s
```

The installed bundle still trusted the compromised emSign ECC Root CA - G3.
The full local capture is
`/private/tmp/specfact-dependency-audit-20261020/certifi-root-red.log`.
The frozen audit independently reported GHSA-6q48-6c7w-9gw2 and the separate MCP
finding. Passing-after evidence must use the same test against the refreshed
frozen installation. This local record does not replace native CI execution proof.

## Native CI failing-first proof

The typed test was published at commit
`d6d8f9089bb55f8e834a55dfcac43a8a5e4c61ca` before dependency changes.
[Requirements run 39498007620](https://github.com/nold-ai/specfact-cli/actions/runs/39498007620)
retained artifact `12297219535`, digest
`sha256:10fefe0c9b89815a6a7b29cbe5bca56680fe0fed3aefae693328dfbe6e5406e8`.
The actual JUnit records one intended fingerprint failure, no errors and no skips
on Python 3.12.15. Native reconciliation reports `observed_maturity: red`,
`gate_decision: pass`, and `implementation_evidence: failing-first-proven`.
The run's delivery checks remain blocked at this intermediate failing-test stage.
This is not final implementation or authority evidence.

## Passing after frozen refresh

The canonical `hatch run refresh-frozen-delivery` regenerated the Python lock and
hash-protected CI export after the certifi minimum and 0.55.11 metadata changes.
`uv sync --locked --all-extras` then installed the exact graph in the isolated
environment. The same typed test passed on Python 3.13.14 with certifi 2026.10.19:

```text
1 passed in 0.05s
```

The lock retains 184 packages. Only certifi 2026.7.22 to 2026.10.19 and the project
0.55.10 to 0.55.11 changed version. The installed store has 120 roots and excludes
the compromised fingerprint. Delivery/export parity, lock consistency, license,
dependency trust, synchronized versions, strict PyPI-ahead and Bandit checks pass.
The full audit still fails solely on MCP 1.29.0 / CVE-2026-59951. Both other frozen
exports pass their actual audits. No audit exclusion or resolver override exists.

These passing-after observations describe the local implementation working tree.
Final commit-bound CI evidence and new exact-head authority remain required.
The local logs and package accounting are in
`/private/tmp/specfact-dependency-audit-20261020/certifi-fix-result.txt`.

## Release verification corrections

The broader smart-test attempt had 3427 passes and two failures. Its launcher
selected the Requirements fixture instead of the separately pinned smoke fixture.
Using the exact smoke fixture, then warming the new hash-locked certifi wheel for
its offline child, made the real launcher pass. The first failed results remain
in the local trail and are not reported as passes.

The other failure was the existing release test's fixed 0.55.10 expectation against
the required 0.55.11 patch. Updating only that expected value preserves all original
assertions. All 20 release/security and CA tests then passed. The final full
smart-test rerun is recorded separately after completion; targeted passes do not
turn the earlier failed run into a green gate.

## Final local smart gate

With the separately pinned smoke fixture and frozen cache prepared,
`hatch run smart-test` exited 0. Its actual result was:

```text
3429 passed, 11 skipped, 2 warnings in 262.82s
```

The two warnings are dependency deprecations, not failed tests. The earlier failed
run remains retained. Final local success does not waive MCP, final native CI or
exact-head human authority. Normal dependency commit remains blocked by the
unchanged `frozen-cve-audit` failure.

## Official-only correction, 2026-10-21

The owner rejected the producer/fork and authorized an exact temporary MCP
exception when official Semgrep prevents patched MCP. Superseded producer
evidence remains in Git at 46970dc1 and the private operator archive. It is not
current acceptance evidence and supplies no publication or authority approval.

Latest official Semgrep 1.182.0 wheel metadata requires MCP 1.29.0. A fresh
normal `uv pip compile` with `semgrep==1.182.0` and `mcp>=1.30.0,<2` fails:

```text
Because semgrep>=1.182.0 depends on mcp==1.29.0 ...
your requirements are unsatisfiable.
```

The original strict frozen audit exits 1 for MCP 1.29.0 / CVE-2026-59951.
Before adding the register entry, the new exact-policy and gate tests record
6 failed and 4 passed, including the intended empty-register policy mismatch
and unwaived approved findings. After adding the owner-authorized entry,
all 41 audit/policy tests pass. Twelve unchanged certificate artifact and
adversarial-input tests pass using real hash-pinned official wheel downloads.

All three unchanged strict audit commands then exit 0. The CI graph visibly
reports `WAIVED: mcp==1.29.0 vuln=CVE-2026-59951`; the other two graphs contain
no unreviewed findings. This is accepted temporary risk, not remediation.

Local evidence is retained under
`/private/tmp/specfact-dependency-audit-20261020/official-only/` in
`latest-compatible.log`, `security-before.log`, `exception-tests-red.log`,
`exception-tests-green.log`, `certificate-tests.log` and `security-after.log`.
The gate implementation and all required workflow checks are unchanged.
Normal commit hooks, final CI and exact-head human authority remain pending.

## Native official-only verification and selector correction

At b3bf7cf5, native run 39572650717 passes Security Audit with the exact
reviewed MCP exception. Native Requirements run 39572650571 records 11 tests
with zero failures, errors or skips. Its reconciliation rejects both the
missing prior-RED admission and the unexpanded parametrized selector.

The mapping now names all nine parameter IDs explicitly. Fresh independent
review by `/root/expanded_selector_map_review` confirms the 11 unique selectors
match actual native JUnit and accepts mapping digest
`sha256:9be3a10b220655e55c299b9b3d69c2be0c0b029b1db1c0942abfea1ea6c4f86d`.
This supersedes the earlier three-case mapping acceptance. The prior native
report remains immutable evidence of its original failure. Prior-RED admission
and exact-head human authority are still required. Neither local test evidence
nor technical mapping acceptance fabricates those protected approvals.

Direct yamllint on the changed mapping passes. The repository-wide wrapper
prints unrelated baseline errors while returning success, already tracked by
issue #781. No wrapper behavior is changed in this dependency hotfix.

## Owner-authorized scoped admission implementation, 2026-10-21

The owner authorized actual implementation in policy PR #4 and core PR #782,
with an explicit pause before protected deployment or merging. This supersedes
the previous documentation-only policy checkpoint. Native historical proof
remains missing. No original failed artifact is relabelled RED or modified.

The new workflow wiring test was authored after the updated specification and
before implementation. It extracts and executes the actual final reconciliation
shell from requirements-evidence.yml with a synthetic policy-boundary adapter.
The adapter isolates workflow routing; it does not claim authentic GitHub
approval or signing. The raw failed native packet must remain byte-identical.

The pre-code command was `python -m pytest -q
 tests/unit/scripts/test_requirements_late_cycle_workflow.py` in the existing
full tools environment. Actual result was 1 failed. The behavioral disagreement
was `assert 1 == 0` with stderr:

```text
Final reconciliation requires authenticated red or legacy evidence.
```

This is evidence of the real early-refusal branch, not a missing-module/import
failure. The complete retained log is
`/private/tmp/specfact-dependency-audit-20261020/official-only/implementation/workflow-red.txt`.
The protected policy baseline independently passes all 66 existing tests before
new implementation. Hostile-input policy tests and all three workflow paths are
separate required verification. Final CI and new exact-head grants remain open.

## Separate follow-up verification, 2026-10-21

After PR #782 merged, the owner authorized a separate CI-only core follow-up
with policy PR #4. The fourteen exact mapped selectors pass, including the
actual frozen certifi artifact test. The protected policy suite passes all
179 tests. Its historical-attempt regression first failed against the old
collector and then passed after explicit approved-attempt binding.

The shell tests execute each actual producer, fresh and final boundary using
transport and policy doubles. They prove preserved raw native bytes, ordinary
success, enforced policy refusal, scope guards and isolated CI origin wiring.
They do not prove authentic GitHub attestation or human approval. The final
clean-code review of the refactored test reports zero findings. A fresh
independent reviewer accepted the final fourteen-case mapping under its own
identity in requirements-proof/review-evidence.json.

All three strict frozen audits pass with only the owner-approved MCP exception.
The required contract command exits zero with no modified source detected.
This is a CI-only change; that command does not establish contract execution.
Actual mapped test and policy results are retained separately. Full smart-test,
normal hooks, final native CI origin verification, protected deployment and
new exact-head human approvals remain separate gates.

Policy revision pinned in the workflow is `ea0509fc5261e394cbc8de918b85ea02ac5f4126`.
It remains inactive until separately authorized protected deployment.
Native failed reports remain immutable and missing historical RED stays missing.
