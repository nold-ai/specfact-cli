# Change: Cross-Platform AI IDE Validation Instructions

## Why

Teams use several AI IDEs, each with a different instruction-file format. Those
files should point agents to SpecFact validation and remediation loops without
embedding long planning workflows or clean-code charters inline.

## What Changes

- **NEW**: `specfact ide setup --platforms cursor,copilot,claude,windsurf`
  generates lightweight instruction files for selected platforms.
- **NEW**: Generated files tell agents when to run SpecFact validation, how to
  find JSON evidence, how to handle `ai_bloat` remediation packets, and when to
  rerun proof.
- **NEW**: `specfact ide setup --update` regenerates instruction files from the
  canonical validation skill template.
- **NEW**: Glob-based attachment focuses on code, spec, contract, and test files
  where validation evidence is relevant.
- **MODIFY**: Clean-code enforcement is referenced by alias to the canonical
  code-review skill, not copied inline.

## Capabilities

### New Capabilities

- `cross-platform-validation-instructions`: Auto-generated AI IDE instruction
  files that point to SpecFact validation, evidence interpretation, remediation,
  and rerun proof.

### Modified Capabilities

(none)

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #253
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/253>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 23d56625f9ca6351 -->
