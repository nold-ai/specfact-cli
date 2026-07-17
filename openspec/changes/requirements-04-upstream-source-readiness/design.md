## Context

Core native importers currently parse OpenSpec and Spec Kit artifacts directly
into `RequirementContextImportResult`. They already fail closed for unsupported
schemas, but a pristine official Spec Kit template meets the current structural
pattern and emits placeholder requirement records. The modules runtime cannot
solve this safely: it delegates to these core importers and must not own native
parsing, hashes, or gate policy.

OpenSpec supplies `openspec validate --strict --json` for native validation.
Spec Kit 0.12.15 exposes setup and tool checks but no feature-artifact validator,
so source readiness must inspect its documented native artifact content without
becoming an authoring schema.

## Goals / Non-Goals

**Goals:**

- Return accepted records or zero records with structured error diagnostics.
- Reject known incomplete Spec Kit sources before normalization.
- Support explicit/strict-policy OpenSpec native validation without a mandatory
  executable dependency for portable imports.
- Preserve existing valid import behavior, source hashes, idempotency, and
  read-only source access.

**Non-Goals:**

- Create or require metadata owned by OpenSpec or Spec Kit.
- Write validation results into upstream folders.
- Treat `specify check` as a source validator.
- Detect every semantic ambiguity in prose.
- Move source-readiness policy into the modules repository.

## Decisions

### Return one atomic result from existing importers

`import_openspec_change` and `import_speckit_feature` SHALL evaluate readiness
before returning normalized records. Any error-level readiness diagnostic yields
an empty `RequirementContextImportResult.requirements` collection. Existing
diagnostic fields remain the cross-repository contract used by the Requirements
module.

This reuses the current result model and prevents a rejected source from being
partially persisted. Filtering records only after normalization is rejected
because placeholder records could leak to any other core caller.

### Detect only narrow, source-native incompleteness markers for Spec Kit

The preflight SHALL recognise the official scaffold markers observed in the
supported Spec Kit profile, unresolved `NEEDS CLARIFICATION`, absent substantive
Functional Requirements, and absent meaningful acceptance scenarios when user
stories are present. It SHALL return `incomplete-source-template` for known
template markers and `source-incomplete` for missing required native content.

Detection uses explicit marker rules plus fixture coverage, not a whole-template
hash or generic bracket matching. This keeps ordinary requirement prose valid
and makes upstream template changes visible through compatibility tests.

### Gate OpenSpec CLI validation by explicit policy

The readiness policy SHALL determine whether native OpenSpec validation is
required. When required, core invokes `openspec validate --strict --json` with
bounded process execution and consumes its machine-readable outcome. A failed
validator returns `source-invalid`; a missing executable returns
`upstream-validator-unavailable`. Both are error-level, atomic failures.

The policy is the layered `validation.openspec.require_native_validation`
boolean. Resolve configuration from organization baseline, repository overlay,
then developer-local overlay; the last explicit boolean wins. If no layer sets
the key, the effective validation tier supplies the default: `enterprise` is
`true`, while `solo`, `startup`, and `mid_size` are `false`. The `strict` and
`enterprise_full_stack` aliases resolve to `enterprise`; `team` and
`api_first_team` resolve to `mid_size`.

An explicit `profile` argument chooses the tier default but does not discard an
explicit boolean from a configuration layer. Therefore native validation is
mandatory only when the resolved boolean is `true`; otherwise the importer is
portable and must not invoke an ambient executable.

When policy does not require native validation, importer behavior remains
portable and does not probe an ambient `openspec` executable. Always probing is
rejected because the same source could produce different evidence merely due to
developer PATH state.

### Keep readiness and downstream evidence gates distinct

Readiness decides whether a source may become evidence. Existing validation
gates (`scenario-unverified`, `stale-import`, `source-missing`, and
`ambiguous-mapping`) continue to evaluate accepted records after import.
Readiness failures are import diagnostics, not downstream evidence findings.

## Risks / Trade-offs

- [Spec Kit template drift] → Pin a current official scaffold fixture and add a
  scheduled compatibility test against the supported upstream release.
- [False positives from ordinary bracketed prose] → Detect only narrow known
  markers and add a legitimate bracketed-prose regression fixture.
- [Unavailable OpenSpec CLI] → Fail only when policy explicitly requires it;
  otherwise preserve portable importer behavior.
- [Subprocess output or timeout variation] → Consume JSON, bound execution, and
  surface a stable diagnostic rather than raw tool output as contract data.
- [Core/module release skew] → Publish this core contract before the modules
  patch; modules raises its compatibility floor and preserves the diagnostics.

## Migration Plan

1. Add core specs, failing tests, and the readiness implementation.
2. Release the core version containing the new contract.
3. Unblock modules issue #346; update module compatibility, command tests,
   signature, and patch release.
4. Roll back by pinning the modules runtime to the prior core-compatible module;
   readiness never mutates upstream sources or existing accepted sidecars.

## Compatibility Baseline

The initial official Spec Kit scaffold fixture is pinned to `v0.12.18`. The
previously observed `v0.12.15` placeholder import remains regression context,
not the supported compatibility baseline.
