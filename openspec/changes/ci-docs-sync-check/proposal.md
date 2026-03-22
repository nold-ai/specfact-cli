# CI Docs Sync Check

## Why

While the frontmatter schema provides ownership tracking, there's no enforcement mechanism to ensure documentation stays synchronized with source code changes. Developers can modify tracked source files without updating corresponding documentation, leading to documentation drift.

This change implements CI enforcement to:
- Automatically detect when source files change but tracked docs don't
- Fail PRs with stale documentation
- Provide clear guidance on what needs updating
- Maintain documentation quality through automation

## What Changes

This change implements a CI-based documentation synchronization check:

### New Components
- **Sync Algorithm**: Detects stale documentation based on frontmatter tracking
- **GitHub Workflow**: `.github/workflows/docs-sync.yml` for PR validation
- **Sync Script**: `scripts/check-docs-sync.py` for algorithm implementation
- **Branch Protection**: Required status check for main branch

### Modified Components
- **CI Configuration**: New workflow added to GitHub Actions
- **Branch Protection**: Updated to require docs sync check
- **Documentation**: Updated with CI workflow documentation

## Capabilities

### New Capabilities
- `docs-sync-algorithm`: CI sync algorithm specification and implementation
- `github-workflow`: GitHub Actions workflow for docs sync checking
- `ci-integration`: Branch protection setup and configuration

### Modified Capabilities
- `doc-frontmatter-schema`: Extended with CI integration requirements

## Impact

### Files to Create
- `scripts/check-docs-sync.py` - Sync algorithm implementation
- `.github/workflows/docs-sync.yml` - GitHub Actions workflow
- `docs/contributing/ci-docs-sync.md` - CI workflow documentation

### Files to Modify
- `.github/settings.yml` - Branch protection configuration
- Existing documentation - Updated with CI workflow information

### Development Workflow
- PRs that modify tracked source files must update corresponding docs
- CI provides clear error messages for stale documentation
- Developers get immediate feedback on documentation requirements
- Optional `docs-exempt` label for intentional exemptions

### Quality Gates
- Zero errors policy: CI workflow must pass before merge
- TDD-first approach: Tests for sync algorithm created before implementation
- Specfact code review: All changes go through review process
- Git worktree patterns: Use git worktrees for isolated development

### GitHub Integration
- GitHub issue sync via specfact after openspec change creation
- Proper labels: `documentation`, `quality`, `ci`, `automation`
- Link to parent epic: `feature/docs-sync-epic`
- Required status check for main branch protection

## Success Criteria

### Technical Success
- ✅ CI docs sync check passes on all PRs with updated docs
- ✅ CI fails appropriately when docs are stale
- ✅ Sync algorithm correctly identifies affected documentation
- ✅ Zero errors in all quality gates

### Process Success
- ✅ Openspec change follows spec-driven schema
- ✅ Git worktree patterns used for isolation
- ✅ Specfact code review completes with zero findings
- ✅ GitHub issue synced with proper metadata
- ✅ Branch protection enforced for main branch

## Dependencies

- `doc-frontmatter-schema` change must be implemented first
- Existing GitHub Actions infrastructure
- Python 3.12+ environment for scripts
- PyYAML dependency for frontmatter parsing
- GitHub repository admin permissions for branch protection

## Future Enhancements

- Performance optimization for large repositories
- Caching mechanism for glob pattern matching
- Automated doc update suggestions
- Impact analysis with change previews
- Interactive doc update assistance