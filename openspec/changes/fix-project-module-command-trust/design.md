# Design: Project module command trust boundary

## Context

Project discovery intentionally finds `.specfact/modules`, but discovery must not itself grant permission to execute repository Python. Registration is the narrow trust boundary immediately before lazy loaders become reachable from root CLI commands.

## Decisions

1. Project-sourced packages require both integrity metadata and an official-key-verifiable signature. The existing explicit unsigned override remains the opt-in escape hatch for local development.
2. A recognized bundle string is insufficient evidence of official bundle ownership. Category mounting also requires the canonical module name `nold-ai/<bundle>`.
3. Verification remains local and uses the existing artifact verifier and bundled key resolution.

## Alternatives

- A new interactive trust prompt was rejected because non-interactive CI cannot safely prompt and publisher trust alone does not authenticate repository contents.
- Removing project module discovery was rejected because it would break the supported local module-development workflow.
- Special-casing only `requirements` was rejected because the same bundle-impersonation primitive applies to every official category mapping.

## Risk and fallback

Unsigned project modules will no longer load by default. Their owners can explicitly opt into the existing unsigned development mode, or sign the artifact. No network-dependent fallback is introduced.
