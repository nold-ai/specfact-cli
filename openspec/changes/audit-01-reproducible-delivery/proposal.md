# Change: Reproducible delivery and type authority

## Why

CI and release proof currently resolve unconstrained dependency graphs and can select a moving companion-module branch. A basedpyright configuration file also competes with the strict project configuration. The same source revision can therefore receive materially different validation.

## What Changes

- Commit an immutable `uv.lock` and use it for CI/release Python environments.
- Build a wheel once from that environment and install it without a second dependency resolution.
- Pin cross-repository runtime fixtures to a reviewed modules-repository commit recorded in version control.
- Make `pyproject.toml` the only basedpyright configuration and require explicit project selection plus a JSON artifact in CI.
- Keep an explicitly named scheduled lower-bound compatibility lane outside blocking release evidence.
- Generate deterministic SPDX SBOM evidence from `pip inspect` with repository-owned
  standard-library code; do not add a third-party SBOM generator to delivery CI.

## Capabilities

### New Capabilities

- `reproducible-delivery`: frozen dependency resolution, immutable integration fixtures, and reproducibility evidence for CI/release validation.

### Modified Capabilities

- `basedpyright-runner`: one declared, explicitly selected basedpyright project configuration is enforced in CI.
- `command-package-runtime-validation`: installed-wheel smoke validation uses a locked Python 3.11–3.13 matrix.

## Impact

- **Affected areas**: `pyproject.toml`, `uv.lock`, CI workflows, runtime-validation scripts, type-check configuration, and developer/contributor documentation.
- **Compatibility**: local Hatch commands remain available; CI/release evidence becomes frozen. The lower-bound/latest compatibility lane is advisory and cannot satisfy release proof.
- **Rollback**: retain the advisory unconstrained lane, revert the lock and fixture pin in one change, and keep the prior Hatch entry points available.
- **Documentation impact**: update contributor and CI guidance with lock refresh/review, immutable fixture updates, and type-check authority.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #651
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/651>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open; unblocked; parent #355 Developer Workflow & CI Pipeline
