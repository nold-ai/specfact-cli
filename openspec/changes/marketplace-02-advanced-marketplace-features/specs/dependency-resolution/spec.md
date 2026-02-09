# dependency-resolution Specification

## Purpose

Defines pip-compile style dependency resolution across all installed modules with conflict detection before installation.

## ADDED Requirements

### Requirement: Resolve pip dependencies across all modules

The system SHALL aggregate pip_dependencies from all installed modules and resolve constraints using pip-compile or fallback resolver.

#### Scenario: Dependencies resolved without conflicts
- **WHEN** module installation triggers dependency resolution
- **THEN** system SHALL collect pip_dependencies from all modules
- **AND** SHALL resolve constraints using pip-compile
- **AND** SHALL return list of resolved package versions

#### Scenario: Dependency conflict detected
- **WHEN** new module introduces conflicting pip dependency
- **THEN** system SHALL detect conflict before installation
- **AND** SHALL display error with conflicting packages and versions
- **AND** SHALL suggest resolution options
- **AND** SHALL NOT proceed with installation

#### Scenario: Fallback to basic pip resolver
- **WHEN** pip-tools is not available
- **THEN** system SHALL log warning "pip-tools not found, using basic resolver"
- **AND** SHALL attempt resolution with pip's built-in resolver
- **AND** SHALL proceed if no obvious conflicts

### Requirement: Install command resolves dependencies before proceeding

The system SHALL extend install command to resolve dependencies as pre-flight check.

#### Scenario: Install with dependency resolution
- **WHEN** user runs `specfact module install X`
- **THEN** system SHALL download module metadata
- **AND** SHALL simulate: all_modules = current + X
- **AND** SHALL resolve dependencies
- **AND** SHALL proceed only if resolution succeeds

#### Scenario: Skip dependency resolution with flag
- **WHEN** user runs `specfact module install X --skip-deps`
- **THEN** system SHALL skip dependency resolution
- **AND** SHALL install module and its pip_dependencies independently
- **AND** SHALL log warning about skipped resolution

### Requirement: Clear error messages for dependency conflicts

The system SHALL provide actionable error messages when dependency conflicts occur.

#### Scenario: Conflict error message format
- **WHEN** dependency conflict is detected
- **THEN** error SHALL include: conflicting packages, required versions, affected modules
- **AND** SHALL suggest: uninstall conflicting module, use --force, or skip conflicting module
