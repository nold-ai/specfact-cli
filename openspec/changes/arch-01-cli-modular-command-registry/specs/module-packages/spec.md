# Module Packages (Logical Features)

## ADDED Requirements

### Requirement: Logical Packages by Feature with Dedicated Folder Structure

The CLI SHALL group functionality into **logical module packages** by feature (e.g. "backlog refine", "backlog daily", "validate sidecar"). Each package SHALL live in a dedicated folder under a modules root and SHALL include its own **metadata**, **src**, **resources** (prompts, templates), and **tests**. Resources that are used only by one feature SHALL belong to that package; shared resources remain in core or a shared package.

**Rationale**: Prepares for an extensible ecosystem and future selective install; keeps each feature self-contained and versionable.

#### Scenario: Package Has Metadata and Standard Layout

**Given**: A module package "backlog_refine" exists under the modules root

**When**: Discovery runs (e.g. at startup or on specfact init)

**Then**: The package folder contains at least: `metadata.yaml` (with name, version, commands list, optional pip_dependencies and module_dependencies), `src/` (Python code for the feature), and optionally `resources/` (prompts, templates) and `tests/`

**Acceptance Criteria**:

- metadata.yaml is valid and includes: name, version, commands (list of command names this package provides)
- metadata MAY include: pip_dependencies, module_dependencies, tier, addon_id
- Package loader loads only that package's src (and its resources); no hard dependency on flat commands/ or resources/ layout for that feature

#### Scenario: Discovery Registers Packages with Registry

**Given**: Modules root contains one or more package folders with valid metadata.yaml

**When**: Module discovery runs

**Then**: Each package is registered with the CommandRegistry (or equivalent) so that each command name in package metadata is resolvable via the registry; the loader for that command loads only that package's code and resources

**Acceptance Criteria**:

- Registry receives entries for all commands listed in discovered package metadata
- Invoking a command loads only the package that provides it (and its dependencies if any)
- Design does not block future selective install (metadata and layout support filtering by installed packages later)

---

### Requirement: Core vs Package Grouping

The codebase SHALL distinguish **core** (bootstrapping, CommandRegistry, init scaffolding, auth/runtime/config, shared utils and models) from **module packages** (feature-specific commands and their resources). Moving existing code and resources into package folders MAY be incremental (e.g. one package at a time) but the structure and discovery SHALL support the target state.

**Rationale**: Keeps core stable; allows packages to be developed and versioned independently.

#### Scenario: Core Does Not Depend on Feature-Specific Resources

**Given**: Core is defined as registry, init (scaffolding), auth, runtime, shared utils/models

**When**: Core runs (e.g. discovery, root help from cache)

**Then**: Core does not import feature-specific prompts or templates from a flat resources/ folder; feature-specific resources are loaded only when the package that owns them is loaded

**Acceptance Criteria**:

- Package loaders resolve resources relative to their package folder (e.g. package resources/ or templates/)
- Shared resources (used by more than one package) may remain in a shared location or core until further refactor
