# TDD Evidence for docs-14-first-contact-story-and-onboarding

## Pre-Implementation Test Failure (Expected)

### Test Run: 2026-03-30 - First-contact story contract

**Command:**

```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-14-first-contact-story-and-onboarding
python3 -m pytest tests/unit/docs/test_first_contact_story.py -q
```

**Result:** ✅ 5 tests failed as expected before the README/docs/contributor rewrite.

**Failure summary:**

- `README.md` did not yet define SpecFact as the validation and alignment layer.
- The README still placed documentation topology before the primary start path.
- The README did not yet provide explicit “choose your path” outcome routing.
- `docs/index.md` did not yet mirror the new first-contact story structure.
- `CONTRIBUTING.md` did not yet document the first-contact hierarchy and required questions.

**Status:** ✅ Failing-first evidence captured before implementation.

## Post-Implementation Passing Validation

### Test Run: 2026-03-30 - First-contact story and docs handoff

**Commands:**

```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-14-first-contact-story-and-onboarding
hatch env create
hatch run format
hatch run type-check
hatch run lint
hatch run contract-test
hatch test --cover -v
python3 -m pytest tests/unit/docs/test_first_contact_story.py tests/unit/test_core_docs_site_contract.py tests/unit/docs/test_release_docs_parity.py -q -k 'first_contact_story or core_landing_page_marks_core_repo_as_canonical_owner or readme_and_docs_index_define_core_and_modules_split'
hatch run yaml-lint
openspec validate docs-14-first-contact-story-and-onboarding --strict
```

**Result:** ✅ The full documented quality-gate sequence passed for this change. `hatch run type-check`
completed with `0 errors` and existing repo-wide test warnings outside this change scope; `hatch run
lint`, `hatch run contract-test`, and `hatch test --cover -v` all completed successfully.

**Passing summary:**

- `README.md` now answers the five first-contact questions in order and leads with the validation and
  alignment story.
- `docs/index.md` mirrors the same story and keeps the core-to-modules handoff explicit.
- `docs/README.md` and `docs/reference/documentation-url-contract.md` now document the intended
  `docs.specfact.io` to `modules.specfact.io` onboarding split.
- `CONTRIBUTING.md` now records the entry-point messaging hierarchy and repo-metadata alignment rule.
- The audited `hatch run type-check` gate was executed and recorded for this change; warnings came
  from pre-existing repo-wide test typing debt rather than the touched first-contact files.
- The remaining local quality gates required by the checklist (`lint`, `contract-test`, and full
  covered tests) were executed and passed before the follow-up review fixes were finalized.
