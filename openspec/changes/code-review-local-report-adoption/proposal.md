# Change: Adopt local Code Review reports in ordinary core workflows

## Status

Planned only, 2026-10-16. No runtime implementation, test execution, release support, or completed acceptance is claimed.

- GitHub issue: [core #769](https://github.com/nold-ai/specfact-cli/issues/769).
- Parent: core #375 under epic #285. Project: SpecFact CLI. Status: Todo. Type: User Story.
- Direct blocker: [modules #515](https://github.com/nold-ai/specfact-cli-modules/issues/515), `code-review-19-local-report-and-cutover`.
- Blocks only [modules #516](https://github.com/nold-ai/specfact-cli-modules/issues/516), `code-review-20-external-installation-acceptance`.

## Why

A customer runs an externally installed SpecFact CLI against a trusted local Python repository. Ordinary hooks and workflows need truthful local evidence without making the project adopt SpecFact's interpreter or capsule infrastructure. Core must consume the new producer contract before external installation acceptance can prove the complete workflow.

## What Changes

- Plan explicit report schema 2.0 dispatch in ordinary core consumers. Keep a historical 1.6 reader only where its contract is supported. Preserve explicit schema 1.7 dispatch at consumers governed by C15 until its owner authorizes a separate retirement; this adoption does not enable C15. Reject unsupported major versions.
- Consume producer assurance and completeness. Do not derive success from score or fixability. Shadow rollout preserves adverse results.
- Keep ordinary hook and workflow invocation, module installation compatibility, loading, and discovery in core. Keep project runtime resolution, customer standards, analyzers, and report production in modules.
- Collect exact installed core and signed module compatibility preflight evidence for pipx, uv tool, and uvx, independent of project Python. Modules #516 retains release-level installation acceptance and the manager/platform matrix.

## Capabilities

### New capabilities

- `local-review-consumer`: ordinary core consumption of trusted local schema 2.0 evidence.

## Non-goals

Protected `pr_range`, capsule attestation, analyzer changes, customer-environment dependency injection, broader registry rewrites, and C15 policy redesign are excluded. Local execution trusts the repository, including its project tooling. Optional preflight, architecture, and Requirements addons may consume reports later. They are not blanket blockers.

Core #680 retains its separate protected capsule contract. Local schema 2.0 cannot satisfy it. Core #679 and modules #417 retain their owners, status, and acceptance. Independent security work modules #511 and core #719/#718 remains independent. Signing and security gates remain mandatory.

## Impact

Future work is bounded to existing ordinary consumers and necessary installed-module compatibility paths. Completion requires real installed customer workflow proof, explicit schema rejection, truthful adverse summaries, and normal quality/security/signature gates. Effort requires consumer changes and a multi-install acceptance matrix; no duration estimate is asserted. Rollback pins the previous immutable compatible released CLI/module pair while retaining adverse evidence. It must not silently reinterpret schema 2.0 through an older reader or reduce acceptance to hide incompatibility.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #769
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/769>
- **Last Synced Status**: open
- **Project Status**: Todo
- **Parent Feature**: [#375](https://github.com/nold-ai/specfact-cli/issues/375)
