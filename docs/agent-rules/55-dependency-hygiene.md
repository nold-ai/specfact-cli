---
layout: default
title: Agent dependency hygiene rules
permalink: /contributing/agent-rules/dependency-hygiene/
description: License compliance, CVE audit, and approved-package rules for module manifests and dev dependencies.
keywords: [agents, dependencies, license, GPL, security, pip-audit, bandit]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - pyproject.toml
  - uv.lock
  - requirements/ci/locked.txt
  - ci/module-fixture.lock.json
  - modules/*/module-package.yaml
  - src/specfact_cli/modules/*/module-package.yaml
  - scripts/check_license_compliance.py
  - scripts/license_allowlist.yaml
  - SECURITY.md
last_reviewed: 2026-07-23
exempt: false
exempt_reason: ""
id: agent-rules-dependency-hygiene
always_load: false
applies_when:
  - implementation
  - verification
priority: 55
blocking: true
user_interaction_required: false
stop_conditions:
  - GPL/AGPL package added to module manifest without allowlist entry
  - license-check gate fails
depends_on:
  - 50-quality-gates-and-review.md
---

## 1. (A)GPL prohibition in module manifests (HARD BLOCK)

**SHALL NOT** add any package with a GPL-2.0, GPL-3.0, AGPL-3.0, GPL-2.0-or-later,
GPL-3.0-or-later, or AGPL-3.0-or-later license to any `module-package.yaml`
`pip_dependencies` list. **There is no allowlist path that permits GPL/AGPL in
distributed module manifests.** The `scripts/license_allowlist.yaml` `module-manifest`
scope exists exclusively for **LGPL** packages invoked as a subprocess (see Section 3,
"CONDITIONAL"); it does not unblock GPL or AGPL licenses.

Rationale: `pip_dependencies` in module manifests are installed on end-user
systems via `specfact module install`. Force-installing GPL software constitutes
a license violation under Apache-2.0 and blocks enterprise/commercial adoption.

**Action on violation:** Remove the GPL package, run `hatch run license-check`,
and propose a MIT/Apache-2.0/BSD alternative.

## 2. (A)GPL in dev env extras (MUST DOCUMENT + PHASE 2 PLAN)

GPL packages in dev-only extras require:

1. A `dev-only`-scoped entry in `scripts/license_allowlist.yaml` with a `reason`.
2. An explicit Phase 2 removal plan in the `reason` field.
3. A comment in `pyproject.toml` at the dependency line.

They are **never** acceptable in module manifests (see Section 1).

## 3. Approved licenses for module manifest pip_dependencies

| License | Approved | Notes |
| --- | --- | --- |
| MIT | YES | Unrestricted |
| Apache-2.0 | YES | Unrestricted |
| BSD-2-Clause / BSD-3-Clause | YES | Unrestricted |
| PSF | YES | Unrestricted |
| LGPL-2.1 / LGPL-3.0 | CONDITIONAL | Allowed when invoked as subprocess (not statically linked); requires `module-manifest` allowlist entry with subprocess justification |
| GPL-2.0 / GPL-3.0 / AGPL | BLOCKED | Never in module manifests; dev-only with allowlist + Phase 2 plan |

## 4. Reproducible dependency inputs (HARD BLOCK)

`uv.lock` and `requirements/ci/locked.txt` are the authoritative frozen inputs for
blocking delivery jobs. They are generated artifacts, not hand-maintained dependency
lists. Any change to `pyproject.toml`, either frozen file, or the frozen CI setup action
MUST include a reviewed refresh and verification:

```bash
hatch run refresh-frozen-delivery
hatch run python scripts/check_reproducible_delivery.py
```

Review the resulting lock diff and the hash-protected export together. Do not use an
unlocked `pip install`, `uv add`, or resolver fallback in a blocking delivery/release
job. A temporary compatibility experiment belongs in the scheduled/manual advisory lane
and cannot replace frozen evidence.

The companion-module fixture at `ci/module-fixture.lock.json` MUST name the exact
repository and a full, reviewed 40-character commit SHA. Never replace it with a branch,
tag, or PR-head lookup; update it only with accompanying validation evidence.

The BasedPyright runner is a separate committed npm lock at
`tools/basedpyright/package-lock.json`. CI SHALL install it with `npm ci --ignore-scripts`
after a SHA-pinned `actions/setup-node` step; do not add a Python wheel that bundles an
unofficial Node runtime. Flagged dependencies that remain necessary require an exact
version, PyPI artifact URL, artifact SHA-256, source-provenance classification, review
date, expiry, and transitive path in `ci/dependency-trust-exceptions.json`. Expiry is
fail-closed: renew the review or remove the package. A release with a security or
obfuscation alert is a block entry, not an exception: the dependency-trust checker rejects
it even if a record exists and verifies each remaining record against `uv.lock`.

`Dependency Trust Gate` runs for every PR; its matching local pre-commit hook runs before
a dependency-input commit. Socket Security's `Project Report` and `Pull Request Alerts`
are required status checks on protected `dev` and `main` branches. Keep both layers: the
native gate prevents known/reviewed artifact drift, while Socket supplies independent
obfuscation and supply-chain analysis.

## 5. Required gates before any manifest or dependency change is merged

Run these in order:

```bash
hatch run license-check   # scripts/check_license_compliance.py — exit 0 required
hatch run security-audit  # audit the frozen requirements; all unreviewed advisories block
hatch run bandit-scan     # bandit -r src/ -ll — review and document findings
```

## 6. New pip_dependencies in module manifests — checklist

Before adding a new `pip_dependencies` entry to any `module-package.yaml`:

1. Check the package license on PyPI (`pip show <pkg>` or PyPI JSON API).
2. Verify the license is in the Approved column above (Section 3).
3. If LGPL: document subprocess invocation in `license_allowlist.yaml`.
4. Run `hatch run license-check` — must exit 0.
5. Re-sign the module manifest (`hatch run sign-modules`).
6. Run `hatch run verify-modules-signature` (strict bundle from `module-verify-policy.sh`) — must pass.

## 7. Phase 2 tracking

| Package | Current status | Phase 2 action |
| --- | --- | --- |
| `yamllint` | dev-only (GPL-3.0-or-later) | Replace with a non-GPL YAML lint path once CI / pre-commit parity is preserved |
| `gitpython` | runtime (CVE history) | Replace with `dulwich` adapter (3-file rewrite) |

## 8. Static license map

`check_license_compliance.py` uses a static license map for known module
pip_dependencies to avoid network calls. The mapping lives in
`scripts/module_pip_dependencies_licenses.yaml` (`licenses:` key, lowercase
package name → SPDX expression).

If you add a new manifest dependency that is not in the map, the gate
will **fail** (not warn) and flag it for review. Update
`scripts/module_pip_dependencies_licenses.yaml` after license review before
the manifest can be merged.
