# TDD evidence — audit-01-reproducible-delivery

All times are Europe/Berlin (2026-07-23).

## Failing-first evidence

Before the frozen-delivery files and workflow changes were added, this focused policy
suite was run:

```text
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py \
  tests/unit/scripts/test_reproducible_delivery.py -q

36 collected; 31 passed; 5 failed
```

The failures established the missing controls: no `ci/module-fixture.lock.json`, no
committed `uv.lock`, no 3.11–3.13 runtime matrix, a competing `pyrightconfig.json`,
and no frozen-delivery verifier. The tests were added before the corresponding CI,
lock, fixture, and verifier implementation.

After extending the policy to the standalone contract and documentation command
validation workflows, the focused workflow suite also failed as expected:

```text
36 collected; 34 passed; 2 failed
```

Both failures identified a branch-selected companion-module checkout and dynamic pip/
Hatch installation. Those workflows now use the same reviewed fixture lock and frozen
setup action as the blocking orchestrator jobs.

## Passing evidence

```text
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py \
  tests/unit/scripts/test_reproducible_delivery.py \
  tests/unit/specfact_cli/registry/test_signing_artifacts.py -q
84 passed, 1 sandbox cache warning

hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py -q
36 passed, 1 sandbox cache warning

uv run --locked pytest tests/unit/docs/ tests/unit/scripts/test_doc_frontmatter/ \
  tests/integration/scripts/test_doc_frontmatter/ -q
109 passed, 1 skipped, 3 warnings

hatch run lint-workflows
exit 0

openspec validate audit-01-reproducible-delivery --strict
Change 'audit-01-reproducible-delivery' is valid

hatch run python scripts/check_reproducible_delivery.py
reproducible delivery inputs are valid

uv run --locked basedpyright --project pyproject.toml --outputjson
filesAnalyzed: 602; errorCount: 0; warningCount: 1626; informationCount: 0

hatch run license-check
PASS — overall exit code: 0

hatch run security-audit
Security audit passed. No high-severity vulnerabilities found

hatch run bandit-scan
No issues identified (0 medium/high findings)

hatch run specfact code review run --json --out .specfact/code-review.json
Review completed with no findings; findings: 0

python tools/smart_test_coverage.py run --level full
2882 passed, 9 skipped, 2 warnings; coverage 64%
```

The BasedPyright warnings are the existing diagnostic baseline. The sole authority is
now the `[tool.basedpyright]` section in `pyproject.toml`; the former competing
`pyrightconfig.json` was removed. The JSON report is the CI artifact and was retained
locally at `/tmp/specfact-basedpyright.json` for this verification run.

## Built-wheel evidence

The original local wheel proof is superseded by the security remediation below: it
used `cyclonedx-py`, which is no longer an accepted delivery dependency. The current
blocking job renders each SBOM from its local `pip inspect` report with
`scripts/render_locked_sbom.py`, then compares the deterministic SPDX 2.3 documents.
The 3.11, 3.12, and 3.13 built-wheel matrix remains merge-blocking; hosted proof is
pending the updated pull-request run.

`ruff format --check .` currently reports formatting violations in unrelated tracked
documentation/archive files. The four Python files introduced by this change passed
both scoped `ruff format --check` and `ruff check`; no global reformat was applied.

The final focused policy command used an isolated temporary uv cache because this
sandbox cannot open the caller's existing `~/.cache/uv` Git metadata. The same
checker succeeds with that writable cache; CI uses its own writable cache.

## Security remediation evidence — 2026-07-24

Socket Security identified `cyclonedx-bom@7.3.1`, newly added by this change for
SBOM rendering, as a potential-malware AI signal. The alert was not waived, ignored,
or resolved. The package was removed rather than accepted as a delivery dependency.

The reproducible-delivery OpenSpec delta was updated and validated before the
replacement tests were added:

```text
openspec validate audit-01-reproducible-delivery --strict
Change 'audit-01-reproducible-delivery' is valid

hatch run pytest tests/unit/scripts/test_reproducible_delivery.py \
  tests/unit/workflows/test_trustworthy_green_checks.py -q
41 collected; 38 passed; 3 failed
```

Two failures proved the missing renderer and the prohibited `cyclonedx-py` workflow
call. The remaining failure was the pre-existing sandbox restriction on the shared uv
cache while the test checked the stale export. No production replacement had been
applied at that point.

After removal and frozen-input refresh:

```text
hatch run refresh-frozen-delivery
Resolved 188 packages
Removed cyclonedx-bom v7.3.1 and its generator-only transitive dependencies
reproducible delivery inputs are valid

hatch run pytest tests/unit/scripts/test_reproducible_delivery.py \
  tests/unit/workflows/test_trustworthy_green_checks.py -q
41 passed

hatch run python tools/smart_test_coverage.py run --level full
2884 passed, 9 skipped, 2 warnings; coverage 64%
```

The replacement `scripts/render_locked_sbom.py` uses only the Python standard library
to render deterministic SPDX 2.3 JSON from each local `pip inspect` report. Existing
Socket warnings for `dill`, `nodejs-wheel-binaries`, and `pycparser` remain unwaived;
they are pre-existing dependency paths and require separate review before being
accepted or changed.

`cyclonedx-python-lib` remains in the frozen export only because the pre-existing
`pip-audit` development tool depends on it; delivery CI neither invokes it nor uses it
to render SBOM evidence.

## CI regression evidence — 2026-07-24

GitHub Actions run `30048392658` failed the Package Runtime Matrix pipx launcher
because pipx delegated to uv with `--no-deps` already present, while the workflow
also supplied `--pip-args="--no-deps"`. uv rejected the duplicate flag before the
wheel launcher could be exercised.

The new workflow-policy test was added before the workflow edit:

```text
hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py -q
38 collected; 37 passed; 1 failed
```

After removing only the redundant pipx argument, while retaining the subsequent
hash-verified frozen dependency install:

```text
hatch run pytest tests/unit/scripts/test_reproducible_delivery.py \
  tests/unit/workflows/test_trustworthy_green_checks.py -q
42 passed

hatch run lint-workflows
exit 0

hatch run python scripts/check_reproducible_delivery.py
reproducible delivery inputs are valid
```

## Known environmental limitation

The sibling internal wiki worktree was already dirty before this change (`wiki/graph.md`
and unrelated source pages). The new `wiki/sources/audit-01-reproducible-delivery.md`
was added without overwriting those changes, but `wiki_rebuild_graph.py` is deferred
until the existing graph edits are reconciled.
