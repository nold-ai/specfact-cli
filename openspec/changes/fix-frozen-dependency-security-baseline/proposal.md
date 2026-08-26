# Change: Fix the frozen dependency security baseline

## Why

The committed `dev` dependency graph installs `pip==26.1.2`, which the repository's
blocking audit identifies as affected by PYSEC-2026-3721 / CVE-2026-13346. The same
baseline also leaves two open Python Dependabot updates targeted at `main` rather
than integrating and resolving them on `dev`. C14 needs a released, reproducible,
security-clean core baseline before its implementation begins.

## What Changes

- **MODIFY** the frozen dependency graph so `pip` resolves to the minimum patched
  release line for CVE-2026-13346, with a durable patched floor on development
  and Hatch tooling surfaces only (never core runtime dependencies).
- **MODIFY** the reviewed development tool constraints to incorporate the open
  Hatchling and Setuptools Dependabot updates on `dev`, then regenerate the
  authoritative lock and hash-protected CI export together.
- **VERIFY** that the docs `json` security update is already present on `dev`, so
  the open `main`-targeted Dependabot PR is a duplicate rather than a missing edit.
- **VERIFY** all accessible Dependabot, code-scanning, and secret-scanning findings
  without dismissing or weakening any alert or gate.
- **RELEASE** only the next patch version, `0.55.2`, with the required changelog and
  canonical version-source updates after every remediation gate passes.

## Capabilities

### Modified Capabilities

- `dep-license-gate`: require a compatible fixed dependency release to be selected
  and all authoritative frozen inputs to be regenerated when an unreviewed advisory
  is validated.

## Impact

- **Affected specifications**: `dep-license-gate` only; the existing audit remains
  fail-closed and no exception semantics change.
- **Affected code/configuration**: `pyproject.toml`, `uv.lock`,
  `requirements/ci/locked.txt`, a focused dependency-policy test, `SECURITY.md`,
  the four canonical version files, and `CHANGELOG.md`.
- **Integration points**: frozen CI setup, package builds, pip-audit, Dependabot,
  GitHub security checks, PyPI publication, and the C14 baseline handoff.
- **Compatibility**: no public CLI/API or runtime dependency contract changes.
  Hatchling 1.32 and Setuptools 84 must pass the existing build and release matrix.
- **Documentation impact**: no user guide or navigation change; release/security
  impact is documented in `CHANGELOG.md` and the issue/PR evidence ledger.
- **Rollback**: revert the security PR on `dev` before release. After publication,
  publish a forward patch for corrections and use normal PyPI yank guidance only
  when the released artifact itself is unsafe; never rewrite the tag/history.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #686
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/686>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open; native type Bug; project SpecFact CLI #1 status Todo; assigned to djm81; labels bug/security; no parent or dependency relationships (standalone remediation)

## Dependencies

- Baseline: `origin/dev@e3a20f20df440dff49f8c6d1f73375451bea1d8c`.
- Prior delivery contract: `audit-01-reproducible-delivery` is already represented
  in the current `dev` tree; this bugfix does not alter its active branch or scope.
- C14 consumes the final merged and released patch tag; C14 does not contribute code
  to this remediation.
