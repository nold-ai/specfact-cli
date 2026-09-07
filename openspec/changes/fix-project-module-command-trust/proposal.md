# Change: Verify project modules before command registration

## Why

Workspace-local module manifests are repository-controlled input. An unsigned project module can currently claim an official bundle name and become the root `requirements` command, causing Python import-time code to execute when a developer or CI runner asks for command help.

## What Changes

- Require project-scoped modules to carry valid integrity metadata and a signature before their commands can be registered, unless the operator explicitly enables the existing unsigned-module override.
- Bind recognized official bundle names to their expected `nold-ai/<bundle>` module identity before mounting category groups.
- Add regression coverage proving an unsigned project module cannot register or execute and cannot impersonate the requirements bundle.

## Capabilities

### Modified Capabilities

- `module-security`: Project-discovered executable modules fail closed unless cryptographically verified or explicitly allowed as unsigned.
- `category-command-groups`: Official category bundle mounting requires the expected official module identity.

## Impact

- **Code**: Module registration and category-group eligibility in `src/specfact_cli/registry/module_packages.py`.
- **Tests**: Focused registry tests for unsigned project modules and official bundle identity binding.
- **Compatibility**: Existing signed project modules continue to work. Deliberately unsigned project modules require the existing explicit unsigned override.
- **Offline-first**: Verification uses the bundled public key and local artifact contents; no network request is added.
- **Documentation**: Review `docs/reference/module-categories.md`, module security documentation, README, site index, and navigation; document the fail-closed project-module rule where module trust is explained.
- **Rollback**: Revert this change to restore the earlier permissive behavior; doing so reopens repository-triggered code execution and is not recommended.

## Source Tracking

- **Security report**: Aardvark, “Requirements mount trusts unverified project bundle metadata”
- **Affected commit**: `b75f524750172eda7f1b38a3ca5bcd44f1a3dc09`
- **Repository**: `nold-ai/specfact-cli`
- **Last Synced Status**: confirmed against branch HEAD

## Verification Exception

The mandatory SpecFact self-review report was generated and contains no code findings, but its assurance status is `UNKNOWN` because the released review module could not acquire its verified OCI analyzer cache in this environment. This narrowly documented environment exception does not waive analysis: repository Ruff, BasedPyright, Semgrep, Bandit, contract, and focused regression gates run independently, and the report details are preserved in `TDD_EVIDENCE.md`.
