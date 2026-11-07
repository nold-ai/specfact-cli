## ADDED Requirements

### Requirement: Use the upstream native scanner without Python fallback

Existing scanner owners SHALL discover `osemgrep` and invoke native scanning with explicit `scan --experimental`. They SHALL preserve existing rule bytes, configured rule sets, JSON finding consumers, logical Semgrep tool labels, timeouts and optional-tool behavior. The Python `semgrep` executable alone SHALL NOT satisfy native availability.

#### Scenario: Native executable is available without the Python CLI

- **GIVEN** the reviewed native executable is on PATH and the Python CLI is absent
- **WHEN** scanner availability and scanning run
- **THEN** scanning succeeds and preserves literal and propagated shell-true findings while excluding shell-false controls.

#### Scenario: Every configured rule set is scanned

- **GIVEN** two configured rule files with distinct findings
- **WHEN** an existing scanner owner scans a source file
- **THEN** both rule sets produce their expected findings.

#### Scenario: Only the Python CLI is installed

- **GIVEN** Python semgrep is present but osemgrep is absent
- **WHEN** native scanner availability is checked
- **THEN** the native scanner remains unavailable and no Python fallback executes.

### Requirement: Remove the vulnerable Python dependency through reviewed delivery

Native migration SHALL NOT claim dependency remediation until every selected input, including the reviewed official module manifest, omits pip Semgrep and normal resolution establishes the complete replacement graph. Per-platform artifacts, rule parity, licenses, signatures and required current-head checks SHALL pass before adoption.

#### Scenario: Preparation is not adoption

- **GIVEN** caller tests pass but artifact installation, parser classification or module signatures remain incomplete
- **WHEN** readiness is evaluated
- **THEN** the candidate remains unfinalized and PR786 is not reported READY.

### Requirement: Capture native JSON at the existing CI boundary

Existing CI SHALL capture native JSON stdout into its existing result file. It SHALL NOT assume native `--output` created a file.

#### Scenario: The native scan returns findings on stdout

- **GIVEN** the native scanner runs with JSON output
- **WHEN** the existing static-analysis producer completes
- **THEN** its result file contains the actual JSON object consumed by the existing SAST gate.

#### Scenario: The CI scanner owns its absent CA default

- **GIVEN** the existing frozen CI setup provides selected Python and certifi
- **WHEN** the existing independent scanner runs without SSL_CERT_FILE
- **THEN** only that native child receives the installed certifi CA path and writes valid JSON to the existing result file.

#### Scenario: Explicit CI CA values remain authoritative

- **GIVEN** SSL_CERT_FILE is explicitly present with a valid, invalid or empty value
- **WHEN** the existing independent scanner runs
- **THEN** its native child receives that value unchanged, including failure for invalid or empty trust, and no default is installed in the surrounding shell.

### Requirement: Preserve migration scope and gates

The migration SHALL NOT introduce a compatibility launcher, framework, index, fork, forced resolver or expired exception transfer. Existing resource, cleanup, clock, signature and authority bounds SHALL remain enforced.

#### Scenario: Git checks out byte-authenticated validation metadata on Windows

- **GIVEN** Git enables automatic CRLF conversion and the validation workflow hashes its checked-out workflow bytes
- **WHEN** Git checks out the exact workflow and operation-descriptor paths
- **THEN** both paths retain their committed bytes through finite literal attributes, without normalizing the checksum input, changing caller Git configuration or weakening the signature and authority guards.

#### Scenario: Git checks out byte-authenticated isolated graph inputs

- **GIVEN** Git enables automatic CRLF conversion and the existing trust and reproducibility gates authenticate the two isolated dependency inputs
- **WHEN** Git checks out requirements/code-review/requirements.in and requirements/runtime-smoke/requirements.in
- **THEN** both exact paths retain committed bytes and their existing lock bindings through finite literal attributes, without changing the requirement text, lock digests, Git configuration or checksum validation.

#### Scenario: A preparation gate is incomplete

- **GIVEN** licensing, platform execution or any required delivery proof is missing
- **WHEN** readiness is assessed
- **THEN** adoption remains blocked without substituting a local probe for the missing gate.

### Requirement: Preserve project-import scanner coverage

The existing project-bundle analyzer and OpenAPI converter SHALL use the approved native command and CA default. The analyzer SHALL retain its environment-manager command prefix, optional-tool status message and ten-second scan timeout. The converter SHALL retain its five-second scan timeout and existing AST fallback. Native availability SHALL reject a Python-only installation. The existing project manifest SHALL declare certifi when these owners import it directly.

#### Scenario: Project analysis has native Semgrep only

- **GIVEN** osemgrep is available without Python semgrep and both project analyzer configs are selected
- **WHEN** the existing project analyzer scans a file
- **THEN** literal and propagated shell-true findings and a distinct second-config finding are preserved, excluding shell-false controls.

#### Scenario: Project test conversion has native Semgrep only

- **GIVEN** the upstream native scanner is available and the configured rule file matches a test source
- **WHEN** the existing project converter runs its scanner
- **THEN** it receives the actual native JSON findings within its unchanged timeout.

#### Scenario: The project caller supplies a CA override

- **GIVEN** SSL_CERT_FILE has an explicit caller value
- **WHEN** either project scanner owner executes
- **THEN** it preserves that value instead of replacing it with the default.

### Requirement: Preserve existing external Code Review providers

The code-review bundle SHALL retain existing Pylint and BasedPyright checks through their PATH executables without declaring either provider as a pip dependency. Missing-tool warnings SHALL identify the reviewed isolated Pylint or npm BasedPyright provider. Native report prerequisites SHALL accept osemgrep and reject Python-only Semgrep. Existing versions, runner arguments, result contracts and installation behavior SHALL remain unchanged.

#### Scenario: An external Code Review provider is missing

- **GIVEN** the Pylint or BasedPyright executable is absent
- **WHEN** the existing review availability check runs
- **THEN** it returns the existing warning finding with truthful isolated-Pylint or npm-BasedPyright guidance.

#### Scenario: Native report-contract prerequisites are available

- **GIVEN** the existing review tools and osemgrep are available without Python Semgrep
- **WHEN** the report-contract test checks its prerequisites
- **THEN** the native executable satisfies the Semgrep prerequisite while Python Semgrep alone does not.

### Requirement: Check the actual companion Python dependency license boundary

The existing offline module license map SHALL identify the retained direct Python dependencies of the selected companion manifests from reviewed package metadata. The existing gate SHALL run against the actual companion package root, retain rejection of unknown and GPL dependencies, and distinguish module-manifest results from installed-environment and native-library attribution. This mapping is license metadata, not an exception, artifact/trust approval or native-library clearance.

#### Scenario: Direct certifi has reviewed metadata

- **GIVEN** the unchanged selected certifi artifact and its published MPL-2.0 metadata
- **WHEN** the existing manifest license gate checks the project and code-review direct declarations
- **THEN** it finds the canonical SPDX entry rather than bypassing the map or supplying a fabricated temporary license map.

#### Scenario: CI checks the selected companion manifests

- **GIVEN** the existing license job checks out the exact commit and tree from its module fixture lock
- **WHEN** its existing canonical manifest scanner examines that checkout's packages
- **THEN** reviewed dependencies pass, unknown dependencies fail, and absent or empty companion manifests fail instead of silently skipping.

### Requirement: Preserve native repro coverage and missing-tool reports

The migrated core and Codebase repro checks SHALL resolve native osemgrep while retaining logical Semgrep report IDs. The Codebase owner SHALL retain its managed command prefix, optional check, thirty-second timeout and autofix behavior. Its copied environment SHALL default SSL_CERT_FILE from certifi and preserve explicit overrides. Its manifest SHALL declare direct certifi. Missing-tool reports SHALL recommend the native provider without suggesting Python Semgrep.

#### Scenario: Codebase repro has only the native scanner

- **GIVEN** the existing async configuration and osemgrep are available without Python Semgrep
- **WHEN** the existing Codebase repro checker runs
- **THEN** it executes the native scan and preserves findings, timeout and logical tool identity.

#### Scenario: A migrated repro check has no scanner

- **GIVEN** the core or Codebase repro checker has an async configuration and neither scanner executable
- **WHEN** it returns its optional skipped check
- **THEN** the report retains the Semgrep ID and identifies the missing native provider without a pip-install recommendation.

### Requirement: Keep native Hatch trust local to the scanner

Existing Hatch scan commands SHALL invoke native Semgrep directly. An absent SSL_CERT_FILE SHALL select immutable data copied exactly from the selected certifi bundle, checked against its filename digest and the installed bundle before scanning. Every explicit value, including empty, SHALL bypass the default check and remain authoritative. Other Hatch commands SHALL retain their environment. No launcher, helper alias, marker, plugin or runtime CA writer SHALL be added.

#### Scenario: Native Hatch scan has no explicit CA

- **GIVEN** the fixed data and installed selected certifi bytes match
- **WHEN** an existing Hatch scan runs without SSL_CERT_FILE
- **THEN** the scanner receives the checked bundle through its own command environment and executes directly.

#### Scenario: Caller controls the CA value

- **GIVEN** SSL_CERT_FILE is present, even when empty or equal to the default data path
- **WHEN** an existing Hatch scan runs
- **THEN** it invokes native with that exact value without checking or repairing the default data.

#### Scenario: Selected CA data drifts

- **GIVEN** the default data or installed certifi bundle differs from the reviewed bytes
- **WHEN** a default native Hatch scan starts
- **THEN** bounded data validation fails before native scanning and changes no CA file.

#### Scenario: Git checks out trust data with automatic CRLF conversion

- **GIVEN** core.autocrlf is true
- **WHEN** Git materializes the fixed CA data and its accompanying selected license notice
- **THEN** exact-path attributes preserve their bytes without runtime normalization.

#### Scenario: Platform and explicit-value command branches agree

- **GIVEN** an existing scan command has default, Windows and explicit-value forms
- **WHEN** those forms are compared
- **THEN** their native scanner arguments, rule paths, JSON output and autofix behavior are identical.

#### Scenario: The preflight retains the dedicated SAST rule set

- **GIVEN** the existing Hatch SAST command includes a data-only CA preflight
- **WHEN** its configured command sequence is checked
- **THEN** it still selects only tools/semgrep/sast.yml and never automatic discovery or the full development rule directory.

### Requirement: Provision only the frozen upstream native payload

The existing frozen action SHALL select one declared native artifact from the existing security-tool policy. It SHALL authenticate the complete archive and exact native members/notices, preserve library layout, and expose only a complete installation. It SHALL NOT install Python Semgrep, resolve dependencies, generate a launcher, overwrite mismatched bytes or select fallback artifacts. Existing risk, resource, cleanup, signature and authority bounds SHALL remain unchanged.

#### Scenario: A complete frozen native installation is available

- **GIVEN** one supported platform with the exact declared archive and notices
- **WHEN** the existing setup action provisions its invocation-owned directory
- **THEN** direct osemgrep and every required adjacent library match declared hashes, excluded Python files are absent, and a repeated invocation verifies and reuses the exact bytes.

#### Scenario: Native payload validation fails before publication

- **GIVEN** an unsupported platform, a bad archive or member digest, unsafe or duplicate paths, missing members, conflicting destinations, or altered retained notices
- **WHEN** native provisioning runs
- **THEN** it fails without exposing a partial installation or modifying an existing one.

#### Scenario: Installation does not imply native audit clearance

- **GIVEN** native bytes install correctly while component/advisory/license assessment remains incomplete
- **WHEN** delivery readiness is evaluated
- **THEN** installation evidence retains its precise scope and existing audit, license and final-head gates remain mandatory.

#### Scenario: The official Linux vendor correction preserves the native engine

- **GIVEN** the exact selected upstream engine and the separately pinned official vendor-fixed libcurl payload
- **WHEN** Linux native provisioning composes the private installation
- **THEN** only the shared libcurl member is replaced with its unmodified fixed vendor bytes, its notice is retained, the engine remains byte-exact, and no system package, launcher, binary patch, source fork or advisory waiver is introduced.

#### Scenario: Native Linux children select their private libraries

- **GIVEN** no explicit caller LD_LIBRARY_PATH and the existing scanner environment owner
- **WHEN** it starts a Linux native scan
- **THEN** only its child receives the literal loader default $ORIGIN/libs, without changing argv or the parent environment, and explicit values remain authoritative.

### Requirement: Verify the current selection without transferring expired approvals

The frozen Python graph SHALL omit Python Semgrep, MCP and specfact-semgrep, select official OpenTelemetry1.45.1 and parser3.11, and retain exact official exports and other reviewed pins. Public parser declarations SHALL match3.11. Active exception registers SHALL be empty. Historical MCP/OTel/3.12 records SHALL NOT confer current eligibility. Parser3.11 SHALL pass fresh supply-chain and compatibility gates.

#### Scenario: Empty trust registers bootstrap without timezone data

- **GIVEN** a bare interpreter without site packages or IANA timezone data and a valid empty exception register
- **WHEN** the pre-synchronization dependency-trust check validates the frozen graphs
- **THEN** the empty register requires no date calculation, while every graph and pin check still executes; malformed registers remain rejected and any nonempty register still requires its unchanged Berlin-date validation without a timezone fallback or approval renewal.

#### Scenario: Current release tests cover the actual candidate

- **GIVEN** the exact five-file source-preparation approval call_e159e584bfc44c0292d9a980c14efc4e
- **WHEN** current selection tests run
- **THEN** they bind the actual native provider/artifacts and current frozen graph, preserve all security/source/hash checks, and select no new blocking exclusions.

#### Scenario: Historical policy behavior remains executable without live waivers

- **GIVEN** explicitly isolated historical or synthetic package/version/ID/date fixtures
- **WHEN** rejection and expiry policy cases run
- **THEN** the original fail-closed cases remain covered independently of the empty active registers, and no current approval, recovered investigation or fresh source-proof claim is inferred.

#### Scenario: Original proof evidence cannot authorize changed inputs

- **GIVEN** five current test files change while the original eight snapshots and native01..36 remain immutable
- **WHEN** later adoption is proposed
- **THEN** new exact TEST/source identities and fresh independently verified native evidence are required, without modifying or retargeting historical consumers, selectors, signatures or consumed grants.

### Requirement: Native delivery evidence reports the verified composition

The existing SBOM command SHALL verify the actual native installation before appending exact file hashes to Python evidence. Its namespace SHALL bind platform, selection and final inventory. The pure Python renderer signature SHALL remain unchanged. Missing or altered files SHALL fail without provisioning, repair or success output. Supplier credits SHALL remain attribution rather than installed-package assertions.

#### Scenario: Native identity changes independently of Python packages

- **WHEN** identical Python inventories accompany different verified native selections
- **THEN** the combined SPDX document namespaces differ and expose the exact native file identities.

#### Scenario: Actual native installation is absent or changed

- **WHEN** the SBOM command cannot verify the complete selected native installation
- **THEN** it fails without downloading, repairing, or emitting a success artifact.

### Requirement: Fixed native PCRE2 preserves the actual macOS scanner platform

The private provisioner SHALL compose the unmodified engine with exact official Homebrew PCRE2 10.49 arm64 library and notice bytes. Required symbols, input/final hashes, complete inventory validation, fail-closed reuse and read-only evidence SHALL remain enforced. No binary rewriting or core CLI runtime-admission change is permitted. The misleading macosx11 wheel filename SHALL NOT imply scanner compatibility.

#### Scenario: Exact fixed Mac payload

- **WHEN** a Mac preparation selects the authenticated fixed bottle and complete expected SDK
- **THEN** its copied PCRE2 reports10.49 and the unmodified native scanner retains positive regex detection and a negative control; measured original and selected engines both require macOS15.

#### Scenario: Invalid correction archive or member

- **WHEN** the bottle has a wrong digest, wrong selected member, unsafe path, link, missing member or conflicting entry
- **THEN** installation fails without publishing or repairing an SDK.

#### Scenario: Public bottle authentication

- **WHEN** the official public OCI blob needs an anonymous pull token
- **THEN** only the fixed public repository pull request is made, the bounded token remains in memory, and artifact URL/size/digest validation remains authoritative.

### Requirement: Development scan commands do not restore the removed Python graph

The existing core and companion Hatch default environments SHALL NOT install Python Semgrep or MCP after their scanner commands migrate to the supplied native executable. The native prerequisite remains explicit and the actual native caller checks remain mandatory; dependency absence is not native availability evidence.

#### Scenario: Standalone development scanning has its direct CA dependency

- **GIVEN** Python Semgrep and its transitive dependencies have been removed
- **WHEN** the existing standalone companion Hatch scan environment is prepared
- **THEN** exact certifi2026.10.19 remains directly declared and both existing native scan commands retain their CA behavior.

### Requirement: Build the Windows curl correction from frozen inputs

The private native provider SHALL retain the original Windows engine and build unmodified curl8.23.0 from authenticated source and tools. Its correction SHALL retain all required curl exports, matching MSVCRT allocation, HTTP/HTTPS and exact final DLL hashes. SSH and the unneeded version-resource compiler SHALL be excluded. No source fork, binary rewriting, fallback resolver, advisory waiver or toolchain-wide clearance follows.

#### Scenario: Source-build output differs from the reviewed candidate

- **GIVEN** independent clean builds established the expected DLL size and hash before provisioning
- **WHEN** a later build produces different bytes
- **THEN** provisioning fails before publishing an SDK and does not learn a new expected hash from that output.

#### Scenario: A copied SSH library is no longer needed

- **GIVEN** independent complete PE import inspection proves only the replaced curl imports libssh2
- **WHEN** the reviewed Windows composition is prepared
- **THEN** only the exact declared SSH member is removed after authenticating the original archive and native member set.

### Requirement: Isolate native source building and preserve argument boundaries

The private Windows producer SHALL use authenticated temporary tools and owned build/cache directories. It SHALL preserve the existing archive/native-byte bounds and use response files for linker arguments. It SHALL NOT parse the compiler's unquoted display log, inherit credential environment, use ambiguous cache content, build during read-only inventory, or replace an existing SDK. Actual Windows execution remains required before adoption.

#### Scenario: Build paths contain spaces

- **GIVEN** an owned build/cache path contains spaces and the final linker uses Windows response-file rules
- **WHEN** the frozen producer links the actual objects
- **THEN** the arguments retain their boundaries and produce the same frozen DLL bytes.

#### Scenario: The compiler cache repeats one input

- **GIVEN** a fresh owned link cache contains repeated copies of one named CRT input
- **WHEN** the producer selects that input
- **THEN** identical content is accepted and conflicting, absent, linked or nonregular content is rejected.

### Requirement: Keep native component identities visible in existing delivery evidence

The existing native policy and SPDX producer SHALL retain finite component records tied to verified installed files. Known engine and corrected-library versions SHALL be emitted. Unproved component versions and licenses SHALL remain unasserted; supplier credits SHALL NOT be reclassified as proof of C-library identity or complete notice coverage. Removed libraries SHALL NOT be reported as installed.

#### Scenario: Corrected component versions reach downstream consumers

- **WHEN** the verified SDK contains a selected corrected library
- **THEN** its known version and exact file relationship appear in the existing SPDX document alongside all original file hashes.

#### Scenario: Component metadata names a removed or absent file

- **WHEN** selected component metadata references a file outside the verified final composition
- **THEN** the provider rejects it instead of emitting misleading delivery evidence.
