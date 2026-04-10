# Doc Frontmatter Schema & Validation - Technical Design

## Context

The current documentation system lacks ownership tracking and synchronization mechanisms. Documentation files can become outdated when source code changes, leading to maintenance challenges and potential misinformation. This design implements a frontmatter-based ownership and validation system to address these issues.

### Current State

- Documentation files in `docs/` and root-level markdown files
- No ownership tracking mechanism
- Manual review process for documentation updates
- No automated validation of documentation metadata

### Constraints

- Must integrate with existing pre-commit infrastructure
- Must support Python 3.12+ environment
- Must use existing code quality tools and patterns
- Must follow contract-first development approach
- Must be compatible with GitHub Actions workflows

### Stakeholders

- Developers: Need clear ownership and validation feedback
- Technical Writers: Need documentation standards and templates
- CI/CD Pipeline: Needs reliable validation mechanism
- Code Reviewers: Need automated quality gates

## Goals / Non-Goals

### Goals

- Implement YAML frontmatter schema for documentation ownership
- Create validation script with comprehensive error handling
- Integrate with existing pre-commit workflow
- Provide clear documentation and examples
- Support TDD-first development approach
- Ensure zero errors policy compliance

### Non-Goals

- Automated documentation updates (future enhancement)
- Real-time synchronization (future enhancement)
- Cross-repository documentation tracking (out of scope)
- Natural language processing for content analysis (out of scope)

## Decisions

### 1. YAML Frontmatter Schema

**Decision**: Use YAML frontmatter with specific fields: `title`, `doc_owner`, `tracks`, `last_reviewed`, `exempt`, `exempt_reason`

**Rationale**:

- YAML is already used in the codebase (Jekyll, OpenSpec)
- Standard format that's familiar to developers
- Supports structured data with validation
- Human-readable and editable

**Alternatives Considered**:

- JSON frontmatter: More rigid, less human-friendly
- TOML frontmatter: Less common in documentation
- Custom header format: Non-standard, harder to parse

### 2. Validation Script Implementation

**Decision**: Implement validation script in Python using PyYAML and standard library

**Rationale**:

- Python is the primary language of the codebase
- PyYAML provides robust YAML parsing
- Standard library supports file operations and glob matching
- Easy to integrate with existing hatch-based tooling

**Alternatives Considered**:

- Shell script: Less maintainable, harder to test
- Node.js: Would require additional runtime dependency
- Rust: Overkill for this use case, would add complexity

### 3. Owner Resolution Strategy

**Decision**: Support both path-like identifiers and known tokens

**Rationale**:

- Path-like identifiers provide direct mapping to code modules
- Known tokens support repository-level and organizational ownership
- Flexible approach accommodates different ownership patterns
- Maintains compatibility with existing module structure

**Alternatives Considered**:

- Path-only resolution: Too restrictive for some use cases
- Token-only resolution: Loses direct code mapping
- Complex ownership hierarchy: Overly complicated for current needs

### 4. Pre-commit Integration

**Decision**: Integrate as a separate pre-commit hook that runs after other validations

**Rationale**:

- Separate hook allows independent execution and testing
- Runs after other validations to catch issues early
- Follows existing pre-commit patterns in the codebase
- Easy to disable temporarily if needed

**Alternatives Considered**:

- Integrated into existing code review gate: Would complicate existing validation
- Post-commit hook: Too late to prevent bad commits
- CI-only validation: Loses local developer feedback loop

### 5. Error Handling and User Experience

**Decision**: Provide detailed error messages with fix hints and `--fix-hint` flag

**Rationale**:

- Reduces developer friction during adoption
- Provides immediate guidance for common issues
- Follows CLI best practices for user experience
- Supports gradual adoption and learning curve

**Alternatives Considered**:

- Minimal error messages: Poor user experience
- Automatic fixes: Too risky, could make incorrect changes
- Interactive prompts: Would complicate CI integration

### 6. Test-Driven Development Approach

**Decision**: Follow strict TDD-first approach with contract testing

**Rationale**:

- Ensures robust implementation from the start
- Provides living documentation through tests
- Follows codebase conventions and quality standards
- Enables safe refactoring and maintenance

**Alternatives Considered**:

- Test-last approach: Higher risk of bugs and regressions
- No formal testing: Unacceptable for quality standards
- Property-based testing only: Would miss specific scenarios

## Risks / Trade-offs

### [Developer Adoption Resistance] → Mitigation

**Risk**: Developers may resist adding frontmatter to existing documentation
**Mitigation**:

- Provide clear migration guide and templates
- Offer `--fix-hint` flag for easy fixes
- Phase rollout starting with new documentation
- Provide comprehensive documentation and examples

### [Performance Impact on Large Repositories] → Mitigation

**Risk**: Validation script may be slow on repositories with many documentation files
**Mitigation**:

- Implement efficient file discovery using glob patterns
- Use caching for owner resolution where appropriate
- Optimize YAML parsing with streaming where possible
- Set performance requirements in specs

### [False Positives in Owner Resolution] → Mitigation

**Risk**: Owner resolution may incorrectly flag valid owners
**Mitigation**:

- Make `VALID_OWNER_TOKENS` and `SOURCE_ROOTS` configurable
- Provide clear error messages with suggestions
- Allow easy configuration updates
- Implement comprehensive test coverage

### [Complexity for New Contributors] → Mitigation

**Risk**: Frontmatter requirements may be confusing for new contributors
**Mitigation**:

- Provide detailed documentation with examples
- Create templates for common documentation types
- Offer clear error messages with guidance
- Include in contributing guidelines and onboarding

### [Integration with Existing Workflows] → Mitigation

**Risk**: May disrupt existing documentation workflows
**Mitigation**:

- Phase rollout with opt-in period
- Provide clear migration path
- Maintain backward compatibility where possible
- Offer configuration options for gradual adoption

## Migration Plan

### Phase 1: Infrastructure Setup

1. Create validation script with comprehensive tests
2. Update pre-commit configuration
3. Add documentation for frontmatter schema
4. Test with sample documentation files

### Phase 2: Gradual Adoption

1. Start with new documentation files
2. Add frontmatter to critical documentation first
3. Provide migration guide for existing docs
4. Offer team training and Q&A sessions

### Phase 3: Full Enforcement

1. Enable pre-commit hook for all developers
2. Update CI configuration for enforcement
3. Monitor and address any issues
4. Celebrate successful adoption

### Rollback Strategy

1. Disable pre-commit hook if critical issues arise
2. Revert to manual review process temporarily
3. Address issues in validation script
4. Re-enable with fixes and improved documentation

## Open Questions

1. **Configuration Management**: Should `VALID_OWNER_TOKENS` and `SOURCE_ROOTS` be configurable via environment variables or config file?
2. **Performance Optimization**: What's the threshold for "too slow" on large repositories? Should we implement caching?
3. **Exemption Process**: Should we implement a formal review process for exempt documents?
4. **CI Integration Timing**: Should docs sync check run before or after other CI checks?
5. **Gradual Enforcement**: Should we implement warnings before hard failures during adoption phase?
