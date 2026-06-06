# Change: Dogfooding Proof for AI-Bloat Defense and Validation

## Why

SpecFact's flagship claim is no longer that it owns the full planning chain. The
claim to prove is sharper: run deterministic validation on a real repo, emit
JSON evidence, identify AI-bloat and drift findings, hand remediation packets to
an AI IDE, rerun, and show improved evidence.

## What Changes

- **NEW**: Define a dogfooding scenario set using real SpecFact PRs or a pinned
  demo repository slice.
- **NEW**: Require one end-to-end validation loop:
  - run `specfact code review` or equivalent validation command;
  - persist JSON evidence;
  - identify `ai_bloat`, drift, contract, or weak-test findings;
  - hand remediation packets to an AI IDE or headless agent;
  - rerun validation and compare evidence.
- **NEW**: Define release-readiness proof criteria for AI-bloat defense and
  validation positioning claims.
- **NEW**: Add CI/report outputs proving the evidence loop rather than a
  requirements-to-code lifecycle.

## Capabilities

### New Capabilities

- `dogfooding-validation-ai-bloat-proof`: Self-validation flow that proves
  evidence generation, AI-bloat remediation, rerun comparison, and improved
  validation evidence on a real project slice.

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
