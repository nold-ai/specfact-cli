# TDD Evidence for ci-02-trustworthy-green-checks

## Pre-Implementation Test Failure (Expected)

### Test Run: 2026-03-30 - Pre-commit Review Report Failure Handling

**Command:**

```bash
cd /home/dom/git/nold-ai/specfact-cli
python3 -m pytest tests/unit/scripts/test_pre_commit_code_review.py -q -k 'missing_report or rejects_non_object_json'
```

**Result:** ✅ 2 tests failed as expected before implementation.

**Failure summary:**

- `test_main_missing_report_still_returns_exit_code_and_warns` failed because the hook did not
  create the `.specfact/` parent directory before invoking the subprocess and treated a missing
  review report as a non-fatal outcome.
- `test_print_summary_rejects_non_object_json` failed because malformed report content printed an
  error but still returned exit code `0`.

**Status:** ✅ TDD workflow confirmed for review-report enforcement hardening.

## Post-Implementation Test Success

### Test Run: 2026-03-30 - Hardened Review Report and Doc Frontmatter Validation Slice

**Commands:**

```bash
cd /home/dom/git/nold-ai/specfact-cli
python3 -m pytest tests/unit/scripts/test_pre_commit_code_review.py -q -k 'missing_report or rejects_non_object_json or count_findings_by_severity'
python3 -m pytest tests/unit/scripts/test_doc_frontmatter/test_validation.py -q -k 'fix_hint_for_missing_frontmatter or fix_hint_for_invalid_owner'
python3 -m pytest tests/integration/scripts/test_doc_frontmatter/test_integration.py -q -k 'complete_validation_workflow or validation_with_all_valid_files or cli_with_fix_hint_flag'
```

**Result:** ✅ All targeted tests passed after implementation.

**Passing summary:**

- `scripts/pre_commit_code_review.py` now creates the review-report directory, validates
  `.specfact/code-review.json` with Pydantic models, and fails non-zero when the report is missing
  or malformed.
- `scripts/check_doc_frontmatter.py` now preserves fallback discovery behavior while emitting
  debug-level diagnostics when `parse_frontmatter(file_path)` raises file/YAML errors.
- The CLI root command now propagates validation exit codes correctly, so `--fix-hint` failures do
  not return a false green status.
- Helper fixtures and tests now assert the implemented required fields and valid owner behavior.

**Status:** ✅ Remediation implemented and verified.

## Pre-Implementation Test Failure (Expected)

### Test Run: 2026-03-30 - Trustworthy green-check workflow policy

**Command:**

```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/ci-02-trustworthy-green-checks
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata \
  hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py -q
```

**Result:** ✅ 6 tests failed as expected before implementation.

**Failure summary:**

- `pr-orchestrator.yml` still used workflow-level `paths-ignore`, so required checks disappeared on
  docs-only follow-up commits instead of reporting a status on the new head SHA.
- Required jobs still swallowed failures (`compat-py311`, `contract-first-ci`, `cli-validation`,
  and `linting`) or did not yet expose a dedicated required workflow-lint job.
- `dev -> main` release PRs still used a branch-only fast path without any commit-parity proof.
- `.pre-commit-config.yaml` did not expose the supported smart-check wrapper, and `.coderabbit.yaml`
  still auto-reviewed only `dev`-targeted PRs.
- The dedicated `sign-modules.yml` workflow emitted a different required check name casing than the
  orchestrator.

**Status:** ✅ TDD workflow confirmed for CI/check semantics hardening.

## Pre-Implementation Test Failure (Expected)

### Test Run: 2026-03-30 - Legacy actionlint wrapper fallback

**Command:**

```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/ci-02-trustworthy-green-checks
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata \
  hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py -q -k actionlint_runner
```

**Result:** ✅ 1 test failed as expected before implementation.

**Failure summary:**

- `scripts/run_actionlint.sh` returned success immediately after `docker run`, so a missing Docker
  daemon could silently bypass workflow lint instead of falling back to the local binary path.

**Status:** ✅ TDD workflow confirmed for legacy actionlint fallback hardening.

## Post-Implementation Test Success

### Test Run: 2026-03-30 - Trustworthy green-check remediation slice

**Commands:**

```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/ci-02-trustworthy-green-checks
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata \
  hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py tests/unit/scripts/test_pre_commit_smart_checks_docs.py tests/unit/scripts/test_pre_commit_code_review.py tests/unit/scripts/test_doc_frontmatter/test_validation.py tests/integration/scripts/test_doc_frontmatter/test_integration.py -q
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata \
  hatch run specfact code review run --json --out .specfact/code-review.json tests/unit/workflows/test_trustworthy_green_checks.py tests/unit/scripts/test_doc_frontmatter/test_validation.py
```

**Result:** ✅ Targeted tests passed and the changed-file SpecFact review reported `PASS` with `0` findings.

**Passing summary:**

- `pr-orchestrator.yml` now triggers on every PR head commit, uses explicit required versus
  advisory gate naming, fails required jobs closed, and runs a dedicated workflow-lint gate.
- `dev -> main` release validation no longer uses a branch-only shortcut; the skip path now
  requires an explicit commit-parity proof and otherwise reruns the required validation set.
- `.pre-commit-config.yaml` now exposes the supported smart-check wrapper and `.coderabbit.yaml`
  covers both `dev` and `main` PR targets.
- `scripts/run_actionlint.sh` now falls back cleanly when Docker is installed but the daemon is not
  reachable.
- Contributor/docs surfaces now distinguish merge-blocking versus advisory outputs, and the updated
  doc-frontmatter validation tests cover malformed YAML diagnostics.

**Status:** ✅ Remediation implemented and verified for the change surface.

### Follow-up verification: 2026-03-30T22:42:42+02:00 - actionlint install strategy cleanup

**Commands:**

```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/ci-02-trustworthy-green-checks
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata \
  hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py -q
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata \
  hatch run type-check
```

**Result:** ✅ Follow-up workflow tests passed and type-check remained green after removing repo-local
`actionlint` downloads.

**Passing summary:**

- `scripts/run_actionlint.sh` now prefers a globally installed `actionlint`, then Docker when the
  daemon is reachable, and otherwise exits with explicit install guidance instead of downloading
  into the repository tree.
- `scripts/yaml-tools.sh` now delegates workflow linting to the same runner, so local and CI paths
  share a single source of truth.
- `pr-orchestrator.yml` now installs a pinned `actionlint` release in CI before running
  `hatch run lint-workflows`, so GitHub Actions does not rely on Docker availability for this gate.

**Status:** ✅ Actionlint installation strategy aligned with repo expectations and re-verified.
