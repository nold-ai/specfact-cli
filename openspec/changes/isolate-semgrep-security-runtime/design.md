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
docs/Gemfile.lock, and scripts/check_jekyll_dependencies.rb and .github/workflows/docs-dependency-checks.yml.
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

The existing parameter table binds the eight exact runtime and tooling versions
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

The accepted 23-case receipt is preserved as `pre-advisory-review-evidence.json`.
The active receipt records fresh independent AI technical acceptance in
`requirements-proof/advisory-mapping-review.md`; new native RED remains pending. The new
plan includes only observed baseline failures. Supplementary controls must pass.
Root owns independent acceptance, native RED, wiki synchronization, and production.
