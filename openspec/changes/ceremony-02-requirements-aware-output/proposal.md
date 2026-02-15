# Change: Ceremony Integration — Requirements-Aware Ceremony Output

## Why




Current backlog ceremony commands (`backlog ceremony refinement`, `backlog ceremony standup`, `backlog ceremony planning`) operate purely on technical signals — story points, acceptance criteria quality, spec coverage. They don't surface business requirement coverage, value gaps, or architectural readiness. This means ceremonies miss the most impactful signals: "Is the business case defined?" and "Does the architecture support this?" Extending ceremony output with a `--with-requirements` flag enriches refinement and planning with business context, catching value gaps before they become code.

## What Changes




- **EXTEND**: `specfact backlog ceremony refinement` extended with `--with-requirements` flag:
  - Show per-story business requirement status (defined/missing/incomplete)
  - Flag stories missing business value quantification
  - Flag stories with requirements but no solution architecture
  - Detect orphaned specs (spec exists but no business requirement)
  - Recommendation engine: "Defer until business case clarified" for value-undefined stories
- **EXTEND**: `specfact backlog ceremony planning` extended with `--with-requirements` flag:
  - Sprint readiness assessment: business value coverage percentage
  - Risk items: stories entering sprint without full traceability chain
  - Capacity allocation by business outcome (not just story points)
- **EXTEND**: `specfact backlog ceremony standup` extended with `--with-requirements` flag:
  - Yesterday/today items annotated with business requirement they serve
  - Blockers annotated with impacted business outcomes
- **NEW**: Ceremony output sections: "Business Value Coverage", "Business Risk Items", "Ready for Sprint" with profile-aware detail level (solo gets summary only, enterprise gets full breakdown)
- **EXTEND**: Ceremony cockpit (ceremony-cockpit-01) integration — requirements-aware output available through all ceremony aliases

## Capabilities
### New Capabilities

- `ceremony-requirements-awareness`: Requirements-aware enrichment for backlog ceremony commands (`backlog ceremony refinement`, `backlog ceremony planning`, `backlog ceremony standup`) showing business value coverage, risk items, orphaned specs, and sprint readiness with profile-aware detail levels.

### Modified Capabilities

- `backlog-refinement`: Extended with `--with-requirements` flag for business context enrichment
- `daily-standup`: Extended with `--with-requirements` flag for business outcome annotations


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #245
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/245>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 108a457fc6bbdc2f -->