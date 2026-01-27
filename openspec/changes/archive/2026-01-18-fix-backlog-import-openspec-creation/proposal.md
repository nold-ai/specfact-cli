# Change: Fix backlog import to create complete OpenSpec change artifacts

## Why


When importing backlog items (GitHub Issues, ADO Work Items) as OpenSpec change proposals via `specfact sync bridge --adapter github --bidirectional --backlog-ids <ids>`, the system currently only creates a `ChangeProposal` object and stores it in the project bundle's `change_tracking.proposals`. However, it does NOT create the required OpenSpec change artifacts:

- `proposal.md` file (with proper OpenSpec format)
- `tasks.md` file (implementation task breakdown)
- `specs/` directory with spec deltas

This creates incomplete OpenSpec changes that cannot be validated, applied, or properly tracked. The imported change proposals are only stored in bundle memory and are not persisted as proper OpenSpec change artifacts that can be validated, reviewed, and implemented following the OpenSpec workflow.

## What Changes


- **FIX**: Extend `import_backlog_items_to_bundle()` in `BridgeSync` to create OpenSpec change directory structure after importing to bundle
- **FIX**: Add `_write_openspec_change_from_proposal()` method to `BridgeSync` that creates `proposal.md`, `tasks.md`, and spec deltas from imported `ChangeProposal`
- **FIX**: Ensure `proposal.md` follows OpenSpec format (title format, required sections: Why, What Changes, Impact)
- **FIX**: Generate `tasks.md` with hierarchical numbered format from proposal acceptance criteria:
  - Extract ALL subsections from "Acceptance Criteria" section (not just first one)
  - Handle subsections with leading "- " prefix (when converted to bullet list format)
  - Properly number tasks with hierarchical format: `## 1. Implementation`, `### 1.1 Subsection`, `- [ ] 1.1.1 Task`
  - Create placeholder structure if no Acceptance Criteria found
- **FIX**: Create spec deltas in `specs/` directory based on proposal content analysis:
  - Extract actual requirements from "What Changes" section (not placeholders)
  - Parse subsections like "- ### Architecture Overview" to extract requirement text
  - Generate proper "The system SHALL..." statements from proposal content
  - Determine ADDED vs MODIFIED based on proposal keywords
  - Create meaningful scenarios from proposal content
- **FIX**: Handle change ID generation from backlog item (use existing logic from `extract_change_proposal_data()`)
- **FIX**: Ensure source tracking is properly written to `proposal.md` Source Tracking section
- **EXTEND**: Add validation step after OpenSpec file creation to ensure format compliance
- **EXTEND**: Add error handling for file creation failures (permissions, disk space, etc.)


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #117
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/117>
- **Last Synced Status**: proposed
- **Sanitized**: true
<!-- content_hash: 279383cca982cdaf -->