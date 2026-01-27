# Change: Fix Backlog Refinement Documentation and AI IDE Prompts

## Why

The backlog refinement feature has been fully implemented, but documentation and AI IDE slash command prompts are incomplete or outdated. Additionally, critical ADO adapter fixes have been implemented that need to be documented. This creates a gap between the implemented functionality and user-facing documentation, making it difficult for users to discover and use the feature effectively.

**Current Issues:**

- AI IDE slash command prompt (`specfact.backlog-refine.md`) may be missing recent parameter updates
- Documentation may not reflect all implemented features (cross-adapter state mapping, generic state mapping)
- Missing or incomplete examples for new features (state mapping, cross-adapter sync integration)
- Prompt templates may not include all CLI options and workflows
- ADO adapter fixes (WIQL API, on-premise support, organization-level endpoints) not documented
- Azure DevOps Server (on-premise) URL format differences not explained

This change updates documentation and prompts to match the fully implemented backlog refinement functionality, including recent ADO adapter improvements.

## What Changes

- **UPDATE**: `resources/prompts/specfact.backlog-refine.md` - Update AI IDE slash command prompt with:
  - Complete parameter list including all adapter configuration options
  - Cross-adapter state mapping documentation
  - Generic state mapping examples
  - Updated workflow examples
  - Field preservation policy clarifications
  - OpenSpec comment integration details
- **UPDATE**: `docs/guides/backlog-refinement.md` - Update guide with:
  - Cross-adapter state mapping explanation
  - Generic state mapping between adapters
  - Updated examples for GitHub ↔ ADO sync
  - State preservation during cross-adapter sync
- **UPDATE**: `docs/reference/commands.md` - Update `backlog refine` command reference with:
  - All available parameters
  - Cross-adapter state mapping behavior
  - State preservation guarantees
  - ADO adapter configuration (cloud vs on-premise)
  - Azure DevOps Server (on-premise) URL format requirements
- **UPDATE**: `docs/guides/backlog-refinement.md` - Add ADO adapter section:
  - Azure DevOps Services (cloud) vs Azure DevOps Server (on-premise) differences
  - WIQL query endpoint requirements
  - Organization-level vs project-level API endpoints
  - URL format examples for both cloud and on-premise
- **UPDATE**: `README.md` - Ensure backlog refinement is properly documented in quick start
- **UPDATE**: `CHANGELOG.md` - Document documentation updates and ADO adapter fixes

## Impact

- **Affected specs**: backlog-refinement (documentation updates only, no spec changes)
- **Affected code**: None (documentation-only change, but documents recent ADO adapter fixes)
- **Integration points**:
  - AI IDE copilot integration - Updated prompts ensure correct command usage
  - User documentation - Complete and accurate feature documentation
  - Cross-adapter sync documentation - State mapping behavior clearly explained
  - ADO adapter documentation - Cloud vs on-premise configuration and API endpoint differences
- **Recent fixes documented**:
  - ADO WIQL API endpoint fix (api-version parameter requirement)
  - Work items batch GET endpoint fix (organization-level vs project-level)
  - Azure DevOps Server (on-premise) support and URL format handling
  - Improved error messages for ADO API calls

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD (bugfix change)
- **Issue URL**: TBD
- **Last Synced Status**: proposed
- **Sanitized**: true
