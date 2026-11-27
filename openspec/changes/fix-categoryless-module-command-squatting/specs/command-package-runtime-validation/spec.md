## ADDED Requirements

### Requirement: Permanent Core Commands Cannot Be Extended By External Packages

The system SHALL reserve `init`, `module` and `upgrade` for packages whose resolved path belongs to the
effective built-in module tree selected by the operator-controlled discovery configuration. External packages SHALL NOT
register or extend these commands in either command
registry, regardless of category, grouping mode, discovery source label or manifest name.

#### Scenario: Workspace package impersonates a core category

- **GIVEN** a workspace package declares `category: core` and a permanent core command
- **WHEN** package commands are registered and the existing root command is invoked
- **THEN** the original built-in loader SHALL remain unchanged
- **AND** no external loader SHALL be registered or executed for that command

#### Scenario: Forged source and symlink cannot grant core authority

- **GIVEN** an external package claims a built-in source or is symlinked from the built-in tree
- **WHEN** its resolved path is outside the built-in tree and it declares a permanent core command
- **THEN** both registries SHALL reject that external command in either grouping mode
- **AND** legitimate built-in commands SHALL continue to load

#### Scenario: Explicit repository root preserves legitimate built-ins

- **GIVEN** the operator sets SPECFACT_REPO_ROOT to another checkout containing built-in modules
- **WHEN** discovery loads a permanent core package from that effective root
- **THEN** resolved contained packages SHALL retain core authority
- **AND** a symlink escaping that root SHALL NOT gain core authority

### Requirement: Workspace Packages Cannot Supply Official Category Roots

Unauthenticated project packages SHALL NOT supply official category root command names in either mode, regardless of
claimed category, bundle or source fields in their manifest. Rejected packages SHALL cause no registration
side effects, including category-builder imports or app initialization during eligibility checks. Eligible
non-project installed bundles SHALL retain their category roots.

#### Scenario: Workspace manifest impersonates an official category root

- **GIVEN** a project package declares any official category root command
- **WHEN** package commands are registered in either grouping mode
- **THEN** the entire package SHALL be rejected before registration side effects
- **AND** existing category root loaders SHALL remain unchanged
- **AND** the rejected package SHALL NOT create a category mount through bundle metadata

#### Scenario: Workspace bundle metadata cannot induce or extend an official category mount

- **GIVEN** a project package whose category, bundle identity or registered member commands can create or extend an official category group
- **AND** its declared commands need not contain the category root name
- **WHEN** registration runs in either grouping mode with an empty or existing root registry
- **THEN** the package SHALL require the same authenticated official project-bundle authority before selection and registration effects
- **AND** an unauthenticated package SHALL NOT mount a category, extend its loaders or activate executable sources
- **AND** authenticated official bundles, non-project packages and explicit unreserved category-less legacy commands SHALL remain supported

### Requirement: Authenticated Project Bundles Retain Official Category Roots

Official bundles installed with `--scope project` SHALL retain their canonical category root in both grouping modes
only when their complete filesystem artifact checksum and signature verify against the public key bundled with the
core CLI. Verification SHALL include untracked module source files in a project Git checkout and SHALL reject
symlink members whose directory traversal or target is not covered by that complete artifact. Executable Python or
native-library files omitted from the signed payload SHALL NOT grant project-root authority. A Python source cache
may remain compatible only when its current-interpreter code is independently reproduced from a covered signed
source file. Verification SHALL authenticate one captured source-byte snapshot before compiler work, and SHALL
compile exactly those authenticated bytes with the original filename and current optimization level. A later
filesystem reread SHALL NOT replace the captured source. Cache verification SHALL neither execute nor deserialize
candidate code. Unsupported native-library artifacts, including DLL, dylib and bundle files in excluded directories,
SHALL remain outside privileged project-root authority. Standalone
bytecode and executable files under excluded directories SHALL fail closed.
Their signed official publisher identity, tier, category and bundle group SHALL match the canonical root. The
claimed reserved category commands SHALL consist only of that root; other signed bundle commands remain compatible. This admission check SHALL precede schema, bridge, protocol, command and active-import effects. Discovery SHALL retain same-name candidates until enabled state and root authority select the first eligible installation in existing source-priority order. Rejected project claims SHALL NOT suppress eligible installed alternatives or satisfy dependencies. Disabled names SHALL perform no artifact payload verification or registration effects; normal metadata discovery and stored/explicit enablement semantics SHALL remain unchanged.
Permanent core command authority SHALL remain limited to resolved built-in paths.

Unsigned/test flags, environment-supplied public keys, publisher/name/category claims, missing keys, unavailable
signature backends, self-recomputed checksums and installation receipts SHALL NOT grant project category-root
authority. Tampered payloads or signatures SHALL be rejected without registration or import effects.

#### Scenario: Verified project-scoped official bundle keeps its category root

- **GIVEN** any canonical official bundle or official category add-on is installed in the project module root
- **WHEN** its complete checksum and signature verify against the core-bundled public key before registration
- **THEN** its canonical category root SHALL remain registered in both grouping modes
- **AND** the normal compatibility, dependency and integrity checks SHALL still apply
- **AND** an authenticated official category add-on SHALL expose its declared subgroup alongside its verified dependency
- **AND** an unverified replacement SHALL NOT extend that dependency group
- **AND** unsigned, tampered or self-signed replacements SHALL remain excluded even with permissive test flags

#### Scenario: Workspace key and receipt cannot create official authority

- **GIVEN** a workspace copy claims an official bundle identity and supplies its own signature key or receipt
- **WHEN** registration checks the project category-root claim
- **THEN** environment overrides, local receipts and unsigned/test flags SHALL NOT replace core-bundled key verification
- **AND** a missing key or unavailable verifier SHALL fail closed before package side effects

#### Scenario: Source replacement cannot disconnect cache and signature verification

- **GIVEN** an otherwise authentic project bundle has a forged valid-app cache and its source changes between reads
- **WHEN** project-root admission verifies the artifact
- **THEN** authentication and cache reproduction SHALL use the same captured source bytes
- **AND** an unauthenticated snapshot SHALL be rejected before compilation, registration or import activation

#### Scenario: Rejected project copy cannot suppress a same-name installed bundle

- **GIVEN** an authentic installed bundle and an unverified project copy claim the same module name
- **WHEN** public registration selects candidates in either grouping mode
- **THEN** the installed bundle and its dependents SHALL retain their commands and activated source
- **AND** the rejected project copy SHALL NOT register commands or activate source
- **AND** a verified project copy SHALL retain its normal higher discovery priority
- **AND** ordinary discovery and state consumers SHALL retain their deduplicated result contract

#### Scenario: Disabled project roots avoid payload verification

- **GIVEN** a project bundle is disabled by stored state or an explicit disable override
- **WHEN** public registration reads its metadata
- **THEN** its payload SHALL NOT be hashed, compiled, imported or activated
- **AND** explicitly enabling the authentic bundle SHALL preserve normal loading
- **AND** enabling an unsigned replacement SHALL NOT grant category-root authority

#### Scenario: Discovery metadata must match the authenticated manifest

- **GIVEN** discovery observes altered schema, bridge, command or version fields while integrity stays unchanged
- **AND** the signed manifest is restored before artifact verification
- **WHEN** project-root authority authenticates the captured artifact
- **THEN** every normalized registration metadata field SHALL match that same authenticated manifest snapshot
- **AND** mismatched metadata SHALL be rejected before schema, bridge, command or active-import effects
- **AND** comparison SHALL preserve canonical category normalization, discovery provenance and derived protocol state
- **AND** a fresh discovery of the authentic restored manifest SHALL retain normal project-root loading

#### Scenario: Executable coverage matches the authenticated snapshot

- **GIVEN** a project artifact genuinely authenticates its captured file inventory
- **AND** a Python executable is added or modified before admission finishes
- **WHEN** coverage validates the live executable files
- **THEN** signed-payload eligibility alone SHALL NOT count as authenticated coverage
- **AND** executable membership and content SHALL match the authenticated snapshot before activation
- **AND** legitimate unchanged artifacts and reproducible caches SHALL retain normal loading

#### Scenario: Cache reproduction precedes the final admission inventory

- **GIVEN** a genuinely signed project bundle has authentic current-interpreter source caches
- **AND** an executable is inserted or a previously observed source is changed while a cache is reproduced
- **WHEN** public registration decides project-root authority
- **THEN** cache reproduction SHALL finish before a fresh final executable membership/content check
- **AND** that final check SHALL NOT invoke compilation or execute candidate code
- **AND** no unauthenticated package SHALL register schema, bridge, protocol, commands or active source even transiently
- **AND** any command-stage authority recheck SHALL precede all registration effects
- **AND** restoring the authentic package SHALL preserve normal public loading

#### Scenario: Malformed alternate manifest cannot abort project admission

- **GIVEN** a discovered project package has a valid primary manifest and malformed alternate manifest YAML
- **WHEN** artifact admission canonicalizes the complete filesystem payload in either grouping mode
- **THEN** parsing failure SHALL deny the package without escaping public registration or aborting startup
- **AND** no rejected root/import effects SHALL occur while authentic project bundles remain loadable

#### Scenario: Full eligibility precedes duplicate selection

- **GIVEN** two genuine same-name copies in discovery priority order
- **WHEN** the higher-priority copy fails core compatibility, schema compatibility, integrity or its declared dependencies
- **THEN** the first lower-priority copy passing all existing eligibility gates SHALL supply its commands and activated source
- **AND** rejected copies SHALL NOT supply dependency availability, versions, schema/bridge effects or category mounts
- **AND** a compatible higher-priority copy SHALL retain its priority and disabled copies SHALL remain unread

#### Scenario: Dependency fallback uses a coherent selected set

- **GIVEN** a selected provider falls back to another version and same-name consumers have distinct requirements
- **WHEN** selection checks declared dependencies before registration effects
- **THEN** selection SHALL reconsider eligible consumer copies against the actual selected versions
- **AND** missing providers SHALL NOT be supplied by rejected or disabled candidates
- **AND** already consistent dependency cycles SHALL retain existing edge-local compatibility
- **AND** contradictory priority selections SHALL terminate with explicit refusal rather than oscillation or partial registration
- **AND** registration SHALL NOT introduce a global dependency solver or downgrade a provider solely to satisfy a consumer

#### Scenario: A candidate self-dependency uses its own selected version

- **GIVEN** two same-name signed copies declare a versioned dependency on their own module identity
- **WHEN** the higher-priority version fails that constraint and the fallback satisfies it
- **THEN** candidate evaluation SHALL use the candidate's own enabled identity and actual version
- **AND** the fallback SHALL activate without downgrading or changing any other provider's priority

#### Scenario: Extensionless executable payloads cannot evade authenticated inventory

- **GIVEN** an otherwise authentic project bundle contains an unsigned file under a signing-excluded directory
- **AND** that file has executable mode bits or a shebang, ELF, PE, or Mach-O executable header regardless of its suffix
- **WHEN** public registration checks project-root authority in either grouping mode
- **THEN** the omitted executable SHALL fail closed before activation
- **AND** unchanged signed artifacts and ordinary excluded non-executable diagnostics SHALL retain loading
- **AND** admission SHALL inspect bytes and mode only, without executing candidate artifacts

#### Scenario: Every canonical identity field has genuine signature coverage

- **GIVEN** each noncanonical publisher, tier, category, or bundle group variant has a genuine valid artifact signature
- **WHEN** public project registration applies its existing validation and official-root policy
- **THEN** every variant SHALL remain inactive in both grouping modes
- **AND** the equivalent canonical signed bundle SHALL retain its command

#### Scenario: Every executable mode class and Mach-O encoding is covered

- **GIVEN** an otherwise authentic project artifact contains an unsigned excluded file
- **AND** only its owner, group, or other execute permission bit is set, or its bytes use any thin/fat 32/64-bit Mach-O magic in either byte order
- **WHEN** public project registration checks the file in either grouping mode
- **THEN** each individual mode/header class SHALL be refused before activation
- **AND** canonical signed compatibility SHALL remain, and probes SHALL be inspected without execution

#### Scenario: Bounded selectors preserve every executable encoding observation

- **GIVEN** the protected native proof executor admits at most100 exact selectors
- **WHEN** executable encoding controls consolidate owner/group/other modes and paired registration modes
- **THEN** every probe's genuine signature, canonical compatibility, root admission and active-source result is observed before aggregate denial assertions
- **AND** the seven existing accepted93 files and all runtime/proof execution limits remain unchanged

#### Scenario: Project package path links cannot grant root authority

- **GIVEN** a genuinely signed official bundle reached through a symlink at its package directory, workspace `.specfact` directory or workspace `modules` directory
- **WHEN** project registration runs in either grouping mode
- **THEN** the linked package SHALL obtain no root command or source import authority
- **AND** rejection SHALL occur before selection effects while preserving eligible lower-priority installations
- **AND** ordinary signed directories reached from the canonical workspace SHALL retain authority, including workspaces originally selected through system path aliases
- **AND** package and owned-store link checks SHALL be repeated after artifact authentication and final inventory verification, before granting official project authority
- **AND** this admission observation SHALL NOT claim atomic sealing against later filesystem mutation

#### Scenario: Omitted native library denial retains legacy routing coverage

- **GIVEN** each omitted `.dll`, `.dylib`, `.bundle`, `.so` or `.pyd` file under a genuinely signed project bundle's excluded diagnostics directory
- **WHEN** legacy registration runs after an authentic compatibility control
- **THEN** each bundle SHALL obtain no root command or source import authority
- **AND** all named suffix observations SHALL be collected before the aggregate assertion without executing the probe bytes

### Admission observation boundary

Filesystem admission authenticates the source snapshot and executable inventory observed during admission and standard cache compilation. It prevents unauthenticated paths from gaining authority during those steps. The registered loader later reads the live filesystem. A concurrent writer replacing otherwise admitted ordinary files after the final observation and before a later lazy load is outside this guarantee. This change does not seal the filesystem or execute an immutable snapshot. Official project category-root authority requires unlinked package and owned workspace-store components at the final admission observation. Category-less, unreserved legacy routing keeps its existing compatibility policy.

#### Scenario: Path-link controls preserve the protected selector bound

- **GIVEN** the unchanged100-selector execution limit and93 preceding exact selectors
- **WHEN** new path-link and legacy native controls are mapped
- **THEN** the same18 encoding observations SHALL be recorded in four nodes before aggregate assertions
- **AND** two path-link nodes SHALL record all three owned path components plus installed fallback in each grouping mode
- **AND** one legacy native node SHALL record all five suffix denials before its assertion
- **AND** no prior93 selector, analyzer pin, execution budget or proof limit SHALL be weakened
