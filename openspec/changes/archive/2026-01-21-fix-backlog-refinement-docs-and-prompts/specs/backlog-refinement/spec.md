## MODIFIED Requirements

### Requirement: Backlog Item Refinement Command

The system SHALL provide a `specfact backlog refine` command that enables teams to standardize backlog items using AI-assisted template matching and refinement.

#### Scenario: Documentation accuracy for cross-adapter state mapping

- **WHEN** cross-adapter state mapping is implemented (GitHub ↔ ADO, etc.)
- **THEN** the system documentation and AI IDE prompts SHALL accurately document:
  - Generic state mapping mechanism using OpenSpec as intermediate format
  - State preservation during cross-adapter sync
  - Bidirectional state mapping behavior (source → target and target → source)
  - Examples for common adapter pairs (GitHub ↔ ADO)

#### Scenario: AI IDE prompt completeness

- **WHEN** backlog refinement features are implemented
- **THEN** the AI IDE slash command prompt (`specfact.backlog-refine.md`) SHALL include:
  - All available CLI parameters and options
  - Complete workflow examples for all supported adapters
  - Cross-adapter state mapping documentation
  - Field preservation policy details
  - OpenSpec integration examples

#### Scenario: User documentation completeness

- **WHEN** backlog refinement features are implemented
- **THEN** user documentation (guides, command reference) SHALL include:
  - Complete parameter reference
  - Cross-adapter state mapping explanation
  - State preservation guarantees
  - Workflow examples for all supported use cases
  - Integration with `sync bridge` command

#### Scenario: ADO adapter configuration and API endpoint documentation

- **WHEN** ADO adapter fixes are implemented (WIQL API, on-premise support, organization-level endpoints)
- **THEN** the system documentation SHALL accurately document:
  - Azure DevOps Services (cloud) vs Azure DevOps Server (on-premise) differences
  - WIQL query endpoint requirements (POST with api-version parameter)
  - Work items batch GET endpoint (organization-level, not project-level)
  - URL format examples for both cloud and on-premise configurations
  - Base URL configuration options (with/without collection in base_url)
  - Error handling and troubleshooting for ADO API calls
