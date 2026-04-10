# Change: Dogfooding E2E Proof for Full-Chain Traceability

## Why

To claim SpecFact CLI as the end-to-end "swiss knife" for agile DevOps teams, the tool must prove its own flow with real artifacts. This change establishes a dedicated dogfooding implementation and evidence path from requirements through architecture, specs, code, tests, and CI evidence output.

## What Changes

- **NEW**: Define a dogfooding scenario set using real SpecFact backlog items and requirements
- **NEW**: Require one complete end-to-end traceability run:
  - backlog item -> requirement -> architecture artifact -> spec -> code/test references -> full-chain evidence JSON
- **EXTEND**: The dogfooding proof also runs clean-code review as a side-channel so the final evidence bundle demonstrates both traceability and clean-code compliance
- **NEW**: Define release-readiness proof criteria for end-to-end positioning claims
- **NEW**: Add CI/report outputs proving wave gate completion for E2E chain

## Capabilities

### New Capabilities

- `dogfooding-full-chain-e2e`: End-to-end self-validation flow for SpecFact CLI that proves requirements-to-evidence traceability in a real project slice.
- `dogfooding-full-chain-e2e`: Extended to include clean-code review evidence in the final proof bundle

### Modified Capabilities

(none)

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #255
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/255>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: f9086a54d2678c76 -->
