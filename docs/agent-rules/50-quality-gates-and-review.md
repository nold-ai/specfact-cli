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
  - scripts/module-verify-policy.sh
  - docs/agent-rules/**
last_reviewed: 2026-07-23
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

## Frozen delivery and type-authority gates

When a change touches `pyproject.toml`, `uv.lock`, `requirements/ci/locked.txt`,
`ci/module-fixture.lock.json`, `.github/actions/setup-frozen-python/`, or delivery CI,
run and record these additional gates before finalization:

```bash
hatch run python scripts/check_reproducible_delivery.py
uv lock --check
npm ci --ignore-scripts --prefix tools/basedpyright
bash tools/run_basedpyright.sh --project pyproject.toml --outputjson > /tmp/specfact-basedpyright.json
```

When a dependency input or locked export changes, run the advisory gate against
the committed requirements graph as well:

```bash
hatch run security-audit
```

Every unreviewed advisory blocks the gate. An exception must be exact to the
package, version, and advisory ID, state a mitigation and expiry, and is not a
substitute for upgrading when a compatible release exists. Dependabot proposes
weekly patch/minor updates for review; it does not auto-merge or bypass these gates.

Blocking delivery CI MUST use the checked-in frozen inputs, build the wheel once, and
install the wheel with dependency resolution disabled. The 3.11, 3.12, and 3.13
built-wheel matrix is merge-blocking; scheduled/manual lower-bound and latest-resolution
checks are advisory only. Attach the normalized installed-package and SBOM evidence from
the `Reproducible Delivery Evidence` job to the run artifacts.

`pyproject.toml` is the sole BasedPyright authority. Do not add `pyrightconfig.json` or
invoke BasedPyright without `--project pyproject.toml`; CI JSON results are retained as
the authoritative type-check artifact.

## SpecFact code review JSON

- Treat `.specfact/code-review.json` as mandatory evidence before an OpenSpec change is complete.
- Re-run the review when the report is missing or stale.
- Resolve every finding at any severity unless a rare, explicit exception is documented.
- Record the review command and timestamps in `TDD_EVIDENCE.md` or the PR description when quality gates are part of the change.

## Independent static analysis

Do not treat `specfact code review run` as sufficient security evidence for this repository. The review gate is intentionally self-referential: it is valuable for SpecFact-specific conventions, command-surface expectations, OpenSpec alignment, and local clean-code policy, but it can inherit blind spots from SpecFact itself.

PR validation therefore requires an independent static-analysis check alongside the self-review gate:

- `Independent Static Analysis` runs Semgrep OSS SAST through `hatch run semgrep-sast` and validates results with `hatch run semgrep-sast-gate`.
- Existing Semgrep findings are tracked in `tools/semgrep/sast-baseline.json`; new findings outside that baseline fail CI.
- Bandit runs through `hatch run bandit-scan` and is expected to remain clean for blocking medium/high findings.
- The Semgrep and Bandit artifacts are external evidence and must not be replaced by `.specfact/code-review.json`.

## Clean-code review gate

The repository enforces the clean-code charter through `specfact code review run`. Zero regressions in `naming`, `kiss`, `yagni`, `dry`, and `solid` are required before merge.

## Module signature gate

Every change that affects signed module assets or bundled manifests must satisfy verification **before
the change reaches `main`**.

- **Local / feature branches**: pre-commit runs `verify-modules-signature.py` with
  **`VERIFY_MODULES_PR`** (version bump vs base; **`--skip-checksum-verification`**) when the branch is
  not `main` — see `scripts/module-verify-policy.sh`, `scripts/pre-commit-verify-modules.sh`, and
  `scripts/git-branch-module-signature-flag.sh`.
- **Before merging to `main` or when validating release readiness**, run strict verification:

```bash
hatch run verify-modules-signature
```

CI mirrors this boundary: `pr-orchestrator.yml` uses **`VERIFY_MODULES_STRICT`** for pull requests
targeting `main` and for pushes to `main`; relaxed PR verification is only for development PRs that do
not cross the release boundary.

If verification fails because module contents changed, re-sign the affected manifests and bump the
module version before re-running verification. Note: `verify-modules-signature.py` has **no**
`--allow-unsigned` flag. The `--allow-unsigned` option on **`sign-modules.py`** is only for local test signing.
