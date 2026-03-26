# Delta: documentation-alignment (handoff conversion)

Extends `documentation-alignment` so core handoff pages are thin summaries with canonical links to modules.

## ADDED Requirements

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
