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

The local frozen proof completed with the committed export:

```text
uv sync --locked --all-extras
uv build --wheel
python -m venv <temporary wheel environment>
<venv>/bin/python -m pip install --require-hashes -r requirements/ci/locked.txt
<venv>/bin/python -m pip install --no-deps dist/specfact_cli-0.53.2-py3-none-any.whl
<venv>/bin/specfact --version
SpecFact CLI version 0.53.2
<venv>/bin/cyclonedx-py environment --output-format JSON --output-file <sbom.json>
```

The blocking `Reproducible Delivery Evidence` CI job repeats this install twice,
compares normalized package name/version identities and normalized SBOMs, and uploads
the raw evidence. The local proof compared 197 installed package identities and
identical normalized SBOMs. `pip inspect` includes installer-specific relationships,
so those raw reports are retained for diagnosis rather than compared byte-for-byte.
The 3.11, 3.12, and 3.13 built-wheel matrix is configured as merge-blocking; those
hosted runners are not available in this local environment.

`ruff format --check .` currently reports formatting violations in unrelated tracked
documentation/archive files. The four Python files introduced by this change passed
both scoped `ruff format --check` and `ruff check`; no global reformat was applied.

The final focused policy command used an isolated temporary uv cache because this
sandbox cannot open the caller's existing `~/.cache/uv` Git metadata. The same
checker succeeds with that writable cache; CI uses its own writable cache.

## Known environmental limitation

The sibling internal wiki worktree was already dirty before this change (`wiki/graph.md`
and unrelated source pages). The new `wiki/sources/audit-01-reproducible-delivery.md`
was added without overwriting those changes, but `wiki_rebuild_graph.py` is deferred
until the existing graph edits are reconciled.
