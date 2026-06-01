## MODIFIED Requirements

### Requirement: Package Manager Runtime Checks Block Pull Requests

CI SHALL execute command contract smoke tests through the supported package-manager launch paths before pull requests can merge.

#### Scenario: Pull request package-manager matrix

- **GIVEN** a pull request changes CLI runtime, command docs, command validators, packaging, module discovery, or CI smoke scripts
- **WHEN** PR validation runs
- **THEN** CI executes a runtime matrix that covers hatch, pip wheel install, pipx install, uv run, and uv tool or uvx execution
- **AND** each matrix leg validates root help, unknown command guidance, module command discovery, generated command overview checks, and representative official module help paths.

#### Scenario: Matrix failures identify package-manager context

- **GIVEN** one matrix leg fails
- **WHEN** CI reports the failure
- **THEN** the failure output identifies the package-manager launcher, command path, exit code, and relevant stdout/stderr excerpt
- **AND** the PR is blocked until the mismatch is fixed or an explicit documented exception is accepted.
