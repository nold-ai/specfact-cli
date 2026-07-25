# Change Validation Report: audit-01-reproducible-delivery

**Validation date:** 2026-07-25 Europe/Berlin
**Change proposal:** [proposal.md](./proposal.md)
**Validation method:** Metadata interface dry run in
`/private/tmp/specfact-validation-audit-01-20260725`, dependency search, focused
tests, and strict OpenSpec validation.

## Executive summary

- **Breaking changes:** 0 detected.
- **Dependent files:** 7 reviewed; 0 require caller changes.
- **Impact level:** Low.
- **Validation result:** Pass.
- **User decision:** Address all five unresolved PR #652 review threads.

## Interface and dependency analysis

The reviewed changes only correct documentation/specification text and narrow the
published `pycparser` requirement from `!=3.0` to `!=3.0.*`. No function signature,
CLI option, runtime contract, adapter interface, or package entry point changes.

The frozen resolution remains `pycparser==2.22`; the hash-protected CI export is
unchanged. The regenerated `uv.lock` records the narrowed source requirement, so
future resolvers cannot select a patch or post-release in the blocked 3.0 family.
The dependency-trust policy already rejects equivalent PEP 440 spellings before
installation, providing a second enforcement boundary.

## Affected files

| Area | Files | Impact |
| --- | --- | --- |
| Package metadata | `pyproject.toml`, `setup.py`, `uv.lock` | Narrower safe resolver constraint; no installed-version change. |
| Regression proof | `tests/unit/packaging/test_core_package_includes.py` | Covers 3.0, 3.0.1, and 3.0.post1 exclusion. |
| Documentation/specification | dependency-trust review, TDD evidence, license-gate spec | Corrected reviewability, date range, line length, and purpose text. |

## Format and OpenSpec validation

- **Proposal/tasks/design/spec format:** Pass; existing active change artifacts are
  complete and remain in scope.
- **Compatibility:** Pass; no public API or runtime behavior is removed or changed.
- **Required follow-up:** The existing internal-wiki mirror remains separately
  deferred because its sibling worktree was already dirty; this review-fix scope does
  not change the active proposal, design, task ordering, or dependencies.

## Validation artifacts

- Failing-before package metadata test and passing-after command are recorded in
  [TDD_EVIDENCE.md](./TDD_EVIDENCE.md).
- Strict validation: `hatch run openspec validate audit-01-reproducible-delivery --strict`.
- Hosted BasedPyright artifact: GitHub Actions run
  [`30132168259`](https://github.com/nold-ai/specfact-cli/actions/runs/30132168259).
