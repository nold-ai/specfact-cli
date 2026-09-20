# Design: Schema 1.7 Code Review Gate Adoption

## Scope rescope — 2026-09-20

Keep the signed C14/C15, profile, policy and exception-authority prerequisites. Optional preflight is not an indirect prerequisite. Use meaningful regression reproduction, current test results and independent review; no immutable RED history or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## Trust Boundary

The modules producer owns analyzer execution and code-review policy application.
Core owns local helper consumption and the protected workflow verifier. The
protected consumer accepts only the signed module/schema/profile identities
approved by the paired change and authenticates exceptions from trusted base
policy. It never treats candidate files or a report boolean as trust authority.

## Local Pre-Commit

The helper requests explicit changed enforcement and bug-hunt timeouts. It
loads the JSON report into a strict schema-aware projection, validates the
closed status/exit matrix, prints the evidence summary, and returns
`ci_exit_code`. Subprocess failure, missing report, invalid schema, contradictory
status/exit, or unsupported enforcing schema fails closed.

For one migration release, schema 1.6 may be read only when effective mode is
shadow. The legacy error-count fallback is removed rather than retained as an
alternate authority.

## Protected CI

Extend the C14 verifier after that implementation exists. It requires schema
1.7, the approved signed module and calibration-profile digest, the C14
verification envelope, and complete waiver evidence. A waived error is accepted
only when the verifier independently matches the directive to a trusted-base,
active governance exception for the same canonical rule/path/symbol.

## Rollout

1. Consume the released signed C15 module in shadow.
2. Prove consumer matrix and both repository dogfood runs.
3. Activate changed local and protected range/full enforcement only after the
   modules measurement gate succeeds.
4. Roll back by returning to shadow; preserve the validated consumer and report.
