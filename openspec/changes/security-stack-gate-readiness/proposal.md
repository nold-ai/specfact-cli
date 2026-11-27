# Change: Resolve security stack readiness gates

## Why

On 2026-10-11 Europe/Berlin the owner explicitly requested resolving Requirements
member authority, native parent-proof reuse and local smart-test failures for
stack #757, preserving required gates. The existing dependency slice excludes
these workflow repairs, so this prerequisite has its own scope and evidence.

## What Changes

- Isolate direct and console runtime smoke launchers from the running test
  interpreter. Borrow the already frozen runtime through an explicit child path,
  constrain marketplace pip resolution to committed versions and prohibit new
  package downloads in those launchers.
- Authenticate same-repository native GitHub stack ancestry through live API data
  before selecting the root branch and immutable base for retained RED lookup.
- Revalidate stack context independently in producer, execution and final verdict;
  retain original Git/JUnit/digest, immutable fixture and test-support checks.
- Add organization-policy support for authenticated native stack bases while
  retaining the exact head/tree member grant, expiry and live write permission.
- Rebase the dependency PRs onto the reviewed prerequisite and author their entire
  unchanged five-layer plan before replaying dependency implementation. Obtain
  fresh RED/final evidence; keep historical evidence and all five PR numbers.

No inferred member approval, fabricated proof, mutable fixture, waiver or ignored
failure is permitted. No CLI dependency upgrade beyond the approved stack or
change to the released Requirements reconciliation semantics is included.

## Capabilities

### New Capabilities

- `requirements-stack-evidence`: authenticated native-stack proof selection.
- `runtime-smoke-isolation`: isolated direct/console marketplace smoke execution.

### Modified Capabilities

None. Existing authority, frozen delivery and native reconciliation remain gates.

## Impact

Affected code: runtime smoke harness, data-only stack context validator and
Requirements workflow; companion organization policy. One prepared 0.55.5
bugfix remains shared with the dependency stack. A prerequisite merge changes
proof bases and requires signed rebases and new final-head evidence.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- GitHub issue: #747, <https://github.com/nold-ai/specfact-cli/issues/747>
- Parent Epic: #194; project: SpecFact CLI #1; owner explicitly resumed this work.
- Related stack: #757; preserved PRs: #744, #727, #752, #754, #753.
- Dependency consolidation remains open for broader accepted work.
