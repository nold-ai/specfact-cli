# Main dependency-only release design

Use the existing main runtime and release workflows. Refresh generated frozen
inputs through the repository tooling after authentic native RED evidence exists.
No application function boundary changes are required.

Artifact tests install or inspect the exact hash-pinned delivery wheel independently
of the verifier's package versions. Certificate parsing uses trusted SSL over inert
wheel data. GitPython and PyJWT run isolated subprocess probes. Malformed wheel
controls demonstrate rejection of altered contents, identity, hashes, paths,
origins, and duplicate records.

The existing audit gate reads an exact MCP register entry. Tests exercise both
advisory IDs, the inclusive expiry day, wrong versions, unrelated and mixed
advisories, skipped dependencies, expiry, and a future review date. No audit lane
is disabled. The official Semgrep 1.179.0 package continues to select MCP 1.29.0.

The source-distribution test invokes the ordinary uv build path with the installed
frozen build backend and verifies exact bundled manifest bytes in the resulting
wheel. The later fix adds only the missing source inclusion.

The full intended production touchpoints are pyproject.toml, uv.lock,
requirements/ci/locked.txt, ci/vulnerability-audit-exceptions.json, setup.py,
src/__init__.py, src/specfact_cli/__init__.py, CHANGELOG.md, docs/Gemfile,
docs/Gemfile.lock, scripts/check_jekyll_dependencies.rb, .github/workflows/docs-dependency-checks.yml,
and ci/dependency-trust-exceptions.json.
The Ruby probe runs against installed locked gems after the dependency update.
Its output is supplementary compatibility evidence, not a substitute for native
mapped Python evidence.

Risk controls retain published runtime bytes and signed manifests, constrain the
resolver to reviewed upgrades, and keep the exception exact and expiring. A failed
build, widened package graph, or failing audit blocks finalization. Rollback is the
unmerged PR diff. No release side effect occurs during this work.

Native mapped proof covers the Python artifact behavior, release selections,
source build, bounded audit decision, and version metadata. Real Ruby behavior
published-runtime equality, and changelog scope are separate final acceptance checks. Their output
must be retained before final review and is not implied by the Python mapping.

## Native failing-first selection

The pinned native reconciler requires every RED-plan selector to fail. The first
34-case CI attempt retained genuine output but refused fifteen passing controls.
It remains incomplete evidence and must not be relabelled RED. That historical corrected
plan contained nineteen genuinely failing change cases. The fifteen malformed
artifact and negative audit controls remain unchanged in their test files and
in the normal required pytest suite. They are supplementary safety checks,
not new behavior needing failure-before-fix provenance. The newly approved dependency correction expands the plan to 23 cases.
It adds exact certifi, GitPython, PyJWT, and packaging lock/export selections
and updates the virtualenv and python-discovery expectations. That correction verified all 23 selected cases and all fifteen supplementary controls.
No artifact behavior assertion, negative control, or native policy is weakened.

## Corrected dependency selection and review boundary

The existing parameter table binds the nine exact runtime and tooling versions
to both uv.lock and its hashed export. The separate scanner case binds official
Semgrep 1.179.0 and MCP 1.29.0. Artifact probes continue to inspect the actual
frozen certifi, GitPython, and PyJWT wheels. Exact-version assertions complement
those behavior checks.

The prior accepted 19-case proof applies only to its original test and mapping
bytes. Keep its reports as history. That corrected mapping was independently accepted before native RED. Any subsequent
changed mapping requires fresh independent acceptance, and its reference must be
repository-relative or pinned to an immutable commit. The coordinator must
verify fresh native RED before restoring the saved production patch.

## Advisory correction boundary

The checkout probe adds a path-scenario table around the existing full three-package
hash-pinned wheel extraction. A dedicated sentinel replaces `Submodule._clone_repo`.
`Repo.create_submodule` must raise ValueError before that sentinel for Git metadata
paths. The probe records clone calls and compares inert hook bytes before and after.
It creates no malicious remote repository or executable hook. Passing ordinary-path
controls stay outside the native RED mapping. Preserve the existing `../outside`
update probe unchanged.

The audit scenario table covers the committed register through the existing strict
gate. Ordinary MCP evaluations move to 2026-10-22 because the whole register includes
the new OpenTelemetry review date. MCP's own 2026-10-21 record and true future and
expiry tests remain unchanged. The scanner graph contract now requires exactly
two separate records and official opentelemetry-api 1.37.0. No gate code changes.

The active independent review is selected by
`requirements-proof/review-evidence.json`. Historical receipts and measured local
and native outcomes belong in `TDD_EVIDENCE.md`, so progress updates do not change
this design's review binding. A scope or test change requires fresh technical
acceptance. Before production, authenticate native RED against its immutable
head/tree/base, every selected test hash and the accepted canonical plan.
Supplementary controls must pass.

## Supported parser and current review boundary

The existing version table gains pycparser 3.12. The existing provenance-record
case binds its exact official wheel URL, SHA-256, classification, UTC review date,
and bounded expiry. These two selectors extend the 31-case plan to 33 cases.
The record's future implementation uses the existing JSON shape and records the
immutable upstream source, matching BSD license, disclosed Socket capabilities,
and license-heading classification in its rationale. No checker changes are needed.
The 2026-10-22 review date is the actual UTC day of the 2026-10-23 Berlin review,
so the unchanged date.today() check also works on native UTC runners.

The wrong-hash and wrong-package fixtures derive only their baseline version and
review date from the actual reviewed record. Their expected rejection conditions
remain fixed. Explicit expiry, prohibited-wheel and 3.0-alias tests remain intact.
The existing real-clock checker test continues to execute without an injected date.

Review comment 4354335605 identifies inherited PYTHONPATH and PYTHONHOME in the
otherwise disposable direct-launcher smoke environment. A controlled child-Python
probe must first demonstrate that inheritance. The fixture then removes only those
two keys before its existing bootstrap and actual CLI calls. Parent package inventory
and every existing success assertion remain intact. This test-fixture correction
requires the full bootstrap/CLI smoke check and does not change application behavior.
