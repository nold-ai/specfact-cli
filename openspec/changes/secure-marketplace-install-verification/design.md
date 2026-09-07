## Context

The archive checksum in a registry index proves consistency with that index, not publisher authenticity. The extracted manifest is attacker-controlled until its embedded integrity signature is checked against trusted key material. Dependency resolution, including recursive marketplace installs and pip invocation, is therefore a privileged side effect that must follow artifact authentication.

## Decision

Immediately after parsing and validating the extracted manifest, the marketplace installer will verify the artifact. Requested module IDs in the official `nold-ai` namespace require integrity metadata and a valid signature. Only after that check succeeds may the installer resolve bundle or pip dependencies and atomically place the module.

The requested module ID, rather than the manifest's self-asserted publisher, selects the official signature policy. This prevents a custom or compromised registry from bypassing verification by changing manifest publisher metadata while claiming an official ID.

## Alternatives Considered

- **Trust the registry archive checksum**: rejected because the same compromised registry can replace both the archive and checksum.
- **Verify only during final placement**: rejected because manifest-controlled dependency installation already creates side effects.
- **Disable dependencies for init profiles**: rejected because it would remove supported functionality instead of securing it.

## Compatibility and Rollback

Non-official marketplace modules retain the current optional-signature behavior. Official modules without valid signed integrity metadata now fail closed. Reverting the single ordering/policy change restores the prior behavior if an emergency rollback is required.
