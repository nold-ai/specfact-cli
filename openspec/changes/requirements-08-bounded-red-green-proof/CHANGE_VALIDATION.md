# Change Validation

## Status

`PLANNED — NO IMPLEMENTATION OR EXECUTION EVIDENCE`

The proposal, design, scenarios, bounded tasks, non-goals, and rollback path are defined. Runtime proof has not started. No statement in this folder is evidence that R08 is implemented.

## Current delivery-tree validation contract

- Planning command: `openspec validate --all --strict`.
- Required per-change command before and after implementation: `openspec validate requirements-08-bounded-red-green-proof --strict`.
- The authoritative planning result is the final successful SpecFact CLI Validation check on PR #674 whose recorded `head_sha` equals the PR delivery head.
- The exact final head SHA, workflow run URL, status, and result belong in the PR/check-suite delivery record after the last content commit. They are intentionally not hard-coded here: adding a commit's own SHA to this file would change that SHA and create an impossible self-reference.
- The earlier run for `4b12860a70c9e29dd67a01bd5f3cd55dcb86af60` is historical planning evidence only and is not evidence for the final PR tree.
- No failing-before implementation artifact, passing-after artifact, R/H/D replay, capsule, or verifier-epoch result exists yet.

## Planning sources and constraints

- Applied sources: `AGENTS.md`, `openspec/config.yaml`, and `docs/agent-rules/40-openspec-and-tdd.md`, `60-github-change-governance.md`, and `70-release-commit-and-docs.md`.
- GitHub governance check, live-read 2026-08-13T21:49:59Z: issue #675 exists and is open; labels are `enhancement`, `openspec`, and `change-proposal`; assignee is `djm81`; no blocker relationship is recorded. The ephemeral hierarchy cache was unavailable in this connector-only workspace, so the documented live-GitHub fallback was used.
- Unverified stop conditions: issue type, actual parent relationship, project assignment, and project status/concurrency are not exposed or not set in the returned issue metadata. Task B.3 stops implementation until a fresh cache/project check verifies them.
- Internal wiki: unavailable in this workspace; `tasks.md` requires the exact source-page and graph-rebuild follow-up.
- Affected planning files: `.openspec.yaml`, `README.md`, `proposal.md`, `design.md`, `tasks.md`, `CHANGE_VALIDATION.md`, `TDD_EVIDENCE.md`, `requirements-evidence.yaml`, and the R08 delta specification.
- Excluded or unavailable dependencies: signed immutable modules R08 release/fixture, accepted capsule-schema version, approved signing-key/trust-root identity, promoted verifier epoch, external checkpoint issuer/trust set, protected tag-ruleset identity, checkpoint-policy epoch, internal-wiki checkout, and benchmark corpus results.

## Future pre-R readiness evidence

Before accepting R, task B.3 SHALL append a readiness section recording the fresh governance/project/dependency checks, repository administrator approval, external checkpoint issuer/trust set, non-rewritable tag-ruleset identity, canonical annotation schema, checkpoint-policy epoch, signed-module prerequisites, environment limitations, and exact validation results. The readiness bytes SHALL be enclosed by exactly one `specfact:frozen-readiness` marker pair. The mapping SHALL classify that section as `readiness_validation_evidence`; its bytes and digest are frozen at R and must remain exactly once and byte-identical through D. Only after H may this file be extended outside the markers in H..D under its separate delivery-evidence role.

## Required implementation evidence

After H, outside the frozen readiness markers, this file SHALL record validation scope and impact, affected files, exact commands, actual outcomes and test counts, focused and full tests, skipped or unavailable tests/dependencies with reasons, artifact locations and identities, environment limitations, B/R/H/D and capsule identities, approved signer/trust-root verification, verifier epoch, and release hygiene. Planning evidence, failing-before evidence, and H..D passing/implementation evidence remain separate.

## Readiness blockers

- The paired modules R08 versioned capsule schema accepting B/R/H/D and the signed immutable release are not published.
- The signed fixture identity does not yet bind an accepted capsule-schema version, approved signing-key/trust-root identity, and verifier epoch.
- Failing tests, exact selectors, and failing-before evidence have not been written or recorded.
- No enforced network-isolation policy or verifier policy epoch exists.
- No external checkpoint issuer/trust set, non-rewritable `refs/tags/specfact-checkpoint/**` ruleset, canonical annotation schema, or checkpoint-policy epoch has been established; red/green issuance is blocked.
- No benchmark result has been produced by the proposed replay runner.
- Issue #675 exists with the required labels and assignee, but its requested User Story type, actual parent relation, project assignment/status, and concurrency state must be verified before implementation because the current connector cannot update project fields.
- Issue #675 currently records no GitHub blocker relationship. Before implementation, it must explicitly record and verify the corrected R07 current-run prerequisite (#662) and the paired signed modules R08 release tracked by modules issue #414/PR #412; missing or ambiguous dependency links are a stop condition.
- The internal-wiki follow-up in `tasks.md` remains incomplete.
