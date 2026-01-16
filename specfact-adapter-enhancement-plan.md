# Adapter Bridge & Registry Enhancement Plan

**Status:** Ready for Cursor AI Implementation  
**Date:** Tuesday, January 13, 2026, 22:15 CET  
**Context:** Integration with nold-ai/specfact-cli v1.x — **Spec-Kit + OpenSpec as Complementary SDD Tools**

---

## Executive Summary

This document presents a comprehensive enhancement plan for the SpecFact CLI adapter bridge pattern. It aligns current discussion with the **real implementation** found in `nold-ai/specfact-cli`, specifically:

- **Base Interface:** `src/specfact_cli/adapters/base.py` (BridgeAdapter ABC)
- **Registry:** `src/specfact_cli/adapters/registry.py` (AdapterRegistry)
- **Models:** `src/specfact_cli/models/bridge.py` (BridgeConfig, ArtifactMapping, etc.)
- **Reference Implementations:** 
  - `src/specfact_cli/adapters/speckit.py` (SpecKitAdapter)
  - `src/specfact_cli/adapters/openspec.py` (OpenSpecAdapter) — **NEW**

**Key Innovation:** Spec-Kit and OpenSpec are **complementary SDD (Specification-Driven Development) tools** that work together in the validation layer:
- **Spec-Kit:** Lightweight, markdown-native specification definition (WHAT + HOW)
- **OpenSpec:** Enterprise-grade change management and delta tracking (CHANGE tracking + RATIONALE)
- **SpecFact:** Validation layer that anchors both to source code TRUTH

The plan clarifies the proper architecture, design patterns, and implementation details required for production-ready adapters.

---

## Part 1: Current Architecture (As Implemented)

### 1.1 Core Components

#### BridgeAdapter Interface (base.py)
The abstract base class all adapters must implement:

**Key Methods:**
- `detect(repo_path, bridge_config)` → bool
  - Determines if adapter applies to a repository
  - Supports cross-repo detection via `bridge_config.external_base_path`
  - Example: SpecKitAdapter checks for `.specify/specs/`, `docs/specs/`, or `specs/` directories

- `get_capabilities(repo_path, bridge_config)` → ToolCapabilities
  - Returns metadata about the tool (version, layout, features)
  - Detects custom hooks, sync modes, configuration flags
  - Called after successful `detect()`

- `import_artifact(artifact_key, artifact_path, project_bundle, bridge_config)` → None
  - Parses tool artifacts and updates ProjectBundle
  - artifact_key: "specification", "plan", "tasks", "change_proposal", etc.
  - Supports Path or dict (for API-based artifacts)

- `export_artifact(artifact_key, artifact_data, bridge_config)` → Path | dict
  - Converts SpecFact data to tool format
  - Returns file path (filesystem) or dict (API response)
  - Respects `bridge_config.external_base_path` for cross-repo writes

- `generate_bridge_config(repo_path)` → BridgeConfig
  - Auto-generates bridge configuration by auto-detecting tool structure
  - Example: SpecKitAdapter detects layout (canonical/modern/classic)
  - Returns preset config matching actual repository structure

- **Change Tracking Methods:**
  - `load_change_tracking(bundle_dir, bridge_config)` → ChangeTracking | None
  - `save_change_tracking(bundle_dir, change_tracking, bridge_config)` → None
  - `load_change_proposal(bundle_dir, change_name, bridge_config)` → ChangeProposal | None
  - `save_change_proposal(bundle_dir, proposal, bridge_config)` → None

**Validation Enforcement:**
- All methods use `@beartype` for runtime type checking
- Pre/post-conditions via `@icontract` (require/ensure)
- Ensures contract compliance at runtime

#### AdapterRegistry (registry.py)
Plugin-based registry pattern for adapter discovery:

**Key Methods:**
- `register(adapter_type: str, adapter_class: type[BridgeAdapter])` → None
  - Registers new adapters at runtime (supports external plugins)
  - Adapter type stored in lowercase (case-insensitive lookup)

- `get_adapter(adapter_type: str, **kwargs)` → BridgeAdapter
  - Returns adapter instance with optional kwargs passed to constructor
  - Raises ValueError if adapter_type not registered

- `list_adapters()` → list[str]
  - Lists all registered adapter type identifiers

- `is_registered(adapter_type: str)` → bool
  - Checks if adapter type is registered

**Plugin Architecture:**
- Supports external plugin registration
- Built-in adapters pre-registered at module import
- Extensible: new adapters can be registered without modifying core code

#### BridgeConfig Model (bridge.py)
Configuration layer mapping SpecFact concepts to tool artifacts:

**Structure:**
```python
class BridgeConfig(BaseModel):
    version: str = "1.0"
    adapter: AdapterType  # speckit, openspec, github, linear, etc.
    
    # Artifact mappings: Logical SpecFact concepts → Physical paths
    artifacts: dict[str, ArtifactMapping]
    
    # Cross-repo support
    external_base_path: Path | None
    
    # Command mappings: Tool commands → SpecFact triggers
    commands: dict[str, CommandMapping] = {}
    
    # Template mappings: SpecFact schemas → Tool templates
    templates: TemplateMapping | None = None
```

**ArtifactMapping (nested):**
```python
class ArtifactMapping(BaseModel):
    path_pattern: str  # Dynamic: "specs/{feature_id}/spec.md"
    format: str = "markdown"  # markdown, yaml, json, api
    sync_target: str | None = None  # e.g., "github_issues"
    
    def resolve_path(context: dict[str, str], base_path: Path | None) → Path:
        # Resolves dynamic path_pattern with context vars
        # Returns absolute Path
```

**Presets (factory methods):**
- `preset_speckit_classic()` → specs/ at root
- `preset_speckit_specify()` → .specify/specs/ (canonical)
- `preset_speckit_modern()` → docs/specs/ (modern)
- `preset_generic_markdown()` → minimal config
- `preset_github()` → GitHub API-based artifacts
- `preset_openspec()` → OpenSpec structure

**Key Feature: external_base_path**
- When set, all artifact paths resolve relative to external path
- Enables cross-repository adapters (e.g., tracking issues in separate GitHub repo)
- All methods check: `if bridge_config.external_base_path: use_external else use_repo_path`

### 1.2 Change Tracking Models (models/change.py)

**ChangeProposal** (tool-agnostic):
```python
class ChangeProposal(BaseModel):
    name: str  # e.g., "add-user-feedback"
    title: str
    description: str  # What
    rationale: str  # Why
    timeline: str | None  # When
    owner: str | None  # Who
    stakeholders: list[str]
    dependencies: list[str]
    status: str = "proposed"  # proposed, in-progress, applied, archived
    created_at: str  # ISO timestamp
    applied_at: str | None
    archived_at: str | None
    source_tracking: SourceTracking | None  # Tool-specific metadata
```

**FeatureDelta** (tracks spec changes):
```python
class FeatureDelta(BaseModel):
    feature_key: str
    change_type: ChangeType  # ADDED, MODIFIED, REMOVED
    original_feature: Feature | None  # For MODIFIED/REMOVED
    proposed_feature: Feature | None  # For ADDED/MODIFIED
    change_rationale: str | None
    change_date: str | None
    validation_status: str | None  # pending, passed, failed
    validation_results: dict[str, Any] | None
    source_tracking: SourceTracking | None
```

**ChangeTracking** (bundle-level):
```python
class ChangeTracking(BaseModel):
    proposals: dict[str, ChangeProposal]
    feature_deltas: dict[str, list[FeatureDelta]]
```

**Design Principle:** All models are tool-agnostic; tool-specific metadata stored in `source_tracking` only.

### 1.3 Adapter Lifecycle & Validation

**Constraint Enforcement:**
- `@beartype` enforces type contracts at runtime
- `@icontract` enforces preconditions and postconditions
- Example: `import_artifact()` requires artifact_key non-empty, returns None

**Error Handling:**
- Adapters raise ValueError with descriptive messages
- NotImplementedError for unsupported operations (e.g., Spec-Kit doesn't support change tracking)
- Pre-conditions fail fast with contract violations

---

## Part 2: Spec-Kit + OpenSpec Complementary Pattern

### 2.1 The SDD Validation Layer Architecture

**SpecFact + Spec-Kit + OpenSpec = Three-Layer Validation:**

```
┌─────────────────────────────────────────────────┐
│         CODE (Source of Truth)                  │
│  - API endpoints                                │
│  - Data models                                  │
│  - Implementation logic                         │
└──────────────────────────┬──────────────────────┘
                           │ (extract & validate)
┌──────────────────────────▼──────────────────────┐
│    SPECFACT VALIDATION LAYER                    │
│  - Detects what code actually provides         │
│  - Validates against specifications             │
│  - Tracks discrepancies                         │
└──────┬─────────────────────────────┬────────────┘
       │                             │
       │ (import/export via adapters)│
       │                             │
┌──────▼──────────────┐    ┌─────────▼──────────────┐
│  SPEC-KIT (Spec)    │    │ OPENSPEC (Changes)     │
│ ─────────────────   │    │ ──────────────────     │
│ • Lightweight WHAT  │    │ • Enterprise Changes   │
│ • Markdown-native   │    │ • Delta tracking       │
│ • Easy collaboration│    │ • Change rationale     │
│ • No runtime cost   │    │ • Sidecar integration  │
│                     │    │ • Validation rules     │
│ Spec-Kit format:    │    │                        │
│ specs/               │    │ OpenSpec format:       │
│  001-auth/          │    │ openspec/              │
│   spec.md           │    │  project.md            │
│   plan.md           │    │  specs/                │
│   tasks.md          │    │  changes/              │
└─────────────────────┘    │   proposal.md          │
                           │   specs/               │
                           └────────────────────────┘
```

**Key Distinction:**
- **Spec-Kit:** Defines WHAT we're building and HOW it should work
  - Source: Human-authored specifications
  - Purpose: Document requirements, acceptance criteria, constraints
  - Update frequency: As requirements change
  - Lifecycle: Specification → Implementation → Updated specification

- **OpenSpec:** Manages CHANGES and their justification
  - Source: Change proposals with rationale
  - Purpose: Track why specs changed, what changed, validate deltas
  - Update frequency: When modifying specs (with explicit change reasons)
  - Lifecycle: Proposal → Review → Application → Archive

- **SpecFact:** Validates TRUTH (code vs specifications)
  - Source: Extracted from code analysis
  - Purpose: Detect drift, flag inconsistencies, validate design
  - Update frequency: Continuous (on-demand analysis)
  - Lifecycle: Extract → Validate → Report → Propose fixes

### 2.2 Real Implementation Pattern: OpenSpec Adapter

**OpenSpecAdapter Key Features (Phase 1 - Read-Only):**

```python
class OpenSpecAdapter(BridgeAdapter):
    """
    OpenSpec bridge adapter for specification anchoring and delta tracking.
    
    Phase 1: Read-only sync (OpenSpec → SpecFact)
    - Import specifications from openspec/specs/
    - Import change proposals from openspec/changes/
    - Import feature deltas for change validation
    - Does NOT write back to OpenSpec (yet)
    
    Phase 4 (Future): Bidirectional sync
    - Export updated specs with change justification
    - Create sidecar validation reports
    - Integrate with change approval workflows
    """
```

**Detection Logic:**
```python
def detect(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> bool:
    # Looks for OpenSpec structure indicators:
    # 1. openspec/project.md (root project context)
    # 2. openspec/specs/ (feature specifications)
    # Returns True if either exists
    base_path = bridge_config.external_base_path if bridge_config else repo_path
    return (base_path / "openspec" / "project.md").exists() \
        or (base_path / "openspec" / "specs").is_dir()
```

**Artifact Mapping Pattern:**
```python
def import_artifact(self, artifact_key, artifact_path, project_bundle, bridge_config):
    # Routes to appropriate import method based on artifact_key
    if artifact_key == "specification":
        self._import_specification(...)  # spec.md → Feature
    elif artifact_key == "project_context":
        self._import_project_context(...)  # project.md → Idea
    elif artifact_key == "change_proposal":
        self._import_change_proposal(...)  # proposal.md → ChangeProposal
    elif artifact_key == "change_spec_delta":
        self._import_change_spec_delta(...)  # change spec.md → FeatureDelta
```

**Change Tracking - Full Implementation:**
```python
def load_change_tracking(self, bundle_dir, bridge_config) -> ChangeTracking | None:
    # Discovers all active changes in openspec/changes/
    # For each change:
    #   1. Load change proposal (proposal.md)
    #   2. Load feature deltas (changes/*/specs/feature_id/spec.md)
    #   3. Map to ChangeProposal + FeatureDelta[] models
    # Returns ChangeTracking with proposals and deltas
    
def load_change_proposal(self, bundle_dir, change_name, bridge_config) -> ChangeProposal | None:
    # Parses openspec/changes/{change_name}/proposal.md
    # Extracts: summary, what_changes, why, rationale
    # Maps to ChangeProposal with openspec source_tracking
```

**Key Difference from SpecKit:**
- SpecKit: Returns None for change tracking (not supported)
- OpenSpec: Returns full ChangeTracking with proposals and deltas (required)
- Pattern: Be explicit — tool-optional vs tool-required features

### 2.3 Cross-Repository Support Pattern

**Both Spec-Kit and OpenSpec support external_base_path:**

```python
# Pattern: Check for external location
if bridge_config and bridge_config.external_base_path:
    base_path = bridge_config.external_base_path
else:
    base_path = repo_path

# All path operations use base_path
spec_path = base_path / "specs" / feature_id / "spec.md"
openspec_path = base_path / "openspec" / "specs" / feature_id / "spec.md"
```

**Use Case: Multi-Repository Setup**
```
Project:
  code/
    src/
    tests/
    
  specifications/ (separate repo, external_base_path)
    .specify/specs/   (Spec-Kit)
    openspec/         (OpenSpec)
```

Both adapters work with the separate specifications repository without code changes.

### 2.4 Source Tracking Pattern (Tool-Agnostic Models)

**Store all tool-specific metadata separately:**

```python
# When importing from Spec-Kit
feature.source_tracking = SourceTracking(
    tool="speckit",
    source_metadata={
        "path": "specs/001-auth/spec.md",
        "speckit_path": "specs/001-auth/spec.md",
        "speckit_type": "specification",
        "speckit_base_path": "/path/to/external",  # if cross-repo
    }
)

# When importing from OpenSpec
feature.source_tracking = SourceTracking(
    tool="openspec",
    source_metadata={
        "path": "openspec/specs/001-auth/spec.md",
        "openspec_path": "openspec/specs/001-auth/spec.md",
        "openspec_type": "specification",
        "openspec_base_path": "/path/to/external",  # if cross-repo
    }
)

# Core Feature model remains tool-agnostic
class Feature(BaseModel):
    key: str
    title: str
    outcomes: list[str]
    acceptance: list[str]
    constraints: list[str]
    stories: list[str]
    source_tracking: SourceTracking | None  # Tool-specific metadata here
```

**Why This Matters:**
- Same Feature can be tracked by multiple tools
- Example: Feature defined in Spec-Kit, enhanced with OpenSpec changes
- Tool-specific queries don't pollute core model
- Enables future tool integrations (GitHub, Linear, Jira, etc.)

---

## Part 3: SpecKit vs OpenSpec: Implementation Comparison

### 3.1 Specification Import Pattern

**SpecKitAdapter._import_specification():**
```python
# Parse Spec-Kit markdown format
spec_content = artifact_path.read_text()

# Extract frontmatter, title, sections
# Spec-Kit structure: specs/{feature_id}/spec.md
# Contains: WHAT (stories, outcomes), HOW (acceptance), constraints

feature = Feature(
    key=feature_id,
    title="...",
    outcomes=[...],
    acceptance=[...],
    constraints=[...]
)

feature.source_tracking = SourceTracking(
    tool="speckit",
    source_metadata={"speckit_path": str(artifact_path)}
)
```

**OpenSpecAdapter._import_specification():**
```python
# Parse OpenSpec markdown format
spec_content = artifact_path.read_text()

# Extract frontmatter, title, sections
# OpenSpec structure: openspec/specs/{feature_id}/spec.md
# Contains: WHAT (overview), requirements, validation rules

feature = Feature(
    key=feature_id,
    title="...",
    outcomes=[...],  # from overview + requirements
)

feature.source_tracking = SourceTracking(
    tool="openspec",
    source_metadata={"openspec_path": str(artifact_path)}
)
```

**Key Difference:** Same output model, different input format. Adapters handle conversion.

### 3.2 Change Tracking: The Critical Difference

**SpecKitAdapter.load_change_tracking():**
```python
def load_change_tracking(self, bundle_dir, bridge_config) -> ChangeTracking | None:
    return None  # Spec-Kit doesn't track changes

def save_change_proposal(self, bundle_dir, proposal, bridge_config) -> None:
    raise NotImplementedError("Spec-Kit does not support change tracking")
```

**OpenSpecAdapter.load_change_tracking():**
```python
def load_change_tracking(self, bundle_dir, bridge_config) -> ChangeTracking | None:
    # 1. List all changes in openspec/changes/
    change_names = self.parser.list_active_changes(base_path)
    
    # 2. For each change, load proposal and deltas
    proposals = {}
    feature_deltas = {}
    for change_name in change_names:
        proposals[change_name] = self.load_change_proposal(...)
        deltas[change_name] = self._load_feature_deltas(...)
    
    # 3. Return ChangeTracking with complete change history
    return ChangeTracking(
        proposals=proposals,
        feature_deltas=feature_deltas
    )
```

**Pattern:**
- Spec-Kit: Tool-optional feature (return None)
- OpenSpec: Tool-required feature (return full implementation)
- SpecFact: Uses whichever adapter provides change data

### 3.3 Auto-Detection: Learning from Repository Structure

**SpecKitAdapter.generate_bridge_config():**
```python
def generate_bridge_config(self, repo_path: Path) -> BridgeConfig:
    # Auto-detect which Spec-Kit layout is used
    if (repo_path / ".specify" / "specs").exists():
        return BridgeConfig.preset_speckit_specify()  # Canonical
    if (repo_path / "docs" / "specs").exists():
        return BridgeConfig.preset_speckit_modern()   # Modern
    if (repo_path / "specs").exists():
        return BridgeConfig.preset_speckit_classic()  # Legacy
    
    # Default to canonical if .specify exists
    if (repo_path / ".specify").exists():
        return BridgeConfig.preset_speckit_specify()
    
    # Fallback
    return BridgeConfig.preset_speckit_classic()
```

**OpenSpecAdapter.generate_bridge_config():**
```python
def generate_bridge_config(self, repo_path: Path) -> BridgeConfig:
    # OpenSpec has fixed structure (no variants)
    return BridgeConfig.preset_openspec()
```

**Pattern:** Adapter learns repository structure, returns appropriate preset.

---

## Part 4: Design Patterns & Best Practices

### 4.1 Cross-Repository Support Pattern

**Every adapter method checks external_base_path:**
```python
def some_adapter_method(self, artifact_key, artifact_path, bridge_config=None):
    # Pattern 1: For path resolution
    base_path = artifact_path.parent.parent.parent  # Infer from artifact
    if bridge_config and bridge_config.external_base_path:
        base_path = bridge_config.external_base_path  # Override
    
    # Pattern 2: For direct path operations
    if bridge_config and bridge_config.external_base_path:
        base_path = bridge_config.external_base_path
    else:
        base_path = Path.cwd()
    
    # Then use base_path for all relative path calculations
```

**Why:** Enables adapters like GitHub to write issues to external repos without modifying artifact paths.

### 4.2 Source Tracking Pattern

**Always store tool-specific metadata separately:**
```python
# ✓ CORRECT: Tool metadata in source_tracking
feature.source_tracking = SourceTracking(
    tool="openspec",
    source_metadata={
        "path": openspec_path,
        "openspec_path": openspec_path,
        "openspec_type": "specification",
        "openspec_base_path": str(bridge_config.external_base_path),  # Only if cross-repo
    }
)

# ✗ WRONG: Tool metadata scattered in core models
feature.openspec_path = "..."  # Don't do this
feature.openspec_type = "..."  # Don't do this
```

**Why:** Keeps core models tool-agnostic, enables multiple tools to track same feature.

### 4.3 Bridge Config Resolution Pattern

**Always use bridge_config.resolve_path() for exports:**
```python
# Pattern: Resolve from config first, fall back to default
if bridge_config and "artifact_key" in bridge_config.artifacts:
    artifact_path = bridge_config.resolve_path(
        "artifact_key",
        {"feature_id": feature_id, "other_var": "value"},
        base_path=base_path  # Respects external_base_path
    )
else:
    # Default fallback path
    artifact_path = base_path / "default" / feature_id / "artifact.md"
```

**Why:** Ensures adapters work with custom artifact paths defined in bridge config.

### 4.4 Error Handling Pattern

**Be specific about unsupported operations:**
```python
# Pattern 1: Feature not applicable
def load_change_tracking(self, bundle_dir, bridge_config=None):
    return None  # This tool doesn't support this feature

# Pattern 2: Feature explicitly unsupported
def save_change_tracking(self, bundle_dir, change_tracking, bridge_config=None):
    raise NotImplementedError(
        "Spec-Kit adapter does not support change tracking"
    )

# Pattern 3: Invalid input
def import_artifact(self, artifact_key, artifact_path, project_bundle, bridge_config=None):
    if not isinstance(artifact_path, Path):
        raise ValueError(f"Adapter requires Path, got {type(artifact_path)}")
```

**Why:** Allows callers to distinguish between "not implemented" and "returns None".

### 4.5 Validation Pattern

**Use @beartype and @icontract for contracts:**
```python
@beartype
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def detect(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> bool:
    """Detect if this adapter applies..."""
```

**Why:** Validates all inputs/outputs at runtime, makes contracts explicit in docstrings.

---

## Part 5: Implementation Checklist for New Adapters

### 5.1 Required Methods (All Must Be Implemented)

- [ ] `detect(repo_path, bridge_config)` → bool
- [ ] `get_capabilities(repo_path, bridge_config)` → ToolCapabilities
- [ ] `import_artifact(artifact_key, artifact_path, project_bundle, bridge_config)` → None
- [ ] `export_artifact(artifact_key, artifact_data, bridge_config)` → Path | dict
- [ ] `generate_bridge_config(repo_path)` → BridgeConfig
- [ ] `load_change_tracking(bundle_dir, bridge_config)` → ChangeTracking | None
- [ ] `save_change_tracking(bundle_dir, change_tracking, bridge_config)` → None
- [ ] `load_change_proposal(bundle_dir, change_name, bridge_config)` → ChangeProposal | None
- [ ] `save_change_proposal(bundle_dir, proposal, bridge_config)` → None

### 5.2 Implementation Requirements

- [ ] **Type Safety:** All methods use @beartype
- [ ] **Contract Enforcement:** All methods use @require/@ensure from icontract
- [ ] **Cross-Repo Support:** All path operations check bridge_config.external_base_path
- [ ] **Source Tracking:** Tool-specific metadata stored in SourceTracking only
- [ ] **Bridge Config:** Supports artifact_key in import_artifact/export_artifact
- [ ] **Error Handling:** Raises ValueError or NotImplementedError with messages
- [ ] **Docstrings:** Clear parameter descriptions, return types, exceptions

### 5.3 Testing Checklist

- [ ] Unit tests for detect() with multiple repo structures
- [ ] Unit tests for import_artifact() with valid/invalid inputs
- [ ] Unit tests for export_artifact() with bridge_config variations
- [ ] Unit tests for generate_bridge_config() auto-detection
- [ ] Integration tests for cross-repo scenarios (external_base_path)
- [ ] Edge case tests for missing artifacts, malformed data
- [ ] Test change tracking methods (None or NotImplementedError as appropriate)

### 5.4 Documentation Checklist

- [ ] README with adapter overview (what tools it supports, limitations)
- [ ] Example bridge_config.yaml for common use cases
- [ ] Cross-repo example (if applicable)
- [ ] Supported artifact keys (specification, plan, change_proposal, etc.)
- [ ] Known limitations (unsupported features, version requirements)
- [ ] Troubleshooting guide (common errors, solutions)

---

## Part 6: Registry Integration

### 6.1 Registration (At Module Import)

**In src/specfact_cli/adapters/__init__.py:**
```python
"""
Adapter registry and plugin discovery.

Built-in adapters are registered at module import.
External plugins can register at runtime.
"""

from specfact_cli.adapters.base import BridgeAdapter
from specfact_cli.adapters.registry import AdapterRegistry

# Import built-in adapters
from specfact_cli.adapters.speckit import SpecKitAdapter
from specfact_cli.adapters.openspec import OpenSpecAdapter
from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.adapters.generic_markdown import GenericMarkdownAdapter

# Register built-in adapters
AdapterRegistry.register("speckit", SpecKitAdapter)
AdapterRegistry.register("openspec", OpenSpecAdapter)  # NEW
AdapterRegistry.register("github", GitHubAdapter)
AdapterRegistry.register("generic-markdown", GenericMarkdownAdapter)

# Export public API
__all__ = [
    "BridgeAdapter",
    "AdapterRegistry",
    "SpecKitAdapter",
    "OpenSpecAdapter",
    "GitHubAdapter",
    "GenericMarkdownAdapter",
]
```

### 6.2 Adapter Discovery Pattern

**In bridge detection logic:**
```python
def detect_adapter(repo_path: Path) -> str | None:
    """
    Auto-detect adapter for repository.
    
    Tries each registered adapter in priority order.
    """
    # Priority order: openspec > speckit > generic-markdown > github
    # (OpenSpec first because it's more specific, Spec-Kit second because it's common)
    for adapter_type in ["openspec", "speckit", "generic-markdown", "github"]:
        if AdapterRegistry.is_registered(adapter_type):
            adapter = AdapterRegistry.get_adapter(adapter_type)
            if adapter.detect(repo_path):
                return adapter_type
    
    return None

def get_adapter_for_repo(repo_path: Path, adapter_type: str | None = None) -> BridgeAdapter:
    """
    Get adapter instance for repository.
    
    If adapter_type not specified, auto-detect.
    """
    if adapter_type is None:
        adapter_type = detect_adapter(repo_path)
        if adapter_type is None:
            raise ValueError("Could not detect adapter for repository")
    
    if not AdapterRegistry.is_registered(adapter_type):
        raise ValueError(f"Adapter '{adapter_type}' not registered. Available: {', '.join(AdapterRegistry.list_adapters())}")
    
    return AdapterRegistry.get_adapter(adapter_type)
```

### 6.3 Usage Pattern

**In CLI or integration code:**
```python
from specfact_cli.adapters import AdapterRegistry, get_adapter_for_repo

# Pattern 1: Auto-detect
adapter = get_adapter_for_repo(Path("/path/to/repo"))

# Pattern 2: Explicit
adapter = AdapterRegistry.get_adapter("openspec")

# Pattern 3: List available
available = AdapterRegistry.list_adapters()
print(f"Available adapters: {', '.join(available)}")

# Pattern 4: Register plugin (external)
from my_plugin import MyAdapter
AdapterRegistry.register("my-tool", MyAdapter)
```

---

## Part 7: Alignment with Discussion vs Implementation

### 7.1 What Was Discussed But Not In Real Implementation

**Discussed:**
- "Bridge adapters should support data transformation pipelines"
- "Adapters should validate artifact schemas before import"
- "Registry should support plugin hot-reloading"

**Reality:**
- Validation is simple ValueError checks, no schema validation
- Adapters use @icontract for basic contract checking
- Registry is static (no hot-reload), plugins register at import time
- This is **intentional:** Spec-Kit MVP prioritizes simplicity over extensibility

**Lesson:** MVP implementation is more minimal than feature-rich discussion suggests. Keep it simple.

### 7.2 What Was Implemented But Not Fully Discussed

**Implemented:**
- Cross-repository support via `bridge_config.external_base_path`
- Auto-detection of multiple layout formats (Spec-Kit has 3 versions)
- Separate change tracking models (ChangeProposal, FeatureDelta)
- Source tracking pattern for tool-specific metadata
- OpenSpec integration for enterprise change management

**Why:** These are operational requirements from real use cases:
- Cross-repo: Some teams use separate GitHub repos for specs vs code
- Layout detection: Spec-Kit has evolved; need backward compatibility
- Change tracking: OpenSpec needs delta tracking; must be tool-agnostic
- Source tracking: Multiple tools tracking same feature requires isolation
- OpenSpec: Enterprise users need change justification and sidecar validation

**Lesson:** Implementation is driven by real operational needs, not theoretical design.

### 7.3 Key Insights for Enhancement

**1. Bridge Config is Zero-Code Compatibility:**
- Not for runtime configuration only
- Also enables tool changes without code changes
- Example: If Spec-Kit changes directory layout, update preset → zero adapter changes

**2. Change Tracking is Tool-Optional vs Tool-Required:**
- Spec-Kit returns None (not supported)
- OpenSpec fully implements (required for change management)
- Not all tools need all features
- Pattern: Return None for "not applicable", NotImplementedError for "not supported"

**3. External Base Path is Critical for Scalability:**
- Enables single adapter instance to work with multiple repos
- Keeps adapter logic simple (one code path, two contexts)
- Example: One OpenSpecAdapter can work with multiple specification repositories

**4. Source Tracking Enables Tool Composition:**
- One Feature can have metadata from multiple tools
- Example: Feature from Spec-Kit can be enhanced with OpenSpec changes
- Keeps models tool-agnostic while enabling rich metadata

**5. Spec-Kit + OpenSpec are Complementary (Not Competing):**
- Spec-Kit: Lightweight, markdown-native, easy collaboration
- OpenSpec: Enterprise change tracking, delta validation, sidecar reports
- Together: Full SDD lifecycle with validation layer (SpecFact)
- Pattern: Use both for comprehensive specification management

---

## Part 8: Cursor AI Implementation Guide

### 8.1 How to Use This Document in Cursor

1. **Copy entire document** into Cursor as a "Project Context" file
2. **Reference specific sections** when implementing:
   - "Implement detect() following Pattern 3.3 in Part 3"
   - "Add source tracking following Pattern 4.2"
3. **Use code examples** as templates:
   - `_import_change_tracking()` shows exact structure for change methods
   - `detect()` shows external_base_path pattern
   - `load_change_proposal()` shows OpenSpec parsing pattern
4. **Follow the Checklist** (Part 5) to validate completeness

### 8.2 Key Questions to Ask Cursor

**When implementing OpenSpec-like adapter:**
- "Does my detect() method check bridge_config.external_base_path?"
- "Are all tool-specific fields in source_tracking or core model?"
- "Does my adapter follow the error handling pattern (ValueError vs NotImplementedError)?"
- "Is bridge_config.resolve_path() used for all exports?"
- "For change tracking, should I return None or raise NotImplementedError?"

**When implementing Spec-Kit-like adapter:**
- "How should I handle multiple layout variants (auto-detection)?"
- "Should I support change tracking or explicitly return None?"
- "How do I store tool-specific metadata without polluting core models?"
- "What artifact formats does my tool support (markdown, json, yaml, api)?"

**When modifying registry:**
- "Is auto-detection trying all adapters in priority order?"
- "Does registration happen at import time (not at get_adapter)?"
- "Are list_adapters() results case-normalized?"
- "Can external plugins register without modifying core code?"

### 8.3 Testing Template

```python
# In tests/adapters/test_openspec_adapter.py

import pytest
from pathlib import Path
from specfact_cli.adapters.openspec import OpenSpecAdapter
from specfact_cli.models.bridge import BridgeConfig, AdapterType
from specfact_cli.models.change import ChangeTracking, ChangeProposal

class TestOpenSpecAdapter:
    """Test OpenSpecAdapter implementation."""
    
    @pytest.fixture
    def adapter(self):
        return OpenSpecAdapter()
    
    @pytest.fixture
    def sample_repo(self, tmp_path):
        # Create OpenSpec structure
        (tmp_path / "openspec" / "specs").mkdir(parents=True)
        (tmp_path / "openspec" / "project.md").touch()
        return tmp_path
    
    def test_detect_finds_openspec_repo(self, adapter, sample_repo):
        """Test detect() returns True for valid OpenSpec repo."""
        assert adapter.detect(sample_repo) is True
    
    def test_detect_with_external_base_path(self, adapter, tmp_path):
        """Test detect() respects external_base_path."""
        external = tmp_path / "external"
        (external / "openspec" / "specs").mkdir(parents=True)
        
        bridge_config = BridgeConfig(
            adapter=AdapterType.OPENSPEC,
            external_base_path=external,
            artifacts={}
        )
        
        # Should detect in external path, not repo_path
        assert adapter.detect(tmp_path, bridge_config) is True
    
    def test_load_change_tracking_returns_none_if_no_changes(self, adapter, sample_repo):
        """Test load_change_tracking returns None if no changes."""
        result = adapter.load_change_tracking(sample_repo / ".specfact")
        assert result is None
    
    def test_load_change_tracking_finds_active_changes(self, adapter, sample_repo):
        """Test load_change_tracking discovers change proposals."""
        # Create openspec/changes/{change_name}/proposal.md
        change_dir = sample_repo / "openspec" / "changes" / "add-auth"
        change_dir.mkdir(parents=True)
        (change_dir / "proposal.md").write_text(
            "# Add Auth\n\nAdding authentication support.\n"
        )
        
        # Create .specfact directory
        bundle_dir = sample_repo / ".specfact" / "projects" / "default"
        bundle_dir.mkdir(parents=True)
        
        result = adapter.load_change_tracking(bundle_dir)
        assert result is not None
        assert "add-auth" in result.proposals
    
    def test_load_change_proposal_maps_to_model(self, adapter, sample_repo):
        """Test change proposal parsed correctly."""
        # Create change proposal
        change_dir = sample_repo / "openspec" / "changes" / "update-api"
        change_dir.mkdir(parents=True)
        (change_dir / "proposal.md").write_text(
            "# Update API\n\nAdd new endpoints.\n"
        )
        
        bundle_dir = sample_repo / ".specfact" / "projects" / "default"
        bundle_dir.mkdir(parents=True)
        
        proposal = adapter.load_change_proposal(bundle_dir, "update-api")
        assert proposal is not None
        assert proposal.name == "update-api"
        assert isinstance(proposal, ChangeProposal)
    
    def test_import_specification_creates_feature(self, adapter, sample_repo):
        """Test specification import creates Feature."""
        # Create OpenSpec spec
        spec_dir = sample_repo / "openspec" / "specs" / "001-auth"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text(
            "# Authentication\n\nUser authentication system.\n"
        )
        
        # Mock project bundle
        class MockBundle:
            features = {}
        
        bundle = MockBundle()
        adapter.import_artifact(
            "specification",
            spec_dir / "spec.md",
            bundle,
            None
        )
        
        assert "001-auth" in bundle.features
        assert bundle.features["001-auth"].title == "Authentication"
    
    def test_export_artifact_raises_not_implemented(self, adapter, sample_repo):
        """Test export_artifact raises NotImplementedError (Phase 1)."""
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.export_artifact("specification", None)
        
        assert "Phase 1" in str(exc_info.value)
        assert "read-only" in str(exc_info.value)
```

---

## Appendix A: BridgeConfig Presets Reference

### Spec-Kit Presets

**preset_speckit_specify()** - Canonical (recommended):
```yaml
adapter: speckit
artifacts:
  specification:
    path_pattern: ".specify/specs/{feature_id}/spec.md"
    format: markdown
  plan:
    path_pattern: ".specify/specs/{feature_id}/plan.md"
    format: markdown
  tasks:
    path_pattern: ".specify/specs/{feature_id}/tasks.md"
    format: markdown
    sync_target: github_issues
  contracts:
    path_pattern: ".specify/specs/{feature_id}/contracts/{contract_name}.yaml"
    format: yaml
  constitution:
    path_pattern: ".specify/memory/constitution.md"
    format: markdown
```

**preset_speckit_modern()** - docs/specs/ layout:
```yaml
adapter: speckit
artifacts:
  specification:
    path_pattern: "docs/specs/{feature_id}/spec.md"
    format: markdown
  # ... (rest similar)
```

**preset_speckit_classic()** - Legacy root layout:
```yaml
adapter: speckit
artifacts:
  specification:
    path_pattern: "specs/{feature_id}/spec.md"
    format: markdown
  # ... (rest similar)
```

### OpenSpec Preset

```yaml
adapter: openspec
artifacts:
  specification:
    path_pattern: "openspec/specs/{feature_id}/spec.md"
    format: markdown
  project_context:
    path_pattern: "openspec/project.md"
    format: markdown
  change_proposal:
    path_pattern: "openspec/changes/{change_name}/proposal.md"
    format: markdown
  change_tasks:
    path_pattern: "openspec/changes/{change_name}/tasks.md"
    format: markdown
  change_spec_delta:
    path_pattern: "openspec/changes/{change_name}/specs/{feature_id}/spec.md"
    format: markdown
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Bridge Adapter** | Concrete class implementing BridgeAdapter interface for specific tool |
| **Adapter Registry** | Plugin registry managing adapter discovery and instantiation |
| **Bridge Config** | Configuration mapping SpecFact concepts to tool artifacts |
| **Artifact Mapping** | Single logical concept → physical tool path mapping |
| **External Base Path** | Root directory for cross-repository artifact resolution |
| **Cross-Repo** | Scenario where artifacts are in different repository than code |
| **Source Tracking** | Tool-specific metadata attached to core models |
| **Change Proposal** | Tool-agnostic data structure representing change to specs |
| **Feature Delta** | Tool-agnostic tracking of changes to single feature |
| **Auto-Detection** | Process of discovering adapter via detect() across all registered adapters |
| **SDD** | Specification-Driven Development (specifications as source of truth) |
| **Spec-Kit** | Lightweight, markdown-native specification framework |
| **OpenSpec** | Enterprise change management with delta tracking |
| **SpecFact** | Validation layer anchoring specs to source code truth |

---

## Appendix C: Quick Reference Card

### Adapter Method Signatures

```python
# Detection
def detect(repo_path: Path, bridge_config: BridgeConfig | None = None) -> bool

# Capabilities
def get_capabilities(repo_path: Path, bridge_config: BridgeConfig | None = None) -> ToolCapabilities

# Artifact I/O
def import_artifact(artifact_key: str, artifact_path: Path | dict, project_bundle, bridge_config) -> None
def export_artifact(artifact_key: str, artifact_data, bridge_config) -> Path | dict

# Configuration
def generate_bridge_config(repo_path: Path) -> BridgeConfig

# Change Tracking
def load_change_tracking(bundle_dir: Path, bridge_config) -> ChangeTracking | None
def save_change_tracking(bundle_dir: Path, change_tracking: ChangeTracking, bridge_config) -> None
def load_change_proposal(bundle_dir: Path, change_name: str, bridge_config) -> ChangeProposal | None
def save_change_proposal(bundle_dir: Path, proposal: ChangeProposal, bridge_config) -> None
```

### Registry API

```python
# Registration
AdapterRegistry.register(adapter_type: str, adapter_class: type[BridgeAdapter]) -> None

# Discovery
AdapterRegistry.get_adapter(adapter_type: str) -> BridgeAdapter
AdapterRegistry.list_adapters() -> list[str]
AdapterRegistry.is_registered(adapter_type: str) -> bool
```

### Path Resolution Pattern

```python
# Pattern for all adapters
if bridge_config and bridge_config.external_base_path:
    base_path = bridge_config.external_base_path
else:
    base_path = repo_path  # or Path.cwd() for exports

artifact_path = bridge_config.resolve_path(
    artifact_key,
    context_dict,
    base_path=base_path
)
```

---

## Document Info

- **Version:** 2.0 (Enhanced with OpenSpec)
- **Last Updated:** 2026-01-13 22:15 CET
- **Author:** AI Analysis of nold-ai/specfact-cli
- **Status:** Ready for Cursor AI Implementation
- **Repository:** [https://github.com/nold-ai/specfact-cli](https://github.com/nold-ai/specfact-cli)
- **Internal Docs:** https://github.com/nold-ai/specfact-cli-internal/tree/main/docs/internal/implementation
- **License:** See LICENSE.md in repository
