# Capability: core-docs-progressive-nav

Core docs site sidebar provides a 6-section progressive navigation structure.

## Scenarios

### Scenario: Sidebar renders 6 sections in correct order

Given the core docs site is built with Jekyll
When a user visits any page on docs.specfact.io
Then the sidebar displays sections in order: Getting Started, Core CLI, Module System, Architecture, Reference, Migration

### Scenario: Getting Started section contains beginner-friendly entries

Given the sidebar Getting Started section
When a user expands the section
Then it contains: Installation, 5-Minute Quickstart, Profiles & IDE Setup
And does NOT contain module-specific tutorials (backlog quickstart, standup, refine)

### Scenario: Core CLI section links to command reference pages

Given the sidebar Core CLI section
When a user expands the section
Then it contains links to: specfact init, specfact module, specfact upgrade, Operational Modes, Debug Logging

### Scenario: Moved files redirect to new locations

Given a file was moved from its old location
When a user visits the old URL
Then they are redirected to the new URL via jekyll-redirect-from
