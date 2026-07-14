# TDD Evidence: openspec-01-intent-trace

**Date**: 2026-07-13 (Europe/Berlin)

## Failing Before Production Code

```text
$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py -q
ImportError: cannot import name 'import_openspec_change' from 'specfact_cli.requirements'
```

The test was added after the OpenSpec delta defined native import, content-hash,
read-only, gate, and profile-mapping behavior. It failed during collection
because the core normalizers did not yet exist.

## Iteration Finding

```text
$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py tests/unit/requirements/test_context_adapter.py -q
1 failed, 11 passed
KeyError: 'code'
```

The expanded deterministic-gate test exposed that the pre-existing
missing-evidence finding lacked a machine-readable category. The implementation
now emits `missing-evidence` without changing its severity, message, or
location contract.

## Passing After Production Code

```text
$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py tests/unit/requirements/test_context_adapter.py -q
12 passed in 0.47s
```

The passing run covers OpenSpec and Spec Kit normalization, deterministic IDs,
GIVEN/WHEN/THEN preservation, `sha256:` revisions, read-only source behavior,
all four import gates, explicit-profile precedence, layered-profile resolution,
and the evidence-compatible required-field mapping.

## Compatibility Boundary: Failing Before Preflight

```text
$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py -q
3 failed, 5 passed
```

The new tests proved that custom OpenSpec schemas, Spec Kit template
customization roots, and unrecognized Markdown markers were previously
accepted or silently returned no records without an explanatory diagnostic.

## Compatibility Boundary: Passing After Preflight

```text
$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py tests/unit/requirements/test_context_adapter.py -q
18 passed in 0.98s
```

The compatibility tests cover default profile acceptance, project- and
change-local OpenSpec schema rejection, all supported Spec Kit customization
root rejections, unknown Markdown markers, and the no-partial-records
contract for `unsupported-source-schema`.

## PR #646 Review Remediation Evidence (2026-07-13)

### Failing-first

```text
$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py -q
7 failed, 11 passed
```

The failures covered non-string OpenSpec schema declarations, duplicate derived
OpenSpec/Spec Kit identities, project-root-relative source locators, and
malformed optional configuration.

### Passing-after

```text
$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py tests/unit/requirements/test_context_adapter.py -q
25 passed
```

The explicit-profile regression assertion also remains green: configured
profile-derived schema fields cannot override an explicitly passed profile.

### Invalid UTF-8 Schema Remediation (2026-07-13)

```text
$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py::test_import_openspec_change_rejects_invalid_utf8_schema_without_partial_records -q
1 failed (UnicodeDecodeError escaped from config.yaml decoding)

$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py tests/unit/requirements/test_context_adapter.py -q
26 passed
```

Invalid UTF-8 in an OpenSpec schema configuration now produces the same
`unsupported-source-schema` fail-closed result as malformed YAML or a
non-string schema declaration.

## PR #647 Review Remediation Evidence (2026-07-14)

### Failing-first

```text
$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py::test_import_openspec_change_preserves_wrapped_scenario_clauses tests/unit/requirements/test_upstream_evidence_imports.py::test_import_speckit_feature_reports_malformed_requirement_entries tests/unit/requirements/test_upstream_evidence_imports.py::test_validation_ignores_invalid_utf8_optional_config -q
3 failed
```

The failures proved that wrapped OpenSpec clauses were truncated, malformed
Spec Kit requirement entries were silently dropped, and binary optional profile
configuration raised `UnicodeDecodeError`.

### Passing-after

```text
$ hatch run pytest tests/unit/requirements/test_upstream_evidence_imports.py tests/unit/requirements/test_context_adapter.py -q
29 passed
```

The review remediation preserves Markdown clause continuations, emits bounded
warnings for malformed Spec Kit entries, and tolerates invalid UTF-8 in
optional profile configuration.

## Final Gate Evidence

```text
$ hatch run smart-test
2847 passed, 10 skipped; 64.0% coverage (local `fail_under = 50` threshold)

This local result is not evidence that the PR's 80% CI quality-gate threshold
has passed. At the time recorded, the PR Tests job also failed first on the
unrelated `test_contracts_include_parameters` integration regression, so its
dependent Quality Gates job did not run. Coverage remediation is repository-wide
work outside this import-adapter change; this change adds targeted tests for all
new adapter paths.

$ hatch run contract-test
Runtime contracts: PASS; contract exploration: PASS; scenario tests: 21 passed

$ hatch run specfact code review run --json --out .specfact/code-review.json
Review completed with no findings.

$ hatch run semgrep-sast --json --output logs/static-analysis/semgrep.json
$ hatch run semgrep-sast-gate --results logs/static-analysis/semgrep.json --baseline tools/semgrep/sast-baseline.json
0 current findings; no new findings outside baseline

$ hatch run bandit-scan
No medium or high issues identified.
```
