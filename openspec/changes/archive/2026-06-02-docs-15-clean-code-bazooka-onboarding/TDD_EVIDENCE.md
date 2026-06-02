# TDD Evidence: docs-15-clean-code-bazooka-onboarding

This file records failing-before and passing-after evidence for the AI-bloat defense first-contact docs and metadata change.

## Failing-before evidence

### 2026-06-02 targeted docs and metadata tests

Command:

```bash
hatch run pytest tests/unit/docs/test_first_contact_story.py tests/unit/docs/test_wow_entrypoint_contract.py tests/unit/docs/test_release_docs_parity.py tests/unit/test_core_docs_site_contract.py tests/unit/scripts/test_code_review_module_docs.py -q
```

Result: failed as expected before docs/metadata implementation.

Summary:

- 48 tests collected.
- 37 passed.
- 11 failed.
- Failures showed the old README/docs hook, missing AI-bloat defense entrypoint wording, missing JSON-first cleanup loop, incomplete Code Review handoff wording, and old "swiss knife" package metadata.

## Passing evidence

### 2026-06-02 targeted docs and metadata tests

Command:

```bash
hatch run pytest tests/unit/docs/test_first_contact_story.py tests/unit/docs/test_wow_entrypoint_contract.py tests/unit/docs/test_release_docs_parity.py tests/unit/test_core_docs_site_contract.py tests/unit/scripts/test_code_review_module_docs.py -q
```

Result: passed.

Summary:

- 48 tests collected.
- 48 passed.

After rebasing onto current `origin/dev` and parameterizing duplicated test shapes found by the
code review helper, the same targeted command passed with 47 collected tests and 47 passed.

### 2026-06-02 OpenSpec validation

Command:

```bash
openspec validate docs-15-clean-code-bazooka-onboarding --strict
```

Result: passed. The change remained valid after expanding scope to docs entry points, package metadata, and GitHub repository metadata.

### 2026-06-02 docs validation

Command:

```bash
hatch run docs-validate
```

Result: passed.

Summary:

- `check-command-contract`: OK, 107 generated command paths validated.
- `check-docs-commands`: OK, 380 unique command prefixes checked.
- `check-cross-site-links`: OK, 26 unique `modules.specfact.io` URLs checked.
- `check_doc_frontmatter`: OK, 17 enforced docs checked.

### 2026-06-02 metadata/version consistency

Command:

```bash
hatch run check-version-sources
```

Result: passed.

### 2026-06-02 formatting

Command:

```bash
hatch run format
```

Result: passed. All files were already formatted; 627 files left unchanged.

### 2026-06-02 rebase onto current dev

Command:

```bash
git fetch origin
git rebase origin/dev
```

Result: passed. The feature worktree was rebased onto the current `origin/dev`.

Notes:

- Git stash/autostash failed silently in this worktree, so tracked changes were preserved through a temporary `/tmp` patch before the rebase and reapplied afterward with `git apply --3way`.
- Rebase conflicts in `docs/getting-started/README.md` and `pyproject.toml` were resolved by keeping the current upstream version `0.47.3` and this change's AI-bloat defense positioning.

### 2026-06-02 SpecFact code review helper

Command:

```bash
hatch run python scripts/pre_commit_code_review.py setup.py src/specfact_cli/__init__.py tests/unit/docs/docs_test_constants.py tests/unit/docs/test_first_contact_story.py tests/unit/docs/test_release_docs_parity.py tests/unit/scripts/test_code_review_module_docs.py tests/unit/test_core_docs_site_contract.py
```

Result: passed.

Summary:

- The helper reviewed the changed Python files for this docs/test scope.
- Initial helper output produced 11 warning findings; clean-code warnings were fixed in touched tests.
- Final helper output: 0 findings, `overall_verdict='PASS'`.

### 2026-06-02 full lint

Command:

```bash
hatch run lint
```

Result: passed after rebasing onto current `origin/dev`.

Summary:

- 627 files already formatted.
- Type check reported 0 errors, 0 warnings, and 0 notes.
- Pylint rated the code at 10.00/10.

## Blocked or failed external gates

### Internal wiki mirror follow-up

The sibling internal checkout exists, but no matching
`/home/dom/git/nold-ai/specfact-cli-internal/wiki/sources/docs-15-clean-code-bazooka-onboarding.md`
page is present. Because this implementation materially expanded the active change scope, follow up
by creating or updating that wiki source page with the current summary, status, dependencies, and
external-deps, then run `python3 scripts/wiki_rebuild_graph.py` from the `specfact-cli-internal`
repository root.

### 2026-06-02 GitHub repository metadata update

Commands attempted:

```bash
gh api -X PATCH repos/nold-ai/specfact-cli -f description='AI-bloat defense CLI for Python teams: deterministic code review, cleanup forecasts, and spec/contract evidence for AI-assisted and brownfield delivery.'
gh api -X PUT repos/nold-ai/specfact-cli/topics -f names[]=ai ...
```

Initial result: blocked by GitHub token permissions.

GitHub returned HTTP 403 `Resource not accessible by personal access token` for both repository description and topics updates. A readback confirmed the live repository still uses the older "Swiss-knife CLI" description and the previous topic set.

Final readback after manual metadata update:

```bash
gh api repos/nold-ai/specfact-cli --jq '{description, homepage, topics}'
```

Result: passed.

- Description matches the planned AI-bloat defense wording.
- Homepage is `https://docs.specfact.io/`.
- Topics match the planned 20-topic set: `ai`, `ai-assisted-development`, `ai-bloat`, `brownfield`, `clean-code`, `code-quality`, `code-review`, `code2spec`, `contract-first`, `contract-testing`, `developer-tools`, `legacy-modernization`, `python`, `requirements-engineering`, `spec-driven-development`, `spec-first`, `static-analysis`, `technical-debt`, `testing`, and `vibe-coding`.

## Before/after docs summary

- README and docs home now lead with AI-bloat defense for AI-assisted Python code.
- Docs README and getting-started entry points now route users through cleanup forecast, AI-bloat index, remediation packets, and rerun proof.
- Quickstart now includes a JSON-first simplify loop.
- Core Code Review handoff now links to modules-owned AI bloat quickstart and Code Review run guide for exact flags/schema.
- Package/docs metadata no longer uses "Swiss-knife" as the primary product identity.
