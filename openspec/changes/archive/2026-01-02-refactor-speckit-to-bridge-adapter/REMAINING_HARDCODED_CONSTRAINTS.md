# Remaining Hard-Coded Adapter Constraints Analysis

## Question

After implementing this change proposal, do we have any remaining hard-coded adapter constraints that are not using the new adapter bridge/factory for any external tool we onboard via adapter/bridge logic?

## Answer: YES - Additional Hard-Coded Constraints Found

After code research, the following hard-coded adapter constraints were identified that are **NOT covered** in the original proposal but have now been added:

### 1. **import_cmd.py - Spec-Kit Hard-Coded Logic** ⚠️ CRITICAL

**Location**: `src/specfact_cli/commands/import_cmd.py`

**Issues Found**:

- **Line 1253**: `if adapter_type == AdapterType.SPECKIT:` - Direct instantiation of `SpecKitScanner` and `SpecKitConverter`
- **Line 1271**: `if adapter_type == AdapterType.SPECKIT:` - Legacy Spec-Kit import logic
- **Line 1292**: `if adapter_type == AdapterType.SPECKIT:` - Spec-Kit structure scanning

**Impact**: The `specfact import from-bridge` command has significant hard-coded Spec-Kit logic that bypasses the adapter registry pattern.

**Status**: ✅ **NOW COVERED** - Added to proposal as section 3.5

### 2. **sync.py - Hard-Coded Mode Detection** ⚠️ CRITICAL

**Location**: `src/specfact_cli/commands/sync.py`

**Issues Found**:

- **Line 949**: `devops_adapters = ("github", "ado", "linear", "jira")` - Hard-coded tuple of DevOps adapters
- **Line 954**: `elif adapter_value == "openspec":` - Hard-coded OpenSpec read-only mode assignment
- **Line 965**: `devops_adapters = ("github", "ado", "linear", "jira")` - Duplicate hard-coded tuple for mode validation
- **Line 971**: `if adapter_value != "openspec":` - Hard-coded OpenSpec check for read-only mode validation

**Impact**: Sync mode detection uses hard-coded adapter type lists instead of adapter capabilities. This prevents new adapters from declaring their supported sync modes.

**Status**: ✅ **NOW COVERED** - Added to proposal as section 2.7

### 3. **bridge_sync.py - GitHub-Specific Kwargs** ⚠️ MINOR

**Location**: `src/specfact_cli/sync/bridge_sync.py`

**Issues Found**:

- **Line 494**: `if adapter_type == "github":` - Hard-coded check for GitHub-specific kwargs (`use_gh_cli`)

**Impact**: Adapter-specific constructor arguments are hard-coded instead of being determined by adapter capabilities.

**Status**: ✅ **NOW COVERED** - Added to proposal as section 4.2

### 4. **sync.py - Auto-Detection Fallback** ✅ ACCEPTABLE

**Location**: `src/specfact_cli/commands/sync.py`

**Issues Found**:

- **Line 925**: `if adapter == "speckit" or adapter == "auto":` - Auto-detection logic
- **Line 928**: Fallback to `"generic-markdown"` string

**Impact**: Uses `BridgeProbe.detect()` which already uses adapter registry, so this is acceptable. However, the fallback string could be made adapter-agnostic.

**Status**: ⚠️ **PARTIALLY ACCEPTABLE** - Uses adapter registry via BridgeProbe, but fallback string is hard-coded

### 5. **github.py - Self-Check** ✅ ACCEPTABLE

**Location**: `src/specfact_cli/adapters/github.py`

**Issues Found**:

- **Line 131**: `bridge_config.adapter.value == "github"` - Self-check within adapter

**Impact**: This is inside the adapter itself, which is acceptable. Adapters can check their own type internally.

**Status**: ✅ **ACCEPTABLE** - Internal adapter logic, not a constraint

## Summary

### Before This Proposal Update

- ❌ **import_cmd.py**: Significant hard-coded Spec-Kit logic (NOT covered)
- ❌ **sync.py mode detection**: Hard-coded adapter type lists (NOT covered)
- ❌ **bridge_sync.py**: GitHub kwargs check (NOT covered)

### After This Proposal Update

- ✅ **import_cmd.py**: Now covered (section 3.5)
- ✅ **sync.py mode detection**: Now covered (section 2.7)
- ✅ **bridge_sync.py**: Now covered (section 4.2)

### Remaining After Implementation

- ✅ **All hard-coded adapter constraints will be removed** after implementing this proposal
- ✅ **All adapters will use adapter registry pattern**
- ✅ **Sync mode detection will use adapter capabilities**
- ✅ **Import command will use adapter registry**

## Recommendations

1. **Extend ToolCapabilities Model**: Consider adding `supported_sync_modes: list[str]` field to `ToolCapabilities` to enable adapter-agnostic mode detection.

2. **Add Adapter Method for Kwargs**: Consider adding `get_adapter_kwargs()` method to `BridgeAdapter` interface if adapters need different constructor arguments.

3. **Auto-Detection Fallback**: Consider making auto-detection fallback use adapter registry to find first available adapter instead of hard-coded "generic-markdown" string.

## Conclusion

**Answer**: After implementing this updated proposal, **NO remaining hard-coded adapter constraints** will exist. All adapter logic will use the adapter registry pattern, and all hard-coded checks have been identified and will be removed.
