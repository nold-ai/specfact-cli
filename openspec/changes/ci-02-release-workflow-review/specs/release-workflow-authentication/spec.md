## ADDED Requirements

### Requirement: Authentication does not execute the reviewed wrapper

Documentation consumers SHALL authenticate all external module source roots with the base checkout verifier and key
before exporting imports, independently of any PR-owned authentication wrapper. They SHALL retain valid bootstrap
when the trusted base contains only the canonical verifier and key.

#### Scenario: A hostile wrapper cannot suppress authentication

- **GIVEN** a reviewed wrapper that returns success without verification
- **WHEN** either source consumer receives modified, unsigned, or unexpected source bundles
- **THEN** authentication fails before exports

#### Scenario: A hostile wrapper cannot break valid authenticated sources

- **GIVEN** correctly signed sources and a reviewed wrapper that raises if executed
- **WHEN** either source consumer authenticates with a base lacking that wrapper
- **THEN** authentication succeeds without executing the reviewed wrapper

### Requirement: Native workflow tests have an explicit runtime

Every CI job collecting native JavaScript workflow tests SHALL set up the repository-pinned Node version before
execution. Local developer prerequisites SHALL identify the same required runtime.

#### Scenario: Test jobs do not depend on incidental runner tools

- **WHEN** tests, Python3.11 compatibility or scheduled dependency compatibility collects workflow regressions
- **THEN** a SHA-pinned Node setup step selects Node24.16.0 before the test commands
