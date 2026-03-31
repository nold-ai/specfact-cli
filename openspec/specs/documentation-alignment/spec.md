# documentation-alignment Specification

## Purpose
TBD - created by archiving change arch-08-documentation-discrepancies-remediation. Update Purpose after archive.
## Requirements
### Requirement: Module system status in docs

The published architecture documentation SHALL state that the module system is production-ready (e.g. since v0.27) and SHALL NOT describe it as "transitioning" or "experimental."

#### Scenario: Reader checks module system status
- **GIVEN** the published architecture documentation (e.g. docs/reference/architecture.md, docs/architecture/module-system.md)
- **WHEN** a reader looks for the current state of the module system
- **THEN** the docs state production-ready status
- **AND** do not use "transitioning" or "experimental" for the module system

### Requirement: BridgeAdapter interface documented

The adapter documentation SHALL include the full BridgeAdapter interface: detect, import_artifact, export_artifact, load_change_tracking, save_change_tracking (or equivalent), with current behavior and contracts.

#### Scenario: Developer implements BridgeAdapter
- **GIVEN** the adapter documentation
- **WHEN** a developer implements or extends a BridgeAdapter
- **THEN** the documented interface includes all methods above
- **AND** contracts and usage are described

### Requirement: Architecture layers match codebase

The architecture overview SHALL describe the actual layers (Specification, Contract, Enforcement, and where relevant Adapter, Analysis, Module layers) so they match the codebase structure.

#### Scenario: Reader learns layer structure
- **GIVEN** the architecture overview
- **WHEN** a reader learns the high-level layer structure
- **THEN** the docs describe actual layers present in code
- **AND** do not omit Adapter, Analysis, or Module layers where they exist

### Requirement: Operational modes clarity

The documentation for CI/CD and CoPilot modes SHALL clarify current mode detection and any limitations (e.g. mode-specific behavior as planned), and SHALL NOT imply full mode implementations that do not exist.

#### Scenario: Reader checks mode implementation
- **GIVEN** the documentation for CI/CD and CoPilot modes
- **WHEN** a reader checks what is implemented
- **THEN** current detector behavior is stated
- **AND** planned vs implemented behavior is distinguished

### Requirement: CommandRegistry and module structure documented

The architecture or module docs SHALL describe lazy loading, metadata caching, and the required module package structure (e.g. module-package.yaml, src/<name>/main.py) and naming conventions.

#### Scenario: Developer needs registry or module layout details
- **GIVEN** the architecture or module docs
- **WHEN** a developer needs implementation details for the command registry or module layout
- **THEN** lazy loading and metadata caching are described
- **AND** required module package structure and naming are documented

### Requirement: ToolCapabilities and error handling documented

The ToolCapabilities model and adapter selection SHALL be documented; error handling patterns (custom exceptions, logging) SHALL be described in reference or adapter documentation.

#### Scenario: Developer looks for capabilities or error handling
- **GIVEN** the reference or adapter documentation
- **WHEN** a developer looks for adapter capabilities or error handling
- **THEN** ToolCapabilities and adapter selection are documented
- **AND** error handling patterns are described

### Requirement: Terminology and version consistency

The documentation set SHALL use consistent terminology (e.g. Project Bundle, Plan Bundle) and SHALL standardize or remove version references that cause confusion.

#### Scenario: Same concept referenced across docs
- **GIVEN** the documentation set
- **WHEN** the same concept is referenced
- **THEN** terminology is consistent
- **AND** version references are standardized or removed where confusing

### Requirement: Diagrams reference only existing or planned components

Any Mermaid or component diagram in the docs SHALL show only components that exist in the codebase or are clearly marked as planned; non-existent components (e.g. unimplemented "DevOps Adapters") SHALL be removed or relabeled.

#### Scenario: Reader interprets diagram
- **GIVEN** any Mermaid or component diagram in the docs
- **WHEN** a reader interprets the diagram
- **THEN** only existing or clearly planned components are shown
- **AND** non-existent components are removed or relabeled

### Requirement: Performance metrics current or removed

Any stated performance or timing in the docs SHALL reflect current benchmarks or SHALL be removed if outdated.

#### Scenario: Docs publish performance claims
- **GIVEN** any stated performance or timing (e.g. "typical execution: < 10s")
- **WHEN** the docs are published
- **THEN** metrics reflect current benchmarks or are removed if outdated

### Requirement: Live docs reflect lean-core and grouped bundle command topology

The live authored documentation set SHALL use command examples and migration guidance that match the currently shipped core and bundle command groups, and SHALL NOT present removed or transitional command families as current syntax. The core docs site SHALL focus exclusively on core platform concerns and SHALL redirect module-specific workflow content to modules.specfact.io.

#### Scenario: Core docs site excludes module-specific workflow content

- **GIVEN** the docs.specfact.io landing page (index.md)
- **WHEN** a reader arrives at the docs home
- **THEN** the page clearly separates core platform concerns from module-specific workflows
- **AND** provides direct links to modules.specfact.io for bundle-specific guidance

#### Scenario: Core site landing page delineates core vs modules

- **GIVEN** the docs.specfact.io landing page (index.md)
- **WHEN** a reader arrives at the docs home
- **THEN** the page clearly separates core platform concerns from module-specific workflows
- **AND** provides direct links to modules.specfact.io for bundle-specific guidance

#### Scenario: Getting Started section focuses on platform bootstrap

- **GIVEN** the Getting Started section of the core docs
- **WHEN** a new user follows the getting started path
- **THEN** it covers installation, quickstart, and profiles/IDE setup
- **AND** does NOT include module-specific tutorials as inline content
- **AND** links to modules.specfact.io for module workflow tutorials

### Requirement: Marketplace guidance is discoverable and non-duplicative

Marketplace, bundle installation, dependency, trust, and publishing documentation SHALL be available through clear entry points and SHALL avoid contradictory or duplicate guidance across README, landing pages, guides, and reference pages.

#### Scenario: Reader looks for marketplace workflow guidance

- **WHEN** a reader wants to install, trust, publish, or understand official bundles
- **THEN** the docs provide a discoverable path from README or docs landing into marketplace-specific pages
- **AND** they provide a clear path into the modules docs site for bundle-specific deep guidance
- **AND** terminology, command examples, and workflow descriptions are consistent across those pages.

### Requirement: Command reference reflects ownership and package boundaries

The command reference and migration guidance SHALL map old flat or pre-split syntax to currently shipped command groups and supported parameter forms, and SHALL NOT redirect readers from one removed surface to another removed surface.

#### Scenario: Reader checks command reference

- **WHEN** a reader opens command reference documentation
- **THEN** the reference identifies which commands belong to core and which are provided by installed bundles
- **AND** bundle command coverage is grouped by category or package boundary
- **AND** readers can navigate from command docs to the relevant modules docs without ambiguity.

#### Scenario: Reader checks migration mapping for removed syntax

- **WHEN** a reader opens command reference or migration guidance to translate older SpecFact examples
- **THEN** the docs identify whether a legacy surface still exists, moved to a current command group, or no longer has a direct supported equivalent
- **AND** the guidance uses currently executable commands and current option names for any documented replacement path
- **AND** the docs do not present `project plan` as the replacement for removed flat commands in the post-split CLI

### Requirement: Markdown quality workflow auto-fixes low-risk issues before enforcement
The documentation workflow SHALL automatically fix low-risk Markdown issues during pre-commit checks before enforcing markdown lint failures for non-fixable or higher-risk issues.

#### Scenario: Contributor stages Markdown changes with trivial spacing issues
- **WHEN** a contributor stages Markdown files and runs the repository pre-commit checks
- **THEN** the workflow attempts safe markdown auto-fixes first using the configured markdown lint tooling
- **AND** any auto-fixed Markdown files are re-staged automatically
- **AND** markdown lint still runs afterward to fail on remaining non-fixable issues

### Requirement: Cross-site links to modules docs use real published paths

Authored links from `specfact-cli` docs to `https://modules.specfact.io/...` SHALL target the modules page’s actual published `permalink` (or default-derived path), and SHALL NOT assume the same path shape as core docs (for example `/guides/<name>/` on core does not imply `/guides/<name>/` on modules).

#### Scenario: Contributor adds a handoff or reference link to modules

- **WHEN** a contributor adds or updates a link to the canonical modules docs site
- **THEN** the path segment matches the target file’s `permalink` in `specfact-cli-modules` or the URL contract reference
- **AND** contributors can discover rules from `docs/reference/documentation-url-contract.md` on the core site

### Requirement: Navigation-owned docs links match published permalinks

The docs landing page and sidebar navigation SHALL link to the actual published permalinks for their target pages, and SHALL NOT assume a section-prefixed route when the page publishes elsewhere.

#### Scenario: Reader opens a navigation-linked reference page

- **WHEN** a reader selects a reference or guide link from `docs/index.md` or `docs/_layouts/default.html`
- **THEN** the route resolves on `docs.specfact.io`
- **AND** the link target matches the page permalink declared in the authored docs source

### Requirement: Broken published docs routes are corrected in authored source

When docs review identifies a broken published route caused by authored permalink drift, the authored page or link source SHALL be corrected in the same remediation change so the published docs site remains internally consistent.

#### Scenario: Existing docs page has a mismatched permalink

- **WHEN** an authored docs page exists but the linked published route does not resolve because the page permalink differs
- **THEN** the remediation updates the authored permalink or the authored link source to restore route integrity
- **AND** the corrected route remains covered by docs review validation

### Requirement: Core handoff pages are thin summaries with a canonical modules link

Core docs pages that previously duplicated module-owned guides SHALL contain only a short summary, prerequisites, and a prominent link to the canonical URL on `modules.specfact.io` (per `permalink` in `specfact-cli-modules`), not the full guide body.

#### Scenario: Handoff page structure

- **WHEN** a reader opens a converted handoff page on `docs.specfact.io`
- **THEN** the page includes a brief summary of the topic
- **AND** it includes a prerequisites note
- **AND** it includes a prominent link to the full guide on the canonical modules docs site
- **AND** it does not include the duplicated long-form guide content owned by modules

### Requirement: Legacy URLs remain reachable

Handoff pages that previously published under alternate paths SHALL preserve `redirect_from` entries so old bookmarks do not 404.

#### Scenario: Redirect metadata preserved where applicable

- **WHEN** a handoff page had `redirect_from` for legacy paths
- **THEN** those entries remain in front matter after conversion
- **AND** the published URL still serves the thin handoff page

### Requirement: Canonical link targets match modules permalinks

Each converted page’s canonical link SHALL match the modules documentation `permalink` for that topic (which may be `/bundles/.../`, `/guides/.../`, `/integrations/.../`, or a root path), not an assumed mirror of the core `/guides/<name>/` path.

#### Scenario: URL contract compliance

- **WHEN** authors map core handoff pages to modules URLs
- **THEN** they use the checklist and `documentation-url-contract` rules
- **AND** each link targets the verified modules canonical URL for that guide

### Requirement: Entry-point messaging hierarchy is documented

Contributor-facing documentation SHALL define the required messaging hierarchy for first-contact
surfaces so README and homepage edits preserve the same structure over time.

#### Scenario: Contributor updates an entry-point page

- **WHEN** a contributor edits `README.md`, `docs/index.md`, or other designated entry-point copy
- **THEN** the guidance SHALL require them to preserve the ordering of:
  - product identity
  - why it exists
  - user value
  - how to start
  - deeper topology and branching guidance
- **AND** the guidance SHALL define validation/alignment as the product core, with “keep backlog,
  specs, tests, and code in sync” expressed as the user-visible result

### Requirement: Cross-site handoff copy stays aligned

Documentation alignment rules SHALL require core-docs and modules-docs entry points to describe the
same ownership split and onboarding handoff.

#### Scenario: Contributor edits core or modules landing copy

- **WHEN** a contributor updates landing-page copy that references `docs.specfact.io` or
  `modules.specfact.io`
- **THEN** the wording SHALL preserve the same explanation of what belongs to the core docs versus
  the modules docs
- **AND** cross-site links SHALL direct users to the intended next step rather than only the raw site
  URL

### Requirement: First-contact copy encodes the key user questions

Contributor guidance SHALL require entry-point copy to answer the key first-contact questions
explicitly enough that maintainers can review the page against them.

#### Scenario: Maintainer reviews a rewritten entry-point page

- **WHEN** a maintainer reviews changes to an entry-point page
- **THEN** they SHALL be able to verify that the page clearly answers:
  - what SpecFact is
  - why it exists
  - why a user should use it
  - what the user gets
  - how the user gets started
- **AND** the page SHALL not bury those answers underneath topology or implementation details

