## Context

The Requirements module owns mappings, maturity, plan construction, and reconciliation semantics. Core owns immutable module selection, Git snapshot selection, safe subprocess execution, environment limits, artifact retention, workflow ordering, and branch-protection integration.

The previous R07 design treated current-run execution and historical failing-first chronology as one maturity ladder. This forced core to decide which repository inputs could change after a retained red result. For arbitrary Python and pytest, that becomes an open-ended execution model rather than a bounded evidence protocol.

## Goals and Non-Goals

### Goals

- Report one exact and replayable fact: the mapped selectors observed in the current run.
- Keep staged planning index-isolated and keep CI execution bounded.
- Preserve immutable module and environment identities in the evidence packet.
- Publish diagnostics and artifacts before enforcing any verdict.
- Keep Requirements and Code Review decisions independent.

### Non-Goals

- Establish historical red-to-green chronology in R07.
- Discover the complete dependency closure of Python, pytest, plugins, configuration, data files, subprocesses, or external state.
- Interpret a passing test as proof of complete intent or defect absence.
- Introduce the global evidence graph or global status taxonomy.

## Decisions

### Current execution and chronology are separate claims

A current-run Requirements result records mapping and plan digests, exact selectors, source commit and tree, JUnit digest, runner identity, environment identity, and collection/result counts. It may state that the selectors passed in this run.

It must not state or imply `passing-after-red`, `change-proven`, or equivalent chronology unless an independent R08 attestation is present and valid. Missing historical evidence leaves the chronology claim unproven; it does not erase the current-run observation.

### Plans remain structured and untrusted

Core accepts only a supported plan schema from a pinned reviewed module release. Selectors are exact repository-contained pytest node IDs passed after the option boundary as subprocess arguments. Absolute paths, traversal, option-like values, control characters, shell syntax, wildcards, duplicates, unsupported runners, and excessive plan sizes fail before process creation.

### Current-run reconciliation stays module-owned

Core produces deterministic JUnit with a canonical collected-selector property. The same module release reconciles the original plan and JUnit. Core retains the resulting Requirements verdict without parsing or rewriting its semantics.

### Every governed change receives an explicit decision

The PR workflow emits selected, failed, or deterministic no-impact evidence. A no-impact result includes the evaluated base/head identities, changed-path digest, policy identity, and reason. Missing scope or an execution/tool failure is not no-impact.

### Review consumes context without verdict fusion

Code Review receives finalized current-run Requirements evidence as provenance. A passing Requirements result cannot override review, contract, security, or test failures. A passing review cannot override Requirements failure or unknown execution.

### Evidence is published before enforcement

Plan, JUnit, Requirements JSON/Markdown, review JSON, and a concise terminal summary are uploaded before the enforcing step. The summary names the evaluated source and states the limits of the claim.

## Implementation Boundary

This planning change changes no behavior. A later implementation PR may touch only:

- `.github/workflows/requirements-evidence.yml`;
- one small current-run delivery adapter if required;
- focused workflow/unit/integration tests;
- Requirements adoption documentation;
- the module fixture lock only after a signed modules release;
- these OpenSpec artifacts.

The implementation must not cherry-pick PR #671 or add static rules for Python imports, pytest plugins, aliases, mutations, namespace writes, file reads, configuration discovery, symlinks, or dynamic execution.

## Rollout and Rollback

1. Merge and release the corrected modules R07 status separation.
2. Add failing core tests for current-run-only reporting and absence of chronology inflation.
3. Adapt core to the signed module release in advisory mode.
4. Regenerate evidence and enable strict current-run enforcement.
5. Implement R08 separately.
6. Roll back by reverting the core adaptation and fixture pin; retained artifacts remain auditable.

