## Planning validation

Date: 2026-09-20 Europe/Berlin. Scope: standalone workflow proposal and issue metadata; runtime implementation is unstarted and all implementation tasks remain unchecked.

This proposal was separated from the combined lean-evidence planning PR at the owner's request. Its branch stacks on the cleaned lean-planning branch, so the PR diff contains harness-owned planning only. R09 issues #740/#481 and their plans retain their separate ownership; no changes to those issues or files are part of this proposal.

The prior combined plan passed strict OpenSpec and scoped documentation validation. Strict OpenSpec 1.13.0 validation, scoped Markdown and whitespace checks passed on the separated branch. The signed #481/v3 compatibility prerequisite is explicit in proposal/design/spec/tasks; runtime acceptance awaits implementation and actual signed releases.

Native metadata is User Story, djm81, enhancement/openspec/change-proposal, SpecFact CLI project 1 / Todo, core #742 parent #372 or modules #483 parent #163. Native direction remains modules #481 -> modules #483 -> core #742 runtime adoption; independent projection is not blocked on signed runtime delivery. Refresh/read back this metadata before implementation.

Normal hooks on the same combined planning artifacts rejected Requirements with unsupported-sidecar-schema. The existing owner-authorized local planning-only Block2 exception is retained for separation commits; it does not change runtime, protected CI or remote policy and is not a passing Requirements/review claim. Other applicable hooks and scoped documentation checks must pass. Workflow receipts remain disposable local progress, separate from Requirements, ReviewReport and governance envelopes.

Separated branch base: `b84644491fd6f8a7c9b6dbf6245d352c271242a5` on `codex/lean-requirements-evidence`. Proposal scope is limited to this change and the workflow sections of INTEGRATION/CHANGE_ORDER.
