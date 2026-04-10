# Change: Add CI Validation For Docs Command Examples And Cross-Site Links

## Why

Documentation command examples can drift from actual CLI implementations as code evolves. Cross-site links between docs.specfact.io and modules.specfact.io can break when pages are moved or renamed. There is no automated check to catch these regressions before they reach users.

## What Changes

- Add a script that extracts command registrations from module source code and compares against command examples in docs
- Add cross-site link validation (HTTP HEAD checks) for links between core and modules docs
- Add redirect coverage tests to verify that all old URLs resolve to valid new locations
- Integrate both checks into existing CI workflows
- Add `hatch run docs-validate` command for local pre-commit validation

## Capabilities

### New Capabilities

- `docs-command-validation`: automated CI check that docs command examples match actual CLI command registrations
- `docs-cross-site-link-check`: automated validation of links between core and modules docs sites

## Impact

- New scripts: `scripts/check-docs-commands.py`, `scripts/check-cross-site-links.py`
- Modified CI: `.github/workflows/docs-review.yml` extended with command validation and link checking steps
- Modified build: `pyproject.toml` adds `docs-validate` script entry
- Cross-repo: corresponding change in specfact-cli-modules adds the modules-side validation
- Depends on: docs-05, docs-06, docs-07 (content restructure must be complete)

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #440
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/440>
- **Last Synced Status**: synced
- **Sanitized**: true
- **Cross-repo**: specfact-cli-modules/docs-12-docs-validation-ci
