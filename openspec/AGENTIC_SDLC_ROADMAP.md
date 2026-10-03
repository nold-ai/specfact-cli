# Agentic SDLC delivery roadmap

Owner-approved plan, reconciled 2026-10-04 (Europe/Berlin). **Status: planning changes, not delivered runtime.** Prioritize existing Python users, upstream OpenSpec/Spec Kit ownership, bounded deterministic feedback and GitHub CI. Migrate invocation and interchange surfaces while retaining SpecFact's reusable validation runtime.

## Verified starting point

- Modules branch base: `37b6000227ba4be353a4f1769e39e92073b1fced`; core base: `5db1f213f1cd6dca283b86c6710379deb61bad94`. Original dev checkouts remain untouched. Branches are isolated from the active native-platform session.
- Live public issue readback: modules #168/core #350 are closed/Done; their import functionality is baseline, not new work. Modules #481 is open/In Progress; the owner authorized takeover on 2026-10-04. All fetched follow-up issues #164/#169/#170/#171/#230/#431/#434/#483 and core #240/#247/#682/#684/#740/#742 were open/Todo. Core #524 must be rechecked before runtime work.
- #481's existing worktree contains planning, not a delivered schema-v3 reconciler. #483 is also planned. Core #742 has live tracking but its workflow proposal is not present on the fetched core dev base; this PR records its approved amendment here and in the issue instead of replacing another branch's files.
- The public registry at the start of this change lists Code Review 0.50.1 and Requirements 0.5.1. Registry presence is not installed-pair verification. Published review execution documents Linux x86-64/Python 3.11–3.13; ongoing native-platform candidates are not blanket released support.

## Bounded stories and order

| Order | Owning work | Delivery and dependency boundary |
|---|---|---|
| 1 | Modules [#481](https://github.com/nold-ai/specfact-cli-modules/issues/481) / core [#740](https://github.com/nold-ai/specfact-cli/issues/740) | Pure current-run reconciliation, then core protected execution/rollout. No context, graph, seal or telemetry prerequisite. |
| 2 | Core [#749](https://github.com/nold-ai/specfact-cli/issues/749) / modules [#490](https://github.com/nold-ai/specfact-cli-modules/issues/490) | Pinned upstream profiles: shared core contract before module consumption; does not block ordinary lean delivery. |
| 3 | Core [#750](https://github.com/nold-ai/specfact-cli/issues/750) / modules [#491](https://github.com/nold-ai/specfact-cli-modules/issues/491) | Optional context and separate digest: shared core contract before module consumption; does not block ordinary lean delivery. |
| 4 | Modules [#483](https://github.com/nold-ai/specfact-cli-modules/issues/483) / core [#742](https://github.com/nold-ai/specfact-cli/issues/742) | Signed #481 -> signed #483 -> core runtime adoption. Context-bound integration is optional; standalone adapter/projection development is independent. |
| 5 | Modules [#492](https://github.com/nold-ai/specfact-cli-modules/issues/492) | Thin Spec Kit invocation extension, GitHub Action/summary and located SARIF projection. Native JSON is authoritative. Hook import compatibility waits for the exact supported extension profile; full workflow use waits for released #483. |
| 6 | Modules [#164](https://github.com/nold-ai/specfact-cli-modules/issues/164) / core [#240](https://github.com/nold-ai/specfact-cli/issues/240), then modules [#230](https://github.com/nold-ai/specfact-cli-modules/issues/230) / core [#524](https://github.com/nold-ai/specfact-cli/issues/524) | Approved inputs first; one real usage cycle precedes Import Linter evidence. No duplicate graph engine or architecture authoring. |
| 7 | Core [#682](https://github.com/nold-ai/specfact-cli/issues/682) / modules [#431](https://github.com/nold-ai/specfact-cli-modules/issues/431), core [#684](https://github.com/nold-ai/specfact-cli/issues/684) / modules [#434](https://github.com/nold-ai/specfact-cli-modules/issues/434) | Optional context binding and affected obligations. Preserve the context-free optional assurance chain; selected context binding alone waits for its contracts. Share #483 budgets. |
| 8 | Modules [#169](https://github.com/nold-ai/specfact-cli-modules/issues/169) / core [#247](https://github.com/nold-ai/specfact-cli/issues/247); modules [#493](https://github.com/nold-ai/specfact-cli-modules/issues/493) | Optional Statement v1/SCAI v0.3 export and a separate exploratory pilot. No new signer/store or analytics platform; #170/#171 remain later consumers. |

Numbers above express delivery slices, not a single linear prerequisite chain. Compatibility/context can progress beside lean reconciliation. Existing optional assurance order remains core #682 -> modules #431 -> core #683 (also requiring independently delivered core #680) -> modules #432 -> core #684/modules #434. Only specialized optional #433 requires #434 and core #253; generic skills, native review and ordinary validation do not acquire those dependencies.

## Public contracts

RequirementDecisionContext is an optional versioned companion, not a new authoring source or mandatory plan field. Reuse existing clarification records, keep explicit assumptions/decisions with source references/digests and typed links, and preserve a separate canonical decision digest without changing legacy plan hashes. Owner/review date/falsifying-test links are optional unless selected policy requires them. Imported assertions are not authenticated approval.

R09 remains pure supplied-input reconciliation without Git, pytest or network execution. Core owns shared parsing, contracts and protected CI authority; workflow adapters own execution and external access. Structured pytest runner identity is the first certified execution path. External findings retain their original producer, severity/rule, artifact/snapshot identity and verification basis; trusted origin does not make heuristic advice deterministic truth.

A touched unresolved recorded assumption is advisory ordinarily. Required unavailable/ambiguous assurance evidence is UNKNOWN; reconciled contradictions are FAIL. Traceability is association, not behavioral satisfaction. Missing mappings remain not evaluated, and extraction cannot establish completeness of all hidden assumptions or extra behavior.

Native producer JSON remains authoritative. Summaries expose missing/unavailable checks; SARIF 2.1.0 projects only suitable located findings. Standard attestation export binds a digest-addressed bundle with Statement v1 and SCAI v0.3 and reuses existing signing. Authenticity, evidence freshness and claim correctness remain distinct.

## Acceptance and rollout

Each new proposal has formal Given/When/Then deltas, future implementation tasks and planning-only inspection mappings. Runtime implementation requires tests before code with actual failing/passing evidence and current readiness checks. Minimum negative scenarios include unsupported-profile atomic rejection; hook coexistence; legacy hash stability; context/source/config drift; wrong attempt/duplicate/skipped/stale/mismatched results; advisory convergence alongside required failures; unchanged worktree/index; forbidden dependencies; unavailable extraction; SARIF rule/location preservation; tampered bundle/wrong signer/subject; bounded repair exhaustion/no-progress/oscillation/human-decision stops.

Start context/feedback and architecture gates in shadow mode; retain required current checks and disable promotion on any false PASS. Roll back optional checks/projections or restore the prior compatible signed core/module pair without relabeling historical reports. No upstream artifact rewriting, default paid model calls, polyglot runner rollout, hosted graph, predictive cost admission or broad runtime tracing is included. MCP and attribution integrations wait for demonstrated client needs.

## Pilot and statistical limits

Thirty changes are an exploratory pilot, stratified by risk and size, with two independent reviewers. Record human review/clarification minutes, attempts to passing checks, elapsed seconds, actionability, false blocks and escaped defects with follow-up windows. Tokens and money remain separate measured units or unavailable. Analyze at change/team level using JSON/CSV; do not claim causality from an uncontrolled comparison or introduce a blocking specification score.

For #434, 20 known-good observations per pair and 100 overall are operational sample gates. At zero failures, the one-sided 95% binomial upper bound `1 - 0.05^(1/n)` is about 13.9% (n=20) and 3.0% (n=100); 299 independent representative zero-failure observations are needed for a bound below 1%. Retain the operational thresholds and report sampling limitations rather than manufacturing a population guarantee.

## Research and source boundaries

The owner-supplied research review motivates this plan; it does not establish SpecFact productivity, token savings, complete architectural correctness or independent defect recall. Directional review pressure is plausible; business-value and universal cost multipliers are unverified. Smékal's cited specification experiment uses five tasks and one model; the cited ChatDev review-token share is not human review cost. Existing competing extensions rule out an empty-market claim. Private datasets/envelope/graph research are not delivery dependencies.

Interface sources checked again 2026-10-04:

- [Spec Kit v1.1.0 release](https://github.com/github/spec-kit/releases/tag/v1.1.0), released 2026-10-02; pin fixtures alongside v0.12.18 rather than claim universal latest compatibility.
- [Spec Kit extension contract](https://github.github.io/spec-kit/reference/extensions.html); optional documented hooks are invocation assistance.
- [SCAI specification](https://github.com/in-toto/attestation/blob/main/spec/predicates/scai.md), v0.3; pin the exact specification revision during implementation.

Source contracts and existing implementation evidence must be revalidated at each runtime handoff. This roadmap is a multi-release effort measured in engineer-weeks; precise estimates and transferable benefits remain unknown until implementation and pilot data exist.

## Risks, confidence and next action

Confidence: high on isolated source/issue reconciliation and ownership boundaries; medium on product priorities; low on measured impact before a pilot. Assumptions that could change ordering: newer upstream profiles, changed released core/module contracts or new user demand for another ecosystem.

- Ceremony outgrows value: optional context/shadow gates, small independently reviewable releases and removal of ineffective checks.
- Evidence gains unjustified authority: preserve statuses and exact identities; independently verify CI provenance and disable promotion on a false PASS.
- Upstream churn: pinned fixtures/effective profiles and restore the prior compatible signed pair on regression.

Next: implement #481 in its own issue-linked worktree; release its signed current-run producer before #483 integration/core adoption. Implement compatibility and context as separate additive stories. No planning task checkbox is runtime passing evidence.
