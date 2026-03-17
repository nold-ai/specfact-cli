# Change Validation Report: docs-02-core-docs-canonical-portal

**Validation Date**: 2026-03-17
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Dry-run documentation dependency and ownership analysis

## Executive Summary

- Breaking Changes: 0 detected at runtime
- Dependent Files: Multiple docs entry points and bundle-focused pages in `README.md` and `docs/`
- Impact Level: Medium (public docs topology and ownership language change)
- Validation Result: Pass
- User Decision: Proceed with separate core and modules docs changes

## Breaking Changes Detected

None at runtime. This change is documentation-architecture work only.

Potential reader-facing regression risk exists if core docs remove or reword module pages without clear handoff links, but that is a navigation/content continuity risk rather than a runtime/API break.

## Dependencies Affected

### Critical Alignment Dependencies

- `README.md` still points readers at the modules GitHub Pages project URL and describes module docs migration as future work.
- `docs/index.md` still presents bundle docs as temporarily hosted in core while the modules repo already declares itself canonical.
- `docs/_layouts/default.html` will need coordinated top-level navigation changes so the public IA exposes `Docs Home`, `Core CLI`, and `Modules`.
- Multiple bundle-focused pages in `docs/guides/`, `docs/reference/`, and `docs/adapters/` still carry the current-release temporary-hosting note and will need a keep/handoff/retire decision.

### Cross-Repository Dependencies

- `specfact-cli-modules` must publish aligned landing copy and top navigation for the modules site.
- Cloudflare/public-domain work is an external dependency for final public URL cutover, but not a blocker for creating the docs ownership contract and handoff content first.

## Impact Assessment

- **Code Impact**: None expected
- **Docs Impact**: High; README, landing page, shared layout, marketplace pages, and module-focused guides/reference pages are all in scope
- **Test Impact**: New lightweight docs validation or assertion coverage is justified to prevent ownership-language drift
- **Release Impact**: Low-to-medium; the main risk is temporary reader confusion during the transition if navigation and handoff pages are incomplete

## Format Validation

- **proposal.md Format**: Pass
- **tasks.md Format**: Pass
- **specs Format**: Pass
- **Config.yaml Compliance**: Pass

## OpenSpec Validation

- **Status**: Pass
- **Command**: `openspec validate docs-02-core-docs-canonical-portal --strict`
- **Issues Found/Fixed**: 0
