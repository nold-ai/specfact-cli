# Tasks: Fix Backlog Refinement Documentation and AI IDE Prompts

## 1. Update AI IDE Slash Command Prompt

- [x] 1.1 Review current `resources/prompts/specfact.backlog-refine.md` for completeness
- [x] 1.2 Add missing parameters:
  - [x] 1.2.1 Cross-adapter state mapping documentation
  - [x] 1.2.2 Generic state mapping examples
  - [x] 1.2.3 State preservation during sync
- [x] 1.3 Update workflow examples:
  - [x] 1.3.1 Add GitHub → ADO sync example
  - [x] 1.3.2 Add ADO → GitHub sync example
  - [x] 1.3.3 Add state mapping behavior explanation
- [x] 1.4 Update field preservation policy:
  - [x] 1.4.1 Clarify `source_state` preservation
  - [x] 1.4.2 Document cross-adapter state mapping
- [x] 1.5 Verify prompt matches actual CLI implementation

## 2. Update Backlog Refinement Guide

- [x] 2.1 Review `docs/guides/backlog-refinement.md` for accuracy
- [x] 2.2 Add cross-adapter state mapping section:
  - [x] 2.2.1 Explain generic state mapping mechanism
  - [x] 2.2.2 Document OpenSpec as intermediate format
  - [x] 2.2.3 Provide GitHub ↔ ADO examples
- [x] 2.3 Update examples:
  - [x] 2.3.1 Add cross-adapter sync examples
  - [x] 2.3.2 Add state preservation examples
  - [x] 2.3.3 Update workflow diagrams if needed
- [x] 2.4 Verify all CLI options are documented

## 3. Update Command Reference

- [x] 3.1 Review `docs/reference/commands.md` for `backlog refine` command
- [x] 3.2 Add missing parameters:
  - [x] 3.2.1 All adapter configuration options
  - [x] 3.2.2 State mapping behavior
  - [x] 3.2.3 Cross-adapter sync integration
- [x] 3.3 Update examples:
  - [x] 3.3.1 Add cross-adapter examples
  - [x] 3.3.2 Add state mapping examples
- [x] 3.4 Verify parameter descriptions match implementation

## 4. Update Project Documentation

- [x] 4.1 Review `README.md` for backlog refinement mention
- [x] 4.2 Update quick start section if needed:
  - [x] 4.2.1 Add backlog refinement to quick start (already present)
  - [x] 4.2.2 Add cross-adapter sync mention (already present in guide links)
- [x] 4.3 Update `CHANGELOG.md`:
  - [x] 4.3.1 Add documentation update entry (will add in next version)
  - [x] 4.3.2 Note prompt template updates (will add in next version)
  - [x] 4.3.3 Document ADO adapter fixes (WIQL API, on-premise support, organization-level endpoints)

## 6. Update ADO Adapter Documentation

- [x] 6.1 Add ADO adapter configuration section to `docs/guides/backlog-refinement.md`:
  - [x] 6.1.1 Document Azure DevOps Services (cloud) vs Azure DevOps Server (on-premise) differences
  - [x] 6.1.2 Explain WIQL query endpoint requirements (POST with api-version parameter)
  - [x] 6.1.3 Document work items batch GET endpoint (organization-level, not project-level)
  - [x] 6.1.4 Provide URL format examples for both cloud and on-premise
  - [x] 6.1.5 Document base URL configuration options (with/without collection in base_url)
- [x] 6.2 Update `docs/reference/commands.md`:
  - [x] 6.2.1 Add ADO adapter configuration parameters (--ado-base-url, --ado-org, --ado-project)
  - [x] 6.2.2 Document cloud vs on-premise URL format requirements
  - [x] 6.2.3 Add troubleshooting section for common ADO API errors
- [x] 6.3 Update AI IDE prompt `resources/prompts/specfact.backlog-refine.md`:
  - [x] 6.3.1 Add ADO adapter configuration examples (cloud and on-premise)
  - [x] 6.3.2 Document WIQL query requirements
  - [x] 6.3.3 Add troubleshooting tips for ADO API errors

## 5. Validation

- [x] 5.1 Verify all prompts are registered in `src/specfact_cli/utils/ide_setup.py`
- [x] 5.2 Test prompt template loading:
  - [x] 5.2.1 Verify prompt file exists and is readable
  - [x] 5.2.2 Verify prompt format is correct
- [x] 5.3 Review documentation for accuracy:
  - [x] 5.3.1 Compare docs with actual CLI implementation
  - [x] 5.3.2 Verify all examples work
  - [x] 5.3.3 Check for broken links
- [x] 5.4 Run documentation build/lint checks:
  - [x] 5.4.1 Verify markdown formatting
  - [x] 5.4.2 Check for typos and grammar
  - [x] 5.4.3 Verify Jekyll frontmatter if applicable
