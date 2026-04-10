## ADDED Requirements

### Requirement: Active Change Ownership Must Be Classified Against The Canonical Repo Split

The system SHALL classify every active OpenSpec change and linked GitHub user story in `specfact-cli` against the canonical post-migration ownership model before further implementation work proceeds.

#### Scenario: Active change is classified as core, modules, or split

- **WHEN** maintainers review active changes that still reference the pre-split monolithic structure
- **THEN** each change is assigned one of: `core`, `modules`, or `split/rescope`
- **AND** the decision is based on the canonical ownership specs rather than on stale proposal paths or legacy issue location.

### Requirement: Module-Owned Issues Must Use A Defined Reassignment Path

The system SHALL define a deterministic path for any GitHub issue that belongs in `specfact-cli-modules` instead of `specfact-cli`.

#### Scenario: Native issue transfer is available and accepted

- **WHEN** a module-owned issue can be moved between the two repositories with acceptable metadata preservation
- **THEN** the issue is transferred to `nold-ai/specfact-cli-modules`
- **AND** the related OpenSpec artifacts and planning inventory are updated to reference the transferred issue in its new repository.

#### Scenario: Native issue transfer is unavailable or unsuitable

- **WHEN** a module-owned issue cannot be moved cleanly between repositories
- **THEN** the source issue in `specfact-cli` is closed with a comment pointing to the replacement issue in `specfact-cli-modules`
- **AND** a replacement issue is created in `specfact-cli-modules` with updated scope aligned to the current architecture
- **AND** the old and new issues cross-reference each other so planning history remains auditable.

### Requirement: Target Hierarchy Must Exist Before Module-Owned Stories Are Reassigned

The system SHALL establish the necessary Epic and Feature parents in `specfact-cli-modules` before module-owned user stories are transferred or recreated there.

#### Scenario: Module-owned user story is prepared for reassignment

- **WHEN** a user story is classified as module-owned
- **THEN** the target repository already has the Epic and Feature hierarchy needed to parent that story
- **AND** the reassigned story is linked under the target Feature rather than being left as a flat issue.

### Requirement: Planning Inventories Must Be Updated In Both Repositories

The system SHALL keep planning metadata aligned across repositories when change ownership or GitHub issue ownership changes.

#### Scenario: Change ownership is reassigned to modules repo

- **WHEN** a change or linked issue moves from `specfact-cli` planning to `specfact-cli-modules`
- **THEN** `openspec/CHANGE_ORDER.md` in `specfact-cli` is updated to remove or annotate the old core-repo ownership
- **AND** the corresponding planning inventory in `specfact-cli-modules` is updated with the new issue, Epic, Feature, and dependency references.

### Requirement: Rescoped Proposals Must State The Current Architecture And Repo Assignment

The system SHALL update affected active proposals before implementation resumes so they no longer describe obsolete monolithic paths or incorrect repository ownership.

#### Scenario: Active proposal still references in-repo module implementation

- **WHEN** an active proposal describes implementation under `modules/<name>/` in `specfact-cli` for a module-owned capability
- **THEN** the proposal is updated to either reflect its true core-only scope or to point to the owning implementation work in `specfact-cli-modules`
- **AND** the proposal no longer implies that bundle-owned behavior will be implemented in the core repo.
