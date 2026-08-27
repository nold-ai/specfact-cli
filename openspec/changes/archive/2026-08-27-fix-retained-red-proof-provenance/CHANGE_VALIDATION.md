# Change Validation Report: fix-retained-red-proof-provenance

**Validation Date**: 2026-08-26 (Europe/Berlin)
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Static producer/validator/workflow boundary analysis against `origin/dev`

## Executive Summary

- Breaking Changes: 0 detected
- Impact Level: Low and release-blocking
- Validation Result: Pass

## Dependency and interface analysis

- No package dependency, public CLI/API, evidence schema reader, or module fixture changes are required.
- Complete retained reports keep their current shape and validation semantics.
- The change fills fields the validator already requires; it does not add a compatibility reader for incomplete reports.
- Requirements 08's signed replay-capsule boundary is independent and unchanged.

## Documentation and release analysis

- Contributor-facing OpenSpec/TDD evidence is affected.
- README, user guides, docs index, and navigation do not describe this internal CI producer and require no change.
- Issue #686 owns the single `0.55.2` version/changelog/release transaction; this prerequisite must merge before that release rather than consuming `0.55.2` independently.

## Rollback

Revert the prerequisite PR before release. If a regression ships in `0.55.2`, publish a forward patch and retain normal tag/PyPI history.

## OpenSpec validation

- **Command**: `openspec validate fix-retained-red-proof-provenance --strict`
- **Result**: pass; no format or scenario issues.

## Delivered surface

- Requirements producer and validator: `.github/workflows/requirements-evidence.yml`,
  `scripts/requirements_bootstrap_authority.py`,
  `scripts/requirements_proof_provenance.py`, and
  `scripts/requirements_proof_pytest_plugin.py`.
- Frozen Code Review and delivery gates: `.github/workflows/pr-orchestrator.yml`,
  `.pre-commit-config.yaml`, `requirements/code-review/`,
  `scripts/check_license_compliance.py`, and the related focused tests.
- Evidence and governance: this issue-linked OpenSpec change and the already
  archived dependency-security baseline required for the combined delivery.
- Public CLI/API behavior: unchanged. Version ownership remained with the
  dependency-security patch at `0.55.2`.

## Focused and full regression evidence

- Focused producer/authority/security command: 14 passed, including exact
  authority acceptance, metadata rejection, retained-JUnit size/entity
  rejection, toolchain tamper rejection, and replay rejection.
- Full repository command: 3,033 passed and 9 skipped locally; the two
  sandbox-only environment controls were rerun or delegated to the isolated
  GitHub runner as recorded in `TDD_EVIDENCE.md`.
- Ruff format/lint, basedpyright, workflow lint, module signature verification,
  license compliance, dependency trust, pip-audit, Bandit, Semgrep, and
  SpecFact full-enforcement Code Review all passed.

## Artifact and delivery identities

- Authoritative red run: `33011480246`; artifact `9622698922`; signed red
  commit `dcd04b981b5e2a8e8d1fe403cdec6fddd038b678`.
- Final test-only red run: `33013274590`; artifact `9623426074`; signed commit
  `04b6c02eb63f779309d8dced48085f3ef0efe029`.
- Final passing Requirements run: `33016260828`.
- Delivery PR: <https://github.com/nold-ai/specfact-cli/pull/690>.
- Merge commit: `3ea3d9b4492ade6ec5683fac83c5b5090b0cb547`.
- GitHub gate result: Requirements Evidence and every required blocking check
  passed; Security Audit, Dependency Trust, License Compliance, both Socket
  checks, module signatures, tests, type checking, linting, and quality gates
  were successful. Publication jobs correctly skipped on the `dev` target.
