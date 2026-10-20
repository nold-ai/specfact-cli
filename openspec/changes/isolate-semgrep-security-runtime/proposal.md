# Change: Patch the certificate trust store in the frozen Python closure

## Why

The owner requested actual security fixes in PR #782 on 2026-10-20 Europe/Berlin.
Its frozen audit reports certifi 2026.7.22 / GHSA-6q48-6c7w-9gw2. That bundle
trusts the compromised emSign ECC Root CA - G3. The reviewed advisory recommends
certifi 2026.10.19 or later, which removes the affected root and retains unaffected
roots. This dependency can be patched independently of scanner replacement.

The supported Semgrep range still exact-pins affected MCP 1.29.0. The previous
native candidate's build records also include affected certifi. The full native
proposal and its fourteen unimplemented cases are preserved in
`openspec/parking-lot/replace-vulnerable-scanner-runtime/`. They are not claimed as
implemented or verified by this dependency patch. The stable change id is retained
for PR traceability; the active delta now covers only this immediate trust-store unit.

## What Changes

- Require certifi >=2026.10.19 in canonical runtime dependencies and regenerate
  the complete Python lock and hash-protected CI export normally.
- Test the actual installed CA bundle. Reject the compromised certificate's DER
  SHA256 and require a nonempty trust store, before and after the update.
- Preserve scanner behavior, all audit inputs and every required gate. No package
  omission, advisory exclusion, resolver override or local signing is permitted.
- Synchronize the core patch version and changelog for the actual dependency fix.

MCP remediation, native artifact admission, module migration, duplicate closure,
release and promotion remain blocked. This patch must not be described as a clean
aggregate security audit or completed scanner replacement.

## Capabilities

### New Capabilities

- `isolated-scanner-runtime`: immediate certificate trust-store safety in its
  existing Python closure. Future scanner design is preserved separately.

### Modified Capabilities

None.

## Impact

Runtime dependency floor, generated Python inputs, certificate regression test,
canonical core version sources and changelog. The scanner implementation and the
external Code Review module do not change. A certifi-only patch does not satisfy
MCP remediation or authorize closing its related PRs.

## Source Tracking

- **Source Repository**: nold-ai/specfact-cli
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/780>
- **Last Synced Status**: Todo; immediate certifi unit authorized by the owner's
  repeated request to fix PR #782. The module #523 completion dependency applies
  to scanner removal, not this independent CA-bundle correction.

## Acceptance Criteria

- The frozen Python environment rejects DER SHA256
  `86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b`
  while retaining a nonempty certifi CA store.
- Actual old-bundle failure precedes dependency edits; the refreshed environment
  passes the same test and frozen export/parity checks.
- Current-head review, normal hooks and required CI gates remain enforced.
- The remaining MCP finding and unimplemented native work stay explicit blockers.
