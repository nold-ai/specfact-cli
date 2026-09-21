# Dependency and scope review

Reviewed 2026-09-20 against freshly fetched core origin/dev and modules dev, all open issue bodies, native blocked-by/blocking relationships, parent hierarchy and project status. Scope is planning only. All affected implementation issues were Todo at inspection; no concurrent In Progress state was observed.

## Dispositions and dependency edits

- Core #740 owns coordinated default delivery/governance; modules #481 owns current-run product semantics/signing. Native edge: core #740 is blocked by modules #481. Policy preparation can proceed first.
- Core #662 transfers its unfinished R07 scope to #740 and waits for replacement reconciliation. Remove its stale blocker on closed modules #368. Modules #368 remains closed historical delivery; do not reopen it to imply the corrected contract shipped.
- R08 core #675/modules #414 remains closed Not Planned. No replay capsule/checkpoint protocol is reintroduced.
- Remove four optional-assurance prerequisites: core #680 <- modules #431; modules #417 <- modules #432; core #251 <- modules #434; modules #460 <- modules #434.
- Preserve the internal optional chain. Add core #683 <- modules #431 because that dependency is no longer inherited through C14; add modules #433 <- modules #434 because generic installation no longer supplies that transitive prerequisite.
- Keep C14/C15 real producer/runtime/layout/profile/policy/exception dependencies and native-platform regression requirements. Generic skill installation uses bounded fixtures and authentic signed assets when applicable; optional preflight assets wait for their own signed release.
- Scope instruction generation to lean defaults and explicit optional-assurance references. Governance emitters, graph consumers and dogfood retain useful observations without becoming prerequisites for MEB.
- Core #736 and docs16/docs17, required-check triggers, security/provenance/promotion repair changes are merged or historical records awaiting their separate acceptance/archive reconciliation. Preserve real security fixes and historical evidence; do not reopen them as proof prerequisites.
- Core #680/#679 and modules #417 were recovered from uncommitted planning-only feature worktrees into local `dev` and the R09 planning worktrees on 2026-09-20. Remote integration remains pending. All three remain planned; no implementation was imported. Modules C14 #416 shipped and is closed, but its existing proposal remains unarchived on dev; it is distinct from core C14 adoption #680.
- Broader graph backlog has pre-existing prose/native dependency differences (for example core #241/#247). Do not rewrite that unrelated graph here or add it to the MEB critical path.

## Open issue inventory

The inventory below covers all 74 pre-existing open issues (47 core, 27 modules), not only keyword matches. The two new stories are additional. A retained issue is not asserted complete or free of defects; it has no new hard dependency on this migration.

| Repository | Issue | Disposition |
|---|---|---|
| specfact-cli | [#186 [Epic] specfact backlog](https://github.com/nold-ai/specfact-cli/issues/186) | Retain scope; no new MEB blocker |
| specfact-cli | [#194 [Epic] Architecture (CLI structure, modularity, performance)](https://github.com/nold-ai/specfact-cli/issues/194) | Retain scope; no new MEB blocker |
| specfact-cli | [#240 Architecture Boundary Validation Records](https://github.com/nold-ai/specfact-cli/issues/240) | Retain scope; no new MEB blocker |
| specfact-cli | [#241 Validation Evidence Graph Engine](https://github.com/nold-ai/specfact-cli/issues/241) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#244 Backlog Drift Evidence Adapter](https://github.com/nold-ai/specfact-cli/issues/244) | Retain scope; no new MEB blocker |
| specfact-cli | [#247 Evidence & Audit Output for CI/CD Pipelines](https://github.com/nold-ai/specfact-cli/issues/247) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#248 Exception Management — Time-Bound, Tracked Policy Exceptions](https://github.com/nold-ai/specfact-cli/issues/248) | Retain scope; no new MEB blocker |
| specfact-cli | [#251 [User Story] Shared Module-Owned Skill Discovery, Installation, and Export](https://github.com/nold-ai/specfact-cli/issues/251) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#252 Thin MCP Adapter For Validation Tools](https://github.com/nold-ai/specfact-cli/issues/252) | Retain scope; no new MEB blocker |
| specfact-cli | [#253 [User Story] Generated AGENTS, OpenSpec, Spec Kit, and Harness Instructions](https://github.com/nold-ai/specfact-cli/issues/253) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#254 Integration Umbrella for Cross-Change Contracts and Ownership](https://github.com/nold-ai/specfact-cli/issues/254) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#255 AI-Bloat Defense Dogfooding Proof](https://github.com/nold-ai/specfact-cli/issues/255) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#256 Validation evidence and context adapters](https://github.com/nold-ai/specfact-cli/issues/256) | Retain scope; no new MEB blocker |
| specfact-cli | [#257 AI IDE validation integration](https://github.com/nold-ai/specfact-cli/issues/257) | Retain scope; no new MEB blocker |
| specfact-cli | [#258 Evidence dogfooding and governance](https://github.com/nold-ai/specfact-cli/issues/258) | Retain scope; no new MEB blocker |
| specfact-cli | [#281 [Change] Misuse Safety Proof](https://github.com/nold-ai/specfact-cli/issues/281) | Retain scope; no new MEB blocker |
| specfact-cli | [#282 [Change] Acceptance Test Runner](https://github.com/nold-ai/specfact-cli/issues/282) | Retain scope; no new MEB blocker |
| specfact-cli | [#285 CLI validation trust](https://github.com/nold-ai/specfact-cli/issues/285) | Retain scope; no new MEB blocker |
| specfact-cli | [#353 [Feature] Marketplace Module Distribution](https://github.com/nold-ai/specfact-cli/issues/353) | Retain scope; no new MEB blocker |
| specfact-cli | [#354 [Feature] Module Migration & CLI Reorganization](https://github.com/nold-ai/specfact-cli/issues/354) | Retain scope; no new MEB blocker |
| specfact-cli | [#356 [Feature] Documentation & Discrepancy Remediation](https://github.com/nold-ai/specfact-cli/issues/356) | Retain scope; no new MEB blocker |
| specfact-cli | [#357 [Feature] Backlog Core Commands](https://github.com/nold-ai/specfact-cli/issues/357) | Retain scope; no new MEB blocker |
| specfact-cli | [#360 [Feature] Kanban Flow Metrics](https://github.com/nold-ai/specfact-cli/issues/360) | Retain scope; no new MEB blocker |
| specfact-cli | [#361 [Feature] SAFe & PI Planning](https://github.com/nold-ai/specfact-cli/issues/361) | Retain scope; no new MEB blocker |
| specfact-cli | [#365 [Feature] Configuration Profiles](https://github.com/nold-ai/specfact-cli/issues/365) | Retain scope; no new MEB blocker |
| specfact-cli | [#366 [Feature] Requirements Layer](https://github.com/nold-ai/specfact-cli/issues/366) | Retain scope; no new MEB blocker |
| specfact-cli | [#367 [Feature] Solution Architecture Layer](https://github.com/nold-ai/specfact-cli/issues/367) | Retain scope; no new MEB blocker |
| specfact-cli | [#368 [Feature] Full-Chain Validation & Traceability](https://github.com/nold-ai/specfact-cli/issues/368) | Retain scope; no new MEB blocker |
| specfact-cli | [#370 [Feature] Governance, Policy Packs & Evidence](https://github.com/nold-ai/specfact-cli/issues/370) | Retain scope; no new MEB blocker |
| specfact-cli | [#371 [Feature] OpenSpec Bridge Integration](https://github.com/nold-ai/specfact-cli/issues/371) | Retain scope; no new MEB blocker |
| specfact-cli | [#372 [Feature] Agent Skills & Instruction Files](https://github.com/nold-ai/specfact-cli/issues/372) | Retain scope; no new MEB blocker |
| specfact-cli | [#373 [Feature] MCP Server](https://github.com/nold-ai/specfact-cli/issues/373) | Retain scope; no new MEB blocker |
| specfact-cli | [#374 [Feature] End-to-End Integration Proof](https://github.com/nold-ai/specfact-cli/issues/374) | Retain scope; no new MEB blocker |
| specfact-cli | [#375 [Feature] CLI Behavior Validation Suite](https://github.com/nold-ai/specfact-cli/issues/375) | Retain scope; no new MEB blocker |
| specfact-cli | [#514 [Feature] Architecture Review & Interface Governance](https://github.com/nold-ai/specfact-cli/issues/514) | Retain scope; no new MEB blocker |
| specfact-cli | [#518 Opt-In Validation Outcome Telemetry](https://github.com/nold-ai/specfact-cli/issues/518) | Retain scope; no new MEB blocker |
| specfact-cli | [#524 Architecture-Boundary Review Findings (Gated)](https://github.com/nold-ai/specfact-cli/issues/524) | Retain scope; no new MEB blocker |
| specfact-cli | [#662 [Change] Deliver empirical requirements proof in local and CI gates](https://github.com/nold-ai/specfact-cli/issues/662) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#679 [Change] Adopt the signal-calibrated Code Review gate](https://github.com/nold-ai/specfact-cli/issues/679) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#680 [Change] Adopt C14 protected PR-range assurance](https://github.com/nold-ai/specfact-cli/issues/680) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#681 [Feature] Deterministic Pre-Implementation Change Assurance](https://github.com/nold-ai/specfact-cli/issues/681) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#682 [User Story] Deterministic Pre-Implementation Design Contract Core](https://github.com/nold-ai/specfact-cli/issues/682) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#683 [User Story] Preflight Dogfood Evidence and Readiness Decision](https://github.com/nold-ai/specfact-cli/issues/683) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#684 [User Story] Seal-Bound Development Checkpoint and Conformance Core](https://github.com/nold-ai/specfact-cli/issues/684) | Rescoped; see authoritative issue amendment |
| specfact-cli | [#718 [Change] Block category-less module command squatting](https://github.com/nold-ai/specfact-cli/issues/718) | Retain scope; no new MEB blocker |
| specfact-cli | [#720 [Change] Confine IDE prompt exports to the repository](https://github.com/nold-ai/specfact-cli/issues/720) | Retain scope; no new MEB blocker |
| specfact-cli | [#736 [Bug] Close release workflow authentication and evidence gaps](https://github.com/nold-ai/specfact-cli/issues/736) | Rescoped; see authoritative issue amendment |
| specfact-cli-modules | [#124 [Change] docs-14 - Publish-Driven Module Release History And Docs Rendering](https://github.com/nold-ai/specfact-cli-modules/issues/124) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#144 specfact project validation context adapters](https://github.com/nold-ai/specfact-cli-modules/issues/144) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#145 specfact backlog policy and evidence inputs](https://github.com/nold-ai/specfact-cli-modules/issues/145) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#147 Sync Safety For Validation Context Adapters](https://github.com/nold-ai/specfact-cli-modules/issues/147) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#148 [Feature] Policy Engine & Enforcement Modes](https://github.com/nold-ai/specfact-cli-modules/issues/148) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#157 Sync Safety Kernel For Validation Context Adapters](https://github.com/nold-ai/specfact-cli-modules/issues/157) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#158 Policy Packs & Enforcement Modes (Advisory/Mixed/Hard)](https://github.com/nold-ai/specfact-cli-modules/issues/158) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#161 Context Adapters For Validation Evidence](https://github.com/nold-ai/specfact-cli-modules/issues/161) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#162 specfact code / AI-bloat defense](https://github.com/nold-ai/specfact-cli-modules/issues/162) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#163 Validation Evidence And Governance Runtime Follow-Ups](https://github.com/nold-ai/specfact-cli-modules/issues/163) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#164 Architecture Boundary Runtime Input Follow-Up](https://github.com/nold-ai/specfact-cli-modules/issues/164) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#166 Backlog Drift Evidence Runtime Follow-Up](https://github.com/nold-ai/specfact-cli-modules/issues/166) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#167 [Change] Runtime Exception Management And Enforcement Follow-Up](https://github.com/nold-ai/specfact-cli-modules/issues/167) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#169 [Change] Governance Evidence Emitters Follow-Up](https://github.com/nold-ai/specfact-cli-modules/issues/169) | Rescoped; see authoritative issue amendment |
| specfact-cli-modules | [#170 [Change] Traceability Runtime Queries And Orphan Detection Follow-Up](https://github.com/nold-ai/specfact-cli-modules/issues/170) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#171 Validation Evidence Graph Runtime Engine Follow-Up](https://github.com/nold-ai/specfact-cli-modules/issues/171) | Rescoped; see authoritative issue amendment |
| specfact-cli-modules | [#219 [Feature] Architecture Review & Interface Governance](https://github.com/nold-ai/specfact-cli-modules/issues/219) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#230 Architecture Boundary Review Module (Gated)](https://github.com/nold-ai/specfact-cli-modules/issues/230) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#275 [Feature] Code Review Simplification Feedback Loop](https://github.com/nold-ai/specfact-cli-modules/issues/275) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#305 [Feature] Backlog CLI Contract Reliability](https://github.com/nold-ai/specfact-cli-modules/issues/305) | Retain scope; no new MEB blocker |
| specfact-cli-modules | [#417 [Change] Calibrate Code Review into a truthful blocking gate](https://github.com/nold-ai/specfact-cli-modules/issues/417) | Rescoped; see authoritative issue amendment |
| specfact-cli-modules | [#431 [User Story] Pre-Implementation Assurance Runtime and Bundled Workflow](https://github.com/nold-ai/specfact-cli-modules/issues/431) | Rescoped; see authoritative issue amendment |
| specfact-cli-modules | [#432 [User Story] Evidence-Backed Preflight Hardening and Stable Publication](https://github.com/nold-ai/specfact-cli-modules/issues/432) | Rescoped; see authoritative issue amendment |
| specfact-cli-modules | [#433 [User Story] Plug-and-Play Preflight Harness Adapters](https://github.com/nold-ai/specfact-cli-modules/issues/433) | Rescoped; see authoritative issue amendment |
| specfact-cli-modules | [#434 [User Story] Seal-Bound Development Checkpoint and Conformance Runtime](https://github.com/nold-ai/specfact-cli-modules/issues/434) | Rescoped; see authoritative issue amendment |
| specfact-cli-modules | [#460 [Change] Native local Code Review on macOS, Linux, and Windows](https://github.com/nold-ai/specfact-cli-modules/issues/460) | Rescoped; see authoritative issue amendment |
| specfact-cli-modules | [#480 P2 Bug Post-0.50.1: preserve explicit pytest file selection in portable reviews](https://github.com/nold-ai/specfact-cli-modules/issues/480) | Retain scope; no new MEB blocker |

## Active change inventory

| Repository | Change | Disposition |
|---|---|---|
| specfact-cli | `ai-integration-01-agent-skill` | Rescoped planning; existing evidence untouched |
| specfact-cli | `ai-integration-02-mcp-server` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `ai-integration-03-instruction-files` | Rescoped planning; existing evidence untouched |
| specfact-cli | `architecture-01-solution-layer` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `architecture-02-well-architected-review` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `audit-01-reproducible-delivery` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `ci-02-release-workflow-review` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `cli-removed-flat-alias-diagnostics` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `cli-val-03-misuse-safety-proof` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `cli-val-04-acceptance-test-runner` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `cli-val-05-ci-integration` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `docs-16-code-review-runtime-parity` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `docs-17-code-review-pytest-fixture-parity` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `dogfooding-01-full-chain-e2e-proof` | Rescoped planning; existing evidence untouched |
| specfact-cli | `fix-ci-test-environment-isolation` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `fix-final-requirements-review-artifact` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `fix-release-promotion-requirements-parity` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `fix-release-promotion-security-gates` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `governance-01-evidence-output` | Rescoped planning; existing evidence untouched |
| specfact-cli | `governance-02-exception-management` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `module-scope-02-preserve-user-installs` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `openspec-01-intent-trace` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `preflight-01-design-contract-core` | Rescoped planning; existing evidence untouched |
| specfact-cli | `preflight-03-dogfood-hardening-and-release` | Rescoped planning; existing evidence untouched |
| specfact-cli | `preflight-05-implementation-conformance` | Rescoped planning; existing evidence untouched |
| specfact-cli | `profile-01-config-layering` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `required-check-workflow-trigger-parity` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `requirements-03-backlog-sync` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `requirements-04-upstream-source-readiness` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `requirements-06-evidence-enforcement` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `requirements-07-runtime-proof-delivery` | Rescoped planning; existing evidence untouched |
| specfact-cli | `requirements-09-minimal-evidence` | New paired MEB scope |
| specfact-cli | `telemetry-01-opentelemetry-default-on` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `tooling-spaced-env-pythonpath` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `traceability-01-index-and-orphans` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli | `validation-02-full-chain-engine` | Rescoped planning; existing evidence untouched |
| specfact-cli-modules | `architecture-01-solution-layer` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `architecture-02-module-well-architected` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `ci-02-codeql-cache-scope-isolation` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `code-review-14-scope-truth-and-differential-enforcement` | Shipped #416; unarchived historical follow-up tasks need reconciliation; distinct from core C14 #680 |
| specfact-cli-modules | `code-review-16-portable-project-runtime` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `code-review-capsule-customer-execution` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `code-review-installed-payload-layout` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `code-review-native-platform-execution` | Rescoped planning; existing evidence untouched |
| specfact-cli-modules | `docs-14-module-release-history` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `governance-01-evidence-output` | Rescoped planning; existing evidence untouched |
| specfact-cli-modules | `governance-02-exception-management` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `governance-05-hierarchy-cache-freshness` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `openspec-01-intent-trace` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `policy-02-packs-and-modes` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `preflight-02-assurance-runtime` | Rescoped planning; existing evidence untouched |
| specfact-cli-modules | `preflight-03-dogfood-hardening-and-release` | Rescoped planning; existing evidence untouched |
| specfact-cli-modules | `preflight-04-harness-adapters` | Rescoped planning; existing evidence untouched |
| specfact-cli-modules | `preflight-05-implementation-conformance` | Rescoped planning; existing evidence untouched |
| specfact-cli-modules | `requirements-03-backlog-sync` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `requirements-06-evidence-enforcement` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `requirements-07-scenario-runtime-proof` | Rescoped planning; existing evidence untouched |
| specfact-cli-modules | `requirements-09-minimal-evidence` | New paired MEB scope |
| specfact-cli-modules | `sync-01-unified-kernel` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `traceability-01-index-and-orphans` | Reviewed; retain existing scope/status; not a new MEB prerequisite |
| specfact-cli-modules | `validation-02-full-chain-engine` | Rescoped planning; existing evidence untouched |

| specfact-cli | `code-review-14-protected-range-adoption` | Recovered and rescoped planning for #680; implementation not started |
| specfact-cli | `cli-val-07-code-review-gate-adoption` | Recovered and rescoped planning for #679; implementation not started |
| specfact-cli-modules | `code-review-15-signal-calibrated-blocking-gate` | Recovered and rescoped planning for #417; implementation not started |

## Limits and implementation readiness

This audit changes future scope, not deployed guarantees. Required checks, signing, registry data, source code and tests are untouched. New stories remain Todo; metadata and native relations are read back after mutation. Actual protection/ruleset changes need the reviewed cutover task, not a planning-time bypass.

No exact token cost or causal fraction of PR waiting time is known. Evidence-artifact churn is measured separately from useful test/source changes. No archive action is performed before verified completion.

## C14/C15 source recovery

Verified 2026-09-20: each source worktree had only its untracked change directory and a change-order edit; no associated open pull request. Source branches: core `feature/code-review-14-protected-range-adoption` at `e3a20f20`; core `feature/cli-val-07-code-review-gate-adoption` at `31d945e0`; modules `feature/code-review-15-signal-calibrated-blocking-gate` at `c3eda08c`. Recovered documents include their existing design/tasks/specs and dated validation context; the new scope amendment replaces default historical-proof duties. Original worktrees were preserved.

Modules C14 implementation [PR #418](https://github.com/nold-ai/specfact-cli-modules/pull/418) and release [PR #420](https://github.com/nold-ai/specfact-cli-modules/pull/420) merged, and [#416](https://github.com/nold-ai/specfact-cli-modules/issues/416) closed on 2026-08-27. Its proposal is still in the active tree rather than the archive. Do not mark its accumulated later tasks complete or promote its full delta without a separate implementation-to-spec reconciliation.
