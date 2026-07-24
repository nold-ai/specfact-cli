## Context

The PR orchestrator installs `.[dev]` repeatedly and resolves a companion-module branch from the PR name or `dev`. Basedpyright can discover both `pyrightconfig.json` and `[tool.basedpyright]`, which carry different strictness. These are supply-chain and confidence boundaries, not product-runtime dependencies.

## Goals / Non-Goals

**Goals:** freeze blocking CI/release resolution, prove selected type configuration, lock companion runtime fixtures, and preserve useful compatibility discovery.

**Non-Goals:** replace Hatch for local development, change package runtime dependencies, or modify `specfact-cli-modules`.

## Decisions

1. `uv.lock` is the committed lock authority. A checked-in export generated from the lock is used only where pip requires hash-verified requirements; CI never resolves from `pyproject.toml` alone.
2. CI tool dependencies are declared through project extras rather than ad-hoc runtime `pip install` calls. Jobs prepare one frozen environment, build one wheel, then use `--no-deps` for wheel installation.
3. `ci/module-fixture.lock.json` records the modules repository URL and immutable commit SHA. Runtime jobs checkout that SHA and verify `HEAD` before invoking tests; branch probing remains only in the advisory compatibility workflow.
4. `pyproject.toml` is the sole basedpyright configuration. `pyrightconfig.json` is removed, commands pass `--project pyproject.toml`, and JSON output is retained as a CI artifact.
5. The blocking matrix covers Python 3.11, 3.12, and 3.13 for built-wheel smoke. The lower-bound/latest resolver lane runs weekly/manual with a clearly advisory result.
6. BasedPyright is installed only from `tools/basedpyright/package-lock.json` with `npm ci --ignore-scripts`. CI obtains Node through a SHA-pinned `actions/setup-node` action. The PyPI `basedpyright` and `nodejs-wheel-binaries` packages are not permitted in frozen Python inputs.
7. Pylint is removed from the frozen CI and Hatch lint stacks. Ruff remains the blocking Python lint authority; the existing Semgrep, Bandit, and clean-code gates retain their independent roles.
8. A dependency exception records package, exact version, source URL, review date, expiry, rationale, and required transitive path. `pycparser` is permitted only while this record is current. The license scanner fails on explicit GPL/AGPL expressions and rejects ambiguous mixed metadata unless a reviewed classifier record permits it.
9. Dependency trust is a no-install standard-library control. The shared frozen setup action runs it before synchronization, and the checker canonicalizes package identities and binds every reviewed URL/hash to the matching parsed `uv.lock` package record rather than searching the lock as text.
10. Security tooling uses checked-in reviewed minimum patched versions rather than resolving a moving “latest” release during local setup. The pre-install gate rejects a lock downgrade; scheduled advisory audit and compatibility lanes surface new upstream releases for review.

## Risks / Mitigations

- A stale lock blocks CI: provide a documented lock-refresh command and a policy test that detects stale exports.
- A companion revision becomes incompatible: update the fixture lock in a reviewed PR with cross-repo contract evidence; no moving fallback is permitted in blocking jobs.
- A tool is absent from the frozen environment: add it to the declared development extra and regenerate the lock, rather than installing it ad hoc.
- Node/npm bootstrap fails: the type-check job fails before executing BasedPyright; restoring the prior Python package is not an approved rollback because it reintroduces the unofficial binary distribution.
- A dependency exception expires: CI fails closed and requires a new review rather than silently extending acceptance.
- A malformed or adversarial exception reuses another package's artifact evidence: parse the exact
  package record and require canonical identity plus matching artifact metadata before any install.

## Verification strategy

- Policy tests inspect workflow commands, lock metadata, fixture immutability, and explicit basedpyright project selection.
- A reproducibility script creates two isolated frozen environments, records normalized
  `pip inspect` and an SPDX 2.3 SBOM rendered by repository-owned standard-library
  code, and compares digests. This avoids a separate unreviewed SBOM generator in the
  delivery trust boundary.
- The package matrix installs the built wheel without dependency resolution and exercises the existing command-runtime smoke suite.
