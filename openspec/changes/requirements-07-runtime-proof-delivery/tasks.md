# Tasks: R07 replacement reconciliation

Implementation ownership moved to core [#740](https://github.com/nold-ai/specfact-cli/issues/740)
and modules [#481](https://github.com/nold-ai/specfact-cli-modules/issues/481).
The former implementation queue is superseded, not completed. Its
[historical task list](https://github.com/nold-ai/specfact-cli/blob/d306d2a8e855cba493c8e5b07093565be75e89cc/openspec/changes/requirements-07-runtime-proof-delivery/tasks.md)
is retained in Git history. Existing shipped evidence files remain unchanged.

## Remaining reconciliation

- [ ] 1. After #740/#481 delivery, verify #662's current-run outcome requirements against the delivered behavior and tests.
- [ ] 2. Reconcile canonical specs through R09 and retire superseded unimplemented R07 deltas without applying or marking them implemented. Preserve shipped history; R08 remains abandoned.
- [ ] 3. Update #662, change ordering and internal mirrors with the replacement release and disposition. Refresh hierarchy/concurrency state first; use a dedicated worktree.
