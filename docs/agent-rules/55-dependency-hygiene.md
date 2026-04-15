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
  - modules/*/module-package.yaml
  - src/specfact_cli/modules/*/module-package.yaml
  - scripts/check_license_compliance.py
  - scripts/license_allowlist.yaml
  - SECURITY.md
last_reviewed: 2026-04-15
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
`pip_dependencies` list without a `module-manifest`-scoped entry in
`scripts/license_allowlist.yaml`.

Rationale: `pip_dependencies` in module manifests are installed on end-user
systems via `specfact module install`. Force-installing GPL software constitutes
a license violation under Apache-2.0 and blocks enterprise/commercial adoption.

**Action on violation:** Remove the GPL package, run `hatch run license-check`,
and propose a MIT/Apache-2.0/BSD alternative.

## 2. (A)GPL in dev env extras (MUST DOCUMENT + PHASE 2 PLAN)

GPL packages in dev-only extras (e.g. `pylint`) require:

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

## 4. Required gates before any manifest or dependency change is merged

Run these in order:

```bash
hatch run license-check   # scripts/check_license_compliance.py — exit 0 required
hatch run security-audit  # pip-audit --desc --strict — review CVEs ≥ CVSS 7.0
hatch run bandit-scan     # bandit -r src/ -ll — review and document findings
```

## 5. New pip_dependencies in module manifests — checklist

Before adding a new `pip_dependencies` entry to any `module-package.yaml`:

1. Check the package license on PyPI (`pip show <pkg>` or PyPI JSON API).
2. Verify the license is in the Approved column above (Section 3).
3. If LGPL: document subprocess invocation in `license_allowlist.yaml`.
4. Run `hatch run license-check` — must exit 0.
5. Re-sign the module manifest (`hatch run sign-modules`).
6. Run `hatch run verify-modules-signature` (strict bundle from `module-verify-policy.sh`) — must pass.

## 6. Phase 2 tracking

| Package | Current status | Phase 2 action |
| --- | --- | --- |
| `pylint` | dev-only (GPL-2.0-or-later) | Replace with `ruff --select ALL` once SLF001/W0212 and R0801 gaps are resolved |
| `gitpython` | runtime (CVE history) | Replace with `dulwich` adapter (3-file rewrite) |

## 7. Static license map

`check_license_compliance.py` uses a static license map for known module
pip_dependencies to avoid network calls. If you add a new manifest dependency
that is not in the map, the gate will warn (not fail) and flag it for manual
review. Add it to `_STATIC_LICENSE_MAP` in the script.
