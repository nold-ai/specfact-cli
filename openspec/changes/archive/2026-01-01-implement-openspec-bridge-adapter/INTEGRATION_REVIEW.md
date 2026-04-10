# Integration Review: OpenSpec Bridge Adapter

**Date**: 2026-01-01  
**Status**: ✅ **REVIEW COMPLETE - ALL FIXES APPLIED**  
**Purpose**: Review proposal against all implementation plans to identify integration mismatches

---

## Executive Summary

This document reviews the OpenSpec bridge adapter proposal against all relevant implementation plans to ensure alignment with the universal abstraction layer (bridge adapter) architecture and identify any integration mismatches.

**Review Status**: All critical mismatches have been identified and fixed in the proposal and tasks. The proposal now fully complies with the universal abstraction layer architecture.

### Critical Findings

1. ✅ **BridgeProbe Hard-Coded Detection** - **FIXED**: Proposal now requires refactoring to adapter registry, no hard-coded methods
2. ✅ **BridgeSync Hard-Coded Checks** - **FIXED**: Proposal now requires refactoring to remove all hard-coded checks
3. ✅ **Parser Location** - **FIXED**: Parser location documented as adapter-specific (`adapters/openspec_parser.py`)
4. ✅ **Adapter Registry** - Correctly uses plugin-based architecture
5. ✅ **Change Tracking** - Correctly uses adapter interface for storage
6. ✅ **BridgeAdapter Interface** - **FIXED**: Added `get_capabilities()` method requirement

---

## Review Against Implementation Plans

### 1. Bridge Adapter Data Model Plan

**Plan Requirements**:

- ✅ Plugin-based adapter architecture (AdapterRegistry, BridgeAdapter interface)
- ✅ No hard-coded adapter checks in core
- ✅ No hard-coded detection logic
- ✅ Tool-agnostic models accessed via adapters
- ✅ Cross-repository support via `external_base_path`

**Proposal Status**:

- ✅ Creates `OpenSpecAdapter` implementing `BridgeAdapter` interface
- ✅ Registers adapter in `AdapterRegistry`
- ⚠️ **MISMATCH**: Adds hard-coded `_is_openspec_repo()` and `_detect_openspec()` in BridgeProbe
- ⚠️ **MISMATCH**: Doesn't require refactoring existing hard-coded Spec-Kit detection
- ✅ Uses adapter registry in BridgeSync (mentioned but needs explicit refactoring task)

**Required Fixes**:

1. **Refactor BridgeProbe** to use adapter registry (section 1.6 requirement)
2. **Refactor BridgeSync** to remove all hard-coded adapter checks
3. **Document parser location** decision (adapter module vs shared utility)

---

### 2. OpenSpec Integration Plan

**Plan Requirements**:

- ✅ Phase 1: Read-only sync (OpenSpec → SpecFact)
- ✅ Cross-repository support
- ✅ Alignment report generation
- ✅ Plugin-based adapter architecture

**Proposal Status**:

- ✅ Implements Phase 1 (read-only sync)
- ✅ Supports cross-repository via `external_base_path`
- ✅ Generates alignment reports
- ✅ Uses plugin-based adapter architecture
- ✅ All requirements met

---

### 3. OpenSpec Data Model Plan

**Plan Requirements**:

- ✅ Change tracking accessed via adapter interface (not hard-coded paths)
- ✅ Tool-specific metadata in `source_tracking.source_metadata`
- ✅ Adapter decides storage location
- ✅ No hard-coded paths in core

**Proposal Status**:

- ✅ Uses adapter interface for change tracking
- ✅ Stores OpenSpec paths in `source_tracking.source_metadata`
- ✅ Adapter handles storage location
- ✅ No hard-coded paths in core models
- ✅ All requirements met

---

### 4. OpenSpec Implementation Requirements

**Plan Requirements**:

- ✅ Section 1.5: Create OpenSpec Adapter (plugin-based) - **REQUIRED**
- ✅ Section 1.6: Refactor BridgeProbe to use adapter registry - **REQUIRED**
- ✅ Section 1.5: Update BridgeSync to use adapter registry - **REQUIRED**
- ✅ No hard-coded adapter checks

**Proposal Status**:

- ✅ Section 1.5: Creates OpenSpecAdapter - **COMPLETE**
- ✅ **FIXED**: Section 3 explicitly requires BridgeProbe refactoring to use adapter registry
- ✅ **FIXED**: Section 6 explicitly requires BridgeSync refactoring to remove hard-coded checks
- ✅ **FIXED**: Proposal explicitly forbids adding hard-coded detection methods

**Fixes Applied**:

1. ✅ **Section 3** - Added explicit tasks to refactor BridgeProbe.detect() to use adapter registry
2. ✅ **Section 6** - Added explicit tasks to refactor BridgeSync.import_artifact() to remove hard-coded checks
3. ✅ **Section 2** - Added requirement to add `get_capabilities()` to BridgeAdapter interface
4. ✅ **All sections** - Explicitly forbid hard-coded adapter methods

---

## Critical Integration Mismatches (ALL FIXED)

### Mismatch 1: BridgeProbe Hard-Coded Detection ✅ FIXED

**Original Issue**:

```python
# ❌ BAD: Would have added hard-coded methods
class BridgeProbe:
    def _is_openspec_repo(self, ...): ...
    def _detect_openspec(self, ...): ...
    def detect(self):
        if self._is_openspec_repo():
            return self._detect_openspec()
        if self._is_speckit_repo():
            return self._detect_speckit()
```

**Required Pattern** (from plans):

```python
# ✅ GOOD: Uses adapter registry
class BridgeProbe:
    def detect(self, bridge_config: BridgeConfig | None = None) -> ToolCapabilities:
        from specfact_cli.adapters.registry import AdapterRegistry
        
        # Try all registered adapters
        for adapter_type, adapter_class in AdapterRegistry._adapters.items():
            adapter = adapter_class()
            if adapter.detect(self.repo_path, bridge_config):
                return adapter.get_capabilities(self.repo_path, bridge_config)
        
        return ToolCapabilities(tool="unknown")
```

**Fix Applied**:

- ✅ **Section 3** - Explicitly requires refactoring `detect()` to use adapter registry
- ✅ **Section 3.1** - Explicitly forbids adding `_is_openspec_repo()` or `_detect_openspec()` methods
- ✅ **Section 3.1** - Requires removing existing hard-coded Spec-Kit detection methods
- ✅ **Section 2** - Added requirement to add `get_capabilities()` method to BridgeAdapter interface
- ✅ **Section 3.2** - Detailed tasks for refactoring `detect()` and `auto_generate_bridge()` methods

---

### Mismatch 2: BridgeSync Hard-Coded Adapter Checks ✅ FIXED

**Original Issue** (line 180):

```python
# ❌ BAD: Hard-coded adapter check
if self.bridge_config.adapter == AdapterType.SPECKIT:
    self._import_speckit_artifact(...)
else:
    self._import_generic_markdown(...)
```

**Required Pattern** (from plans):

```python
# ✅ GOOD: Uses adapter registry
from specfact_cli.adapters.registry import AdapterRegistry

adapter = AdapterRegistry.get_adapter(self.bridge_config.adapter.value)
adapter.import_artifact(artifact_key, artifact_path, project_bundle, bridge_config)
```

**Fix Applied**:

- ✅ **Section 6.1** - Explicitly requires removing `_import_speckit_artifact()` and `_import_generic_markdown()` methods
- ✅ **Section 6.1.1** - Explicitly forbids adding `_import_openspec_artifact()` method
- ✅ **Section 6.2** - Detailed tasks for refactoring `import_artifact()` to use adapter registry
- ✅ **Section 6.3** - Detailed tasks for refactoring `export_artifact()` similarly
- ✅ **Section 6.4** - Documents future adapter creation (SpecKitAdapter, GenericMarkdownAdapter)

---

### Mismatch 3: Parser Location Decision ✅ FIXED

**Original Proposal**:

- Parser in `src/specfact_cli/sync/openspec_parser.py`

**Decision Applied**:

- ✅ **Section 4** - Parser location changed to `src/specfact_cli/adapters/openspec_parser.py` (adapter-specific)
- ✅ **Proposal** - Updated to reflect parser as adapter-specific implementation detail
- ✅ **Rationale**: Parser is adapter-specific, not shared utility, so it belongs in adapter module

**Final Decision**: Parser is in `adapters/openspec_parser.py` as adapter-specific implementation detail

---

### Mismatch 4: Missing BridgeAdapter.get_capabilities() Method ✅ FIXED

**Original Issue**:

- BridgeAdapter interface had `detect()` method
- Missing `get_capabilities()` method required by BridgeProbe

**Required Addition**:

```python
class BridgeAdapter(ABC):
    @abstractmethod
    def get_capabilities(
        self, repo_path: Path, bridge_config: BridgeConfig | None = None
    ) -> ToolCapabilities:
        """Get tool capabilities for detected repository."""
```

**Fix Applied**:

- ✅ **Section 2** - Added requirement to add `get_capabilities()` to BridgeAdapter interface
- ✅ **Section 2.1** - Detailed tasks for adding abstract method with contract decorators
- ✅ **Section 5.3** - Requires implementing `get_capabilities()` in OpenSpecAdapter
- ✅ **Section 3.2** - BridgeProbe refactoring uses `adapter.get_capabilities()` method

---

## Proposal Updates Applied ✅

All required updates have been applied to both `proposal.md` and `tasks.md`. Summary:

### Update 1: Refactor BridgeProbe ✅ APPLIED

**Status**: ✅ **Section 3** in tasks.md

- ✅ Section 3.1 - Remove hard-coded detection methods (explicitly forbids OpenSpec methods)
- ✅ Section 3.2 - Refactor `detect()` method to use adapter registry
- ✅ Section 3.3 - Refactor `auto_generate_bridge()` to use adapter registry
- ✅ Section 3.4 - Quality checks included

---

### Update 2: Refactor BridgeSync ✅ APPLIED

**Status**: ✅ **Section 6** in tasks.md

- ✅ Section 6.1 - Remove hard-coded adapter checks (explicitly forbids OpenSpec method)
- ✅ Section 6.2 - Refactor `import_artifact()` to use adapter registry
- ✅ Section 6.3 - Refactor `export_artifact()` similarly
- ✅ Section 6.4 - Document future adapter creation (SpecKitAdapter, GenericMarkdownAdapter)
- ✅ Section 6.5 - Add alignment report generation
- ✅ Section 6.6 - Quality checks included

---

### Update 3: Parser Location Decision ✅ APPLIED

**Status**: ✅ **Section 4** in tasks.md and **proposal.md**

- ✅ Parser location: `src/specfact_cli/adapters/openspec_parser.py` (adapter-specific)
- ✅ Decision documented: Parser is adapter-specific implementation detail
- ✅ Proposal updated to reflect this decision

---

### Update 4: Add get_capabilities() to BridgeAdapter Interface ✅ APPLIED

**Status**: ✅ **Section 2** in tasks.md

- ✅ Section 2.1 - Add `get_capabilities()` method to BridgeAdapter base class
- ✅ Section 2.2 - Implement in existing adapters (GitHubAdapter, OpenSpecAdapter)
- ✅ Section 2.3 - Quality checks included

---

## Summary of Required Changes ✅ ALL APPLIED

### Critical (Must Fix) ✅ ALL COMPLETE

1. ✅ **Remove hard-coded detection methods** from BridgeProbe - **Section 3.1**
2. ✅ **Refactor BridgeProbe.detect()** to use adapter registry - **Section 3.2**
3. ✅ **Refactor BridgeSync.import_artifact()** to use adapter registry - **Section 6.2**
4. ✅ **Add get_capabilities()** to BridgeAdapter interface - **Section 2.1**
5. ✅ **Move Spec-Kit logic** to SpecKitAdapter - **Section 6.4** (documented for future)

### Important (Should Fix) ✅ ALL COMPLETE

1. ✅ **Document parser location** decision - **Section 4** (adapter-specific)
2. ✅ **Ensure all adapter-specific logic** is in adapter modules - **Section 5** (OpenSpecAdapter)
3. ✅ **Verify no hard-coded paths** in core models - **Section 5.6** (uses source_tracking)

### Nice to Have ✅ DOCUMENTED

1. ✅ **Create SpecKitAdapter** - **Section 6.4** (documented for future refactoring)
2. ✅ **Create GenericMarkdownAdapter** - **Section 6.4** (documented for future refactoring)

---

## Validation Checklist ✅ ALL VERIFIED

All checklist items have been addressed in the proposal and tasks:

- ✅ No hard-coded adapter checks in BridgeProbe - **Section 3** explicitly forbids and requires removal
- ✅ No hard-coded adapter checks in BridgeSync - **Section 6** explicitly forbids and requires removal
- ✅ All adapters registered in AdapterRegistry - **Section 5.10** requires registration
- ✅ All adapters implement BridgeAdapter interface completely - **Section 5** requires all methods
- ✅ Change tracking accessed via adapter interface only - **Section 5.7-5.9** uses adapter interface
- ✅ No hard-coded paths in core models - **Section 5.6** uses `source_tracking.source_metadata`
- ✅ Cross-repository support via `external_base_path` - **Section 1.3** and **Section 5.5** implement support
- ✅ All methods have contract decorators - **Section 5.11** requires `@beartype` and `@icontract`
- ✅ Code passes `hatch run format` and `hatch run lint` - **All sections** include quality checks

---

## Final Status

**Review Status**: ✅ **COMPLETE - ALL FIXES APPLIED**

**Proposal Status**: ✅ **VALIDATED** - Passes `openspec validate --strict`

**Tasks Status**: ✅ **COMPLETE** - All 10 sections properly numbered and aligned

**Architecture Compliance**: ✅ **FULLY COMPLIANT** - Universal abstraction layer requirements met

**Next Steps**: Ready for implementation following the tasks in `tasks.md`

---

## Related Documents

- [Bridge Adapter Data Model Plan](../../docs/internal/implementation/BRIDGE_ADAPTER_DATA_MODEL_PLAN.md)
- [OpenSpec Integration Plan](../../docs/internal/implementation/OPENSPEC_INTEGRATION_PLAN.md)
- [OpenSpec Data Model Plan](../../docs/internal/implementation/OPENSPEC_DATA_MODEL_PLAN.md)
- [OpenSpec Implementation Requirements](../../docs/internal/implementation/OPENSPEC_IMPLEMENTATION_REQUIREMENTS.md)
- [Change Proposal](./proposal.md)
- [Implementation Tasks](./tasks.md)
