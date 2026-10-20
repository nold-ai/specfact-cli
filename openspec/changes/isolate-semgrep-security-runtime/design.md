## Context

Semgrep is a subprocess integration, not a core runtime import. It appears in
project dev/scanning extras and the Hatch environment. Shared CI installs all
extras; the frozen CI export therefore includes Semgrep 1.179.0 and MCP 1.29.0.
The normal resolver cannot select patched MCP 1.30.0 because both current frozen
Semgrep and latest 1.181.0 require exactly 1.29.0.

Core consumers are CodeAnalyzer, OpenAPITestConverter and ReproChecker. CI runs
checked-in SAST rules and scripts/semgrep_sast_gate.py. External Code Review and
generated workflows are additional compatibility surfaces to inventory explicitly.

The first design selected isolated downstream Semgrep. A fresh independent review
found an adoption cycle: #779's unchanged frozen audit fails on MCP, while that
plan prohibited dependency movement before #779 adoption. Its protected-producer
also unconditionally refuses production bootstrap. Merging #779 alone would not
supply production admission. The selected direction is therefore independent
upstream native-scanner replacement investigation, with OpenGrep as a candidate.

## Goals / Non-goals

Remove the incompatible Python Semgrep/MCP lineage without hiding an executed
vulnerable graph. Preserve effective rule coverage, baseline identities, installed
consumer results, complete audit evidence and required authority checks.

This planning PR changes no application, dependency input, version, admission,
exception or baseline. It neither adopts nor closes #772/#779 and does not require
their prior merge. It does not restore retired Code Review capsules, VMs or
protected runtime publication. Trusted-local reset ownership remains unchanged.
There is no production dual-engine fallback or generic scanner plugin framework.

## Usage and organizing shape

One packaged owner selects an authenticated native executable and constructs the
command used by existing consumers. Preserve existing client return contracts;
keep backend command/output details private. Do not introduce a public Finding
hierarchy or new scanner command tree without a demonstrated requirement.

Proposed explicit preparation uses
`python -m specfact_cli.utils.scanner_runtime prepare`. Existing Hatch aliases
invoke the packaged owner. Installed users receive the same preparation path and
clear unavailable diagnostics. Ordinary invocation does not download software.
The exact command is a design sketch, not existing functionality.

```python
command = scanner_command(args=("scan", "--config", config, "--json", target))
command = scanner_command(args=("--config", test_rules, "--json", test_path))
command = scanner_command(args=("--config", async_rules, "."))
```

The domain identity binds engine release, source revision, target, artifact digest,
exact publisher identity and complete component-inventory digest. Validated identity
selects one executable. It does not expose an arbitrary URL or PATH override.

```python
class ScannerUnavailable(RuntimeError): ...


@dataclass(frozen=True)
class PreparedScanner:
    identity: ScannerIdentity
    executable: Path


def prepare_scanner(cache_root: Path) -> PreparedScanner:
    raise NotImplementedError


def scanner_command(*, args: tuple[str, ...]) -> tuple[str, ...]:
    raise NotImplementedError
```

All public implementations require meaningful icontract and beartype contracts.
External artifact, signature and scanner-result parsing belong at the boundary.
Consumers retain their public result types and existing optional-tool outcomes.
Required SAST fails on missing, timed-out, malformed, partial or failed scans.

## Module and policy ownership

- The packaged scanner owner handles identity, safe acquisition, verified cache
  selection and argument/result compatibility. Its policy resources ship in wheel
  and sdist and work in external projects without a checkout.
- A single reviewed artifact/component inventory names exact upstream release
  bytes, native target, source revision, signing issuer and exact signing identity,
  complete components/licenses and advisory-assessment evidence. A candidate entry
  with missing assurance cannot become admitted by executing candidate code.
- Existing delivery/audit verification retains every Python graph and adds native
  scanner coverage. Extend the existing owner; do not create a generic environment
  registry. Unknown component identity or unavailable advisory data fails adoption.
- CI, Hatch, installed consumers and generated workflows migrate together before
  removing every Semgrep declaration. Regenerate locks normally and account for
  each removed package as absent from the actual supported installation.
- scripts/semgrep_sast_gate.py retains baseline semantics. Use the existing JSON
  contract where compatible; any required private adaptation must be covered by
  actual parity evidence. No bulk baseline refresh is permitted.

## Candidate identity and independent verification

OpenGrep v1.31.0 resolves to source commit
`87668f6dbd28a9b97bcaf294a564fe79e0a7b56e`. Its upstream release publishes native
CLI assets and signature/certificate companions. This is an inventory observation,
not proof of authenticity, platform support, component safety or scanner parity.

Before executing or admitting candidate bytes, verify exact release identity and
provenance with an independently trusted verifier, record transparency evidence
and check the artifact digest. A repository wildcard signer selector, an asset
filename or GitHub-published hash alone is insufficient. Do not run the upstream
installer as an opaque shell script. In particular, do not copy its behavior that
can skip verification for an existing installation.

Establish complete native component and license inventory and a reproducible
advisory assessment over that inventory. A binary being outside pip-audit is not
security evidence. LGPL subprocess use needs the repository's applicable license
review; no module manifest dependency is added by this plan. Unsupported native
components, unknown identities or unreviewed advisories remain blocking.

## Behavior and installation feasibility

Before production edits, compare the existing engine and authenticated candidate
on identical checked-in rules and planted positive/negative fixtures. Cover
captures, ignores, path prefixes, multiline locations, used taint behavior, JSON,
autofix where currently supported, failures and target completeness. Preserve
exact baseline keys and required blocking decisions. Additional real findings
require disposition; missing findings or unresolved errors reject the candidate.

Run each advertised native target, including actual Windows architecture and
runtime dependencies, plus installed-wheel consumers on Python 3.11-3.13.
Published filenames do not establish that matrix. A new engine cannot silently
reduce platform support. External Code Review compatibility must use its actual
public contract; this core proposal does not implement or approve module changes.
Track that migration in modules #523 separately from the existing local cutover.
Its acceptance covers scanner command paths, clean-code/bug/AI-bloat rule payloads,
bundle-resource tests, checksums, module version and CI/CD signatures. Core-only
acceptance does not establish end-to-end replacement while that module remains
on Semgrep. Preserve the existing reset sequence and owners.

Removing the scanning extra's implicit Python tool installation changes its setup
contract. Specify explicit native preparation and verify patch compatibility
before migration. If a patch cannot preserve the supported contract, keep the
requested hotfix blocked and reconcile release scope rather than silently shipping
that change as 0.55.11.

## State, retries and failure handling

Acquisition uses per-attempt temporary state and publishes only complete verified
bytes to a content-addressed location. Verify cached bytes on every selection.
Concurrent or interrupted preparation cannot publish a partial executable.
Windows companion files, if required, need their own complete identity and safe
extraction checks. Logs and mutable scan state remain caller-specific.

Run the absolute verified executable without a shell, with bounded timeouts,
explicit local rules and preserved caller output/signal semantics. Never fall back
to unmanaged Semgrep or another engine to make a required check pass. Offline
unprepared consumers report unavailable; required scans fail.

## Alternatives and synthesis

Three independent architect candidates compared isolated admitted Semgrep,
upstream native replacement and direct downstream adoption. The first cross-judge
preferred isolation. The later independent cycle review supersedes that choice
because the assumed producer/admission path is not executable under current gates.

Select the replacement candidate as the investigation base. Graft the isolation
candidate's single execution owner, complete audit union and retry/identity
requirements. Graft direct adoption's inspection of actual artifact metadata and
its refusal to invent production coordinates. Narrow the replacement design by
retaining existing client types and avoiding a new CLI tree or multi-backend API.

Isolated or directly adopted downstream Semgrep remains a blocked alternative.
It cannot be selected by bypassing #772 authority or its failing audit. A container
holding the same vulnerable closure also does not remediate the advisory. Native
replacement has no such producer-ordering prerequisite, but its own provenance,
component, parity and compatibility evidence remains unproved.

## Dependencies, risks and rollback

There is no native issue dependency on #772 for replacement investigation. Actual
production adoption still needs existing protected review/Requirements authority,
complete Python/native audits and every required gate. This proposal cannot clear
the independent Trusted Requirements Authority failure or approve its own bytes.
No requirement to merge the known-blocked planning PR before the corrective
implementation is invented here; use applicable governance at implementation start.

- Lost findings are mitigated by real planted-rule and baseline parity tests.
- Untrusted or unaccounted binary components are mitigated by independent publisher
  verification and complete component/license/advisory coverage before execution.
- Silent scanner loss is mitigated by installed-wheel and offline diagnostics,
  one execution owner and failure of every required incomplete scan.

This is multi-platform feasibility and integration, likely days rather than an
hours-only lock refresh [Hypothesis]. Reject the candidate if feasibility fails.
Rollback restores previous consumers and frozen inputs together, but the old MCP
advisory remains blocking. Functional rollback is not security remediation.

## Implementation reconciliation

No production code or adopted artifact exists. Next, establish independent exact
publisher/component evidence and authored scenario tests, then run the bounded
candidate parity proof before any production dependency movement.
