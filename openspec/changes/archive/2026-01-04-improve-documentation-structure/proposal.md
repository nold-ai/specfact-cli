# Change: Improve Documentation Structure

## Why

Users must navigate 3-5 separate documents to understand a single workflow. No consolidated command-chain reference exists. No "How do I X?" quick reference. Integration score is 42% due to isolated guides. Critical documentation gaps: 9 command chains exist but aren't unified, 8 commands are orphaned, and cross-linking score is only 42%.

This change transforms SpecFact CLI documentation from scattered silos to unified workflows by creating consolidated command chain references, common tasks index, and comprehensive cross-linking. Users will be able to find complete workflows in < 10 minutes (down from 30-45 minutes). Cross-linking score will improve to 75%+. All command chains and orphaned commands will have clear workflow context.

## What Changes

- **NEW**: `specfact-cli/docs/guides/command-chains.md` (unified command chain reference)
  - Documents all 9 command chains with workflows, decision points, and cross-references
  - Includes visual flow diagrams (mermaid) and "When to use" decision tree
  - Cross-referenced from README.md and commands.md

- **NEW**: `specfact-cli/docs/guides/common-tasks.md` (common tasks index)
  - Maps 20+ user goals to recommended commands or command chains
  - Each entry includes task description, recommended command/chain, link to detailed guide, quick example
  - Linked from README.md and guides/README.md

- **NEW/EXTEND**: `specfact-cli/docs/guides/team-collaboration-workflow.md` (team collaboration guide)
  - Documents when to use `project export/import/lock/unlock` commands
  - Explains integration with `project init-personas` and version management
  - Provides complete workflow examples

- **NEW/EXTEND**: `specfact-cli/docs/guides/migration-guide.md` (migration decision tree)
  - Documents migration decision tree
  - Adds migration workflow examples

- **NEW**: `specfact-cli/docs/guides/ai-ide-workflow.md` (AI IDE workflow guide)
  - Documents setup process (`init --ide cursor`)
  - Documents available slash commands
  - Documents prompt generation → AI IDE → validation loop
  - Documents integration with command chains

- **EXTEND**: `specfact-cli/docs/prompts/README.md` (slash commands reference)
  - Expands with slash commands reference
  - Adds examples for each slash command

- **MODIFY**: `specfact-cli/docs/README.md` (add links to new guides)
  - Adds links to command-chains.md and common-tasks.md

- **MODIFY**: `specfact-cli/docs/reference/commands.md` (add workflow matrix)
  - Adds "Commands by Workflow" matrix at the top
  - Organizes commands by workflow/chain
  - Adds links to relevant command chain sections

- **MODIFY**: `specfact-cli/docs/guides/*.md` (add "See Also" sections)
  - Adds "See Also" sections to all guide files
  - Includes links to Related Guides, Related Commands, Related Examples

- **MODIFY**: Integration guides (specmatic-integration.md, speckit-journey.md, devops-adapter-integration.md)
  - Updates with cross-links
  - Adds "Related Workflows" sections

- **OPTIONAL**: `specfact-cli/docs/guides/integrations-overview.md` (integrations overview)
  - Provides overview of all integration options
  - Links to detailed integration guides

## Impact

- Affected specs: documentation-structure
- Affected code: Documentation files only (no code changes)
- Integration points: All existing documentation guides and references

## Status

- status: proposed

## Source

- **Plan Document**: `docs/internal/brownfield-strategy/2026-01-04-SpecFact-CLI-Documentation-Improvement-Plan.md`
- **Target Repository**: `nold-ai/specfact-cli` (public)
- **Estimated Effort**: 30-40 hours over 2 weeks

---

## Source Tracking

- **GitHub Issue**: #78
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/78>
- **Last Synced Status**: proposed
<!-- content_hash: b551bd0a67014110 -->
## Scope

### Phases

1. **Phase 1**: Create Unified Command Chain Reference (High Priority)
   - Create `docs/guides/command-chains.md` documenting all 9 command chains
   - Add cross-references from README.md and commands.md

2. **Phase 2**: Create Common Tasks Index (High Priority)
   - Create `docs/guides/common-tasks.md` with 20+ task→command mappings
   - Add links from README.md

3. **Phase 3**: Document Orphaned Commands (Medium Priority)
   - Create team collaboration workflow guide
   - Document migration decision tree
   - Document SDD Constitution Management workflow
   - Integrate orphaned commands into workflows

4. **Phase 4**: Complete Emerging Chains Documentation (Medium Priority)
   - Create AI IDE workflow guide
   - Expand prompts documentation
   - Cross-link integration guides

5. **Phase 5**: Improve Cross-Linking and Navigation (Medium Priority)
   - Add "See Also" sections to all guides
   - Update commands.md with workflow matrix
   - Update integration guides with cross-links
   - Create integrations overview (optional)

6. **Phase 6**: Reference Refactoring (Low Priority, Future)
   - Deferred - focus on cross-linking first

## Success Criteria

- [ ] All 9 command chains documented in unified reference
- [ ] 20+ common tasks indexed with clear command mappings
- [ ] All 8 orphaned commands have workflow context or deprecation path
- [ ] Cross-linking score improves from 42% to 75%+ (measured by "See Also" sections in all guides)
- [ ] User journey test: "Sync with Spec-Kit" workflow findable in < 10 minutes (down from 30-45 minutes)

## Quality Standards

### Testing Requirements

- All markdown files pass linting checks
- All links verified (no broken references)
- All diagrams render correctly (mermaid syntax validated)
- Documentation structure validated against existing patterns

### Code Quality Requirements

**Note**: This is a documentation-only change. Python-specific quality gates do not apply:

- `hatch run format` - Not applicable (Python code formatting)
- `hatch run type-check` - Not applicable (no Python code changes)
- `hatch run contract-test` - Not applicable (no contract changes)
- `hatch test --cover -v` - Not applicable (no code changes)

**Documentation Quality Requirements**:

- Markdown formatting follows project standards (see `.cursor/rules/markdown-rules.mdc`)
- Consistent cross-linking patterns across all guides
- Proper heading hierarchy and structure
- Clear, user-focused language
- All markdown files pass `markdownlint --config .markdownlint.json --fix`

### Validation Requirements

- **OpenSpec validation**: `openspec validate improve-documentation-structure --strict`
- **Link validation**: All internal and external links verified (manual or automated)
- **Markdown linting**: All files pass `markdownlint --config .markdownlint.json --fix` checks
- **Cursor rules compliance**: All documentation follows rules from `.cursor/rules/markdown-rules.mdc`

## Git Workflow Requirements

- **Branch creation**: Work must be done in `feature/improve-documentation-structure` branch (not on main/dev)
- **Branch protection**: `main` and `dev` branches are protected - no direct commits
- **Pull Request**: All changes must be merged via PR to `dev` branch
- **Branch naming**: `feature/improve-documentation-structure` format

## Acceptance Criteria

- Git branch created before any code modifications
- All documentation files created/modified as specified
- All links verified and working
- All cross-references added
- No linting errors
- Pull Request created and ready for review
