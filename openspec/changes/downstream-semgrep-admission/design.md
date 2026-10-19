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
from downstream_semgrep import aggregate_candidate_reports, build_candidate, verify_candidate

candidate = build_candidate(recipe_path, upstream_wheel, output_directory)
verified = verify_candidate(recipe_path, upstream_wheel, candidate.path)
assert verified.sha256 == candidate.sha256
matrix = aggregate_candidate_reports(recipe_path, native_reports)
assert matrix["status"] == "passed"
assert matrix["production_admission"] == "not_requested"
```

Production setup caller, before any project dependency installation:

```python
from downstream_semgrep import admit_artifact

admitted = admit_artifact(wheel, evidence_bundle)
install_frozen_environment(admitted.wheel, locked_requirements)
```

Existing audit caller, after admission verification and before accepting findings:

```python
audit_input = admitted.audit_input(requirements_file, audit_output)
result = run_existing_strict_audit(audit_input.requirements)
audit_input.assert_complete_result(result)
# Report original Semgrep local identity + mapped upstream + actual MCP identity.
```

Archive verification returns `CandidateWheel`. The native driver separately
executes functional checks and collects `native_reports`; aggregation validates
their complete matrix and returns a dictionary. Neither result grants production
authority.

The production CLI has no `--allow-untrusted`, `--skip-provenance`, candidate flag, or caller-selected trust root. Candidate validation is a separate entry point and result type. Its passing result cannot be supplied to production admission.

## Types and signatures

The following public signatures match `scripts/downstream_semgrep.py`. Bodies and
private authority fields are omitted. `_Recipe` and `_Wheel` are private parsed
values; policy and native reports are validated dictionaries. There is no public
recipe, policy or functional-report class. Boundary functions construct the
frozen candidate, admission and audit objects. Their private authority fields
prevent accidental use, not hostile Python code execution.

```python
class CandidateWheel:
    path: Path
    sha256: str
    platform: str
    recipe_sha256: str

    def candidate_audit_input(self, actual_requirements: Path, output: Path) -> BoundAuditInput: ...


class AdmittedWheel:
    wheel: Path

    def audit_input(self, actual_requirements: Path, output: Path) -> BoundAuditInput: ...


class BoundAuditInput:
    requirements: Path
    actual_inventory: Mapping[str, str]

    def assert_complete_result(self, proc: subprocess.CompletedProcess[str]) -> dict[str, object]: ...


def build_candidate(recipe_path: Path, upstream_wheel: Path, output_directory: Path) -> CandidateWheel: ...


def verify_candidate(recipe_path: Path, upstream_wheel: Path, candidate_wheel: Path) -> CandidateWheel: ...


def required_matrix(recipe_path: Path) -> list[dict[str, str]]: ...


def aggregate_candidate_reports(recipe_path: Path, reports: list[dict[str, object]]) -> dict[str, object]: ...


def admit_artifact(wheel: Path, evidence_bundle: Path) -> AdmittedWheel: ...
```

The core validates version grammar, exact identities, unique platforms, complete matrix, hashes, metadata cardinality, record format and provenance at entry. Validated values then flow without repeated caller checks. Public surface hides ZIP and evidence schemas, audit transformation and policy evaluation. Existing gate scripts retain their current entry points.

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

The private policy loader reads canonical protected dev policy at an immutable,
freshly resolved source commit. Evidence is a directory containing `recipe.json`,
`matrix.json`, `provenance.jsonl` and the exact original wheel under `upstream/`.
Protected approval binds recipe and matrix SHA-256, source and signer commits,
dates and exact wheel identities. The trusted attestation verifier enforces the
repository, signer workflow/digest, protected source ref/digest, OIDC issuer and
hosted runner identity. Plain predicate claims do not establish these facts.

Admission hashes and parses the same matrix byte snapshot. Both the aggregate
result and candidate verification must retain the initially approved recipe
SHA-256. Reopening a path cannot substitute different approved inputs. The
existing immutable `_Recipe` and validated report dictionaries suffice; a bytes
JSON parser retains the former file reader’s strict UTF-8 and duplicate-key
handling. A new
snapshot framework or public configuration option is unnecessary.

All active actual package identities remain visible. Only an admitted exact
Semgrep artifact may query its authenticated upstream code identity. Every other
actual dependency, including fixed MCP, is audited without upstream re-resolution.
The response must cover every requested identity exactly once. Empty/malformed
skip records, missing/extra/duplicate packages, changed versions, service failures
and advisories fail. No vulnerability exception is added. Production adoption,
floor/lock refresh and frozen setup changes remain blocked until protected
artifacts exist; isolated candidate audits are labeled candidate evidence.
The audit input accepts a complete active per-cell flat hashed inventory;
unsupported markers/options reject. Bound result reconciliation rejects unknown,
skipped, missing, duplicate, malformed, vulnerable or nonzero results.

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
Check production defaults independently by constructing the actual SDK manager
without lifecycle keyword overrides, while retaining signature checks. Semgrep CLI/stdio integration must
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
