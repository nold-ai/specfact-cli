## 1. Change Setup

- [x] 1.1 Create worktree branch `bugfix/backlog-core-06-refine-custom-field-writeback` from `origin/dev` using `scripts/worktree.sh create` and run all implementation commands from that worktree.
- [x] 1.2 Run `openspec validate backlog-core-06-refine-custom-field-writeback --strict` and fix artifact issues.
- [x] 1.3 Run `.cursor/commands/wf-validate-change.md` workflow expectations and capture output in `openspec/changes/backlog-core-06-refine-custom-field-writeback/CHANGE_VALIDATION.md`.

## 2. Tests First (TDD)

- [x] 2.1 Add/modify mapper tests to verify deterministic canonical write-target selection prefers custom mapping and mapped provider-present fields for `story_points`, `acceptance_criteria`, `business_value`, and `priority`.
- [x] 2.2 Add/modify adapter tests to assert ADO PATCH paths use resolved mapped fields (including `Microsoft.VSTS.Scheduling.StoryPoints` and custom story points field cases).
- [x] 2.3 Add/modify command tests to enforce tmp import ID contract and explicit mismatch failure when parsed IDs do not match fetched items.
- [x] 2.4 Run targeted tests and record failing pre-implementation evidence in `TDD_EVIDENCE.md` with command, timestamp, and failure summary.

## 3. Implementation

- [x] 3.1 Implement mapper-level canonical write-target resolution helper and integrate it into writeback path.
- [x] 3.2 Update `AdoAdapter.update_backlog_item` to use mapper write-target resolution for mapped canonical fields and remove order-sensitive reverse mapping behavior.
- [x] 3.3 Update refine export instructions and prompt guidance to mark `**ID**` as mandatory and unchanged for tmp import.
- [x] 3.4 Update tmp import flow to fail fast with actionable message when parsed IDs do not map to fetched backlog items.

## 4. Verification and Quality Gates

- [x] 4.1 Re-run targeted tests and record passing post-implementation evidence in `TDD_EVIDENCE.md`.
- [x] 4.2 Run quality gates in order: `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run yaml-lint`, `hatch run contract-test`, `hatch run smart-test`.
- [x] 4.3 Update docs impacted by behavior changes (`resources/prompts/specfact.backlog-refine.md`, command reference if required).
- [x] 4.4 Run `hatch run ./scripts/verify-modules-signature.py --require-signature`.
- [x] 4.5 Prepare PR to `dev` with TDD evidence and change validation artifacts linked.

## 5. Extended Runtime Findings Coverage

- [x] 5.1 Fix parser/template mismatch across backlog prompt resources so tmp/import structure instructions exactly match parser expectations per provider.
- [x] 5.2 Ensure ADO markdown-supported fields are consistently written in markdown format (including acceptance criteria and description paths).
- [x] 5.3 Prevent title pollution on tmp import/writeback (no accidental `## Item <no>:` prefix in title updates).
- [x] 5.4 Correct template steering for ADO user stories (prefer `user_story_v1` over generic `ado_work_item_v1` where applicable).
- [x] 5.5 Prevent duplicated section headings in structured backend fields (for example ADO `Description` content).
- [x] 5.6 Extend `map-fields` to include explicit ADO process/framework selection and persist/apply it for template/prompt steering.
- [x] 5.7 Align prompt guidance with provider-specific field schemas (for example story points handling in ADO process templates).
- [x] 5.8 Add/strengthen anti-summarization guardrails in refine prompting/import flow so bulk refine does not silently drop required detail.
- [x] 5.9 Add explicit no-filter override semantics for backlog commands: `--state any` and `--assignee any` must disable filtering, and document this behavior in command/help docs.

## 6. ADO Comment API Version Compatibility

- [x] 6.1 Add/modify adapter tests to assert ADO comment POST (`/workitems/{id}/comments`) uses `api-version=7.1-preview.4`.
- [x] 6.2 Record failing pre-implementation test evidence for the comment API-version mismatch in `TDD_EVIDENCE.md`.
- [x] 6.3 Update ADO comment write path to use preview comments API version while preserving `7.1` on standard operations.
- [x] 6.4 Re-run targeted tests and record passing evidence in `TDD_EVIDENCE.md`.
