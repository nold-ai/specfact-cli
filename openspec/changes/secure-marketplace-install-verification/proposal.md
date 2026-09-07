## Why

Marketplace module manifests currently control bundle and pip dependency installation before the downloaded module artifact is verified. A registry that serves a matching archive checksum can therefore supply an unsigned `nold-ai/*` manifest whose dependency metadata executes code before the installer rejects the artifact.

## What Changes

- Verify downloaded official marketplace modules before reading their manifest dependency declarations as installation instructions.
- Require both integrity metadata and a valid signature for requested `nold-ai/*` marketplace module IDs.
- Preserve the existing dependency and atomic placement flow after successful verification.

## Capabilities

### Modified Capabilities

- `module-installation`

## Impact

- Affected code: marketplace module installation ordering and official publisher verification policy.
- Affected tests: marketplace installer security regressions.
- Affected docs: existing marketplace installation documentation remains accurate; no command or option changes are required.
- Rollback: revert the verification-order change and its regression coverage.

## Source Tracking

- **Source**: Aardvark security report for commit `e87058b273da36e240db26366dfdf179db85c26d`
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: Report validated against current branch HEAD; no public issue supplied for the security report.
