# TDD Evidence: docs-03-command-syntax-parity

## Existing Syntax-Parity Evidence (2026-03-18)

### Pre-Implementation Failing Run

**Timestamp**: 2026-03-18

**Command**:
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-03-command-syntax-parity
hatch test -- tests/unit/docs/test_release_docs_parity.py -v -k "removed or current"
```

**Result**: 9 FAILED, 3 PASSED

**Failure summary**:

- removed syntax families still appeared in authored docs
- command reference still reflected stale grouped-command mappings

### Post-Implementation Passing Run

**Timestamp**: 2026-03-18

**Command**:
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-03-command-syntax-parity
hatch test -- tests/unit/docs/test_release_docs_parity.py -v
```

**Result**: 21 PASSED

That earlier work established the command-syntax parity baseline for the change.

## Front-Matter Integrity Follow-Up (2026-03-20)

### Pre-Fix Failing Run

**Timestamp**: 2026-03-20T10:45:52+01:00

**Command**:
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-03-command-syntax-parity
PATH=/home/dom/git/nold-ai/specfact-cli/.venv/bin:$PATH \
PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-03-command-syntax-parity/src \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/python -m pytest tests/unit/docs/test_release_docs_parity.py -q
```

**Result**: 1 FAILED, 21 PASSED

**Failure summary**:

- new docs integrity coverage showed 41 published Markdown pages under `docs/` missing Jekyll front matter
- missing pages included architecture deep dives, examples, prompts, technical docs, and multiple guide/reference pages

### Post-Fix Passing Run

**Timestamp**: 2026-03-20T10:45:52+01:00

**Command**:
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-03-command-syntax-parity
PATH=/home/dom/git/nold-ai/specfact-cli/.venv/bin:$PATH \
PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-03-command-syntax-parity/src \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/python -m pytest tests/unit/docs/test_release_docs_parity.py -q
```

**Result**: 22 PASSED

**Verification summary**:

- command-syntax parity checks pass
- core/modules docs split checks pass
- canonical modules-site handoff checks pass
- all published Markdown docs now have Jekyll front matter
