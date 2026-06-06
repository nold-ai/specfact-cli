# Change: Agent Skill for SpecFact Validation

## Why

AI IDEs need a low-context way to invoke SpecFact after they change code, read
the evidence, apply remediation packets, and rerun proof. A skills-first
integration is a good distribution path because it keeps the CLI authoritative
and avoids a large always-loaded MCP context.

## What Changes

- **NEW**: Agent Skill at `skills/specfact/SKILL.md` that teaches agents when
  and how to run SpecFact validation and code review.
- **NEW**: Skill instructions for interpreting JSON evidence, severity, policy
  exceptions, `ai_bloat` advisories, cleanup forecasts, and remediation packets.
- **NEW**: Small workflow sub-skills focused on validation use cases:
  PR evidence review, code-bloat cleanup loop, contract/spec validation, and
  rerun comparison.
- **NEW**: `specfact ide skill install` copies skill files to the appropriate
  project or IDE location.
- **REMOVED FROM SCOPE**: Upstream intent interviews, requirement authoring, and
  architecture generation.

## Capabilities

### New Capabilities

- `agent-skill-validation`: Agent Skill for running SpecFact validation,
  interpreting evidence, applying remediation packets, and rerunning proof.

### Modified Capabilities

(none)

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #251
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/251>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 2b715dada0ffb0b0 -->
