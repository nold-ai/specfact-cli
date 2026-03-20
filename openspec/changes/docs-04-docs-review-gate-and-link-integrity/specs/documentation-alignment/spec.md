## ADDED Requirements

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
