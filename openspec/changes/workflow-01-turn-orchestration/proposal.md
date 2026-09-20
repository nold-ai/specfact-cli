# Change: Adopt the Bounded Turn Workflow

## Why

Agents currently reconstruct repository gate order from prose. Repeated skill copies and mutating verification helpers make that flow inconsistent. Adopt a reproducible local validation/remediation flow while preserving the current-run evidence policy of R09 and independent producer authority.

## What Changes

- Adopt the paired module-owned `specfact workflow` surface; core does not gain a built-in orchestration engine or duplicate analyzers.
- Add repository-owned check-only gate configuration and thin, prefixed skill references. Project canonical repository skills into supported harness directories with a drift check covering source, destination and generator edits.
- Keep standalone verification independent of earlier turn receipts. Local resumable state is operational context, never historical proof or protected CI authority.
- Pilot the signed module against worktree/index/range inputs before enabling contributor guidance; retain normal required checks and effective governance.

## Capabilities

### New Capabilities

- `turn-workflow-adoption`: check-only repository integration, canonical skill projection, standalone verification and bounded adoption.

### Modified Capabilities

None. R09 receives its own consumer-boundary clarification; generic skill installation, review policy, optional preflight and evidence schemas retain their existing owners.

## Impact

Planning artifacts only in this delivery. Later implementation touches repository scripts, selected hooks/CI drift checks, agent guidance, command reference generation and documentation. Regeneration/staging are explicit preparation steps, never verification side effects. No current runtime, CI/ruleset, signature, registry or version changes are made here.

Core owns repository configuration, projection and adoption; modules owns reusable workflow content and runtime. Use existing registry/discovery interfaces, with an actionable install hint if the module is absent. Generic module skill distribution remains #251; generated general instructions remain #253. Repository-local projection does not require those features to ship first.

Document usage and limitations in contributor/agent guidance and the existing CLI reference on docs.specfact.io; validate real cross-site permalinks for module help. Update generated command references only when the module is actually adopted. No new navigation is needed at proposal stage.

## Dependencies and rollout

Signed modules #483 precedes core runtime adoption; independent repository skill projection can land first. Modules #481 supplies the workflow's current-run Requirements integration. Core #740 continues to own the R09 required-policy cutover; this story neither duplicates it nor makes independent tooling wait for its complete rollout. Before behavior work, follow effective governance or an explicit owner-authorized exception.

Optional preflight, #251/#253, the full-chain graph and parked #522 are related capabilities, not blanket prerequisites. A C15-specific adapter consumes the signed C15 policy contract only after its existing prerequisites. No new producer verdict semantics or policy exceptions are introduced here.

Roll out projection -> signed deterministic verification -> bounded local repair -> opt-in PR automation. Roll back repository invocation/configuration and its module pin together if scope selection or gate outcomes regress; ordinary standalone checks remain available.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #742
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/742>
- **Repository**: `nold-ai/specfact-cli`
- **Parent Feature**: #372
- **Paired Modules Story**: <https://github.com/nold-ai/specfact-cli-modules/issues/483>
- **Last Synced Status**: proposed / Todo, 2026-09-20
