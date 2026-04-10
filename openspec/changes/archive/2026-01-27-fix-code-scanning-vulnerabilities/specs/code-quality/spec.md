## MODIFIED Requirements

### Requirement: Code Security and Quality Standards

The system SHALL implement security best practices and maintain code quality standards to prevent vulnerabilities and follow least-privilege security models.

#### Scenario: ReDoS Vulnerability Mitigation

- **WHEN** processing markdown content with many newline repetitions
- **THEN** the system SHALL use line-by-line processing instead of regex patterns that may cause exponential backtracking
- **AND** the processing SHALL complete in reasonable time without denial of service

#### Scenario: URL Validation Security

- **WHEN** validating URLs for GitHub or Azure DevOps repositories
- **THEN** the system SHALL use proper URL parsing with `urllib.parse.urlparse()` to validate hostnames
- **AND** the system SHALL match hostnames exactly (not as substrings) to prevent matching malicious domains like "evil-github.com"

#### Scenario: GitHub Actions Least Privilege

- **WHEN** GitHub Actions workflows execute
- **THEN** each job SHALL have explicit `permissions` blocks defined
- **AND** permissions SHALL follow the least-privilege model (e.g., `contents: read` for read-only operations)
- **AND** workflows SHALL not use default GITHUB_TOKEN permissions without explicit declaration
