# PR785 isolated CI signing probe

## Why

PR785 has ten reviewed unsigned source commits. The owner approved bounded CI signing recovery on 23 October 2026. Actual REST signing has not been established.

## What changes

Create an auxiliary-only manual executor at the registered specfact.yml path. Freeze all original source identities and a harmless workflow probe tree. Mint and verify two independent objects using only CI GITHUB_TOKEN. Reject all other stages. The root operator authenticates artifacts and owns any subsequent auxiliary anchoring.

## Capabilities

- `pr785-signing-probe` bounds the auxiliary CI experiment and its acceptance evidence.

## Impact

Only auxiliary branch codex/pr785-ci-signing-recovery receives this operational change. No release payload, dependency, signing key, module manifest, ref, merge, deployment, or publication changes are permitted. Existing issue #780 and PR #785 remain the recovery context. The root verified current issue metadata and explicit owner approval before this work. The private unsigned recovery bundle and original input manifest remain recovery evidence.

No user-facing documentation changes apply. This operational executor adds no product CLI or API. Shared adapters and plugin registration remain outside scope. The network requirement is confined to this explicit CI experiment. Rollback consists of abandoning the auxiliary executor; no release ref is changed by this unit.

## Source Tracking

- **GitHub Issue**: #780
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/780>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: Open / Todo, root verified 23 October 2026
