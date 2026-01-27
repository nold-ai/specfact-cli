## ADDED Requirements

### Requirement: Backlog Item Refinement Command

The system SHALL provide a `specfact backlog refine` command that enables teams to standardize backlog items using AI-assisted template matching and refinement.

#### Scenario: Refine backlog items with template detection

- **WHEN** a user runs `specfact backlog refine --adapter github --search "auth"`
- **THEN** the system fetches matching backlog items, detects template matches with confidence scores, and identifies items needing refinement

#### Scenario: Interactive refinement workflow

- **WHEN** a backlog item has low template confidence (<0.6)
- **THEN** the system prompts the user to accept AI-refined content, skip, or edit manually

#### Scenario: High-confidence auto-accept

- **WHEN** a refined item has confidence >= 0.85 and `--auto-accept-high-confidence` flag is set
- **THEN** the system automatically accepts the refinement without user confirmation

#### Scenario: Update remote backlog after refinement

- **WHEN** a user accepts a refined backlog item
- **THEN** the system updates the remote backlog (GitHub/ADO) with the refined content and records refinement metadata in source tracking

#### Scenario: Import refined items to OpenSpec

- **WHEN** a user specifies `--bundle` or `--auto-bundle` flag during refinement
- **THEN** the system imports refined items into the specified OpenSpec bundle with template metadata recorded

#### Scenario: Filter by common fields

- **WHEN** a user runs `specfact backlog refine --adapter github --labels "feature,enhancement" --state "open" --assignee "user1"`
- **THEN** the system fetches backlog items and filters by matching labels, state, and assignee (using BacklogItem fields)

#### Scenario: Filter by iteration/sprint

- **WHEN** a user runs `specfact backlog refine --adapter ado --iteration "Project\\Sprint 1" --sprint "Sprint 1"`
- **THEN** the system fetches only backlog items matching the specified iteration and sprint filters

#### Scenario: Filter by persona

- **WHEN** a user runs `specfact backlog refine --adapter github --persona product-owner`
- **THEN** the system uses persona-specific templates (product-owner-focused user story template) for refinement

#### Scenario: Filter by framework

- **WHEN** a user runs `specfact backlog refine --adapter ado --framework scrum`
- **THEN** the system uses framework-specific templates (Scrum user story template) for refinement

### Requirement: Backlog Item Domain Model

The system SHALL provide a unified `BacklogItem` domain model that represents backlog items from any provider (GitHub, ADO, JIRA, etc.) with lossless data preservation.

#### Scenario: BacklogItem creation from GitHub issue

- **WHEN** a GitHub issue is fetched via adapter
- **THEN** the system creates a `BacklogItem` with normalized fields (title, body_markdown, state) and preserves provider-specific data in `provider_fields`

#### Scenario: Lossless round-trip preservation

- **WHEN** a `BacklogItem` is created from a provider and then updated back to the provider
- **THEN** all original provider-specific data is preserved via `provider_fields`, ensuring zero data loss

#### Scenario: Refinement state tracking

- **WHEN** a backlog item is refined
- **THEN** the system records `detected_template`, `template_confidence`, `refined_body`, `refinement_applied`, and `refinement_timestamp` in the item

#### Scenario: Sprint and release tracking

- **WHEN** a backlog item is created from a provider (ADO, GitHub, Jira)
- **THEN** the system extracts and normalizes sprint and release information into `sprint` and `release` fields, preserving original provider format in `provider_fields`

### Requirement: Template Registry Management

The system SHALL provide a template registry that manages backlog templates with detection, matching, and scoping capabilities.

#### Scenario: Register corporate template

- **WHEN** a template is registered with scope "corporate"
- **THEN** the template is available to all teams and projects

#### Scenario: Register team-specific template

- **WHEN** a template is registered with scope "team" and team_id
- **THEN** the template is only available to that specific team

#### Scenario: List available templates

- **WHEN** a user queries the template registry
- **THEN** the system returns all templates matching the requested scope (corporate, team, or user)

#### Scenario: Persona-specific template selection

- **WHEN** a template is registered with `personas: ["product-owner"]`
- **THEN** the template is only used when `--persona product-owner` is specified or when resolving templates for product-owner workflows

#### Scenario: Framework-specific template selection

- **WHEN** a template is registered with `framework: "scrum"`
- **THEN** the template is only used when `--framework scrum` is specified or when resolving templates for Scrum workflows

#### Scenario: Provider-specific template selection

- **WHEN** a template is registered with `provider: "ado"`
- **THEN** the template is prioritized when refining items from Azure DevOps adapter

#### Scenario: Priority-based template resolution

- **WHEN** multiple templates match (provider+framework+persona, framework+persona, framework, default)
- **THEN** the system selects the most specific match (provider+framework+persona) and falls back to less specific matches if not found
