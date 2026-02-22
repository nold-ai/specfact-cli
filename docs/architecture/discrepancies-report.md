# SpecFact CLI Architecture Discrepancies Report

## Executive Summary

This report identifies discrepancies, conflicts, misalignments, and ambiguities between the SpecFact CLI documentation, codebase, and specifications. These findings require follow-up to ensure architectural consistency.

## Methodology

1. **Documentation Review**: Analyzed existing docs in `docs/reference/architecture.md` and related files
2. **Codebase Analysis**: Examined core components in `src/specfact_cli/` and module structure
3. **Spec Review**: Reviewed OpenSpec changes in `openspec/changes/` and derived specs
4. **Cross-Referencing**: Compared claims across all three sources

## Critical Discrepancies

### 1. Module System Implementation vs Documentation

**Issue**: Documentation claims module system is "transitioning" but code shows it's fully implemented

**Evidence**:

- **Docs** (`docs/reference/architecture.md`): "SpecFact is transitioning from hard-wired command wiring to a module-first architecture"
- **Code** (`src/specfact_cli/registry/`): Fully functional module registry with lazy loading
- **Specs** (`openspec/changes/architecture-01-solution-layer/`): No mention of transition state

**Impact**: High - Creates confusion about current state and stability

**Recommendation**: Update documentation to reflect that module system is production-ready since v0.27

### 2. Bridge Adapter Interface Mismatch

**Issue**: Documentation shows incomplete BridgeAdapter interface compared to actual implementation

**Evidence**:

- **Docs**: Shows basic `detect()`, `import_artifact()`, `export_artifact()` methods
- **Code** (`src/specfact_cli/adapters/base.py`): Includes additional `load_change_tracking()`, `save_change_tracking()` methods
- **Specs** (`openspec/changes/architecture-01-solution-layer/specs/data-models/spec.md`): References change tracking capabilities

**Impact**: Medium - Developers may implement incomplete adapters

**Recommendation**: Update documentation to include full v0.21.1+ BridgeAdapter interface with change tracking methods

### 3. Operational Modes Documentation Gap

**Issue**: Documentation describes CI/CD and CoPilot modes but lacks implementation details

**Evidence**:

- **Docs**: Describes mode detection and characteristics
- **Code** (`src/specfact_cli/modes/`): Only `detector.py` exists, no actual mode-specific implementations
- **Specs**: No specific mode-related specifications found

**Impact**: Medium - Users expect mode-specific behavior that may not exist

**Recommendation**: Either implement full mode support or clarify current limitations in documentation

### 4. Architecture Layer Mismatch

**Issue**: Documentation describes 3 layers but code shows more complex structure

**Evidence**:

- **Docs**: "Specification Layer", "Contract Layer", "Enforcement Layer"
- **Code**: Additional layers like "Adapter Layer", "Analysis Layer", "Module Layer"
- **Specs**: References "Solution Architecture" layer not mentioned in docs

**Impact**: Medium - Architectural understanding mismatch

**Recommendation**: Update architecture documentation to reflect actual layer structure

## Documentation vs Code Discrepancies

### 5. Command Registry Implementation Details

**Issue**: Documentation lacks details on CommandRegistry implementation

**Evidence**:

- **Docs**: High-level description only
- **Code** (`src/specfact_cli/registry/registry.py`): Complex lazy loading with metadata caching
- **Specs**: No registry-specific specifications

**Impact**: Medium - Developers need implementation details for extensions

**Recommendation**: Add detailed CommandRegistry documentation with code examples

### 6. Module Package Structure

**Issue**: Documentation doesn't specify required module structure

**Evidence**:

- **Docs**: Mentions `module-package.yaml` but no structure details
- **Code** (`src/specfact_cli/modules/*/`): Consistent structure across all modules
- **Specs**: No module structure specifications

**Impact**: Low - Developers may create inconsistent module structures

**Recommendation**: Document required module package structure and naming conventions

### 7. Adapter Capabilities

**Issue**: Documentation doesn't explain ToolCapabilities model

**Evidence**:

- **Docs**: No mention of capabilities system
- **Code** (`src/specfact_cli/models/bridge.py`): Full ToolCapabilities model with sync modes
- **Specs**: References adapter capabilities in sync scenarios

**Impact**: Medium - Adapter developers unaware of capabilities system

**Recommendation**: Document ToolCapabilities model and its role in adapter selection

## Specification vs Implementation Discrepancies

### 8. Architecture Derive Command

**Issue**: Spec defines `specfact architecture derive` but no implementation exists

**Evidence**:

- **Docs**: No mention of architecture commands
- **Code**: No architecture-related commands found
- **Specs** (`openspec/changes/architecture-01-solution-layer/specs/solution-architecture/spec.md`): Defines derive, validate, trace commands

**Impact**: High - Spec defines non-existent functionality

**Recommendation**: Either implement architecture commands or update specs to match current capabilities

### 9. Change Tracking Implementation

**Issue**: Specs reference change tracking but implementation is partial

**Evidence**:

- **Docs**: Mentions change tracking in data models
- **Code**: ChangeTracking models exist but limited adapter support
- **Specs**: Extensive change tracking scenarios defined

**Impact**: Medium - Users expect change tracking features that are partially implemented

**Recommendation**: Document current change tracking limitations and roadmap

### 10. Protocol FSM Implementation

**Issue**: Specs define protocol FSM but implementation is minimal

**Evidence**:

- **Docs**: Shows protocol FSM diagrams
- **Code**: Basic ProtocolSpec model exists but no FSM engine
- **Specs**: Detailed FSM scenarios with guards and transitions

**Impact**: Medium - Protocol functionality is more limited than specs suggest

**Recommendation**: Implement FSM engine or update specs to match current implementation

## Documentation Quality Issues

### 11. Incomplete Mermaid Diagrams

**Issue**: Some diagrams reference components that don't exist

**Evidence**:

- **Docs**: Shows "DevOps Adapters" in component graph
- **Code**: No DevOps adapter implementation found
- **Specs**: No DevOps adapter specifications

**Impact**: Low - Confusing but doesn't affect functionality

**Recommendation**: Remove or implement referenced components

### 12. Outdated Performance Metrics

**Issue**: Documentation shows outdated performance numbers

**Evidence**:

- **Docs**: "Typical execution: < 10s" for various operations
- **Code**: Actual performance is significantly better (sub-second for most operations)
- **Specs**: No performance specifications

**Impact**: Low - Sets incorrect expectations

**Recommendation**: Update performance metrics with current benchmarks

### 13. Missing Error Handling Documentation

**Issue**: Documentation lacks error handling patterns

**Evidence**:

- **Docs**: No error handling section
- **Code**: Comprehensive error handling with custom exceptions
- **Specs**: Some error scenarios defined

**Impact**: Medium - Developers unaware of error handling conventions

**Recommendation**: Add error handling patterns and best practices documentation

## Code vs Spec Discrepancies

### 14. Missing Architecture Module

**Issue**: Specs define architecture capabilities but no architecture module exists

**Evidence**:

- **Docs**: No architecture module mentioned
- **Code**: No `modules/architecture/` directory
- **Specs**: Detailed architecture requirements defined

**Impact**: High - Architecture functionality completely missing

**Recommendation**: Create architecture module or remove architecture specs

### 15. Incomplete Bridge Adapter Implementations

**Issue**: Some adapters referenced in specs don't exist

**Evidence**:

- **Docs**: Mentions GitHub, ADO adapters
- **Code**: Only OpenSpec and SpecKit adapters implemented
- **Specs**: References multiple adapter types

**Impact**: Medium - Users expect adapters that don't exist

**Recommendation**: Implement missing adapters or update documentation

### 16. Protocol Validation Gaps

**Issue**: Specs define protocol validation that isn't fully implemented

**Evidence**:

- **Docs**: Shows protocol validation concepts
- **Code**: Basic protocol models but no validation engine
- **Specs**: Detailed protocol validation scenarios

**Impact**: Medium - Protocol functionality is incomplete

**Recommendation**: Implement protocol validation or update specs

## Consistency Issues

### 17. Terminology Inconsistencies

**Issue**: Different terms used for same concepts

**Evidence**:

- **Docs**: "Project Bundle", "Plan Bundle"
- **Code**: `ProjectBundle`, `PlanBundle` classes
- **Specs**: Uses both terms interchangeably

**Impact**: Low - Confusing but understandable

**Recommendation**: Standardize terminology across all sources

### 18. Version Numbering Conflicts

**Issue**: Inconsistent version references

**Evidence**:

- **Docs**: References v0.21.1 features
- **Code**: Current version is v0.35.0
- **Specs**: Mixed version references

**Impact**: Low - Version confusion

**Recommendation**: Use consistent version references or remove specific versions

### 19. Feature Maturity Mismatch

**Issue**: Features described as "experimental" are actually production-ready

**Evidence**:

- **Docs**: Calls module system "experimental"
- **Code**: Module system is fully implemented and tested
- **Specs**: No experimental designation

**Impact**: Medium - Understates feature readiness

**Recommendation**: Update documentation to reflect actual maturity level

## Missing Documentation

### 20. No Architecture Decision Records

**Issue**: No ADRs documented for major architectural decisions

**Evidence**:

- **Docs**: No ADR section
- **Code**: Major architectural patterns implemented
- **Specs**: Architectural decisions referenced

**Impact**: High - Loss of architectural context

**Recommendation**: Create ADR documentation for major decisions

### 21. Missing Module Development Guide

**Issue**: No guide for developing new modules

**Evidence**:

- **Docs**: No module development documentation
- **Code**: Module development patterns established
- **Specs**: No module development specifications

**Impact**: High - Developers lack guidance for extensions

**Recommendation**: Create comprehensive module development guide

### 22. No Adapter Development Guide

**Issue**: No documentation for creating new adapters

**Evidence**:

- **Docs**: No adapter development section
- **Code**: Adapter patterns established
- **Specs**: Adapter requirements defined

**Impact**: High - Adapter developers lack guidance

**Recommendation**: Create adapter development guide with examples

## Implementation Gaps

### 23. Missing Architecture Commands

**Issue**: Architecture specs define commands that don't exist

**Evidence**:

- **Docs**: No architecture commands documented
- **Code**: No architecture command implementations
- **Specs**: `specfact architecture derive/validate/trace` defined

**Impact**: High - Spec defines non-existent functionality

**Recommendation**: Implement architecture commands or remove specs

### 24. Partial Change Tracking

**Issue**: Change tracking partially implemented

**Evidence**:

- **Docs**: Mentions change tracking capabilities
- **Code**: ChangeTracking models exist, limited adapter support
- **Specs**: Full change tracking workflows defined

**Impact**: Medium - Incomplete feature implementation

**Recommendation**: Complete change tracking implementation or document limitations

### 25. Incomplete Protocol Support

**Issue**: Protocol FSM defined but not fully implemented

**Evidence**:

- **Docs**: Shows protocol FSM diagrams
- **Code**: Basic protocol models, no FSM engine
- **Specs**: Detailed FSM scenarios

**Impact**: Medium - Protocol functionality limited

**Recommendation**: Implement FSM engine or update documentation

## Recommendations Summary

### High Priority (Critical Issues)

1. **Update module system documentation** to reflect production-ready status
2. **Implement architecture commands** or remove architecture specs
3. **Create ADR documentation** for major architectural decisions
4. **Develop module development guide** with patterns and best practices
5. **Create adapter development guide** with implementation examples

### Medium Priority (Important Issues)

1. **Update BridgeAdapter documentation** with full interface including change tracking
2. **Clarify operational modes** - implement fully or document current limitations
3. **Document ToolCapabilities model** and adapter selection process
4. **Complete change tracking implementation** or document current limitations
5. **Implement protocol FSM engine** or update specs to match implementation

### Low Priority (Nice to Have)

1. **Fix terminology inconsistencies** across documentation
2. **Update performance metrics** with current benchmarks
3. **Add error handling documentation** with patterns and best practices
4. **Remove references to non-existent components** from diagrams
5. **Standardize version references** or remove specific versions

## Follow-Up Plan

### Phase 1: Critical Fixes (Next 2 Weeks)

- [ ] Update module system documentation
- [ ] Create ADR documentation template
- [ ] Develop module development guide
- [ ] Create adapter development guide
- [ ] Review architecture specs vs implementation

### Phase 2: Documentation Enhancements (Next Month)

- [ ] Update BridgeAdapter interface documentation
- [ ] Clarify operational modes documentation
- [ ] Document ToolCapabilities model
- [ ] Add error handling patterns documentation
- [ ] Update performance metrics

### Phase 3: Implementation Gaps (Next Quarter)

- [ ] Implement architecture commands (or remove specs)
- [ ] Complete change tracking implementation
- [ ] Implement protocol FSM engine
- [ ] Add missing adapters (GitHub, ADO)
- [ ] Enhance protocol validation

## Monitoring and Maintenance

### Ongoing Processes

1. **Pre-Commit Documentation Checks**: Add documentation validation to CI
2. **Spec-Code Sync Reviews**: Regular reviews to ensure spec-code alignment
3. **Documentation First**: Require documentation updates with code changes
4. **Change Impact Analysis**: Assess documentation impact of all changes
5. **User Feedback Loop**: Collect and address documentation feedback

### Success Metrics

- **Documentation Coverage**: 100% of public APIs documented
- **Spec-Code Alignment**: < 5% discrepancy rate
- **User Satisfaction**: Documentation quality ratings
- **Issue Reduction**: Decrease in documentation-related issues
- **Update Frequency**: Regular documentation updates with releases

## Conclusion

This analysis identified 25 specific discrepancies between SpecFact CLI documentation, code, and specifications. The most critical issues involve:

1. **Module system documentation** not reflecting current implementation
2. **Missing architecture functionality** defined in specs but not implemented
3. **Lack of development guides** for modules and adapters
4. **Incomplete interface documentation** for key components
5. **Terminology inconsistencies** causing confusion

Addressing these discrepancies will significantly improve developer experience, reduce confusion, and ensure architectural consistency across the codebase.
