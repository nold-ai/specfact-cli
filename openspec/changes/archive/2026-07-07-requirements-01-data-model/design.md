## Context

This change implements `requirements-01-data-model` as a validation input model. Upstream tools remain the systems of record for requirement intent; SpecFact only stores normalized references and evidence links needed for deterministic validation, drift checks, and downstream adapters.

## Goals / Non-Goals

**Goals:**

- Define a compact, source-reference-first requirement input model.
- Keep compatibility with existing ProjectBundle schema extensions.
- Preserve offline-first behavior and deterministic validation evidence.
- Avoid taking ownership of product-management or requirement-authoring workflows.

**Non-Goals:**

- No interactive requirement authoring commands.
- No bidirectional backlog sync.
- No required ProjectBundle schema field.
- No dependency expansion beyond existing Pydantic, icontract, and beartype runtime dependencies.

## Decisions

- Represent upstream sources explicitly with `RequirementSourceReference` so evidence can point back to issues, docs, OpenSpec changes, Spec Kit artifacts, or local files.
- Store requirement inputs as ordinary Pydantic models and let import adapters populate them later.
- Use the existing ProjectBundle `extensions` field with namespace `requirements.inputs`; do not add a first-class required ProjectBundle field.
- Keep helper APIs contract-first with `@icontract` and `@beartype`.
- Treat profile-aware completeness as evidence severity data, not a hard authoring workflow.

## Risks / Trade-offs

- [Scope creep into planning workflow] -> Mitigation: docs and specs state that SpecFact consumes requirement context; it does not own authoring.
- [ProjectBundle compatibility regression] -> Mitigation: use optional extension storage and regression tests for bundles without extensions.
- [Evidence ambiguity] -> Mitigation: require source references and stable IDs on requirement input records.

## Migration Plan

1. Align proposal, tasks, and spec deltas to the validation-evidence framing.
2. Add tests from spec scenarios and capture failing-first evidence.
3. Implement minimal model and export changes needed for passing scenarios.
4. Update docs, changelog, and version files.
5. Run quality gates, code review, and OpenSpec validation before PR.

## Open Questions

- GitHub issue hierarchy metadata for issue #238 does not expose parent/blocker fields through `gh issue view`; the roadmap places it under Requirements Layer / Epic #256 and notes the older arch-07 dependency.
