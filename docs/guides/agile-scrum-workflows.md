# Agile/Scrum Workflows with SpecFact CLI

This guide explains how to use SpecFact CLI for agile/scrum workflows, including backlog management, sprint planning, dependency tracking, and Definition of Ready (DoR) validation.

## Overview

SpecFact CLI supports real-world agile/scrum practices through:

- **Definition of Ready (DoR)**: Automatic validation of story readiness for sprint planning
- **Dependency Management**: Track story-to-story and feature-to-feature dependencies
- **Prioritization**: Priority levels, ranking, and business value scoring
- **Sprint Planning**: Target sprint/release assignment and story point tracking
- **Business Value Focus**: User-focused value statements and measurable outcomes

## Persona-Based Workflows

SpecFact uses persona-based workflows where different roles work on different aspects:

- **Product Owner**: Owns requirements, user stories, business value, prioritization, sprint planning
- **Architect**: Owns technical constraints, protocols, contracts, architectural decisions, non-functional requirements, risk assessment, deployment architecture
- **Developer**: Owns implementation tasks, technical design, code mappings, test scenarios, Definition of Done

### Exporting Persona Artifacts

Export persona-specific Markdown files for editing:

```bash
# Export Product Owner view
specfact project export --bundle my-project --persona product-owner

# Export Developer view
specfact project export --bundle my-project --persona developer

# Export Architect view
specfact project export --bundle my-project --persona architect

# Export to custom location
specfact project export --bundle my-project --persona product-owner --output docs/backlog.md
```

The exported Markdown includes persona-specific content:

**Product Owner Export**:

- **Definition of Ready Checklist**: Visual indicators for each DoR criterion
- **Prioritization Data**: Priority, rank, business value scores
- **Dependencies**: Clear dependency chains (depends on, blocks)
- **Business Value**: User-focused value statements and metrics
- **Sprint Planning**: Target dates, sprints, and releases

**Developer Export**:

- **Acceptance Criteria**: Feature and story acceptance criteria
- **User Stories**: Detailed story context with tasks, contracts, scenarios
- **Implementation Tasks**: Granular tasks with file paths
- **Code Mappings**: Source and test function mappings
- **Sprint Context**: Story points, priority, dependencies, target sprint/release
- **Definition of Done**: Completion criteria checklist

**Architect Export**:

- **Technical Constraints**: Feature-level technical constraints
- **Architectural Decisions**: Technology choices, patterns, integration approaches
- **Non-Functional Requirements**: Performance, scalability, availability, security, reliability targets
- **Protocols & State Machines**: Complete protocol definitions with states and transitions
- **Contracts**: OpenAPI/AsyncAPI contract details
- **Risk Assessment**: Technical risks and mitigation strategies
- **Deployment Architecture**: Infrastructure and deployment patterns

### Importing Persona Edits

After editing the Markdown file, import changes back:

```bash
# Import Product Owner edits
specfact project import --bundle my-project --persona product-owner --source docs/backlog.md

# Import Developer edits
specfact project import --bundle my-project --persona developer --source docs/developer.md

# Import Architect edits
specfact project import --bundle my-project --persona architect --source docs/architect.md

# Dry-run to validate without applying
specfact project import --bundle my-project --persona product-owner --source docs/backlog.md --dry-run
```

The import process validates:

- **Template Structure**: Required sections present
- **DoR Completeness**: All DoR criteria met
- **Dependency Integrity**: No circular dependencies, all references exist
- **Priority Consistency**: Valid priority formats (P0-P3, MoSCoW)
- **Date Formats**: ISO 8601 date validation
- **Story Point Ranges**: Valid Fibonacci-like values

## Definition of Ready (DoR)

### DoR Checklist

Each story must meet these criteria before sprint planning:

- [x] **Story Points**: Complexity estimated (1, 2, 3, 5, 8, 13, 21...)
- [x] **Value Points**: Business value estimated (1, 2, 3, 5, 8, 13, 21...)
- [x] **Priority**: Priority level set (P0-P3 or MoSCoW)
- [x] **Dependencies**: Dependencies identified and validated
- [x] **Business Value**: Clear business value description present
- [x] **Target Date**: Target completion date set (optional but recommended)
- [x] **Target Sprint**: Target sprint assigned (optional but recommended)

### Example: Story with Complete DoR

```markdown
**Story 1**: User can login with email

**Definition of Ready**:
- [x] Story Points: 5 (Complexity)
- [x] Value Points: 8 (Business Value)
- [x] Priority: P1
- [x] Dependencies: 1 identified
- [x] Business Value: ✓
- [x] Target Date: 2025-01-15
- [x] Target Sprint: Sprint 2025-01

**Story Details**:
- **Story Points**: 5 (Complexity)
- **Value Points**: 8 (Business Value)
- **Priority**: P1
- **Rank**: 1
- **Target Date**: 2025-01-15
- **Target Sprint**: Sprint 2025-01
- **Target Release**: v2.1.0

**Business Value**:
Enables users to securely access their accounts, reducing support tickets by 30% and improving user satisfaction.

**Business Metrics**:
- Reduce support tickets by 30%
- Increase user login success rate to 99.5%
- Reduce password reset requests by 25%

**Dependencies**:
**Depends On**:
- STORY-000: User registration system

**Acceptance Criteria** (User-Focused):
- [ ] As a user, I can enter my email and password to log in
- [ ] As a user, I receive clear error messages if login fails
- [ ] As a user, I am redirected to my dashboard after successful login
```

## Dependency Management

### Story Dependencies

Track dependencies between stories:

```markdown
**Dependencies**:
**Depends On**:
- STORY-001: User registration system
- STORY-002: Email verification

**Blocks**:
- STORY-010: Password reset flow
```

### Feature Dependencies

Track dependencies between features:

```markdown
### FEATURE-001: User Authentication

#### Dependencies

**Depends On Features**:
- FEATURE-000: User Management Infrastructure

**Blocks Features**:
- FEATURE-002: User Profile Management
```

### Validation Rules

The import process validates:

1. **Reference Existence**: All referenced stories/features exist
2. **No Circular Dependencies**: Prevents A → B → A cycles
3. **Format Validation**: Dependency keys match expected format (STORY-001, FEATURE-001)

### Example: Circular Dependency Error

```bash
$ specfact project import --bundle my-project --persona product-owner --source backlog.md

Error: Agile/Scrum validation failed:
  - Story STORY-001: Circular dependency detected with 'STORY-002'
  - Feature FEATURE-001: Circular dependency detected with 'FEATURE-002'
```

## Prioritization

### Priority Levels

Use one of these priority formats:

- **P0-P3**: P0=Critical, P1=High, P2=Medium, P3=Low
- **MoSCoW**: Must, Should, Could, Won't
- **Descriptive**: Critical, High, Medium, Low

### Ranking

Use backlog rank (1 = highest priority):

```markdown
**Priority**: P1 | **Rank**: 1
```

### Business Value Scoring

Score features 0-100 for business value:

```markdown
**Business Value Score**: 75/100
```

### Example: Prioritized Feature

```markdown
### FEATURE-001: User Authentication

**Priority**: P1 | **Rank**: 1  
**Business Value Score**: 75/100  
**Target Release**: v2.1.0  
**Estimated Story Points**: 13

#### Business Value

Enables secure user access, reducing support overhead and improving user experience.

**Target Users**: end-user, admin

**Success Metrics**:
- Reduce support tickets by 30%
- Increase user login success rate to 99.5%
- Reduce password reset requests by 25%
```

## Sprint Planning

### Story Point Estimation

Use Fibonacci-like values: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 100

```markdown
- **Story Points**: 5 (Complexity)
- **Value Points**: 8 (Business Value)
```

### Target Sprint Assignment

Assign stories to specific sprints:

```markdown
- **Target Sprint**: Sprint 2025-01
- **Target Release**: v2.1.0
- **Target Date**: 2025-01-15
```

### Feature-Level Totals

Feature story point totals are automatically calculated:

```markdown
**Estimated Story Points**: 13
```

This is the sum of all story points for stories in this feature.

## Business Value Focus

### User-Focused Value Statements

Write stories with clear user value:

```markdown
**Business Value**:
As a user, I want to securely log in to my account so that I can access my personalized dashboard and manage my data.

**Business Metrics**:
- Reduce support tickets by 30%
- Increase user login success rate to 99.5%
- Reduce password reset requests by 25%
```

### Acceptance Criteria Format

Use "As a [user], I want [capability] so that [outcome]" format:

```markdown
**Acceptance Criteria** (User-Focused):
- [ ] As a user, I can enter my email and password to log in
- [ ] As a user, I receive clear error messages if login fails
- [ ] As a user, I am redirected to my dashboard after successful login
```

## Template Customization

### Override Default Templates

Create project-specific templates in `.specfact/templates/persona/`:

```bash
.specfact/
└── templates/
    └── persona/
        └── product-owner.md.j2  # Project-specific template
```

The project-specific template overrides the default template in `resources/templates/persona/`.

### Template Structure

Templates use Jinja2 syntax with these variables:

- `bundle_name`: Project bundle name
- `features`: Dictionary of features (key -> feature dict)
- `idea`: Idea section data
- `business`: Business section data
- `locks`: Section locks information

### Example: Custom Template Section

```jinja2
{% if features %}
## Features & User Stories

{% for feature_key, feature in features.items() %}
### {{ feature.key }}: {{ feature.title }}

**Priority**: {{ feature.priority | default('Not Set') }}
**Business Value**: {{ feature.business_value_score | default('Not Set') }}/100

{% if feature.stories %}
#### User Stories

{% for story in feature.stories %}
**Story {{ loop.index }}**: {{ story.title }}

**DoR Status**: {{ '✓ Complete' if story.definition_of_ready.values() | all else '✗ Incomplete' }}

{% endfor %}
{% endif %}

{% endfor %}
{% endif %}
```

## Validation Examples

### DoR Validation

```bash
$ specfact project import --bundle my-project --persona product-owner --source backlog.md

Error: Agile/Scrum validation failed:
  - Story STORY-001 (Feature FEATURE-001): Missing story points (required for DoR)
  - Story STORY-001 (Feature FEATURE-001): Missing value points (required for DoR)
  - Story STORY-001 (Feature FEATURE-001): Missing priority (required for DoR)
  - Story STORY-001 (Feature FEATURE-001): Missing business value description (required for DoR)
```

### Dependency Validation

```bash
$ specfact project import --bundle my-project --persona product-owner --source backlog.md

Error: Agile/Scrum validation failed:
  - Story STORY-001: Dependency 'STORY-999' does not exist
  - Story STORY-001: Circular dependency detected with 'STORY-002'
  - Feature FEATURE-001: Dependency 'FEATURE-999' does not exist
```

### Priority Validation

```bash
$ specfact project import --bundle my-project --persona product-owner --source backlog.md

Error: Agile/Scrum validation failed:
  - Story STORY-001: Invalid priority 'P5' (must be P0-P3, MoSCoW, or Critical/High/Medium/Low)
  - Feature FEATURE-001: Invalid priority 'Invalid' (must be P0-P3, MoSCoW, or Critical/High/Medium/Low)
```

### Date Format Validation

```bash
$ specfact project import --bundle my-project --persona product-owner --source backlog.md

Error: Agile/Scrum validation failed:
  - Story STORY-001: Invalid date format '2025/01/15' (expected ISO 8601: YYYY-MM-DD)
  - Story STORY-001: Warning - target date '2024-01-15' is in the past (may need updating)
```

## Best Practices

### 1. Complete DoR Before Sprint Planning

Ensure all stories meet DoR criteria before assigning to sprints:

```bash
# Validate DoR completeness
specfact project import --bundle my-project --persona product-owner --source backlog.md --dry-run
```

### 2. Track Dependencies Early

Identify dependencies during story creation to avoid blockers:

```markdown
**Dependencies**:
**Depends On**:
- STORY-001: User registration (must complete first)
```

### 3. Use Consistent Priority Formats

Choose one priority format per project and use consistently:

- **Option 1**: P0-P3 (recommended for technical teams)
- **Option 2**: MoSCoW (recommended for business-focused teams)
- **Option 3**: Descriptive (Critical/High/Medium/Low)

### 4. Set Business Value for All Stories

Every story should have a clear business value statement:

```markdown
**Business Value**:
Enables users to securely access their accounts, reducing support tickets by 30%.
```

### 5. Use Story Points for Capacity Planning

Track story points to estimate sprint capacity:

```markdown
**Estimated Story Points**: 21  # Sum of all stories in feature
```

## Troubleshooting

### Validation Errors

If import fails with validation errors:

1. **Check DoR Completeness**: Ensure all required fields are present
2. **Verify Dependencies**: Check that all referenced stories/features exist
3. **Validate Formats**: Ensure priority, dates, and story points use correct formats
4. **Review Business Value**: Ensure business value descriptions are present and meaningful

### Template Issues

If template rendering fails:

1. **Check Template Syntax**: Verify Jinja2 syntax is correct
2. **Verify Variables**: Ensure template variables match exported data structure
3. **Test Template**: Use `--dry-run` to test template without importing

## Related Documentation

- [Persona Workflows](../reference/persona-workflows.md) - Detailed persona workflow documentation
- [Project Bundle Structure](../reference/directory-structure.md) - Project bundle organization
- [Template Customization](../guides/template-customization.md) - Advanced template customization
