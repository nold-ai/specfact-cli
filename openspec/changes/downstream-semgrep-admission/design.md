# Design: downstream Semgrep build and admission

## Decision

Use one standard-library artifact owner under scripts. Candidate build/validation
and protected production admission are separate operations. The implementation PR
must not install an unadmitted candidate into the ordinary project environment or
claim that the existing frozen MCP audit is green. Protected publication/adoption
requires subsequent human-controlled integration; no merge is part of this task.

## Synthesis decision

Three independent architecture candidates were compared against trust bootstrap,
closed failure modes, frozen/audit coverage, real matrix verification and interface
depth. The independent judge selected candidate A. Retain A's single preinstall
identity boundary and real lifecycle tests; graft B's reviewed output hashes.
Do not add a new hosting/provider surface or a second production route. Candidate
artifacts may be retained by CI but are never protected producer evidence.

## Caller contracts

PR validation caller (unprivileged, disposable environment):

```python
from scripts.downstream_semgrep import aggregate_candidate_reports, build_candidate, verify_candidate

candidate = build_candidate(recipe_path, upstream_wheel, output_directory)
verified = verify_candidate(recipe_path, upstream_wheel, candidate.path)
assert verified.sha256 == candidate.sha256
summary = aggregate_candidate_reports(recipe_path, cell_reports)
assert summary["status"] == "passed"
assert summary["production_admission"] == "not_requested"
```

Production setup caller, before any project dependency installation:

```python
from scripts.downstream_semgrep import admit_artifact

admitted = admit_artifact(wheel, evidence_bundle)
with admitted.materialize() as verified_wheel:
    install_frozen_environment(verified_wheel, locked_requirements)
```

Existing audit caller, after admission verification and before accepting findings:

```python
audit_input = admitted.audit_input(requirements_file, audit_output)
result = run_existing_strict_audit(audit_input.requirements)
audit_input.assert_complete_result(result)
# Report original Semgrep local identity + mapped upstream + actual MCP identity.
```

The production CLI has no `--allow-untrusted`, `--skip-provenance`, candidate flag, or caller-selected trust root. Candidate validation is a separate entry point and result type. Its passing result cannot be supplied to production admission.

## Types and signatures

Sketch only; bodies raise `NotImplementedError`. Serialized dictionaries and attestation transport objects are parsed inside the core. Opaque production objects are created only by boundary functions; private constructors prevent accidental use, not a security sandbox against hostile Python.

```python
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlatformWheel:
    filename: str
    platform_tag: str
    upstream_sha256: str
    upstream_url: str


@dataclass(frozen=True)
class Recipe:
    upstream_version: str
    downstream_version: str
    mcp_from: str
    mcp_to: str
    wheels: tuple[PlatformWheel, ...]
    python_versions: tuple[str, ...]
    build_runtime_digest: str


class CandidateWheel:
    # Private validated constructor; path, digest, recipe digest, platform.
    ...


class TrustedPolicy:
    # Obtained from the protected verifier's immutable configuration only.
    ...


class AdmittedWheel:
    # Private constructor; exact digest + provenance + policy binding.
    def materialize(self) -> AbstractContextManager[Path]:
        raise NotImplementedError

    def audit_input(self, actual_requirements: Path, output: Path) -> BoundAuditInput:
        raise NotImplementedError


class BoundAuditInput:
    requirements: Path

    def assert_complete_result(self, result: AuditResult) -> None:
        raise NotImplementedError


def build_candidate(recipe_path: Path, upstream_wheel: Path, output_directory: Path) -> CandidateWheel:
    raise NotImplementedError


def verify_candidate(recipe_path: Path, upstream_wheel: Path, candidate_wheel: Path) -> CandidateWheel:
    raise NotImplementedError


def required_matrix(recipe_path: Path) -> list[dict[str, str]]:
    raise NotImplementedError


def aggregate_candidate_reports(recipe_path: Path, reports: list[dict]) -> dict:
    raise NotImplementedError


def admit_artifact(wheel: Path, evidence_bundle: Path) -> AdmittedWheel:
    raise NotImplementedError
```

The core validates version grammar, exact identities, unique platforms, complete matrix, hashes, metadata cardinality, record format and provenance at entry. Validated values then flow without repeated caller checks. Public surface hides ZIP and evidence schemas, audit transformation and policy evaluation. Existing gate scripts retain their current entry points.

## Installation identity lifetime

Admission owns an immutable byte snapshot. Approval, archive verification and
provenance verification must authenticate that same snapshot, materialized under
the original wheel basename in a private directory owned by the trusted process.
The original caller path is transport input only and is never returned as install
authority. No production install API is introduced by this change.

`materialize()` writes the retained bytes into a fresh private directory, yields
its real Path for the full synchronous install, and removes it on normal or
exceptional exit. In-place source overwrite without unlinking, source replacement,
deletion or symlink substitution after admission cannot change these bytes.
A retained hard link alone is insufficient because an in-place write can preserve
the source inode while changing its bytes. The overwrite regression asserts that
the device and inode remain unchanged and both later materializations retain the
approved bytes, including normal and exceptional cleanup. Admission must preserve the existing during-admission replacement rejection,
including its current error message. The unchanged
`test_admission_rejects_candidate_replacement_after_protected_digest` regression
from the implementation source must be restored with implementation. Audit
binding uses the retained approved digest, never rereads the original transport path. A caller must finish all wheel
reads before leaving the context. Child processes must be joined inside it.

The trust assumption is that the installer, Python process, its account, and its
private temporary storage are trusted. This is not isolation from a hostile
same-account process, privileged attacker, compromised installer or mutable
mount under their control. Unix permission bits alone do not prove Windows ACL
isolation; platform tests must establish private storage behavior or fail closed.
Hash rechecks and pip hash flags are not an atomic path-to-install guarantee.
No claim is made that an arbitrary third-party installer opens a path atomically.

## Trust and scope

The recipe is the sole source of wheel/platform and Python matrix inputs. It binds
upstream Semgrep 1.179.0, downstream 1.179.0+specfact.1 and MCP 1.30.0. Build output
hashes are independently reviewed facts; production admission never generates its
own expected hash. Archive equivalence includes complete RECORD verification,
permissions, executable payload, entry points and unchanged license notices.

Production uses an independent protected policy source, never a caller-selected
PR policy. It binds exact repository, protected source commit, signer workflow,
recipe, output hashes, complete matrix proof and expiry. Verify provenance before
interpreting claims. Tool absence, API failure, PR-origin/ref, stale policy and
unknown identities reject. There is no allow-untrusted or skip-provenance switch.
The initial production admission register is empty. Existing provider/capsule
catalogs and signature keys are not modified or reused for downstream identity.

All active actual package identities remain visible. Only an admitted exact
Semgrep artifact may query its authenticated upstream code identity. Every other
actual dependency, including fixed MCP, is audited without upstream re-resolution.
The response must cover every requested identity exactly once. Empty/malformed
skip records, missing/extra/duplicate packages, changed versions, service failures
and advisories fail. No vulnerability exception is added. Production adoption,
floor/lock refresh and frozen setup changes remain blocked until protected
artifacts exist; isolated candidate audits are labeled candidate evidence.

## Platform and MCP verification

Generate 21 cells from seven reviewed wheel platforms and Python 3.11–3.13.
Native macOS x86_64/arm64, Windows AMD64 and Linux glibc/musl x86_64/arm64 must
actually install and execute. Native musl containers on matching native Linux
hosts are valid; emulation or tag-only downloads are not execution proof. Record
actual OS, architecture, libc, interpreter, wheel hashes and installed graph.
Missing, duplicate, failed or skipped cells reject aggregate admission.

Use clean hashed installs with normal resolution and pip check. Preserve the
existing SAST rules, findings/error behavior and positive/negative controls.
Drive actual SDK ASGI lifespan and HTTP initialization, tool requests, DELETE,
short configured idle expiry, small capacity, refused openings and shutdown.
Check production defaults independently. Semgrep CLI/stdio integration must
remain functional. Deterministic OAuth discovery in a bounded protocol test may
not disable credential validation or substitute for an actual integration run.

## Risks and rollback

Protected bootstrap cannot be completed by trusting this unmerged PR. Candidate
verification may finish while production admission and the original MCP audit
remain blocked. Removing/expiring admission blocks installation again. Restoring
the vulnerable original pins is not a release-ready rollback. Matrix runtime and
CI cost are unmeasured; all 21 cells and ordinary quality/native/FULL proof remain
required. Artifact transport/frozen materialization is not considered proven until
actual cross-platform experiments pass.

## Implementation contract reconciliation (2026-10-16)

The root architect selected explicit candidate verification and matrix operations
instead of the earlier generic validation sketch. Production admission takes no
caller-selected policy: its private loader reads the canonical protected dev
policy at an immutable freshly resolved source commit. The initial register is
empty. Evidence is a directory containing recipe.json, matrix.json,
provenance.jsonl and the exact original wheel under upstream/. Protected approval
binds recipe/matrix SHA-256, source/signer commit, dates and exact wheel identities.
The trusted attestation verifier enforces repository, signer workflow/digest,
protected source ref/digest, OIDC issuer and hosted runner identity. Plain claims
inside the predicate do not establish these facts.

The first audit input contract accepts a complete active per-cell flat hashed
inventory; unsupported markers/options reject rather than being guessed. Bound
result reconciliation rejects every unknown, skipped, missing, duplicate,
malformed, vulnerable or nonzero result. This operation is not wired into normal
frozen delivery until independently protected artifact adoption is available.

## Native report boundary

The shared standard-library boundary owns private pure validation of runtime
identity and command-record shapes. The candidate driver collects these values;
aggregation independently validates them before producing a passing summary.
Protected admission reuses the same aggregate boundary.

The runtime claim contains system, machine, full Python version, executable path
and SHA-256, sysconfig platform and a two-string libc record. OS, architecture
aliases, Python minor and Linux libc compatibility are checked against the cell.
macOS and Windows empty libc strings, musl `Version 1.2`, and macOS universal2
sysconfig values remain legitimate producer formats. The aggregate does not
inspect its own host executable or require exact sysconfig/wheel-tag equality.

Command records require argv, an integer return code excluding booleans, and
stdout/stderr SHA-256 values. The executable argument is nonempty; later arguments
may be empty. Nonzero detection-control exits remain valid evidence data. The
driver retains responsibility for checking each invocation's expected outcome.
No new command-label policy or interpreter-version pin is introduced.

The existing dictionary boundary needs validation rather than a second parsed
report model. One private validator in `scripts/downstream_semgrep.py` is reused
by the driver and consumer. A separate schema module or dataclass conversion layer
adds no current consumer. This is the synthesis of the three architecture reviews.

These checks establish completeness and consistency. They do not authenticate
a producer, prove command execution or verify unavailable log bytes. Exact source,
recipe, artifact, protected-policy and provenance controls remain required.
Faithful synthetic positive fixtures are authored before the new hosted RED source
is frozen. Additional schema regressions remain separate from the accepted
85-case execution plan.
