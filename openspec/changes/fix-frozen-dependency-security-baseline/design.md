# Design: Frozen dependency security baseline patch

## Context

The blocking Security Audit synchronizes `uv.lock`, audits the committed
hash-protected export, and currently observes `pip==26.1.2`. PSF advisory evidence
marks pip versions before 26.2 as affected by CVE-2026-13346. The remediation must
keep `pyproject.toml`, `uv.lock`, and `requirements/ci/locked.txt` coherent while
preserving every legitimate build, test, and packaging workflow.

## Security boundary

The shared enforcement boundary is the committed frozen dependency graph:

1. `pyproject.toml` declares direct build/development constraints.
2. `uv.lock` resolves the complete environment, including pip as a transitive tool.
3. `requirements/ci/locked.txt` exports the same graph with artifact hashes.
4. CI and release jobs install those committed inputs before running the audit.

Updating only an ambient virtual environment, only the export, or only a Dependabot
branch would leave an alternate vulnerable representation reachable. The lock and
export therefore change only through the repository refresh command and are reviewed
together.

## Decisions

### Use the minimum patched pip line

Resolve pip 26.2 or later within the current compatible graph. Do not create an
advisory exception because a compatible fixed release exists. Declare
`pip>=26.2` in both `project.optional-dependencies.dev` and the default Hatch
environment so ordinary refreshes cannot silently retain an affected but otherwise
compatible pip. Require `pip-tools>=7.6.1` on both tooling surfaces because 7.6.0
calls a pip internal API that changed in 26.2; 7.6.1 is the first upstream release
with pip 26.2 compatibility. Keep both tools out of core project dependencies and
`setup.py`.

### Consolidate the requested dev-tool updates

Apply Hatchling 1.32.0 and widen Setuptools to the 84.x line on the `dev` bugfix
branch, then let the single frozen resolver prove compatibility. Do not cherry-pick
or modify the `main`-targeted Dependabot PRs. Hatchling 1.32.0 defaults to Core
Metadata 2.5, which frozen Twine 6.2.0 cannot validate. Upgrade the development-only
publication client to Twine 7.0.0, whose documented compatibility fix accepts Core
Metadata 2.5. A no-write resolution proves that only Twine changes; its removal of
never-standardized Core Metadata 2.0 does not affect Hatchling output or SpecFact's
runtime surface.

### Preserve the existing docs security update

`docs/Gemfile.lock` already contains json 2.21.2 on `dev`; changing it again would
add no security value. Record the corresponding open PR as duplicate/already safe
for the `dev` baseline.

### Policy test plus dependency audit evidence

No runtime behavior or audit implementation changes. A focused policy test first
proves the missing durable pip floor while protecting the pip-free core runtime. The
dependency failing-before artifact is the unchanged repository audit against the
original frozen graph; passing-after is the same test, audit, and reproducibility
controls against the regenerated graph. Existing build/package tests remain
compatibility controls.

## Failure modes and mitigations

- **Lock/export drift**: run the repository refresh and reproducible-delivery checker;
  reject any hand-edited export.
- **Build backend regression**: run wheel builds, package validation, and the Python
  3.11-3.13 applicable release checks locally/CI; keep the frozen publication client
  on the release that accepts the build backend's current metadata format.
- **Incomplete alert inventory**: classify inaccessible authenticated alert families
  as unproven and block dismissal; require read access before claiming zero alerts.
- **Core dependency expansion**: assert that pip remains absent from project runtime
  dependencies and `setup.py` while the two tooling surfaces carry the fixed pip and
  compatible pip-tools floors.
