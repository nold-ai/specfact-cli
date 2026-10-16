# Preinstallation review exceptions

The unchanged SpecFact review reports nine `MISSING_ICONTRACT` warnings and one
`kiss.parameter-count.warning`. These are explicit, scoped exceptions under
`docs/agent-rules/50-quality-gates-and-review.md`. The review scorer, thresholds,
configuration and contract checker remain unchanged.

## Standard-library preinstallation boundary

The nine affected entry points are `build_candidate`, `verify_candidate`,
`required_matrix`, `aggregate_candidate_reports`, `admit_artifact`,
`CandidateWheel.candidate_audit_input`, `AdmittedWheel.audit_input`,
`BoundAuditInput.assert_complete_result`, and the verification driver's `main`.

These scripts run before an environment or a downstream artifact is trusted.
Importing icontract or beartype here would require a third-party installation
before the boundary can check it. A fallback decorator would falsely imply an
enforced contract. Instead, the core validates its external JSON, paths,
identities, archive members, signatures and audit inventory with explicit
fail-closed checks. The driver validates its arguments and invokes the same
boundary. The forty mapped regressions exercise observable success and rejection
behavior. The independent final security review accepted this limited rationale.

This exception applies only to these preinstallation entry points. It does not
permit application APIs to omit contracts, or permit a caller to bypass admission.
Reassess it if this code moves into an authenticated installed environment.

## External MCP factory signature

`_FixedManagerFactory.__call__` mirrors the MCP 1.30.0 factory arguments exactly.
The reported six parameters include `self`. The regression checks the installed
SDK signature before casting it to the protocol. Reducing the signature to five
parameters would lose a tested control or misrepresent the external API. This
exception applies only to that external protocol declaration.

No other current review finding is covered by these exceptions. Real native
platform proof and protected producer provenance remain separate obligations.

## Credential fixture readability

The FULL review also reports `ai-bloat.loc-vs-complexity` on the 53-line private
`_authenticated_fixture`. Manual inspection retains that fixture. The same
function defines ephemeral signed credentials, their signature verifier, and the
server's audience policy. Splitting these single-use pieces into more helpers
would spread the security assumptions across callers without removing logic.
The HTTP test itself now contains only the ownership request sequence. This is
an explicit retained readability advisory, not a change to the clean-code gate.
