# Security and dependency evidence: fix-frozen-dependency-security-baseline

## Baseline

- **Date**: 2026-08-26 (Europe/Berlin)
- **Branch base**: `origin/dev@e3a20f20df440dff49f8c6d1f73375451bea1d8c`
- **Released comparison**: `v0.55.1@b1e517e60e669eaba15a18ecfa83ef5a9df65276`
- **Change type**: dependency-only remediation; no runtime behavior/API code.

## Failing-before evidence

### PR #685 unchanged security job

- **Workflow run**: `32895125663`
- **Job**: `97956011305` (`Security Audit (pip-audit)`)
- **Frozen observation**: `pip==26.1.2`
- **Result**: failed on `PYSEC-2026-3721`, alias `CVE-2026-13346`, with the repository's `ACTION REQUIRED` message.
- **Other findings**: three `mcp==1.23.3` advisories matched existing exact `WAIVED` records; they did not cause this failure and are not silently treated as fixed.

### Local reproduction through the same gate

```text
.venv/bin/python scripts/security_audit_gate.py
```

- **Result**: failed on `pip==26.1.2` / `PYSEC-2026-3721` / `CVE-2026-13346` after synchronizing the exact committed lock with `uv sync --locked --all-extras`.
- **Legitimate control**: the frozen environment synchronized successfully and installed `specfact-cli==0.55.1`; the failure occurred in advisory evaluation, not dependency resolution.

## Independent advisory evidence

- The Python Software Foundation CNA record describes incorrect handling of doubly encoded package URLs from malicious indexes, permitting writes outside the intended destination.
- The affected range is every pip version before 26.2; therefore 26.1.2 is vulnerable and 26.2 is the minimum fixed release line.
- The CNA CVSS v4 score is 5.6 (medium). The repository gate correctly remains fail-closed even though the current pip-audit JSON exposed `CVSS=0.0`, because missing score metadata is not evidence of safety.

## Independent security-boundary investigation

- `pip` is absent from core runtime dependencies and enters only through the dev
  `pip-audit -> pip-api -> pip` and `pip-tools -> pip` paths.
- Both `uv.lock` and `requirements/ci/locked.txt` freeze 26.1.2, and different CI
  consumers install each representation; both must move together.
- `uv lock --dry-run --upgrade-package pip` resolved the existing 184-package graph
  with only pip changing from 26.1.2 to 26.2.1, providing pre-edit compatibility
  evidence.
- A lock-only update is not durable because the normal refresh uses ordinary
  `uv lock`; the selected boundary is a `pip>=26.2` floor on the dev extra and
  default Hatch environment, with a test proving pip remains absent from core.
- Default CI uses trusted hashed PyPI artifacts and does not invoke
  `pip download --only-binary`, which limits default exploit exposure but does not
  satisfy the repository's stronger no-unreviewed-advisory invariant.
- Marketplace requirements can carry index options to pip-tools; this is an adjacent
  broader trust concern, not required to fix CVE-2026-13346, and is not expanded into
  this patch.

## Dependabot baseline classification

- **PR #676 / json 2.21.2 / CVE-2026-71847**: duplicate for `dev`; commit `6a81ad32` already updated `docs/Gemfile.lock` to 2.21.2.
- **PR #677 / hatchling 1.32.0**: pending on `main`; explicitly authorized for compatibility-tested consolidation on this `dev` patch.
- **PR #678 / setuptools 84.x constraint**: pending on `main`; explicitly authorized for compatibility-tested consolidation on this `dev` patch.

## GitHub alert inventory boundary

- GitHub issue/PR, Dependabot-alert, CodeQL-alert, and secret-scanning metadata was
  refreshed through authenticated read-only API calls. Native issue metadata for
  #686 is verified as type Bug, project #1 status Todo, with no parent, blocked-by,
  blocking, or sub-issue relationships.
- Dependabot reports seven open alerts. Alert #33 (`json` / CVE-2026-71847) is
  already safe on `dev`: `docs/Gemfile.lock` contains 2.21.2 from commit `6a81ad32`;
  the alert and PR #676 remain open only because GitHub scans `main`. Alerts #7-#12
  are duplicate lock/export instances of three vulnerable `mcp==1.23.3`
  advisories. They remain covered by the existing exact, expiring exception and
  subprocess-only mitigation; Semgrep still pins that MCP version. This patch does
  not dismiss them or claim they are fixed.
- CodeQL reports 24 open alerts (#25-#48), all duplicate instances of
  `actions/cache-poisoning/poisonable-step` on `main`. The reported checkout value
  is not dispatch/user input: it is the immutable 40-hex commit in the trusted
  default-branch `ci/module-fixture.lock.json`. The locked commit exists in the
  organization-owned modules repository and its tree exactly matches the recorded
  tree; workflows verify the checked-out commit/tree before execution. Under the
  current trust boundary these are scanner false positives/irrelevant to this
  dependency patch, not evidence of an untrusted cache writer. They remain open and
  were not dismissed.
- Secret scanning returns zero alerts. This is an authenticated current result, not
  an inference from an unavailable endpoint.

## Focused failing policy tests

```text
UV_CACHE_DIR=<UV_CACHE> .venv/bin/pytest \
  tests/unit/scripts/test_reproducible_delivery.py::test_reproducible_delivery_wheel_build_uses_a_locked_backend \
  tests/unit/scripts/test_reproducible_delivery.py::test_reproducible_delivery_pins_patched_pip_to_tooling_only -q
```

- **Result**: exit 1; 2 failed.
- **Expected failures**: build backend remained Hatchling 1.31.0, and the dev/Hatch
  dependency lists lacked `pip>=26.2`.
- **Control**: the new test already verified the current core project dependency list
  and `setup.py` remained pip-free before reaching the expected missing-floor assertion.

### pip 26.2 compatibility failure and control

- PR #687's unrestricted Linux Python 3.11/3.12 and macOS runtime-discovery jobs
  reproduced a second boundary failure: frozen `pip-tools==7.6.0` called
  `RequirementCommand.make_requirement_preparer()` without pip 26.2's required
  `allow_editables` argument, so marketplace module dependency resolution failed.
- Upstream pip-tools PR #2438 implements pip 26.2 compatibility and was released in
  pip-tools 7.6.1. An isolated `pip-compile --dry-run` reproduction with exactly
  `pip==26.2.1` and `pip-tools==7.6.1` passed before the repository constraint changed.
- The focused policy test now requires `pip-tools>=7.6.1` on both development-tooling
  surfaces while retaining the same pip-free core-runtime control.

## Requirements review and exact test plan

- The pinned modules fixture accepted `requirements-evidence.yaml` at planned
  maturity with mapping digest
  `sha256:2427e6f7714704f30deee0316c8d6ecbe2a82a2ec3a82a20537d7b0402548126`.
- The issue #686 product-owner acceptance record is bound to that exact digest;
  stale or modified mappings fail closed.
- The staged `test-authored` gate passed with the two exact pytest selectors for
  the patched tooling-only pip floor and Hatchling/Twine publication boundary.
- Signed red-only commit `4bdbcbef` ran those selectors in PR #688 workflow
  `33009793444`: both failed for the intended missing constraints, and GitHub
  retained Requirements evidence artifact `9622042446` before any governed
  production path entered the branch.

## Passing-after evidence

### Combined delivery necessity

- Live PR #690 checks passed every pipeline gate except the repository-wide
  Security Audit, which correctly failed on the `dev` baseline's validated
  `pip==26.1.2` advisory. PR #688 contained the fixed graph but could not pass the
  released Requirements producer repaired by #690.
- The signed #686 red/green commits are therefore preserved as a merge parent in
  #690. No commit, alert, or security gate is waived or rewritten; #688 remains
  as comparison evidence until the combined PR is green.
- Native `openspec archive` finalized this completed dependency change and applied
  its delta to the canonical `dep-license-gate` specification. That leaves #689 as
  #690's single active externally authorized producer-repair plan without changing
  the generic multi-change rejection behavior. The independent Security Audit
  continues to prove both frozen dependency graphs and is the terminal authority
  for the dependency CVE.

### Frozen dependency result

- `uv lock --upgrade-package pip --upgrade-package hatchling --upgrade-package setuptools`
  resolved 184 packages and changed only pip 26.1.2 -> 26.2.1, Hatchling
  1.31.0 -> 1.32.0, and Setuptools 83.0.0 -> 84.0.0. Hatchling 1.32 adds
  an edge to the already-resolved direct development dependency `tomlkit`.
- The later publication compatibility solve changed only Twine 6.2.0 -> 7.0.0;
  the final graph still contains 184 packages.
- The final runtime compatibility solve changed only pip-tools 7.6.0 -> 7.6.1;
  the final graph still contains 184 packages. The runtime-discovery smoke then
  installed all three marketplace modules successfully with pip 26.2.1.
- `scripts/refresh_reproducible_delivery.py` regenerated the hash-protected
  `requirements/ci/locked.txt` export and reported the delivery inputs valid.
- `uv sync --locked --all-extras` installed the exact final graph and
  `specfact-cli==0.55.2`.
- The focused two-test proof passed, followed by all nine tests in
  `tests/unit/scripts/test_reproducible_delivery.py`.

### Publication compatibility red/green proof

- The first no-isolation Hatchling 1.32.0 wheel contained Core Metadata 2.5;
  frozen Twine 6.2.0 rejected it with `InvalidDistribution`.
- An initial compatibility experiment added a Core Metadata 2.4 override. The
  user requested evaluation of the newer security-fixed publication client, so
  the final OpenSpec scenario instead requires Twine 7 and forbids that override.
- Before the Twine constraint changed, the focused policy test failed because
  `twine>=7.0` was absent. A no-write targeted solve showed Twine 6.2.0 to 7.0.0
  as the only additional resolved-package change.
- After adding the development-only Twine 7 floor and refreshing the frozen
  export, all nine reproducible-delivery tests passed. A no-isolation build
  produced `specfact_cli-0.55.2-py3-none-any.whl`; Twine 7 validation passed and
  inspection confirmed `Metadata-Version: 2.5` and `Version: 0.55.2`. Isolated
  Twine 7 checks of that same wheel passed on Python 3.11 and 3.12, and the
  frozen development environment check passed on Python 3.13.

### Security and frozen-delivery controls

- `scripts/check_reproducible_delivery.py`: pass.
- `uv lock --check`: pass, 184 packages.
- `scripts/security_audit_gate.py`: pass; pip's advisory no longer appears.
  The three existing exact MCP waivers remain visible and unchanged.
- The final audit includes Twine 7.0.0 and reports no new unreviewed finding.
- License gate: 143 packages, zero violations; existing documented yamllint
  exception and three manual-review warnings remain.
- Bandit: zero findings and zero scanner errors.
- Semgrep SAST: six rules over 296 targets, zero findings; baseline gate pass.
- Dependency-trust register: valid.
- Strict module-signature verification: four manifests verified.
- BasedPyright JSON authority: 649 files, zero errors (1,657 existing warnings).
- Version sources: synchronized at 0.55.2; strict PyPI check confirms 0.55.2 is
  ahead of the published 0.55.1 release.

### Repository quality controls and bounded exceptions

- `hatch run format`: pass, 933 files unchanged.
- `hatch run type-check` and `hatch run lint`: pass with zero errors.
- `hatch run yaml-lint`: wrapper exit 0; it reported only pre-existing errors in
  unrelated Requirements 07/08 OpenSpec YAML, and this patch changes no YAML.
- `hatch run contract-test`: exit 0; no modified contract-owned source detected.
- The full smart-test run collected 3,023 tests and produced 3,011 passes and
  10 skips. Its two failures were environmental: the restricted run denied the
  temporary runtime smoke's PyPI access and denied an unrelated unisolated test
  write to `~/.specfact/metadata.json`. The runtime smoke passed separately with
  its temporary module environment and network access; the six companion-module
  tests that failed before `SPECFACT_MODULES_REPO` was supplied also passed.
  Protected-branch CI remains the authority for the unrestricted full-suite gate.
- Fresh full SpecFact review: exit 0, no errors, 678 repository-wide advisory
  findings outside this patch. Full-enforcement review of the only changed Python
  test file: exit 0; its sole advisory points to an unchanged 45-line SBOM test,
  while the new security tests have zero findings. Refactoring that existing test
  or the repository-wide advisory backlog is an explicit scope exception because
  it is unrelated to this dependency-only patch and would violate the smallest-fix
  constraint.

## PR review P1: live-index-independent isolated lock verification

- **Finding**: PR #690 discussion `r3867892984` correctly identified that
  `verify_code_review_lock()` re-resolved the exact Pylint input against the current
  package index without constraining transitive versions. An independent reproduction
  resolved `platformdirs==4.11.3` at the historical cutoff and `4.11.4` from the same
  unchanged input after that compatible release was published.
- **Specification first**: the canonical and archived `dep-license-gate` specifications
  now require the committed isolated lock to constrain parity verification while direct
  input changes continue to fail closed.
- **Failing-before command**:
  `python -m pytest tests/unit/scripts/test_reproducible_delivery.py::test_code_review_lock_verification_constrains_live_resolution -q`
  failed because the compile command contained no `--constraints` argument.
- **Candidate bypass review**: constraints alone preserved the lock for a compatible
  input widening from `pylint==4.0.7` to `pylint>=4`. Four additional red cases proved
  that missing, malformed, duplicate, and mismatched input bindings were not rejected.
- **Fix**: the committed lock metadata now binds the exact `requirements.in` bytes by
  SHA-256. The verification-only `uv pip compile` command supplies the same lock through
  `--constraints` and does not request upgrades. No dependency version, resolved graph,
  runtime surface, or release metadata changed.
- **Refresh-path red proof**: the independent bypass/regression review showed that a raw
  `uv pip compile` refresh would discard the input binding. The new refresh-render test
  failed before `render_code_review_lock()` existed.
- **Passing-after controls**:
  - All 17 `tests/unit/scripts/test_reproducible_delivery.py` tests passed, including
    constrained unchanged-lock parity, all four invalid-binding cases, and the existing
    stale-render rejection.
  - `python scripts/refresh_reproducible_delivery.py --code-review` atomically regenerated
    the real isolated lock, renewed its exact input binding, and invoked the verifier
    successfully.
  - `python scripts/check_reproducible_delivery.py` passed against the real committed
    inputs and package index.
  - A constrained real compile remained byte-equivalent to the committed lock after
    generated headers were removed.
  - Changing the direct input to `pylint==4.0.6` while retaining the committed
    `pylint==4.0.7` constraints failed as unsatisfiable, proving intentional input drift
    is not silently accepted.
  - A compatible widening to `pylint>=4` and adding an already-transitive direct input
    are rejected by the exact input digest before resolution.
