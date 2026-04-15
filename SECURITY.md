# Security Policy

## Supported Versions

We currently support the following versions of SpecFact CLI with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of SpecFact CLI seriously. If you believe you've found a security vulnerability, please follow these guidelines for responsible disclosure:

### How to Report

Please **DO NOT** report security vulnerabilities through public GitHub issues.

Instead, please report them via email to:

- `hello@noldai.com`

Please include the following information in your report:

1. Description of the vulnerability
2. Steps to reproduce the issue
3. Potential impact of the vulnerability
4. Any suggested mitigations (if available)

### What to Expect

After you report a vulnerability:

- You'll receive acknowledgment of your report within 48 hours.
- We'll provide an initial assessment of the report within 5 business days.
- We aim to validate and respond to reports as quickly as possible, typically within 10 business days.
- We'll keep you informed about our progress addressing the issue.

### Disclosure Policy

- Please give us a reasonable time to address the issue before any public disclosure.
- We will coordinate with you to ensure that a fix is available before any disclosure.
- We will acknowledge your contribution in our release notes (unless you prefer to remain anonymous).

## Security Best Practices

When using SpecFact CLI in your environment:

- Keep your installation updated with the latest releases.
- Restrict access to the server and its API endpoints.
- Use strong authentication mechanisms when exposing the service.
- Implement proper input validation for all data sent to the service.
- Monitor logs for unexpected access patterns.

Thank you for helping keep SpecFact CLI and our users secure!

## Known dependency risks and Phase 2 plans

### gitpython — CVE history (monitored)

`gitpython` has a recurring CVE history:

- **CVE-2022-24439** (CVSS 9.9) — fixed in 3.1.30+
- **CVE-2023-41040** (CVSS 4.3) — fixed in 3.1.37+
- **CVE-2023-40590** (CVSS 7.8) — fixed in 3.1.40+

**Current pin**: `gitpython>=3.1.45` (all three CVEs patched). Monitored via `hatch run security-audit`.

**Phase 2 plan**: Replace `gitpython` with `dulwich` (BSD-licensed). The migration requires a
3-file adapter rewrite (`src/specfact_cli/utils/git.py`,
`src/specfact_cli/versioning/analyzer.py`,
`src/specfact_cli/analyzers/code_analyzer.py`). Tracked in the `dep-security-cleanup` change.

### License compliance gate

Run `hatch run license-check` (wraps `scripts/check_license_compliance.py`) to verify that no
GPL/AGPL packages are present in module manifests and all dev-env GPL exceptions are documented
in `scripts/license_allowlist.yaml`.

Run `hatch run security-audit` (wraps `pip-audit --desc --strict`) to check for CVEs in the
installed environment. Any CVE with CVSS ≥ 7.0 is a blocker for release.
