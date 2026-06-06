## 1. Governance

- [x] 1.1 Create GitHub issue #565 with labels, parent Feature #353, and proposal source tracking.
- [x] 1.2 Keep internal wiki source tracking aligned for `module-scope-version-diagnostics`.

## 2. Specs and Tests

- [x] 2.1 Add OpenSpec proposal, design, and spec deltas for diagnostics and version enforcement.
- [x] 2.2 Add failing tests for module doctor duplicate-scope diagnostics.
- [x] 2.3 Add failing tests for install-time versioned bundle dependency enforcement.
- [x] 2.4 Add failing tests for registration-time versioned module dependency enforcement.

## 3. Implementation

- [x] 3.1 Implement `specfact module doctor`.
- [x] 3.2 Enforce versioned bundle dependency declarations during install.
- [x] 3.3 Enforce versioned module dependency declarations during registration and lifecycle checks.
- [x] 3.4 Update module docs with duplicate-scope remediation guidance.

## 4. Evidence and Gates

- [x] 4.1 Record failing-before and passing-after test evidence in `TDD_EVIDENCE.md`.
- [x] 4.2 Run targeted tests for touched module registry/installer behavior.
- [x] 4.3 Run required scoped quality gates and SpecFact code review.
