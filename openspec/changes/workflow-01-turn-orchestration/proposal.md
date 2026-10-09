# Change: Adopt the Bounded Turn Workflow

## Owner-approved agentic SDLC amendment — 2026-10-04

Include optional decision-context drift and advisory external findings in #483 producer adapters and #742 adoption. Retain original producer identity, severity/rule, artifact digest, snapshot identity and verification basis. Producer trust and finding epistemic basis are separate fields: a trusted producer can emit heuristic advice. Present affected obligations, missing evidence, source/test/configuration changes and next actions. Context absence does not block ordinary verification. Use structured pytest runner identity first; certify its selected-suite/current-attempt semantics before additional runners. Deterministic verification precedes repair; one controller owns a shared elapsed/attempt budget across optional preflight and PR loops, with exhaustion, no-progress, oscillation and required-human-decision stops. An advisory converged result never overrides a failed or unavailable required producer.

This planning amendment supersedes conflicting scope and prerequisite wording below. It changes no runtime behavior and completes no implementation task. See the [paired modules proposal](https://github.com/nold-ai/specfact-cli-modules/blob/dev/openspec/changes/workflow-01-turn-orchestration/proposal.md).

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

None. This proposal consumes R09 without editing its change or issues; generic skill installation, review policy, optional preflight and evidence schemas retain their existing owners.

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
- **Paired Modules Proposal (public baseline)**: <https://github.com/nold-ai/specfact-cli-modules/blob/dev/openspec/changes/workflow-01-turn-orchestration/proposal.md>; the risk-first amendment is prepared for a separate review PR.
- **Last Synced Status**: proposed / Todo, 2026-10-08 (live readback; planning creation complete, separate publication authorized)

## Signed Requirements compatibility gate

Before selecting or adopting workflow #483 for current-run Requirements integration, validate the exact immutable signed Requirements #481 publication and its schema-v3 `current_execution` contract against the actual core and workflow versions. Verify archive/manifest/payload signatures and identities, then exercise the exact installed pair with existing representative current-result fixtures. An absent, incompatible, unsigned or v2-only producer leaves runtime integration/adoption not ready; do not substitute a passing receipt or silently downgrade the contract. Repository skill projection remains independently deliverable, and core #740 retains policy cutover ownership.

## Risk-first execution amendment — 2026-10-08

The owner selected a minimal adaptation within this existing paired change: discover invalid assumptions before dependent work and reduce avoidable correction overhead. Reuse `specfact-pre-validate`, `specfact-implement`, `specfact-verify`, `specfact-fix` and `specfact-autofix`; add no stage aliases or commands. This amendment preserves the 2026-10-04 decision, current assurance/review policy and signed release dependencies. It adds guidance and acceptance scenarios, not report schemas, receipt formats, producer verdicts or automatic collection.

- For nontrivial behavior changes, select one or two assumptions that could invalidate the approach and run the smallest relevant existing CLI/API/dependency probe before dependent implementation. Record the observed boundary, limitations and result in existing planning/evidence sections. Documentation-only work records applicability; a probe supplements required checks.
- Give the applicable existing review the assumptions, evidence references, affected obligations and exclusions. Triage findings against a violated requirement or concrete invariant, a reachable failure path and evidence. Preserve confirmed defects, disproved concerns, suggestions and unresolved claims as distinct dispositions; no disposition waives required findings.
- Keep one writer and batch compatible repairs. Handoffs carry the delta, affected assumptions, remaining findings and original evidence references. Boundary drift or uncertain impact broadens review and affected-gate rechecks; retain the shared controller and consumed budgets across handoffs.
- Reuse existing records for a bounded trial on the next subsequently authorized nontrivial change in each repository. Report early discoveries, later escapes, correction batches and overhead. Separate token categories, billed charges, elapsed time, active effort and waiting; unavailable values remain unknown. Operational observations do not prove causal or monetary savings.

Non-goals: full pstack installation, default Arena/reviewer panels, a new ledger, importing another project's capability, warning-policy calibration or minimal-evidence cutover. No runtime command becomes active because skills exist. Keep reusable modules content concise, reference existing rules, and let each repository supply its own commands/governance and core-owned wrappers/projection.

Deliver skills/projection -> deterministic verification -> bounded repair -> opt-in PR automation. Review the initial skills/projection slice after two engineer-days as an investment checkpoint, not an estimate for the full paired runtime. Added ceremony, weak probes and incorrect dismissals are mitigated by limiting assumptions, stating proof boundaries and preserving producer authority/current-input binding. Roll back new guidance/projection while retaining evidence and ordinary checks; runtime adoption retains coordinated configuration/module-pin rollback.

Public research context (accessed 2026-10-08): [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) and [Flavio Copes' overview, updated 2026-09-29](https://flaviocopes.com/pstack/). These inform adapted practices, not a framework dependency or savings claim. Confidence: high in architectural fit; medium in reducing defects/overhead. Planning creation leaves runtime implementation and trials unchecked.
