---
layout: default
title: Dependency Trust Security Review
permalink: /technical/dependency-trust-security-review/
description: Security findings, earlier control gaps, and remediation evidence for the reproducible-delivery change.
---

# Dependency Trust Security Review

This record preserves the security findings reviewed for pull request #652 on
2026-07-24 (Europe/Berlin). It is written as factual source material for a
future public post; it does not claim that an alerted package was malware.

## Findings and scope

### CSD-DEP-001 — Medium

- **Finding:** The shared frozen-environment action synchronized dependencies before
  checking the trust register.
- **Effect before remediation:** A changed lock could install or build a dependency
  before the policy rejected it.

### CSD-DEP-002 — Medium

- **Finding:** Review URL and SHA-256 evidence was searched across the entire lock
  file.
- **Effect before remediation:** Evidence from a different package record could
  satisfy a reviewed exception.

### CSD-DEP-003 — Medium

- **Finding:** The executable-wheel denylist did not normalize package names
  consistently.
- **Effect before remediation:** Case, underscore, or dot variants could evade the
  denylist.

Two defence-in-depth opportunities were also found and are remediated here:

- `tools/run_basedpyright.sh` resolved the committed Node runner relative to the
  caller's current directory, so an untrusted working directory could shadow it.
- The frozen-delivery refresh script could follow a repository-controlled
  symlink at its output path.

The review also examined the `source-provenance-reviewed` label. That label is
maintainer review evidence, not an automated proof of an upstream source
repository. It was classified as a policy limitation rather than a reachable
lower-privilege bypass; the register remains restricted, expiring, and bound to
the exact frozen artifact.

## What earlier controls missed

The preceding change removed the Socket-alerted `cyclonedx-bom` dependency,
blocked the alerted `pycparser==3.0` release, and added an expiring review
register for the pinned `pycparser==2.22` artifact. Those controls checked the
right inputs but did not yet prove their ordering, record-level binding, or
canonical identity handling. They also did not cover the two local-path safety
boundaries above.

No review record was used to waive an alert. `cyclonedx-bom` was removed from
the delivery path; existing warnings remain subject to explicit policy and
expiry checks.

## Remediation and proof

The remediation makes the standard-library trust checker run before every
shared `uv sync`, parses `uv.lock` structurally, binds each review URL and
digest to the matching package record, and canonicalizes package names using
the Python package-name normalization rule. The type runner derives its
repository location from its own script path, and refresh writes through a
safe temporary file after rejecting symlinked output paths.

The reviewed lock now pins Semgrep `1.175.0`; there is no older Semgrep lock entry.
The exact hash-protected export is audited with `pip-audit --strict` and every
unreviewed advisory fails locally and in CI. The compatible fixes raised Click
to `8.4.2`, Setuptools to `83.0.0`, Typer to `0.27.0`, and Semgrep to `1.175.0`.
A checked-in minimum floor prevents a Semgrep downgrade below `1.175.0`.

The audit previously found three MCP advisories introduced only by the opt-in
static-analysis and development-tool Semgrep graph. Semgrep 1.175.0 now
publishes an exact
`mcp==1.29.0` dependency, above all three advisory fix floors. The frozen lock
and export use that pair, and the obsolete MCP exception has been removed.
Neither Semgrep nor MCP is declared in the base `specfact-cli` wheel
dependencies, so ordinary runtime installs remain unchanged. A separate
checked-in `mcp>=1.28.1` floor prevents a consistently edited lock/export from
restoring any of those advisory-affected releases before the audit runs. Any
future security-tool downgrade, new advisory, or unreviewed exception fails
before install.

Dependabot opens weekly patch/minor Python update pull requests. It does not
silently mutate a merged lock: each candidate remains subject to frozen-export,
security-audit, and compatibility checks before review and merge.

Regression tests cover a cross-record URL/digest bypass, a mixed-separator
denylist bypass, pre-install ordering, runner shadowing, and an unsafe refresh
output path. The exact commands and results are retained in the OpenSpec change's
`TDD_EVIDENCE.md` artifact.

## Remaining limits

These controls validate the checked-in lock and explicit exceptions. They do
not independently establish an upstream package's source provenance, and they
cannot prove absence of malicious behavior in any dependency. The remaining
mitigations are reviewed lock changes, short exception expiry, dependency
alerts, reproducible builds, and human security review. The MCP exception is
no longer a residual exception because the reviewed Semgrep/MCP pair is fixed
in the frozen dependency set; future advisory or provenance risk remains
subject to the same lock review and audit controls.
