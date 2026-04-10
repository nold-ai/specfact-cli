# Residual Failures and Handoff (module-migration-05)

Date: 2026-03-04

## Scope of this residual list

This list captures items that are either:

- not bundle-scope defects inside `specfact-cli-modules`, or
- not executable from this environment (remote GitHub operations),
after local bundle test migration parity was validated (`hatch run smart-test` passed).

## Residual items

1. Remote branch protection + PR validation for `specfact-cli-modules`
   - Why residual: requires live GitHub API/PR operations (`21.3`, `21.5`) not reachable from this environment (`api.github.com` connectivity failure).
   - Follow-up path: execute once network/GitHub access is available from maintainer environment.

2. Remaining import-path decoupling work (MIGRATE-tier moves)
   - Why residual: tracked in section `19.2+`; not part of the completed baseline test migration checks.
   - Follow-up OpenSpec change: `module-migration-06-core-decoupling-cleanup` (#338).

3. Residual specfact-cli legacy test cleanup outside bundle-scope parity
   - Why residual: explicitly out of scope for migration-05 acceptance once modules-repo parity handoff is complete.
   - Follow-up OpenSpec change: `module-migration-07-test-migration-cleanup` (#339).

## Acceptance boundary

`module-migration-05` acceptance remains focused on modules-repo quality parity and migration handoff.
Unrelated legacy `specfact-cli` suite debt is tracked in the follow-up changes above and should not block this change's parity-focused closure.
