# Doc Frontmatter Schema & Validation

## Why

The repository has extensive documentation but lacks a mechanism to track ownership and ensure documentation stays aligned with source code changes. This leads to documentation drift where docs become outdated when source files change, creating maintenance burden and potential misinformation for developers and users.

The goal is to implement a frontmatter-based ownership model that:

- Clearly defines which module owns each documentation file
- Tracks which source files each doc should stay synchronized with
- Provides validation to prevent metadata drift
- Enables future CI integration for automated sync checking

## What Changes

This change introduces a frontmatter-based documentation ownership and validation system:

### New Components

- **YAML Frontmatter Schema**: Standardized metadata format for documentation files
- **Validation Script**: `scripts/check_doc_frontmatter.py` to validate doc ownership
- **Pre-commit Hook**: Integration with existing pre-commit workflow
- **Documentation**: Updated contributing guidelines with frontmatter requirements

### Modified Components

- **Documentation Files**: Add frontmatter to existing docs in `docs/` directory
- **Pre-commit Config**: `.pre-commit-config.yaml` updated with new validation hook
- **Contributing Guidelines**: `docs/contributing/` updated with frontmatter documentation
- **PR Orchestrator Workflow**: `.github/workflows/pr-orchestrator.yml` dependency graph reduced so
  independent validation jobs can start after signature verification instead of waiting for the
  full Python 3.12 test suite

## Capabilities

### New Capabilities

- `doc-frontmatter-schema`: YAML frontmatter schema definition for documentation ownership
- `doc-frontmatter-validation`: Pre-commit validation script implementation
- `docs-contributing-updates`: Updated contributing guidelines with frontmatter documentation

### Modified Capabilities

- `pr-orchestrator-parallelization`: PR workflow jobs that do not consume test artifacts run in
  parallel after the shared signature gate

## Impact

### Files to Create

- `scripts/check_doc_frontmatter.py` - Validation script
- `docs/contributing/docs-sync.md` - Frontmatter documentation

### Files to Modify

- `.pre-commit-config.yaml` - Add validation hook
- `docs/**/*.md` - Add frontmatter metadata
- `USAGE-FAQ.md` - Add frontmatter (root-level doc)
- `.github/workflows/pr-orchestrator.yml` - remove unnecessary `needs: tests` / downstream
  serialization for independent CI jobs
- `tests/unit/specfact_cli/registry/test_signing_artifacts.py` - lock PR orchestrator dependency
  graph for parallel execution

### Development Workflow

- Developers must add frontmatter to new documentation files
- Pre-commit hooks validate doc metadata on every commit
- CI workflows can use metadata for automated sync checking
- PR validation jobs that do not require coverage artifacts or prior test completion should not wait
  for the `Tests (Python 3.12)` job

### Quality Gates

- Zero errors policy: All validation must pass
- TDD-first approach: Tests for validation script created before implementation
- Specfact code review: All changes go through review process
- Git worktree patterns: Use git worktrees for isolated development

### GitHub Integration

- **Issue**: [#461](https://github.com/nold-ai/specfact-cli/issues/461) — `[Change] Doc Frontmatter Schema & Validation`
- **Labels**: `enhancement`, `documentation`, `change-proposal`, `openspec`
- **Parent Feature**: [#356](https://github.com/nold-ai/specfact-cli/issues/356) — Documentation & Discrepancy Remediation (cross-linked in thread on #356)
- **Repository**: `nold-ai/specfact-cli`
- **Status**: synced 2026-03-29

## Success Criteria

### Technical Success

- ✅ All tracked documentation has valid frontmatter
- ✅ Pre-commit validation prevents invalid commits
- ✅ Validation script passes all tests
- ✅ Zero errors in quality gates

### Process Success

- ✅ Openspec change follows spec-driven schema
- ✅ Git worktree patterns used for isolation
- ✅ Specfact code review completes with zero findings
- ✅ GitHub issue synced with proper metadata

## Dependencies

- Existing pre-commit infrastructure (`hatch run` setup)
- Python 3.12+ environment for scripts
- PyYAML dependency for frontmatter parsing
- GitHub Actions workflow permissions (for future CI integration)

## Future Enhancements

- CI Docs Sync Check (separate change: `ci-docs-sync-check`)
- Automated doc update suggestions
- Impact analysis for source changes
- Ownership visualization tools
