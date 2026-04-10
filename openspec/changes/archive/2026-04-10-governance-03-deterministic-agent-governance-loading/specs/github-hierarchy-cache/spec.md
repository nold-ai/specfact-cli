## MODIFIED Requirements

### Requirement: Repository governance must use cache-first hierarchy lookup

Repository governance instructions SHALL direct contributors and agents to consult the local hierarchy cache before performing manual GitHub lookups for Epic or Feature parenting.

#### Scenario: Cache-first governance guidance

- **WHEN** a contributor reads `AGENTS.md` or `openspec/config.yaml` for GitHub issue setup guidance
- **THEN** the instructions tell them to consult the local hierarchy cache first
- **AND** the instructions define when the sync script must be rerun to refresh stale hierarchy metadata
- **AND** the instructions state that the cache is local ephemeral state and must not be committed

#### Scenario: Session bootstrap refreshes missing or stale cache

- **WHEN** an agent starts a governance-sensitive session that depends on GitHub hierarchy metadata
- **AND** the local hierarchy cache is missing or stale according to repository-defined freshness rules
- **THEN** the bootstrap guidance SHALL require rerunning the hierarchy cache sync script before continuing with issue-parenting or blocker-resolution work
- **AND** the compact governance flow SHALL treat the refresh as part of deterministic startup rather than an optional later reminder
