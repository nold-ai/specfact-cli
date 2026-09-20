## Recovery review — 2026-09-20

Recovered from uncommitted planning files on `feature/code-review-14-protected-range-adoption`; the source worktree contains only this proposal and its change-order edit. Imported into local `dev` and the R09 planning worktree. No runtime changes were imported. Historical readiness and version identities below are dated context and must be revalidated before implementation. Recovery validation preserves existing staged-review scenarios and classifies previously nonexistent requirement headers as ADDED, avoiding invalid archive replacements. Canonical C14 follow-up reconciliation remains a prerequisite to final C15 specification promotion.

# Change Validation Report: code-review-14-protected-range-adoption

**Validation Date**: 2026-08-23
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: repository inspection at core `origin/dev`
`e3a20f20`, signed modules publication `6a0d0b31`, live GitHub issue and
hierarchy readback, and strict OpenSpec validation.

## Executive Summary

- Breaking Changes: 0 existing public core CLI signatures changed by proposal
- Dependency Boundary: modules C14 producer complete; core C14 consumer missing
- Impact Level: High trust impact; deliberately small core edit surface
- Validation Result: Pass for proposal/readiness; implementation not started

## Existing-Change and Issue Check

- No C14 protected-consumer OpenSpec change exists on core `origin/dev`.
- Core #679 is C15/schema 1.7 adoption and is not a substitute for this change.
- Core #680 now tracks this C14 adoption as a User Story under #375, on the
  `SpecFact CLI` project in `Todo`, assigned to `djm81`, with the expected
  labels and a native blocking relationship to #679.

## Frozen Upstream Handoff

- Modules implementation PR: #418
- Signed publication PR: #419
- Modules publication commit/tree:
  `6a0d0b31` / `0531325d68ae21f75abda01ce8968f92ba1b6d06`
- Module/version: `specfact-code-review` `0.49.46`
- Strict core compatibility: `===0.55.1`
- Core tag/commit/tree: `v0.55.1` /
  `b1e517e60e669eaba15a18ecfa83ef5a9df65276` /
  `47984be5434d7ae65ed6908bf525a32053290337`

All complete signature and checksum fields remain an implementation-readiness
gate and must be read directly from the immutable signed publication before
tests or fixture edits.

## Scope Validation

The proposal limits production work to one new verifier, one existing workflow,
one immutable fixture, and schema 1.6 parsing in one staged helper. It expressly
excludes producer/analyzer logic, generic module trust refactors, C15/schema
1.7, Requirements, waivers, scoring, and unrelated CI hardening. Additional
production files require a named failing test plus a spec amendment and strict
revalidation.

## OpenSpec Validation

- **Status**: Pass
- **Command**: `openspec validate code-review-14-protected-range-adoption --strict`
- **Issues Found/Fixed**: 0

## Stop Conditions Before Implementation

- Any signed publication identity differs from the frozen handoff.
- Core `origin/dev` or the module fixture moves without revalidation.
- Issue #680 leaves `Todo` because another implementation session started.
- Parent, labels, project, assignee, or native dependency metadata drifts.
- A required behavior cannot be expressed inside the normative scope boundary.
