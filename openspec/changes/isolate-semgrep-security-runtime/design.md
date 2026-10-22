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
It remains incomplete evidence and must not be relabelled RED. The corrected
plan contains nineteen genuinely failing change cases. The fifteen malformed
artifact and negative audit controls remain unchanged in their test files and
in the normal required pytest suite. They are supplementary safety checks,
not new behavior needing failure-before-fix provenance. Final verification runs
both the nineteen selected cases and all supplementary controls. No check,
assertion, production file, or native policy is changed by this correction.
