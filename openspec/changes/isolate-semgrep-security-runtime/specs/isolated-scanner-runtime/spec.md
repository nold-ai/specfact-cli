## ADDED Requirements

### Requirement: Complete Python and native scanner audit coverage

The system SHALL represent every delivered or executed scanner component in a
committed, reproducible inventory and SHALL require its vulnerability, trust and
license checks alongside the existing CI, Code Review and runtime-smoke checks.
A native executable SHALL have complete component/advisory coverage; a clean
Python audit alone SHALL NOT establish native scanner safety.
Environment separation MUST NOT suppress an advisory or convert an unknown
package identity into a clean audit.

#### Scenario: Clean core dependencies cannot conceal a vulnerable scanner

- **GIVEN** a clean core export and a native scanner component inventory with an unreviewed advisory
- **WHEN** the required aggregate security check runs
- **THEN** the check fails and identifies the scanner graph and advisory.

#### Scenario: Missing inventory or audit evidence blocks promotion

- **GIVEN** an installed scanner closure omitted from the declared inventory,
  a missing export, or unavailable advisory data
- **WHEN** delivery and security verification run
- **THEN** verification fails rather than accepting the remaining clean graphs.

### Requirement: Authenticated compatible scanner preparation

The system SHALL prepare an independently published native scanner only after
exact publisher identity, source provenance, artifact integrity and complete
component/license/advisory evidence are independently verified and reviewed under
the existing protected controls. Candidate-authored policy SHALL NOT grant its
own production approval. Replacement SHALL remove the Python Semgrep/MCP lineage
from every supported core installation rather than hide an executed graph.
It SHALL NOT use dependency overrides, scanner audit exclusions or candidate
evidence as production authority. Adoption of #772/#779 is not a prerequisite
for this independent replacement investigation.

#### Scenario: Empty or invalid admission prevents installation and execution

- **GIVEN** absent, forged, expired, incomplete or wrong-platform admission
- **WHEN** a consumer prepares or selects the scanner
- **THEN** it refuses before installing or executing the candidate bytes.

#### Scenario: Independently authenticated replacement removes the affected lineage

- **GIVEN** exact independently authenticated native artifacts with complete
  reviewed component, license and advisory evidence
- **WHEN** replacement and ordinary Python lock regeneration complete
- **THEN** actual supported installations exclude Python Semgrep/MCP, the selected
  native bytes match their admitted identity, every native component remains
  assessed, and all existing Python and new scanner checks pass.

#### Scenario: Repeated or interrupted preparation cannot publish partial state

- **GIVEN** concurrent preparation or an interrupted earlier attempt
- **WHEN** the scanner environment is prepared again
- **THEN** consumers observe only a complete verified environment bound to the
  current platform, artifact/component inventory and admission, or an explicit unavailable result.

### Requirement: One scanner execution owner

Core repository automation and core installed-package consumers SHALL obtain the scanner
through one packaged execution owner usable without a source checkout. Selection
SHALL bind the executable and installed native component inventory to the current admitted
artifact/component identity. An arbitrary PATH executable or cached version string MUST NOT satisfy
that selection. Network acquisition SHALL require an explicit preparation step.

#### Scenario: Ambient PATH and stale cache cannot select the scanner

- **GIVEN** an unverified `semgrep` on PATH or a prepared cache whose identity no
  longer matches the admitted closure
- **WHEN** a consumer requests scanner execution
- **THEN** it rejects that executable and does not silently fall back.

#### Scenario: Installed distribution resolves the same scanner as the checkout

- **GIVEN** a wheel installed in an external project without this repository
- **WHEN** its analyzer, test-to-OpenAPI generator or reproducibility checker scans
- **THEN** each uses the same admitted execution owner as repository SAST and
  preserves its documented public result and unavailable-tool behavior.

#### Scenario: Offline invocation never initiates acquisition

- **GIVEN** offline invocation with no prepared admitted scanner
- **WHEN** optional analysis or required SAST requests execution
- **THEN** optional analysis reports its existing unavailable outcome, required
  SAST fails, and neither initiates a network installation.

#### Scenario: External module migration remains separately tracked

- **GIVEN** core replacement passes its checks while the external Code Review
  module still invokes Semgrep
- **WHEN** replacement readiness is reported
- **THEN** it identifies the separate module migration, command-path, packaged-rule
  and bundle-integrity acceptance, and makes no end-to-end replacement claim
  until that follow-up is verified complete. Shared Semgrep dependency removal
  remains blocked until the module migration preserves mandatory review coverage.

### Requirement: Preserve effective static analysis

The isolated scanner SHALL retain the checked-in rule corpus, current SAST
baseline identities and existing blocking decisions. Each advertised native
target and installed Python 3.11-3.13 consumer SHALL have actual execution proof;
asset filenames SHALL NOT establish platform support. Missing, failed, malformed
or incomplete scans SHALL NOT produce successful required SAST. Isolation SHALL
NOT refresh the baseline or reduce accepted rule or target coverage.
Shared Python Semgrep dependency removal SHALL wait for verified migration of the
installed Code Review module to the admitted replacement. Its clean-code, bug and
AI-bloat passes, packaged rules and bundle integrity SHALL retain actual execution
proof in a fresh delivery environment with Python Semgrep absent. Separate tracking
or a withheld end-to-end claim SHALL NOT substitute for this cutover prerequisite.

#### Scenario: Semgrep removal waits for required Code Review coverage

- **GIVEN** the installed Code Review module still requires `semgrep` and the
  separate Code Review lock does not supply it
- **WHEN** the shared Python Semgrep dependency is proposed for removal
- **THEN** removal remains blocked until the separately tracked module migration
  proves the admitted replacement executes the required clean-code, bug and
  AI-bloat passes with packaged rules and verified bundle integrity in a fresh
  post-removal environment; skipped or missing scanner coverage fails readiness.

#### Scenario: Actual scanner detects planted violations and accepts corrections

- **GIVEN** representative positive and negative fixtures for each used rule
  family and the unchanged SAST configuration
- **WHEN** the current engine and authenticated replacement run on the same targets
- **THEN** normalized findings and gate decisions retain the required coverage,
  violations fail, corrected fixtures pass, and differences require disposition.

#### Scenario: Incomplete scanner output fails the required gate

- **GIVEN** missing output, invalid JSON, scanner errors, timeouts or partial targets
- **WHEN** required SAST evaluates the scan
- **THEN** it fails rather than treating the result as an empty clean scan.

### Requirement: Coherent hotfix delivery and duplicate disposition

The eventual implementation SHALL synchronize the next core patch version,
canonical sources, generated metadata and changelog after compatibility and quality
verification. It SHALL link a verified replacement implementation PR before closing
any covered dependency PR. Planning artifacts SHALL NOT claim remediation or
authorize closure, admission, release or promotion.

#### Scenario: Final package version follows verified core state

- **GIVEN** a compatible verified implementation and the latest dev and PyPI versions
- **WHEN** the patch release is prepared
- **THEN** all four canonical version sources, generated metadata and changelog
  agree on a patch version strictly ahead of PyPI, followed by fresh final review.

#### Scenario: Duplicate closure follows an actual replacement

- **GIVEN** a verified replacement implementation PR with complete security evidence
- **WHEN** a covered older dependency PR is closed
- **THEN** a preceding comment links the replacement and explains coverage, while
  unimplemented JSON migration and unrelated updates retain explicit dispositions.
