# Implementation Tasks: Improve Documentation Structure

## Prerequisites

- [x] **Dependency Check**: Verify no blocking dependencies
  - [x] All referenced documentation files exist or can be created
  - [x] Target repository (`nold-ai/specfact-cli`) is accessible

## 1. Git Workflow Setup

- [x] 1.1 Create git branch (`feature/improve-documentation-structure` from `dev` branch)
  - [x] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
  - [x] 1.1.2 Create branch with Development link to issue #78: `gh issue develop 78 --repo nold-ai/specfact-cli --name feature/improve-documentation-structure --checkout`
  - [x] 1.1.3 Verify branch was created: `git branch --show-current`
  - [x] 1.1.4 Verify Development link appears on issue page (if issue exists)

**CRITICAL**: This must be the FIRST task - no code modifications before branch creation.

## 2. Phase 1: Create Unified Command Chain Reference

- [x] 2.1 Create `specfact-cli/docs/guides/command-chains.md` documenting all 9 command chains
  - [x] 2.1.1 Add overview section explaining command chains concept
  - [x] 2.1.2 Document each of the 9 command chains with:
    - Command sequence
    - Goal and purpose
    - Decision points and expected outcomes
    - Visual flow diagram (mermaid)
    - Links to detailed guides
  - [x] 2.1.3 Add "When to use" decision tree section
  - [x] 2.1.4 Add cross-references to related chains and guides

- [x] 2.2 Add cross-references from existing documentation
  - [x] 2.2.1 Add link to `command-chains.md` in `specfact-cli/docs/README.md`
  - [x] 2.2.2 Add link to `command-chains.md` in `specfact-cli/docs/reference/commands.md`
  - [x] 2.2.3 Verify all cross-references work correctly

**Testing**: Verify all 9 chains are documented, diagrams render correctly, cross-references work.

## 3. Phase 2: Create Common Tasks Index

- [x] 3.1 Create `specfact-cli/docs/guides/common-tasks.md` with 20+ task→command mappings
  - [x] 3.1.1 For each common task, include:
    - Task description
    - Recommended command/chain
    - Link to detailed guide
    - Quick example
  - [x] 3.1.2 Organize tasks by category (e.g., Getting Started, Brownfield Modernization, API Development)
  - [x] 3.1.3 Add search-friendly structure

- [x] 3.2 Add links from existing documentation
  - [x] 3.2.1 Add link to `common-tasks.md` in `specfact-cli/docs/README.md`
  - [x] 3.2.2 Add link to `common-tasks.md` in `specfact-cli/docs/guides/README.md` (if exists)
  - [x] 3.2.3 Verify all links work correctly

**Testing**: Verify all common tasks are indexed, links work correctly.

## 4. Phase 3: Document Orphaned Commands

- [x] 4.1 Create team collaboration workflow guide
  - [x] 4.1.1 Create or expand `specfact-cli/docs/guides/team-collaboration-workflow.md`
  - [x] 4.1.2 Document when to use `project export/import/lock/unlock` commands
  - [x] 4.1.3 Explain integration with `project init-personas` and version management
  - [x] 4.1.4 Add complete workflow examples

- [x] 4.2 Create migration decision tree guide
  - [x] 4.2.1 Create or expand `specfact-cli/docs/guides/migration-guide.md`
  - [x] 4.2.2 Document migration decision tree
  - [x] 4.2.3 Add migration workflow examples

- [x] 4.3 Document SDD Constitution Management workflow
  - [x] 4.3.1 Create workflow documentation for SDD Constitution commands
  - [x] 4.3.2 Integrate into `command-chains.md`
  - [x] 4.3.3 Add cross-references

- [x] 4.4 Integrate orphaned commands into workflows
  - [x] 4.4.1 Integrate orphaned commands into `command-chains.md`
  - [x] 4.4.2 Update `specfact-cli/docs/reference/commands.md` with workflow context for orphaned commands
  - [x] 4.4.3 Verify all 8 orphaned commands have workflow context or deprecation path

**Testing**: Verify all 8 orphaned commands have workflow context or deprecation path.

## 5. Phase 4: Complete Emerging Chains Documentation

- [x] 5.1 Create AI IDE workflow guide
  - [x] 5.1.1 Create `specfact-cli/docs/guides/ai-ide-workflow.md`
  - [x] 5.1.2 Document setup process (`init --ide cursor`)
  - [x] 5.1.3 Document available slash commands
  - [x] 5.1.4 Document prompt generation → AI IDE → validation loop
  - [x] 5.1.5 Document integration with command chains

- [x] 5.2 Expand prompts documentation
  - [x] 5.2.1 Expand `specfact-cli/docs/prompts/README.md` with slash commands reference
  - [x] 5.2.2 Add examples for each slash command
  - [x] 5.2.3 Add cross-references to workflow guides

- [x] 5.3 Update IDE integration guide
  - [x] 5.3.1 Update `specfact-cli/docs/guides/ide-integration.md` with link to `ai-ide-workflow.md`
  - [x] 5.3.2 Complete emerging chain sections in `command-chains.md`
  - [x] 5.3.3 Verify all cross-links work

**Testing**: Verify AI IDE workflow is complete, all slash commands documented, cross-links work.

## 6. Phase 5: Improve Cross-Linking and Navigation

- [x] 6.1 Add "See Also" sections to all guide files
  - [x] 6.1.1 Add "See Also" sections to all guide files in `specfact-cli/docs/guides/`
  - [x] 6.1.2 Include links to:
    - Related Guides (links to other guide files)
    - Related Commands (links to commands.md)
    - Related Examples (links to examples directory)
  - [x] 6.1.3 Verify consistent format across all guides

- [x] 6.2 Update commands reference with workflow matrix
  - [x] 6.2.1 Update `specfact-cli/docs/reference/commands.md` with "Commands by Workflow" matrix at the top
  - [x] 6.2.2 Organize commands by workflow/chain
  - [x] 6.2.3 Add links to relevant command chain sections
  - [x] 6.2.4 Add quick navigation to command details

- [x] 6.3 Update integration guides with cross-links
  - [x] 6.3.1 Update `specfact-cli/docs/guides/specmatic-integration.md` with cross-links
  - [x] 6.3.2 Update `specfact-cli/docs/guides/speckit-journey.md` with cross-links
  - [x] 6.3.3 Update `specfact-cli/docs/guides/devops-adapter-integration.md` with cross-links
  - [x] 6.3.4 Add "Related Workflows" sections to examples

- [x] 6.4 Create integrations overview (optional)
  - [x] 6.4.1 Create `specfact-cli/docs/guides/integrations-overview.md` (optional)
  - [x] 6.4.2 Provide overview of all integration options
  - [x] 6.4.3 Add links to detailed integration guides
  - [x] 6.4.4 Add cross-references from integration guides to integrations-overview.md
  - [x] 6.4.5 Add link to integrations-overview.md in docs/README.md

**Testing**: Verify cross-linking score improves to 75%+ (measured by "See Also" sections in all guides).

## 7. Code Quality and Validation (Documentation-Specific)

**Note**: This is a documentation-only change. Python-specific quality gates (type-check, contract-test, Python tests) do not apply.

- [x] 7.1 Markdown linting
  - [x] 7.1.1 Run markdown linting: `markdownlint --config .markdownlint.json --fix docs/**/*.md`
  - [x] 7.1.2 Fix any linting errors reported
  - [x] 7.1.3 Re-run until all markdown files pass linting
  - [x] 7.1.4 Verify all markdown files pass markdownlint checks with zero errors

- [x] 7.2 Link validation
  - [x] 7.2.1 Verify all internal links work (no broken references)
  - [x] 7.2.2 Check external links are accessible (or note if intentionally broken)
  - [x] 7.2.3 Use link validation tool if available, or manual verification
  - [x] 7.2.4 Verify all links verified and working (or documented as intentionally broken)

- [x] 7.3 Markdown formatting consistency
  - [x] 7.3.1 Check markdown formatting follows project standards (see `.cursor/rules/markdown-rules.mdc`)
  - [x] 7.3.2 Verify proper heading hierarchy
  - [x] 7.3.3 Ensure consistent list formatting
  - [x] 7.3.4 Check code block language specifiers are present
  - [x] 7.3.5 Verify all documentation follows markdown standards from cursor rules

- [x] 7.4 Diagram validation
  - [x] 7.4.1 Verify all mermaid diagrams render correctly
  - [x] 7.4.2 Check diagram syntax is valid
  - [x] 7.4.3 Test diagrams in GitHub preview or documentation site
  - [x] 7.4.4 Verify all diagrams render correctly without errors

**Note**: Python-specific quality gates skipped (documentation-only change):

- `hatch run format` - Not applicable (Python code formatting)
- `hatch run type-check` - Not applicable (no Python code changes)
- `hatch run contract-test` - Not applicable (no contract changes)
- `hatch test --cover -v` - Not applicable (no code changes)

## 8. OpenSpec Validation

- [x] 8.1 Run OpenSpec validation
  - [x] 8.1.1 Run: `openspec validate improve-documentation-structure --strict`
  - [x] 8.1.2 Fix any validation errors
  - [x] 8.1.3 Re-validate until passing
  - [x] 8.1.4 Verify OpenSpec validation passes with --strict flag

## 9. Create Pull Request

**CRITICAL**: This must be the LAST task - only after all implementation tasks are complete.

- [x] 9.1 Prepare changes for commit
  - [x] 9.1.1 Ensure all changes are committed: `git add .`
  - [x] 9.1.2 Commit with conventional message: `git commit -m "docs: improve documentation structure with unified command chains and cross-linking"`
  - [x] 9.1.3 Push to remote: `git push origin feature/improve-documentation-structure`

- [x] 9.2 Create PR body from template
  - [x] 9.2.1 Create PR body file in `/tmp` to avoid escaping issues: `PR_BODY_FILE="/tmp/pr-body-improve-documentation-structure.md"`
  - [x] 9.2.2 Execute Python script to read template, fill in values, and write to temp file:
    - Set environment variables: `CHANGE_ID="improve-documentation-structure" ISSUE_NUMBER="78" TARGET_REPO="nold-ai/specfact-cli" SUMMARY="..." BRANCH_TYPE="feature" PR_TEMPLATE_PATH="..." PR_BODY_FILE="$PR_BODY_FILE"`
    - Run Python script with these environment variables
    - The script uses full repository path format for issue references (e.g., `nold-ai/specfact-cli#78`) to ensure proper Development linking
  - [x] 9.2.3 Verify PR body file was created: `cat "$PR_BODY_FILE"` (should contain issue reference in format `nold-ai/specfact-cli#78`)
  - [x] 9.2.4 Add OpenSpec reference and summary to description section
  - [x] 9.2.5 Write complete PR body to temp file

- [x] 9.3 Create Pull Request using gh CLI
  - [x] 9.3.1 Create PR without project flag first: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/improve-documentation-structure --title "docs: improve documentation structure with unified command chains and cross-linking" --body-file "$PR_BODY_FILE"`
  - [x] 9.3.2 Verify PR was created and capture PR number and URL from output
  - [x] 9.3.3 Extract PR number from output (format: "Created pull request #<number>" or URL)
  - [x] 9.3.4 Link PR to project: `gh project item-add 1 --owner nold-ai --url "https://github.com/nold-ai/specfact-cli/pull/79"` (if this fails, project linking requires project scope: `gh auth refresh -s project`)
  - [x] 9.3.5 Verify/ensure branch and PR are linked to issue #78 (Development section):
    - [x] 9.3.5.1 Verify branch is linked: Branch was created using `gh issue develop 78` (Step 1.1.2), which automatically links the branch to issue #78
    - [x] 9.3.5.2 Verify PR is linked: PR body contains `Fixes nold-ai/specfact-cli#78`, which should automatically link the PR to issue #78
    - [x] 9.3.5.3 **If automatic linking didn't work**: Manually link from issue's Development section:
      - Open issue page: <https://github.com/nold-ai/specfact-cli/issues/78>
      - In the right sidebar, find the "Development" section
      - Click "Development" and search for PR #79 (or branch `feature/improve-documentation-structure` if PR doesn't exist yet)
      - Select the PR/branch to link it to the issue
    - [x] 9.3.5.4 Verify Development link: Check issue page "Development" section - both branch and PR should appear if properly linked
  - [x] 9.3.6 Update project status for issue #78 to "In Progress": `gh project item-edit --id PVTI_lADODWwjB84BKws4zgjMYnU --field-id PVTSSF_lADODWwjB84BKws4zg6iOak --project-id PVT_kwDODWwjB84BKws4 --single-select-option-id 47fc9ee4` (Status: "In Progress")
  - [x] 9.3.7 Update project status for PR #79 to "In Progress": `gh project item-edit --id PVTI_lADODWwjB84BKws4zgjMaxw --field-id PVTSSF_lADODWwjB84BKws4zg6iOak --project-id PVT_kwDODWwjB84BKws4 --single-select-option-id 47fc9ee4` (Status: "In Progress")
  - [x] 9.3.8 Verify Development link: PR and branch automatically linked to issue #78 (check issue page "Development" section)
  - [x] 9.3.9 Verify project link: PR appears in project board (<https://github.com/orgs/nold-ai/projects/1>)
  - [x] 9.3.10 Cleanup PR body file: `rm /tmp/pr-body-improve-documentation-structure.md`

**Validation**: Verify PR was created, Development link present (if issue exists), PR body follows template structure.
