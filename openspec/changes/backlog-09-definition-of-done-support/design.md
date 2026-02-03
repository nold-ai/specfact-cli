# Design: Definition of Done (DoD) support

## DoD config and validator

- **Config**: DoD config schema (e.g. YAML) with checklist items (e.g. tests_pass, docs_updated, code_reviewed). Store in `.specfact/dod.yaml` or under project templates. Reuse patterns from DoR (framework-specific rules, provider-agnostic where possible).
- **Validator**: Function that takes a BacklogItem (state=Done) and DoD config, runs the checklist (e.g. by checking item fields or linked artifacts), returns pass/fail and list of failed criteria. New public APIs shall have @icontract and @beartype.
- **Integration**: Hook into backlog list/refine/export; when items are in Done state and DoD is enabled, run validator and attach DoD status to output/export. Expose optionally via `specfact backlog list`, `specfact backlog refine`, or a dedicated `specfact backlog dod` / `specfact backlog validate` subcommand under the backlog group (no top-level DoD command).

## Sequence (DoD validation for done items)

```
User → specfact backlog list --dod (or specfact backlog dod)
  → CLI loads .specfact/dod.yaml (if present)
  → CLI fetches backlog items (existing adapter)
  → For each item in Done state: run DoD validator(item, config)
  → Attach DoD status (pass/fail, failed criteria) to item
  → Output/export includes DoD status per done item
```

## Contract enforcement

- DoD config loader and validator shall have @icontract and @beartype.
- Backlog command integration: optional flag (e.g. `--dod`) to enable DoD; default off for backward compatibility.

## Fallback / offline

- DoD config is read from local project; no network required for config load. Validation may require item data already fetched by backlog adapter (offline if cache present).
