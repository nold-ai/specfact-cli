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

## Risks / Mitigations

- A stale lock blocks CI: provide a documented lock-refresh command and a policy test that detects stale exports.
- A companion revision becomes incompatible: update the fixture lock in a reviewed PR with cross-repo contract evidence; no moving fallback is permitted in blocking jobs.
- A tool is absent from the frozen environment: add it to the declared development extra and regenerate the lock, rather than installing it ad hoc.

## Verification strategy

- Policy tests inspect workflow commands, lock metadata, fixture immutability, and explicit basedpyright project selection.
- A reproducibility script creates two isolated frozen environments, records normalized `pip inspect` and CycloneDX-compatible SBOM input, and compares digests.
- The package matrix installs the built wheel without dependency resolution and exercises the existing command-runtime smoke suite.
