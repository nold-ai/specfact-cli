## Why

Marketplace installation currently feeds pip dependency declarations from every discovered module, including repository-controlled project modules, into pip while installing an unrelated trusted module. Pip resolution and installation can execute package build hooks before the downloaded marketplace artifact is integrity verified.

## What Changes

- Verify the selected marketplace artifact before resolving or installing any dependency.
- Resolve and install pip requirements only from that selected, publisher-trusted artifact.
- Reject pip options, local paths, VCS references, and direct URLs before invoking pip.
- Preserve discovered-module dependency conflict visibility without treating discovered declarations as install input.

## Capabilities

### New Capabilities

- `trusted-module-dependency-installation`: Defines the trust boundary and accepted requirement syntax for marketplace dependency installation.

### Modified Capabilities

- `module-installation`: Marketplace modules remain installable, but dependency side effects occur only after artifact verification.

## Impact

- Affects `registry/dependency_resolver.py`, `registry/module_installer.py`, and their unit tests.
- Direct URL, VCS, local-path, and pip-option dependency declarations become invalid for automatic marketplace installation.
- No user-facing command syntax changes; README, `docs/`, `docs/index.md`, and navigation require review but no content update because this restores the documented trust model.
- Rollback is the single security-fix commit, though rollback would reopen arbitrary code execution from repository metadata.

## Source Tracking

- **Security report**: Aardvark, "Project module manifests trigger untrusted pip installation"
- **Repository**: nold-ai/specfact-cli
- **Public issue**: Not created to avoid disclosing an unpatched critical vulnerability.
