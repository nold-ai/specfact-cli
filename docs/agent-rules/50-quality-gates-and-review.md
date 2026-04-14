---
layout: default
title: Agent quality gates and review
permalink: /contributing/agent-rules/quality-gates-and-review/
description: Required formatting, typing, contract, review, and signature gates for touched scope.
keywords: [agents, quality, review, contracts, signatures]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - pyproject.toml
  - scripts/check_doc_frontmatter.py
  - scripts/pre_commit_code_review.py
  - scripts/verify-modules-signature.py
  - docs/agent-rules/**
last_reviewed: 2026-04-14
exempt: false
exempt_reason: ""
id: agent-rules-quality-gates-and-review
always_load: false
applies_when:
  - implementation
  - verification
  - finalization
priority: 50
blocking: true
user_interaction_required: false
stop_conditions:
  - required quality gate failed
  - specfact code review findings unresolved
  - module signature verification failed
depends_on:
  - agent-rules-index
  - agent-rules-openspec-and-tdd
---

## Pre-commit order

1. `hatch run format`
2. `hatch run type-check`
3. `hatch run lint`
4. `hatch run yaml-lint`
5. `hatch run contract-test`
6. `hatch run smart-test`

## SpecFact code review JSON

- Treat `.specfact/code-review.json` as mandatory evidence before an OpenSpec change is complete.
- Re-run the review when the report is missing or stale.
- Resolve every finding at any severity unless a rare, explicit exception is documented.
- Record the review command and timestamps in `TDD_EVIDENCE.md` or the PR description when quality gates are part of the change.

## Clean-code review gate

The repository enforces the clean-code charter through `specfact code review run`. Zero regressions in `naming`, `kiss`, `yagni`, `dry`, and `solid` are required before merge.

## Module signature gate

Every change that affects signed module assets or bundled manifests must satisfy verification **before
the change reaches `main`**.

- **Local / feature branches**: pre-commit may run `verify-modules-signature.py` **without**
  `--require-signature` (checksum-only) when only `dev` or a feature branch is checked out — see
  `scripts/pre-commit-verify-modules.sh` and `scripts/git-branch-module-signature-flag.sh`.
- **Before merging to `main` or when validating release readiness**, run strict verification:

```bash
hatch run ./scripts/verify-modules-signature.py --require-signature --enforce-version-bump
```

If verification fails because module contents changed, re-sign the affected manifests and bump the
module version before re-running verification. Note: `verify-modules-signature.py` has **no**
`--allow-unsigned` flag; checksum-only mode is “omit `--require-signature`”. The `--allow-unsigned`
option on **`sign-modules.py`** is only for local test signing.
