# Change: Restore CLI startup and official module discovery

## Why

SpecFact CLI 0.55.19 permits Typer 0.29, but imports a private parameter-conversion function removed in that release. A fresh uvx install can fail before displaying help or loading modules. The frozen release uses Typer 0.27 and did not exercise this resolution.

The same release rejects approved installed Project and Spec files when their directories also contain inactive Python 3.14 or pytest bytecode caches.

## What Changes

- Use the existing core parameter-discovery hook to hand context parameters to Typer.
- Preserve command argument names in core's generated command inventory.
- Recognize inactive CPython 3.14 and pytest caches next to approved module source.
- Continue to verify the approved module files and active bytecode.
- Retain the current Typer dependency range after verifying the official module fixture.
- Reproduce the original failure and verify a rebuilt wheel through fresh uvx resolution.

## Capabilities

### Modified Capabilities

- `command-package-runtime-validation` covers startup and command dispatch when the wheel resolves dependencies from its published metadata.
- `module-security` defines how the verifier handles inactive bytecode caches.

## Impact

The change concerns the CLI entry point, Typer integration, and command documentation generator. The install instructions in the README and installation guide still apply. The repair adds no runtime service or network requirement. If a compatibility regression requires rollback, the temporary Typer upper bound keeps the released entry point usable.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #808
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/808>
- **GitHub Issue**: #809
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/809>
- **Repository**: nold-ai/specfact-cli
- **Release**: [0.55.19 promotion](https://github.com/nold-ai/specfact-cli/pull/807)
- **Last Synced Status**: Both issues are open. Their parents are #351 and #352.
