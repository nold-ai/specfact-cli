## 1. Change Setup And Spec Deltas

- [x] 1.1 Update `openspec/CHANGE_ORDER.md` with `docs-12-docs-validation-ci` entry
- [x] 1.2 Add `docs-command-validation` capability spec
- [x] 1.3 Add `docs-cross-site-link-check` capability spec

## 2. Command Validation Script

- [x] 2.1 Write `scripts/check-docs-commands.py` to extract @app.command() and add_typer() registrations from module source
- [x] 2.2 Add comparison logic to match extracted commands against docs code blocks
- [x] 2.3 Add `hatch run docs-validate` script entry in `pyproject.toml`

## 3. Cross-Site Link Validation

- [x] 3.1 Write `scripts/check-cross-site-links.py` to find cross-site URLs in markdown and validate via HTTP HEAD
- [x] 3.2 Add redirect coverage tests for all URLs in the migration map

## 4. CI Integration

- [x] 4.1 Extend `.github/workflows/docs-review.yml` with command validation step
- [x] 4.2 Add cross-site link check step (optional/warning-only for external URLs)

## 5. Verification

- [x] 5.1 Run `hatch run docs-validate` locally and verify it catches intentionally broken examples
- [x] 5.2 Run the full CI workflow and verify all checks pass
- [x] 5.3 Run repo quality gates on new scripts
