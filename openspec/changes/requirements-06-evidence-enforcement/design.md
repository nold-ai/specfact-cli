## Context

Core delivery currently runs Block 2 code review and contract checks without a
Requirements evidence verdict. Existing CI already demonstrates the required
fixture pattern: `ci/module-fixture.lock.json` pins the modules repository and
commit, workflows check out that exact ref, and verification compares the
checked-out SHA before any module code is used.

Modules #361 owns the reusable `specfact requirements evidence` command and
its verdict, JSON, Markdown, and `--staged`/`--base-ref` semantics. Core must
not reimplement those semantics. It only materializes the released fixture,
invokes the released command according to its published contract, preserves
its reports, and translates its exit status into delivery-gate behavior.

## Decisions

### Pin and verify a released fixture before execution

The fixture lock SHALL name only `nold-ai/specfact-cli-modules` and an exact
40-character commit from the #361 release. Local and CI execution SHALL verify
the resolved fixture identity before command execution. A missing, malformed,
or mismatched fixture SHALL fail closed and SHALL not fall back to a sibling
checkout, a branch name, or mutable module source.

### Place the staged gate before review and contract checks

The pre-commit sequence SHALL run Requirements evidence after Block 1 quality
checks and before the current Block 2 code-review and contract-test sequence.
On a red verdict, it SHALL leave the module-produced JSON and Markdown reports
at documented local paths, print those paths, and exit non-zero. Later gates
do not run.

### Preserve reports in pull-request CI for every verdict

The pull-request workflow SHALL run the same released fixture contract against
the pull-request base reference, write a concise summary, and upload the JSON
and Markdown reports using an always-run upload step. A red verdict blocks the
workflow only after the report is available.

### Consume the published 0.3.3 command contract

Modules #361 is released as `specfact-requirements` 0.3.3 at immutable commit
`2438372f8e34c96d4e474afa4c66c92a9cee7979` (modules PR #365). Core SHALL
invoke only this public surface:

```text
specfact requirements evidence --repo-root <repo> --output <json> \
  (--staged | --base-ref <ref>) [--summary <markdown>]
```

The command returns `0` for passed or skipped evidence and `1` for failed
evidence after writing the requested JSON and Markdown reports. Argument usage
errors are distinct command failures. The local gate stores reports under
`.specfact/reports/requirements-evidence/`; CI uses
`artifacts/requirements-evidence/` and uploads both report types. A checked-out
fixture is accepted only when its repository and `HEAD` exactly match the lock.
The existing mutable-sibling discovery helper is not an admissible fallback for
this gate.

## Risks and Mitigations

- **Release skew or fixture substitution**: validate repository and exact SHA
  before execution; fail closed on mismatch.
- **Lost remediation evidence on failure**: write reports before returning the
  command's non-zero exit; use CI `always()` artifact upload.
- **Staged/working-tree leakage**: delegate staged-index behavior exclusively
  to the module command and cover it with the module's released fixture.
- **Offline local development**: do not fetch mutable code at hook runtime;
  require the pinned fixture to be present and report actionable remediation
  when it is unavailable.

## Rollout and Rollback

1. Wait for #361 to close and publish its immutable fixture.
2. Pin the published commit and verify it in tests, pre-commit, and CI.
3. Enable the staged pre-commit gate before review/contract gates.
4. Enable pull-request CI summary and artifact retention.
5. Roll back by removing the hook/job and restoring the previous fixture lock;
   no source artifacts or upstream modules are modified by core.
